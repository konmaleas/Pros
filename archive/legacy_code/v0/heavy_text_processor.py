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


class FrequencyBasedFilter:
    """
    Adaptive text filtering based on frequency analysis and title chunk patterns.
    """

    def __init__(self, title_chunks: List[str] = None):
        self.title_chunks = title_chunks or []
        self.title_alpha = [chunk for chunk in self.title_chunks if chunk.isalpha()]
        self.title_digit = [chunk for chunk in self.title_chunks if chunk.isdigit()]
        self.nlp = None
        self.word_frequencies = {}
        self.noise_threshold = 0

    def process_text_with_frequency_filtering(self, text: str,
                                              title_frequency_data: dict = None) -> List[List[str]]:
        """
        Process text with frequency-based adaptive filtering.

        Args:
            text: Raw text from PDF
            title_frequency_data: Dict with title chunk frequencies (optional)

        Returns:
            List of filtered word lists per line
        """
        # Step 1: Count word frequencies across entire text
        self.word_frequencies = self._count_word_frequencies(text)

        # Step 2: Calculate noise threshold from title frequencies
        self.noise_threshold = self._calculate_noise_threshold(title_frequency_data)

        # Step 3: Load spaCy once for grammatical filtering
        self.nlp = spacy.load("en_core_web_sm")

        # Step 4: Process text with combined filtering
        return self._filter_text_lines(text)

    def _count_word_frequencies(self, text: str) -> Dict[str, int]:
        """Count frequency of each word in the entire text."""
        # Clean and split text into words
        words = []
        for line in text.split('\n'):
            # Basic character cleaning
            cleaned_line = self._basic_char_clean(line)
            words.extend(cleaned_line.split())

        # Clean words and count frequencies
        cleaned_words = []
        for word in words:
            word = word.strip('.,!?;:"()[]{}')  # Remove punctuation
            if word:
                cleaned_words.append(word)

        return Counter(cleaned_words)

    def _calculate_noise_threshold(self, title_frequency_data: dict = None) -> int:
        """
        Calculate noise threshold based on title chunk frequencies.

        Args:
            title_frequency_data: Dict from your function showing title chunk positions

        Returns:
            Frequency threshold above which words are considered noise
        """
        if title_frequency_data:
            # Use actual title chunk frequencies
            title_frequencies = [len(positions) for positions in title_frequency_data.values()]
            max_title_freq = max(title_frequencies) if title_frequencies else 0
            # Add small buffer to avoid false positives
            return max_title_freq + 2
        else:
            # Fallback: estimate based on title chunks in word frequencies
            title_freqs = []
            for chunk in self.title_chunks:
                if chunk in self.word_frequencies:
                    title_freqs.append(self.word_frequencies[chunk])

            if title_freqs:
                return max(title_freqs) + 2
            else:
                # Conservative fallback
                return 20

    def _basic_char_clean(self, line: str) -> str:
        """Basic character cleaning while preserving essential punctuation."""
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,-')
        cleaned = ''.join(char if char in allowed_chars else ' ' for char in line)
        return ' '.join(cleaned.split())

    def _filter_text_lines(self, text: str) -> List[List[str]]:
        """Filter text lines using combined frequency and pattern analysis."""
        # Process entire text with spaCy for grammatical analysis
        doc = self.nlp(text)

        # Create lookup for grammatical noise
        grammatical_noise = set()
        for token in doc:
            if token.pos_ in ['ADP', 'DET', 'CCONJ', 'AUX', 'SCONJ', 'PRON', 'PART']:
                grammatical_noise.add(token.text)

        # Process lines
        filtered_lines = []
        for line in text.split('\n'):
            cleaned_line = self._basic_char_clean(line)
            words = cleaned_line.split()

            filtered_words = []
            for word in words:
                word = word.strip('.,!?;:"()[]{}')
                if not word:
                    continue

                # Apply combined filtering
                if self._should_keep_word(word, grammatical_noise):
                    filtered_words.append(word)

            if filtered_words:
                filtered_lines.append(filtered_words)

        return filtered_lines

    def _should_keep_word(self, word: str, grammatical_noise: set) -> bool:
        """
        Determine if word should be kept based on multiple criteria.

        Args:
            word: Word to evaluate
            grammatical_noise: Set of grammatical noise words

        Returns:
            True if word should be kept, False if it should be filtered
        """
        # HIGHEST PRIORITY: Keep known title chunks
        if word in self.title_chunks:
            return True

        # REMOVE: Grammatical noise
        if word in grammatical_noise:
            return False

        # REMOVE: High frequency noise
        word_freq = self.word_frequencies.get(word, 0)
        if word_freq > self.noise_threshold:
            return False

        # REMOVE: Pattern-based noise
        if self._is_pattern_noise(word):
            return False

        # CONDITIONAL: Apply selective rules for remaining words
        return self._apply_selective_rules(word)

    def _is_pattern_noise(self, word: str) -> bool:
        """Identify pattern-based noise (your rules + measurement detection)."""
        # Your rule: long digits are noise
        if word.isdigit() and len(word) > 5:
            return True

        # Decimal numbers
        if '.' in word and word.replace('.', '').replace('-', '').isdigit():
            return True

        # Detect measurement clusters automatically
        if word.isdigit() and len(word) == 4:
            # Check if this 4-digit number appears in high frequency clusters
            # This would catch dimension values like 4370, 4200, etc.
            similar_4digit_count = sum(1 for w, freq in self.word_frequencies.items()
                                       if w.isdigit() and len(w) == 4 and freq > 3)
            if similar_4digit_count > 10:  # Many 4-digit numbers = likely dimensions
                return True

        return False

    def _apply_selective_rules(self, word: str) -> bool:
        """Apply selective rules for words that passed initial filters."""
        # Alphabetic words
        if word.isalpha():
            # Single chars: only if title chunks
            if len(word) == 1:
                return word in self.title_alpha

            # Short words: keep if uppercase (likely codes/abbreviations)
            if len(word) <= 3:
                return word.isupper()

            # Longer words: keep if they look technical
            return word.isupper() or word.istitle()

        # Digit words
        if word.isdigit():
            # Apply length-based rules
            if len(word) == 1:
                return word in self.title_digit
            elif len(word) <= 3:
                return word in self.title_digit or self._looks_like_code(word)
            elif len(word) <= 5:
                # Medium numbers: check if they look like structural codes
                return word in self.title_digit or self._looks_like_structural_code(word)

        # Mixed alphanumeric: generally exclude unless title chunk
        return False

    def _looks_like_code(self, word: str) -> bool:
        """Check if short number looks like a code rather than measurement."""
        # Simple heuristic: numbers starting with 0, 4, 7 often codes in your domain
        return word.startswith(('0', '4', '7'))

    def _looks_like_structural_code(self, word: str) -> bool:
        """Check if medium number looks like structural code."""
        # Avoid common measurement ranges but keep potential codes
        if word.isdigit():
            num = int(word)
            # Exclude common measurement ranges
            measurement_ranges = [(4000, 5000),  # Common dimension range
                                  (100, 999),  # Small measurements
            ]

            for min_val, max_val in measurement_ranges:
                if min_val <= num <= max_val:
                    # Check frequency - if appears very often, likely measurement
                    freq = self.word_frequencies.get(word, 0)
                    if freq > 5:
                        return False

            return True
        return False

    def get_filtering_stats(self) -> Dict:
        """Get statistics about the filtering process."""
        return {'total_unique_words': len(self.word_frequencies),
                'noise_threshold': self.noise_threshold,
                'high_frequency_words': {word: freq for word, freq in self.word_frequencies.items()
                                         if freq > self.noise_threshold},
                'title_chunk_frequencies': {chunk: self.word_frequencies.get(chunk, 0)
                                            for chunk in self.title_chunks}}


