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


class FinalTunedFilter:
    """
    Final tuned text filtering pipeline optimized for v2 performance with smart noise removal.
    """

    def __init__(self, title_chunks: List[str] = None):
        self.title_chunks = title_chunks or []
        self.title_alpha = [chunk for chunk in self.title_chunks if chunk.isalpha()]
        self.title_digit = [chunk for chunk in self.title_chunks if chunk.isdigit()]
        self.nlp = None
        self.word_frequencies = {}
        self.noise_threshold = 0

    def process_text_optimized(self, text: str, title_frequency_data: dict = None) -> List[List[str]]:
        """
        Process text with optimized filtering for v2 speed and smart noise removal.

        Args:
            text: Raw text from PDF
            title_frequency_data: Dict with title chunk frequencies (optional)

        Returns:
            List of filtered word lists per line
        """
        # Step 1: Count word frequencies across entire text
        self.word_frequencies = self._count_word_frequencies(text)

        # Step 2: Calculate smart noise threshold
        self.noise_threshold = self._calculate_smart_threshold(title_frequency_data)

        # Step 3: Load spaCy once for grammatical filtering
        self.nlp = spacy.load("en_core_web_sm")

        # Step 4: Get grammatical noise from entire text (single pass)
        grammatical_noise = self._get_grammatical_noise(text)

        # Step 5: Process lines with optimized filtering
        return self._filter_lines_optimized(text, grammatical_noise)

    def _count_word_frequencies(self, text: str) -> Dict[str, int]:
        """Count frequency of each word in the entire text."""
        words = []
        for line in text.split('\n'):
            # Basic character cleaning
            cleaned_line = self._basic_char_clean(line)
            words.extend(cleaned_line.split())

        # Clean words and count frequencies
        cleaned_words = []
        for word in words:
            word = word.strip('.,!?;:"()[]{}')
            if word:
                cleaned_words.append(word)

        return Counter(cleaned_words)

    def _calculate_smart_threshold(self, title_frequency_data: dict = None) -> int:
        """
        Calculate smart noise threshold that balances structure preservation with noise removal.
        """
        if title_frequency_data:
            # Use actual title chunk frequencies with smart multiplier
            title_frequencies = [len(positions) for positions in title_frequency_data.values()]
            max_title_freq = max(title_frequencies) if title_frequencies else 0
            # Smart threshold: high enough to keep structural elements, low enough to remove obvious noise
            return max_title_freq * 4 + 20  # 15 * 4 + 20 = 80
        else:
            # Fallback with conservative threshold
            title_freqs = []
            for chunk in self.title_chunks:
                if chunk in self.word_frequencies:
                    title_freqs.append(self.word_frequencies[chunk])

            if title_freqs:
                return max(title_freqs) * 4 + 20
            else:
                return 80  # Conservative default

    def _basic_char_clean(self, line: str) -> str:
        """Basic character cleaning while preserving essential punctuation."""
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,-')
        cleaned = ''.join(char if char in allowed_chars else ' ' for char in line)
        return ' '.join(cleaned.split())

    def _get_grammatical_noise(self, text: str) -> set:
        """Get grammatical noise words from entire text in single pass."""
        doc = self.nlp(text)
        grammatical_noise = set()

        for token in doc:
            if token.pos_ in ['ADP', 'DET', 'CCONJ', 'AUX', 'SCONJ', 'PRON', 'PART']:
                grammatical_noise.add(token.text)

        return grammatical_noise

    def _filter_lines_optimized(self, text: str, grammatical_noise: set) -> List[List[str]]:
        """Filter text lines using optimized combined filtering."""
        filtered_lines = []

        for line in text.split('\n'):
            cleaned_line = self._basic_char_clean(line)
            words = cleaned_line.split()

            filtered_words = []
            for word in words:
                word = word.strip('.,!?;:"()[]{}')
                if not word:
                    continue

                # Apply smart filtering
                if self._should_keep_word_smart(word, grammatical_noise):
                    filtered_words.append(word)

            if filtered_words:
                filtered_lines.append(filtered_words)

        return filtered_lines

    def _should_keep_word_smart(self, word: str, grammatical_noise: set) -> bool:
        """
        Smart word filtering that balances structure preservation with noise removal.
        """
        # HIGHEST PRIORITY: Always keep title chunks
        if word in self.title_chunks:
            return True

        # HIGH PRIORITY: Keep essential structural terms
        essential_structural = {'TYPE', 'CABINET', 'DIMENSIONS', 'CODE', 'UNIT', 'CASES', 'LAYOUT', 'SCALE', 'DRAWING',
            'SHEET', 'PLAN', 'SECTION', 'DETAIL', 'ELEVATION', 'VIEW', 'SCHEDULE', 'LEGEND', 'SYMBOLS', 'ISLAND',
            'KITCHEN', 'UNITS', 'STUDIO', 'LINEAR', 'ROOM'}
        if word.upper() in essential_structural:
            return True

        # REMOVE: Grammatical noise
        if word in grammatical_noise:
            return False

        # SMART FREQUENCY FILTERING: Remove only extreme high-frequency noise
        word_freq = self.word_frequencies.get(word, 0)
        if word_freq > self.noise_threshold:
            return False

        # SMART MEASUREMENT FILTERING: Remove obvious measurement noise patterns
        if self._is_obvious_measurement_noise(word):
            return False

        # CONDITIONAL: Apply context-aware rules for remaining words
        return self._apply_context_rules(word)

    def _is_obvious_measurement_noise(self, word: str) -> bool:
        """Identify obvious measurement noise while preserving potential structural codes."""
        # Very long numbers (definitely measurements)
        if word.isdigit() and len(word) > 6:
            return True

        # Decimal numbers
        if '.' in word and word.replace('.', '').replace('-', '').isdigit():
            return True

        # Smart dimension filtering: remove only if appears very frequently AND fits dimension pattern
        if word.isdigit() and len(word) == 4:
            word_freq = self.word_frequencies.get(word, 0)

            # Count other 4-digit numbers with high frequency
            high_freq_4digit = sum(
                    1 for w, freq in self.word_frequencies.items() if w.isdigit() and len(w) == 4 and freq > 8)

            # Remove only if this word appears very often AND there are many similar high-freq 4-digit numbers
            if word_freq > 12 and high_freq_4digit > 15:
                return True

        # Remove specific high-frequency measurement patterns
        if word.isdigit():
            num = int(word)
            word_freq = self.word_frequencies.get(word, 0)

            # Remove common dimension values that appear very frequently
            common_measurements = [450, 600, 700, 900, 1000, 1200, 1300, 1500, 2000]
            if num in common_measurements and word_freq > 15:
                return True

        return False

    def _apply_context_rules(self, word: str) -> bool:
        """Apply context-aware rules for words that passed initial filters."""
        # Alphabetic words
        if word.isalpha():
            # Single chars: only if title chunks
            if len(word) == 1:
                return word in self.title_alpha

            # Short words (2-3 chars): keep if uppercase (likely abbreviations/codes)
            if len(word) <= 3:
                return word.isupper()

            # Longer words: keep if they look technical/architectural
            return word.isupper() or word.istitle()

        # Digit words
        if word.isdigit():
            # Single digits: only if title chunks
            if len(word) == 1:
                return word in self.title_digit

            # 2-3 digit numbers: keep if title chunks or look like codes
            if len(word) <= 3:
                return word in self.title_digit or self._looks_like_code(word)

            # 4-5 digit numbers: more selective (already filtered obvious measurements above)
            if len(word) <= 5:
                return word in self.title_digit or self._looks_like_structural_reference(word)

        # Mixed alphanumeric: generally exclude unless title chunk
        return False

    def _looks_like_code(self, word: str) -> bool:
        """Check if short number looks like a code."""
        # Codes often start with specific digits in architectural context
        return word.startswith(('0', '4', '7', '8'))

    def _looks_like_structural_reference(self, word: str) -> bool:
        """Check if number looks like structural reference rather than measurement."""
        if word.isdigit():
            # Check frequency - structural references appear less frequently than measurements
            freq = self.word_frequencies.get(word, 0)

            # If it appears very frequently, likely a measurement (already filtered above)
            # If it appears moderately (2-8 times), likely structural
            if 2 <= freq <= 8:
                return True

            # Special patterns that look like references
            if word.startswith(('07', '40', '15', '08')):
                return True

        return False

    def get_filtering_stats(self) -> Dict:
        """Get statistics about the filtering process."""
        return {'total_unique_words'                                                          : len(
            self.word_frequencies), 'noise_threshold'                                         : self.noise_threshold,
            'high_frequency_words'                                                            : {word: freq for
                                                                                                 word, freq in
                                                                                                 self.word_frequencies.items()
                                                                                                 if
                                                                                                 freq > self.noise_threshold},
            'title_chunk_frequencies'                                                         : {
                chunk: self.word_frequencies.get(chunk, 0) for chunk in self.title_chunks},
            'extreme_measurements_removed'                                                    : [word for word, freq in
                                                                                                 self.word_frequencies.items()
                                                                                                 if
                                                                                                 word.isdigit() and freq > 50],
            'structural_elements_preserved'                                                   : [word for word, freq in
                                                                                                 self.word_frequencies.items()
                                                                                                 if word.upper() in {
                                                                                                     'TYPE', 'CABINET',
                                                                                                     'DIMENSIONS',
                                                                                                     'CODE', 'UNIT',
                                                                                                     'CASES'}]}


