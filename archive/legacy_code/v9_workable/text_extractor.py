from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Tuple
from collections import Counter
import fitz  # PyMuPDF


@dataclass
class TextExtractor:
    """
    Stage 1A: Pure PDF text extraction.

    Handles only PDF → Raw Text string
    No processing, cleaning, or analysis at this stage.
    """

    @staticmethod
    def extract_raw_text(file_path: Path) -> str:
        """Extract raw text from PDF without any processing."""
        with fitz.open(file_path) as doc:
            text = ''.join([page.get_text() for page in doc])
        return text
