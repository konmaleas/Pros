"""Data models describing title-chunk patterns and per-file analysis results."""
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class DistancePattern:
    """Represents distance patterns from anchor points to other chunks."""
    anchor_chunk: str
    anchor_line: int
    chunk_distances: Dict[str, int]
    chunk_lines: Dict[str, int]


@dataclass
class FileAnalysisResult:
    """Results from analyzing a single file's title patterns."""
    filename: str
    template_file: bool
    distance_patterns: List[DistancePattern]
    anchor_chunks: List[str]
    total_chunks_found: int


@dataclass
class ChunkPattern:
    """Pattern characteristics for a title chunk."""
    original_value: str
    length: int
    is_alpha: bool
    is_digit: bool
    is_mixed: bool
