# This file contains the specific changes needed for batch_processor.py
# Apply these changes to your existing batch_processor.py file

# CHANGE 1: Line ~4 - Ensure Dict is imported  
from typing import List, Dict, Tuple
from dataclasses import dataclass, field
from datetime import datetime as dt2
from icecream import ic


def ict():
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


# CHANGE 2: Line ~30 - Add found_titles field to CaseResult
@dataclass
class CaseResult:
    """Results from processing a single case."""
    case_path: str
    pdf_count: int
    success: bool
    error_message: str = ""
    inferred_title: str = ""
    template_file: str = ""
    total_files_analyzed: int = 0
    files_with_patterns: int = 0
    stable_anchors_found: int = 0
    processing_time: float = 0.0
    found_titles: Dict[str, str] = field(default_factory=dict)  # filename -> reconstructed title

    # CHANGE 3: Line ~160 - Replace the entire try block in process_case()
    try:
        # Run multi-file pattern analysis
        analyzer = MultiFilePatternAnalyzer(title=title, files=pdf_files)

        # Try single-anchor approach first
        results, all_file_data = analyzer.analyze_all_files(extract_and_process)

        # Check if single-anchor failed (no chunks found in any file)
        if all(r.total_chunks_found == 0 for r in results.values()):
            ic(ict(), "Single-anchor approach failed, trying multi-anchor approach...")

            # Try multi-anchor approach
            viable_anchors = analyzer.find_multiple_anchors(all_file_data)

            if viable_anchors:
                ic(ict(), f"Found {len(viable_anchors)} viable anchors for multi-anchor approach")

                # Validate with multi-anchor
                validation_results = analyzer.validate_anchors_on_files(all_file_data)

                # Convert validation results to FileAnalysisResult format
                results = analyzer.convert_validation_to_file_results(validation_results)

                # Get reconstructed titles
                found_titles = analyzer.get_found_titles_dict(validation_results)

                ic(ict(), f"Multi-anchor validation: {validation_results['successful_files']}/{validation_results['total_files']} files successful")
            else:
                ic(ict(), "Multi-anchor approach also failed - no viable anchors found")
                found_titles = {}
        else:
            # Single-anchor succeeded, no reconstructed titles available
            found_titles = {}

        # Count successes
        template_file = ""
        files_with_patterns = 0

        for filename, result in results.items():
            if result.template_file:
                template_file = filename
            if result.total_chunks_found > 0:
                files_with_patterns += 1

        processing_time = (dt2.now() - start).total_seconds()

        return CaseResult(case_path=case_path,
                          pdf_count=len(pdf_files),
                          success=True,
                          inferred_title=title,
                          template_file=template_file,
                          total_files_analyzed=len(results),
                          files_with_patterns=files_with_patterns,
                stable_anchors_found=0,  # Not calculated in debug mode
                processing_time=processing_time, found_titles=found_titles)

# CHANGE 4: Line ~260 - Add found_titles to JSON case_dict
case_dict = {'case_path' : case.case_path, 'pdf_count': case.pdf_count, 'success': case.success,
    'error_message'      : case.error_message, 'inferred_title': case.inferred_title,
    'template_file'      : case.template_file, 'total_files_analyzed': case.total_files_analyzed,
    'files_with_patterns': case.files_with_patterns, 'processing_time': case.processing_time,
    'found_titles'       : case.found_titles}

# CHANGE 5: Line ~319 - Add reconstructed titles section to report
if case.success:
    report_lines.append(
        f"    Template File: {Path(case.template_file).name if case.template_file else 'None'}")
    report_lines.append(f"    Files Analyzed: {case.total_files_analyzed}")
    report_lines.append(f"    Files with Patterns: {case.files_with_patterns}")
    report_lines.append(f"    Processing Time: {case.processing_time:.2f}s")
    
    # Add reconstructed titles if available
    if case.found_titles:
        report_lines.append("")
        report_lines.append("    " + "=" * 56)
        report_lines.append("    RECONSTRUCTED TITLES")
        report_lines.append("    " + "=" * 56)
        for filename, title in sorted(case.found_titles.items()):
            status = "✓" if title else "✗"
            short_name = Path(filename).name
            report_lines.append(f"    {status} {short_name}: {title}")
else:
    report_lines.append(f"    Error: {case.error_message}")
