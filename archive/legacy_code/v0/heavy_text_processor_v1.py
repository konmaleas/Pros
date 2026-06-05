from modules.file_opers import file_read
from modules.time_oper import start_time, end_time
from os.path import isfile, join, exists
from dataclasses import dataclass
from pathlib import Path
from collections import Counter
import spacy
from typing import Dict, List, Tuple
from datetime import datetime as dt2

# Third-party imports
from icecream import ic  # Debug printing utility

def ict():
    """
    Configure IceCream debug output with timestamp and context information.

    This function sets up the debug output format to include:
    - Absolute context path
    - Context information
    - Timestamp prefix with current time
    """
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


@dataclass
class TitleAnalysis:
    title: str
    dct: dict = None

    def __post_init__(self):
        self.dct = dict(enumerate(self.title.split('-')))

    def get_alpha_chunks(self) -> list[str]:
        """Get all alphabetic chunks from title."""
        return [chunk for chunk in self.dct.values() if chunk.isalpha()]

    def get_digit_chunks(self) -> list[str]:
        """Get all digit chunks from title."""
        return [chunk for chunk in self.dct.values() if chunk.isdigit()]

    def get_all_chunks(self) -> list[str]:
        """Get all title chunks."""
        return list(self.dct.values())


class HeavyTextProcessor:
    """
    Heavy filtering text processor that aggressively removes noise while preserving
    only title-relevant structural elements.
    """

    def __init__(self, title_chunks: list[str] = None):
        self.title_chunks = title_chunks or []
        self.title_alpha = [chunk for chunk in self.title_chunks if chunk.isalpha()]
        self.title_digit = [chunk for chunk in self.title_chunks if chunk.isdigit()]

    def clean_text_aggressive(self, text: str) -> list[list[str]]:
        """
        Aggressively clean text with heavy filtering focused on title elements.

        Args:
            text: Raw text from PDF

        Returns:
            List of filtered word lists per line
        """
        lines = []

        for line in text.split('\n'):
            # Step 1: Character-level cleaning
            cleaned_line = self._clean_characters(line)

            # Step 2: Word tokenization
            words = cleaned_line.split()

            # Step 3: Heavy word filtering
            filtered_words = self._heavy_word_filter(words)

            # Only keep lines with content
            if filtered_words:
                lines.append(filtered_words)

        return lines

    def _clean_characters(self, line: str) -> str:
        """Clean characters while preserving only essential punctuation."""
        # Keep only letters, digits, spaces, and minimal punctuation
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,-')
        cleaned = ''.join(char if char in allowed_chars else ' ' for char in line)

        # Remove multiple spaces
        return ' '.join(cleaned.split())

    def _heavy_word_filter(self, words: list[str]) -> list[str]:
        """Apply heavy filtering to remove noise and keep only structural elements."""
        filtered = []

        for word in words:
            word = word.strip('.,')  # Remove trailing punctuation

            if not word:
                continue

            # KEEP: Known title chunks (highest priority)
            if word in self.title_chunks:
                filtered.append(word)
                continue

            # REMOVE: Obvious measurement noise
            if self._is_measurement_noise(word):
                continue

            # REMOVE: Common non-structural words
            if self._is_common_noise(word):
                continue

            # CONDITIONAL: Alphabetic words
            if word.isalpha():
                if self._keep_alpha_word(word):
                    filtered.append(word)
                continue

            # CONDITIONAL: Numeric words
            if word.isdigit():
                if self._keep_digit_word(word):
                    filtered.append(word)
                continue

            # REMOVE: Mixed alphanumeric (unless title chunk)  # Already handled above with title chunks check

        return filtered

    def _is_measurement_noise(self, word: str) -> bool:
        """Identify obvious measurement/dimension noise."""
        # Very long numbers (likely measurements)
        if word.isdigit() and len(word) > 6:
            return True

        # Decimal numbers
        if '.' in word and word.replace('.', '').isdigit():
            return True

        # Numbers with common unit suffixes
        unit_suffixes = ['mm', 'cm', 'm', 'kg', 'g', 'l', 'ml', 'ft', 'in']
        for suffix in unit_suffixes:
            if word.lower().endswith(suffix):
                return True

        # Very common measurement ranges
        if word.isdigit():
            num = int(word)
            # Common measurement values to exclude
            if num in [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1200, 1500, 2000]:
                return True

        return False

    def _is_common_noise(self, word: str) -> bool:
        """Identify common non-structural words to remove."""
        # Load spaCy for POS tagging (cache this in real implementation)
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(word)

        if doc and doc[0].pos_ in ['ADP', 'DET', 'CCONJ', 'AUX', 'SCONJ', 'PRON', 'PART']:
            return True

        # Common architectural/technical noise words
        noise_words = {'scale', 'drawing', 'sheet', 'page', 'date', 'project', 'by', 'checked', 'approved', 'revision',
            'note', 'notes', 'see', 'detail', 'section', 'plan', 'elevation', 'view', 'typical', 'similar', 'unless',
            'otherwise', 'specified', 'indicated', 'shown', 'refer', 'reference'}

        return word.lower() in noise_words

    def _keep_alpha_word(self, word: str) -> bool:
        """Determine if alphabetic word should be kept."""
        # Single characters: only if they're title chunks
        if len(word) == 1:
            return word in self.title_alpha

        # Short words (2-3 chars): likely codes/abbreviations - keep if uppercase
        if len(word) <= 3:
            return word.isupper()

        # Longer words: keep if they look like technical terms (all caps or title case)
        if word.isupper() or word.istitle():
            return True

        return False

    def _keep_digit_word(self, word: str) -> bool:
        """Determine if digit word should be kept."""
        # Single digits: only if they're title chunks
        if len(word) == 1:
            return word in self.title_digit

        # 2-digit numbers: only if they're title chunks or look like codes
        if len(word) == 2:
            return word in self.title_digit

        # 3-5 digit numbers: likely codes/references - keep if title chunk or specific patterns
        if 3 <= len(word) <= 5:
            # Keep if it's a title chunk
            if word in self.title_digit:
                return True
            # Keep if it looks like a code (starts with specific patterns)
            if word.startswith(('4', '7', '0')):  # Based on your examples
                return True

        # 6+ digits: likely measurements - remove (already handled in measurement noise)
        return False