# Usage function
def process_pdf_with_adaptive_filtering(text: str, title: str, title_frequency_data: dict = None) -> Tuple[
    List[List[str]], Dict]:
    """
    Process PDF text with adaptive frequency-based filtering.

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

    # Create adaptive filter
    filter_processor = FrequencyBasedFilter(title_chunks)

    # Process with frequency-based filtering
    filtered_lines = filter_processor.process_text_with_frequency_filtering(text, title_frequency_data)

    # Get statistics
    stats = filter_processor.get_filtering_stats()

    return filtered_lines, stats


# Example usage:
if __name__ == "__main__":
    ic(start_time())
    path = r'C:\PyTests\Submission\Process\2211 au\dst\07xxx\PDF\raw_files'
    file = '4005-RES-VAP-DWG-233-IC-07020-0_111200787202.txt'
    filepath = Path(join(path, file))

    # Your title chunks
    title = "4005-RES-VAP-DWG-233-IC-07020-0"

    # Your frequency data
    title_frequency_data = {'0': [77, 158, 1284],
                            '07020': [166, 170, 1292],
                            '233': [65, 66, 145, 164, 1292, 1293, 1294, 1295, 1296, 1297, 1298, 1299, 1300],
                            '4005': [65, 66, 167, 1292, 1293, 1294, 1295, 1296, 1297, 1298, 1299, 1300],
                            'DWG': [65, 66, 163, 1292, 1293, 1294, 1295, 1296, 1297, 1298, 1299, 1300],
                            'IC': [65, 66, 143, 145, 165],
                            'RES': [65, 66, 161, 1292, 1293, 1294, 1295, 1296, 1297, 1298, 1299, 1300],
                            'VAP': [65, 66, 162, 1287, 1288, 1292, 1293, 1294, 1295, 1296, 1297, 1298, 1299, 1300]}

    # Sample PDF text (simulated)
    sample_text = '\n'.join(file_read(filepath))

    ic(start_time())
    filtered_lines, stats = process_pdf_with_adaptive_filtering(sample_text, title, title_frequency_data)
    ic(end_time(4))

    ic(start_time())
    ic("Filtering Statistics:")
    for key, value in stats.items():
        ic(f"{key}: {value}")

    ic("\nFiltered Results:")
    for i, line in enumerate(filtered_lines[:10]):  # Show first 10 lines
        ic(f"Line {i}: {line}")
    ic(end_time(4))
