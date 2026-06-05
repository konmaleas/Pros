"""Pure data models (dataclasses) used across the pipeline."""
from .patterns import ChunkPattern, DistancePattern, FileAnalysisResult
from .results import CaseResult, ProjectResults

__all__ = [
    "ChunkPattern",
    "DistancePattern",
    "FileAnalysisResult",
    "CaseResult",
    "ProjectResults",
]
