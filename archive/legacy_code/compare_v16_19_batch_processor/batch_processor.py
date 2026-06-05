from text_extractor import TextExtractor
from text_processor import TextProcessor
from pattern_analyzer import MultiFilePatternAnalyzer, FileAnalysisResult
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict
from dataclasses import dataclass, field
import json
from datetime import datetime as dt2
from icecream import ic


def ict():
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


@dataclass
class CaseResult:
    """Results from processing a single case."""
    case_path: str
    pdf_count: int
    success: bool
    error_message: str = ""
    template_title: str = ""
    template_file: str = ""
    total_files_analyzed: int = 0
    files_with_patterns: int = 0
    stable_anchors_found: int = 0
    processing_time: float = 0.0


@dataclass
class ProjectResults:
    """Results for all cases within a project."""
    project_name: str
    project_path: str
    cases: List[CaseResult] = field(default_factory=list)
    total_pdfs: int = 0
    successful_cases: int = 0
    failed_cases: int = 0


def extract_and_process(filepath: Path) -> Tuple[str, List[List[str]]]:
    """
    Run Stages 1A and 1B together.

    Returns:
        Tuple of (raw_text, processed_lines)
    """
    raw_text = TextExtractor.extract_raw_text(filepath)
    processed_lines = TextProcessor.process_text_to_lines(raw_text)
    return raw_text, processed_lines


