"""Pipeline orchestration: composable stages plus single-file and batch flows."""
from .stages import extract_and_process, full_text_analysis

__all__ = [
    "extract_and_process",
    "full_text_analysis",
]
