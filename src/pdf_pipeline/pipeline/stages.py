"""Composable pipeline stage helpers shared by the single-file and batch flows."""
from pathlib import Path
from typing import Dict, List, Tuple

from ..core import FrequencyAnalyzer, TextExtractor, TextProcessor


def extract_and_process(filepath: Path) -> Tuple[str, List[List[str]]]:
    """Run Stages 1A (extract) and 1B (process) together.

    Returns:
        Tuple of (raw_text, processed_lines)
    """
    raw_text = TextExtractor.extract_raw_text(filepath)
    processed_lines = TextProcessor.process_text_to_lines(raw_text)
    return raw_text, processed_lines


def full_text_analysis(filepath: Path) -> Tuple[List[List[str]], Dict]:
    """Run Stages 1A, 1B, and 2 (frequency analysis) together.

    Returns:
        Tuple of (processed_lines, frequency_analysis)
    """
    raw_text, processed_lines = extract_and_process(filepath)

    analyzer = FrequencyAnalyzer()
    frequency_data = analyzer.analyze_text_frequencies(processed_lines)

    return processed_lines, frequency_data