def load_directory_list(file_path: Path) -> List[str]:
    """Load directory paths from the text file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def group_by_projects(dir_list: List[str]) -> Dict[str, List[str]]:
    """
    Group directories by project and cases.

    Returns:
        Dict mapping project_path -> list of case paths
    """
    projects = defaultdict(list)

    for dir_path in dir_list:
        path = Path(dir_path)

        # Check depth from 'Process' directory
        parts = path.parts
        process_idx = parts.index('Process') if 'Process' in parts else -1

        if process_idx == -1:
            continue

        depth_from_process = len(parts) - process_idx - 1

        if depth_from_process == 1:
            # This is a project level directory
            projects[dir_path] = []
        elif depth_from_process == 2:
            # This is a case (subdirectory of a project)
            project_path = str(path.parent)
            projects[project_path].append(dir_path)

    # Add projects without cases (single-case projects)
    final_projects = {}
    for project_path, cases in projects.items():
        if not cases:
            # No subcases found, treat project itself as the case
            final_projects[project_path] = [project_path]
        else:
            final_projects[project_path] = cases

    return final_projects


def get_pdf_files(directory: Path) -> List[Path]:
    """Get all PDF files in a directory."""
    if not directory.exists():
        return []
    return [f for f in directory.iterdir() if f.is_file() and f.suffix.lower() == '.pdf']


def get_template_title_and_file(pdf_files: List[Path]) -> Tuple[str, str]:
    """
    Get template title and file from list of PDFs.
    HARDCODED FOR TEST: Use same file as v19 for comparison.

    Args:
        pdf_files: List of PDF file paths (ignored in test mode)

    Returns:
        Tuple of (template_title, template_filename)
    """
    # HARDCODED - Same as v19
    template_filename = 'ATH1-DC03-CAP-20302-PLN-2-011-AL-00-T00_4-SECTIONS_DC3.pdf'
    template_title = 'ATH1-DC03-CAP-20302-PLN-2-011-AL-00-T00_4-SECTIONS_DC3'

    return template_title, template_filename


def process_case(case_path: str) -> CaseResult:
    """
    Process a single case directory.

    Args:
        case_path: Path to the case directory containing PDFs

    Returns:
        CaseResult with processing details
    """
    import traceback

    start = dt2.now()
    case_dir = Path(case_path)

    ic(ict(), f"Processing case: {case_path}")

    # Get all PDF files in the case
    pdf_files = get_pdf_files(case_dir)

    if not pdf_files:
        return CaseResult(case_path=case_path, pdf_count=0, success=False, error_message="No PDF files found")

    ic(ict(), f"Found {len(pdf_files)} PDF files")

    # Get template title and file (use first file)
    template_title, template_filename = get_template_title_and_file(pdf_files)
    ic(ict(), f"Template title: {template_title}")
    ic(ict(), f"Template file: {template_filename}")

    try:
        # Run multi-file pattern analysis
        analyzer = MultiFilePatternAnalyzer(title=template_title, files=pdf_files)
        results = analyzer.analyze_all_files(extract_and_process)

        # Count successes
        files_with_patterns = 0

        for filename, result in results.items():
            if result.total_chunks_found > 0:
                files_with_patterns += 1

        processing_time = (dt2.now() - start).total_seconds()

        return CaseResult(case_path=case_path, pdf_count=len(pdf_files), success=True, template_title=template_title,
                          template_file=template_filename, total_files_analyzed=len(results),
                          files_with_patterns=files_with_patterns, stable_anchors_found=0,
                          # Not calculated in debug mode
                          processing_time=processing_time)

    except Exception as e:
        processing_time = (dt2.now() - start).total_seconds()
        error_details = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        ic(ict(), f"ERROR processing case {case_path}:")
        ic(ict(), error_details)
        return CaseResult(case_path=case_path, pdf_count=len(pdf_files), success=False, template_title=template_title,
                          template_file=template_filename, error_message=error_details, processing_time=processing_time)


def process_all_projects(projects: Dict[str, List[str]]) -> List[ProjectResults]:
    """
    Process all projects and their cases.

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

    # JSON Report
    json_data = []
    for project in results:
        project_dict = {'project_name': project.project_name, 'project_path': project.project_path,
                        'total_pdfs'  : project.total_pdfs, 'successful_cases': project.successful_cases,
                        'failed_cases': project.failed_cases, 'cases': []}

        for case in project.cases:
            case_dict = {'case_path'          : case.case_path, 'pdf_count': case.pdf_count, 'success': case.success,
                         'error_message'      : case.error_message, 'template_title': case.template_title,
                         'template_file'      : case.template_file, 'total_files_analyzed': case.total_files_analyzed,
                         'files_with_patterns': case.files_with_patterns, 'processing_time': case.processing_time}
            project_dict['cases'].append(case_dict)

        json_data.append(project_dict)

    # Write JSON
    json_path = output_path / 'batch_debug_results.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    # Human-readable report
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
            if case.template_title:
                report_lines.append(f"    Template Title: {case.template_title}")
            if case.template_file:
                report_lines.append(f"    Template File: {case.template_file}")
            report_lines.append(f"    Status: {'âœ“ SUCCESS' if case.success else 'âœ— FAILED'}")

            if case.success:
                report_lines.append(f"    Files Analyzed: {case.total_files_analyzed}")
                report_lines.append(f"    Files with Patterns: {case.files_with_patterns}")
                report_lines.append(f"    Processing Time: {case.processing_time:.2f}s")
            else:
                report_lines.append(f"    Error: {case.error_message}")

            report_lines.append("")

    # Write text report
    report_path = output_path / 'batch_debug_report.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    ic(ict(), f"Reports written to:")
    ic(ict(), f"  - {json_path}")
    ic(ict(), f"  - {report_path}")


if __name__ == '__main__':
    ict()
    start = dt2.now()

    # Input file with directory list
    input_file = Path('/home/konstantinos/PycharmProjects/Pros/claude/files/pkl/project_dirs.txt')

    # Output directory for reports
    output_dir = (Path.home() / 'PycharmProjects/Pros/claude' / Path(
        __file__).parent.name / 'batch_debug' / dt2.now().strftime('%Y%m%d_%H%M%S'))
    output_dir.mkdir(parents=True, exist_ok=True)

    ic(ict(), "Starting batch debug processor")
    ic(ict(), f"Input file: {input_file}")
    ic(ict(), f"Output directory: {output_dir}")

    # Load and group directories
    dir_list = load_directory_list(input_file)
    ic(ict(), f"Loaded {len(dir_list)} directory entries")

    projects = group_by_projects(dir_list)
    ic(ict(), f"Grouped into {len(projects)} projects")

    # Process all projects
    results = process_all_projects(projects)

    # Generate reports
    generate_report(results, output_dir)

    elapsed = (dt2.now() - start).total_seconds()
    ic(ict(), f"Total processing time: {elapsed:.2f}s ({elapsed / 60:.1f} minutes)")
