"""Data models describing batch-processing results (cases and projects)."""
from dataclasses import dataclass, field
from typing import List


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


@dataclass
class ProjectResults:
    """Results for all cases within a project."""
    project_name: str
    project_path: str
    cases: List[CaseResult] = field(default_factory=list)
    total_pdfs: int = 0
    successful_cases: int = 0
    failed_cases: int = 0