# Main processing function
def process_pdf_final_tuned(text: str, title: str, title_frequency_data: dict = None) -> Tuple[List[List[str]], Dict]:
    """
    Final tuned PDF text processing with optimal balance of speed and filtering quality.

    Args:
        text: Raw PDF text
        title: Document title (e.g., "4005-RES-VAP-DWG-233-IC-07020-0")
        title_frequency_data: Optional dict from your frequency analysis function

    Returns:
        Tuple of (filtered_lines, filtering_stats)
    """
    # Analyze title
    title_analysis = TitleAnalysis(title)
    title_chunks = title_analysis.get_all_chunks()

    # Create final tuned filter
    filter_processor = FinalTunedFilter(title_chunks)

    # Process with optimized filtering
    filtered_lines = filter_processor.process_text_optimized(text, title_frequency_data)

    # Get comprehensive statistics
    stats = filter_processor.get_filtering_stats()

    return filtered_lines, stats


# Example usage:
if __name__ == "__main__":
    ic(start_time())
    title = "4005-RES-VAP-DWG-233-IC-07020-0"

    # Your frequency data
    title_frequency_data = {
        '0': [77, 158, 1284],
        '07020': [166, 170, 1292],
        '233': [65, 66, 145, 164, 1292, 1293, 1294, 1295, 1296, 1297, 1298, 1299, 1300],
        '4005': [65, 66, 167, 1292, 1293, 1294, 1295, 1296, 1297, 1298, 1299, 1300],
        'DWG': [65, 66, 163, 1292, 1293, 1294, 1295, 1296, 1297, 1298, 1299, 1300],
        'IC': [65, 66, 143, 145, 165],
        'RES': [65, 66, 161, 1292, 1293, 1294, 1295, 1296, 1297, 1298, 1299, 1300],
        'VAP': [65, 66, 162, 1287, 1288, 1292, 1293, 1294, 1295, 1296, 1297, 1298, 1299, 1300]
    }

    path = r'C:\PyTests\Submission\Process\2211 au\dst\07xxx\PDF\raw_files'
    file = '4005-RES-VAP-DWG-233-IC-07020-0_111200787202.txt'
    filepath = Path(join(path, file))
    sample_text = '\n'.join(file_read(filepath))

    filtered_lines, stats = process_pdf_final_tuned(sample_text, title, title_frequency_data)

    ic("Final Filtering Statistics:")
    for key, value in stats.items():
        ic(f"{key}: {value}")

    ic("\nFiltered Results:")
    for i, line in enumerate(filtered_lines):
        ic(f"Line {i}: {line}")
    ic(end_time(4))

