from dataclasses import dataclass, field
from typing import List, Dict, Set
import spacy


@dataclass
class AdaptiveFilter:
    """
    Stage 3: Intelligent content filtering using pre-calculated frequency data.

    Takes frequency analysis results and applies your tuned filtering rules:
    - 76-threshold logic for noise removal
    - spaCy grammatical filtering
    - Pattern-based noise detection
    - Title chunk preservation

    No circular dependencies - all frequency data comes from Stage 2.
    """

    # Configuration
    title_chunks: List[str] = field(default_factory=list)
    noise_threshold: int = 76

    # Derived title data
    title_alpha: List[str] = field(default_factory=list)
    title_digit: List[str] = field(default_factory=list)

    # External dependencies
    nlp: object = field(default=None, init=False)

    # Frequency data (injected from Stage 2)
    word_frequencies: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize derived fields and spaCy."""
        # Separate title chunks by type
        self.title_alpha = [chunk for chunk in self.title_chunks if chunk.isalpha()]
        self.title_digit = [chunk for chunk in self.title_chunks if chunk.isdigit()]

        # Load spaCy once for grammatical filtering
        self.nlp = spacy.load("en_core_web_sm")

    def filter_text_lines(self, text_lines: List[List[str]], filtering_data: Dict) -> List[List[str]]:
        """
        Apply intelligent filtering to processed text lines.

        Args:
            text_lines: Output from TextProcessor (Stage 1B)
            filtering_data: Frequency analysis from get_filtering_data() (Stage 2)

        Returns:
            List of filtered word lists per line
        """
        # Inject frequency data
        self.word_frequencies = filtering_data['word_frequencies']
        self.noise_threshold = filtering_data.get('noise_threshold', self.noise_threshold)

        # Create grammatical noise lookup using spaCy
        grammatical_noise = self._identify_grammatical_noise(text_lines)

        # Filter each line
        filtered_lines = []
        for words in text_lines:
            filtered_words = []

            for word in words:
                # Clean word for analysis
                clean_word = word.strip('.,!?;:"()[]{}')
                if not clean_word:
                    continue

                # Apply your tuned filtering logic
                if self._should_keep_word(clean_word, grammatical_noise):
                    filtered_words.append(word)  # Keep original word with punctuation

            # Keep non-empty lines
            if filtered_words:
                filtered_lines.append(filtered_words)

        return filtered_lines

    def _identify_grammatical_noise(self, text_lines: List[List[str]]) -> Set[str]:
        """
        Use spaCy to identify grammatical noise words across all text.

        Your existing approach but optimized to run once on all text.
        """
        # Reconstruct text for spaCy analysis
        full_text = ' '.join(' '.join(words) for words in text_lines)

        # Process with spaCy
        doc = self.nlp(full_text)

        # Collect grammatical noise
        grammatical_noise = set()
        for token in doc:
            # Your existing grammatical noise categories
            if token.pos_ in ['ADP', 'DET', 'CCONJ', 'AUX', 'SCONJ', 'PRON', 'PART']:
                grammatical_noise.add(token.text)

        return grammatical_noise

    def _should_keep_word(self, word: str, grammatical_noise: Set[str]) -> bool:
        """
        Your core filtering logic - determine if word should be kept.

        This is your existing _should_keep_word method with frequency data injected.
        """
        # HIGHEST PRIORITY: Keep known title chunks
        if word in self.title_chunks:
            return True

        # REMOVE: Grammatical noise
        if word in grammatical_noise:
            return False

        # REMOVE: High frequency noise (your 76-threshold logic)
        word_freq = self.word_frequencies.get(word, 0)
        if word_freq > self.noise_threshold:
            return False

        # REMOVE: Pattern-based noise
        if self._is_pattern_noise(word):
            return False

        # CONDITIONAL: Apply selective rules for remaining words
        return self._apply_selective_rules(word)

    def _is_pattern_noise(self, word: str) -> bool:
        """
        Your pattern-based noise detection rules.
        """
        # Long digits are noise
        if word.isdigit() and len(word) > 5:
            return True

        # Decimal numbers
        if '.' in word and word.replace('.', '').replace('-', '').isdigit():
            return True

        # Conservative measurement detection for 4-digit numbers
        if word.isdigit() and len(word) == 4:
            word_freq = self.word_frequencies.get(word, 0)

            # Count similar high-frequency 4-digit numbers
            similar_4digit_freqs = [freq for w, freq in self.word_frequencies.items() if w.isdigit() and len(w) == 4]

            # Remove if this word appears very frequently AND there are many other high-freq 4-digit numbers
            if word_freq > 15 and len([f for f in similar_4digit_freqs if f > 10]) > 5:
                return True

        return False

    def _apply_selective_rules(self, word: str) -> bool:
        """
        Your selective rules for words that passed initial filters.
        """
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
        # Your heuristic: numbers starting with 0, 4, 7 often codes in your domain
        return word.startswith(('0', '4', '7'))

    def _looks_like_structural_code(self, word: str) -> bool:
        """Check if medium number looks like structural code."""
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
        """
        Get statistics about the filtering process.

        Your existing stats method adapted.
        """
        high_frequency_words = {word: freq for word, freq in self.word_frequencies.items() if
            freq > self.noise_threshold}

        title_chunk_frequencies = {chunk: self.word_frequencies.get(chunk, 0) for chunk in self.title_chunks}

        return {'total_unique_words': len(self.word_frequencies), 'noise_threshold': self.noise_threshold,
            'high_frequency_words'  : high_frequency_words, 'title_chunk_frequencies': title_chunk_frequencies,
            'words_above_threshold' : len(high_frequency_words),
            'title_chunks_found'    : len([chunk for chunk in self.title_chunks if chunk in self.word_frequencies])}
