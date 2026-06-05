from modules.string_manipulation import singling_symbols, replacer_2
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Tuple


@dataclass
class TextProcessor:
    """
    Stage 1B: Text processing and normalization.

    Handles Raw Text → Clean Line-Split Text
    Uses your existing character cleaning logic.
    """

    @classmethod
    def process_text_to_lines(cls, raw_text: str) -> List[List[str]]:
        """
        Process raw text into clean word lists per line.

        This is your clear_file_() method adapted for the pipeline.

        Args:
            raw_text: Raw string from PDF extraction

        Returns:
            List of word lists per line
        """
        processed_lines = []

        for line in raw_text.split('\n'):
            # Apply your existing character processing
            processed_line_str = singling_symbols(replacer_2(line, ' ', preserve=[',', '.']))

            # Split and filter empty strings
            words = processed_line_str.split(' ')
            filtered_words = [word for word in words if word.strip()]

            # Keep non-empty lines
            if filtered_words:
                processed_lines.append(filtered_words)

        return processed_lines