# Usage example with your title
def process_pdf_with_heavy_filtering(text: str, title: str) -> list[list[str]]:
    """
    Process PDF text with heavy filtering based on title analysis.

    Args:
        text: Raw PDF text
        title: Document title (e.g., "4005-RES-VAP-DWG-233-IC-07020-0")

    Returns:
        List of heavily filtered word lists per line
    """
    # Analyze title to get structural elements
    title_analysis = TitleAnalysis(title)
    title_chunks = title_analysis.get_all_chunks()

    # Create heavy processor
    processor = HeavyTextProcessor(title_chunks)

    # Process text with heavy filtering
    filtered_lines = processor.clean_text_aggressive(text)

    return filtered_lines


# Example usage:
if __name__ == "__main__":
    ic(start_time())

    # Your title chunks
    title = "4005-RES-VAP-DWG-233-IC-07020-0"

    ic(start_time())
    path = r'C:\PyTests\Submission\Process\2211 au\dst\07xxx\PDF\raw_files'
    file = '4005-RES-VAP-DWG-233-IC-07020-0_111200787202.txt'
    filepath = Path(join(path, file))

    sample_text = '\n'.join(file_read(filepath))

    # Process with heavy filtering
    result = process_pdf_with_heavy_filtering(sample_text, title)

    for i, line in enumerate(result):
        ic(f"Line {i}: {line}")

    ic(end_time(4))

# # Example usage:
# if __name__ == "__main__":
#     ic(start_time())
#     path = r'C:\PyTests\Submission\Process\2211 au\dst\07xxx\PDF\raw_files'
#     file = '4005-RES-VAP-DWG-233-IC-07020-0_111200787202.txt'
#     filepath = Path(join(path, file))
#
#     # Your title chunks
#     title = "4005-RES-VAP-DWG-233-IC-07020-0"
#
#     # Your frequency data
#     title_frequency_data = {'0': [77, 158, 1284],
#                             '07020': [166, 170, 1292],
#                             '233': [65, 66, 145, 164, 1292, 1293, 1294, 1295, 1296, 1297, 1298, 1299, 1300],
#                             '4005': [65, 66, 167, 1292, 1293, 1294, 1295, 1296, 1297, 1298, 1299, 1300],
#                             'DWG': [65, 66, 163, 1292, 1293, 1294, 1295, 1296, 1297, 1298, 1299, 1300],
#                             'IC': [65, 66, 143, 145, 165],
#                             'RES': [65, 66, 161, 1292, 1293, 1294, 1295, 1296, 1297, 1298, 1299, 1300],
#                             'VAP': [65, 66, 162, 1287, 1288, 1292, 1293, 1294, 1295, 1296, 1297, 1298, 1299, 1300]}
#
#     # Sample PDF text (simulated)
#     sample_text = '\n'.join(file_read(filepath))
#
#     ic(start_time())
#     filtered_lines, stats = process_pdf_with_adaptive_filtering(sample_text, title, title_frequency_data)
#     ic(end_time(4))
#
#     ic(start_time())
#     ic("Filtering Statistics:")
#     for key, value in stats.items():
#         ic(f"{key}: {value}")
#
#     ic("\nFiltered Results:")
#     for i, line in enumerate(filtered_lines):  # Show first 10 lines
#         ic(f"Line {i}: {line}")
#     ic(end_time(4))
