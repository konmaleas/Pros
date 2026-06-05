"""Batch orchestration: group directories into projects/cases, analyse, report."""
import json
import re
import traceback
from collections import defaultdict
from datetime import datetime as dt2
from pathlib import Path
from typing import Dict, List

from icecream import ic

from ..core import MultiFilePatternAnalyzer
from ..models import CaseResult, ProjectResults
from .stages import extract_and_process


def ict():
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


def load_directory_list(file_path: Path) -> List[str]:
    """Load directory paths from the text file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def group_by_projects(dir_list: List[str]) -> Dict[str, List[str]]:
    """Group directories by project and cases.

    Returns:
        Dict mapping project_path -> list of case paths
    """
    projects = defaultdict(list)

    for dir_path in dir_list:
        path = Path(dir_path)

        parts = path.parts
        process_idx = parts.index('Process') if 'Process' in parts else -1

        if process_idx == -1:
            continue

        depth_from_process = len(parts) - process_idx - 1

        if depth_from_process == 1:
            projects[dir_path] = []
        elif depth_from_process == 2:
            project_path = str(path.parent)
            projects[project_path].append(dir_path)

    final_projects = {}
    for project_path, cases in projects.items():
        if not cases:
            final_projects[project_path] = [project_path]
        else:
            final_projects[project_path] = cases

    return final_projects


def get_pdf_files(directory: Path) -> List[Path]:
    """Get all PDF files in a directory."""
    if not directory.exists():
        return []
    return [f for f in directory.iterdir() if f.is_file() and f.suffix.lower() == '.pdf']


def infer_title_from_filename(pdf_path: Path) -> str:
    """Infer title from PDF filename by splitting on non-alphanumeric characters.

    Example: NCMDDL1DRARC4439P1.pdf -> NCM-DD-L1-DR-ARC-4439-P1
    """
    filename = pdf_path.stem
    chunks = re.findall(r'[A-Za-z0-9]+', filename)
    return '-'.join(chunks) if chunks else filename


def process_case(case_path: str) -> CaseResult:
    """Process a single case directory.

    Args:
        case_path: Path to the case directory containing PDFs

    Returns:
        CaseResult with processing details
    """
    start = dt2.now()
    case_dir = Path(case_path)

    ic(ict(), f"Processing case: {case_path}")

    pdf_files = get_pdf_files(case_dir)

    if not pdf_files:
        return CaseResult(case_path=case_path, pdf_count=0, success=False, error_message="No PDF files found")

    ic(ict(), f"Found {len(pdf_files)} PDF files")

    first_pdf = pdf_files[0]
    title = infer_title_from_filename(first_pdf)
    ic(ict(), f"Inferred title: {title}")

    try:
        analyzer = MultiFilePatternAnalyzer(title=title, files=pdf_files)
        results = analyzer.analyze_all_files(extract_and_process)

        template_file = ""
        files_with_patterns = 0

        for filename, result in results.items():
            if result.template_file:
                template_file = filename
            if result.total_chunks_found > 0:
                files_with_patterns += 1

        processing_time = (dt2.now() - start).total_seconds()

        return CaseResult(case_path=case_path, pdf_count=len(pdf_files), success=True, inferred_title=title,
                template_file=template_file, total_files_analyzed=len(results), files_with_patterns=files_with_patterns,
                stable_anchors_found=0,
                processing_time=processing_time)

    except Exception as e:
        processing_time = (dt2.now() - start).total_seconds()
        error_details = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        ic(ict(), f"ERROR processing case {case_path}:")
        ic(ict(), error_details)
        return CaseResult(case_path=case_path, pdf_count=len(pdf_files), success=False, inferred_title=title,
                error_message=error_details, processing_time=processing_time)


def process_all_projects(projects: Dict[str, List[str]]) -> List[ProjectResults]:
    """Process all projects and their cases.

    Args:
        projects: Dict mapping project_path -> list of case paths

    Returns:
        List of ProjectResults
    """
    all_results = []

    for project_path, cases in projects.items():
        project_name = Path(project_path).name
        ic(ict(), f"\n{'=' * 80}")
        ic(ict(), f"PROJECT: {project_name}")
        ic(ict(), f"Cases: {len(cases)}")

        project_result = ProjectResults(project_name=project_name, project_path=project_path)

        for case_path in cases:
            case_result = process_case(case_path)
            project_result.cases.append(case_result)
            project_result.total_pdfs += case_result.pdf_count

            if case_result.success:
                project_result.successful_cases += 1
            else:
                project_result.failed_cases += 1

        all_results.append(project_result)

        ic(ict(),
           f"Project Summary: {project_result.successful_cases} successful, {project_result.failed_cases} failed")

    return all_results


def generate_report(results: List[ProjectResults], output_path: Path):
    """Generate JSON and human-readable reports."""
    json_data = []
    for project in results:
        project_dict = {'project_name': project.project_name, 'project_path': project.project_path,
            'total_pdfs'              : project.total_pdfs, 'successful_cases': project.successful_cases,
            'failed_cases'            : project.failed_cases, 'cases': []}

        for case in project.cases:
            case_dict = {'case_path' : case.case_path, 'pdf_count': case.pdf_count, 'success': case.success,
                'error_message'      : case.error_message, 'inferred_title': case.inferred_title,
                'template_file'      : case.template_file, 'total_files_analyzed': case.total_files_analyzed,
                'files_with_patterns': case.files_with_patterns, 'processing_time': case.processing_time}
            project_dict['cases'].append(case_dict)

        json_data.append(project_dict)

    json_path = output_path / 'batch_debug_results.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    report_lines = []
    report_lines.append("=" * 100)
    report_lines.append("BATCH DEBUG PROCESSOR - COMPREHENSIVE REPORT")
    report_lines.append("=" * 100)
    report_lines.append("")

    total_projects = len(results)
    total_cases = sum(len(p.cases) for p in results)
    total_pdfs = sum(p.total_pdfs for p in results)
    total_successful = sum(p.successful_cases for p in results)
    total_failed = sum(p.failed_cases for p in results)

    report_lines.append(f"SUMMARY:")
    report_lines.append(f"  Total Projects: {total_projects}")
    report_lines.append(f"  Total Cases: {total_cases}")
    report_lines.append(f"  Total PDFs: {total_pdfs}")
    report_lines.append(f"  Successful Cases: {total_successful}")
    report_lines.append(f"  Failed Cases: {total_failed}")
    report_lines.append(f"  Success Rate: {(total_successful / total_cases * 100):.1f}%")
    report_lines.append("")
    report_lines.append("=" * 100)

    for project in results:
        report_lines.append("")
        report_lines.append(f"PROJECT: {project.project_name}")
        report_lines.append(f"Path: {project.project_path}")
        report_lines.append(f"Total PDFs: {project.total_pdfs}")
        report_lines.append(
            f"Cases: {len(project.cases)} ({project.successful_cases} successful, {project.failed_cases} failed)")
        report_lines.append("-" * 100)

        for i, case in enumerate(project.cases, 1):
            report_lines.append(f"  Case {i}: {Path(case.case_path).name}")
            report_lines.append(f"    Path: {case.case_path}")
            report_lines.append(f"    PDFs: {case.pdf_count}")
            if case.inferred_title:
                report_lines.append(f"    Inferred Title: {case.inferred_title}")
            report_lines.append(f"    Status: {'✓ SUCCESS' if case.success else '✗ FAILED'}")

            if case.success:
                report_lines.append(
                    f"    Template File: {Path(case.template_file).name if case.template_file else 'None'}")
                report_lines.append(f"    Files Analyzed: {case.total_files_analyzed}")
                report_lines.append(f"    Files with Patterns: {case.files_with_patterns}")
                report_lines.append(f"    Processing Time: {case.processing_time:.2f}s")
            else:
                report_lines.append(f"    Error: {case.error_message}")

            report_lines.append("")

    report_path = output_path / 'batch_debug_report.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    ic(ict(), f"Reports written to:")
    ic(ict(), f"  - {json_path}")
    ic(ict(), f"  - {report_path}")
