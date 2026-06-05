from dataclasses import dataclass, field
from typing import List, Dict, Tuple


@dataclass
class FrequencyAnalyzer:
    """
    Stage 2: Frequency analysis on processed text lines.

    Consolidates frequency counting from both TitleSearch and FrequencyBasedFilter.
    """

    # Core frequency data - initialized as empty
    word_frequencies: Dict[str, int] = field(default_factory=dict)
    chunk_line_positions: Dict[str, List[int]] = field(default_factory=dict)

    # Analysis metadata
    total_lines: int = 0
    total_unique_words: int = 0

    def analyze_text_frequencies(self, text_lines: List[List[str]]) -> Dict:
        """
        Analyze frequency patterns in processed text lines.

        Args:
            text_lines: Output from TextProcessor.process_text_to_lines()

        Returns:
            Dict containing all frequency analysis results
        """
        # Reset state for new analysis
        self.word_frequencies.clear()
        self.chunk_line_positions.clear()
        self.total_lines = len(text_lines)

        # Process each line and collect frequency data
        for line_num, words in enumerate(text_lines):
            for word in words:
                # Count word frequencies
                if word in self.word_frequencies:
                    self.word_frequencies[word] += 1
                else:
                    self.word_frequencies[word] = 1

                # Track line positions for each word
                if word in self.chunk_line_positions:
                    self.chunk_line_positions[word].append(line_num)
                else:
                    self.chunk_line_positions[word] = [line_num]

        self.total_unique_words = len(self.word_frequencies)

        return self.get_frequency_analysis()

    def get_frequency_analysis(self) -> Dict:
        """Get complete frequency analysis results."""
        return {'word_frequencies': self.word_frequencies,
                'chunk_line_positions': self.chunk_line_positions,
                'total_lines': self.total_lines,
                'total_unique_words': self.total_unique_words,
                'sorted_by_frequency': self.get_sorted_by_frequency(),
                'high_frequency_words': self.get_high_frequency_words(), }

    def get_sorted_by_frequency(self, reverse: bool = True) -> List[Tuple[str, int]]:
        """Get words sorted by frequency."""
        return sorted(self.word_frequencies.items(), key=lambda x: x[1], reverse=reverse)

    def get_high_frequency_words(self, threshold: int = 10) -> Dict[str, int]:
        """Get words above frequency threshold."""
        return {word: freq for word, freq in self.word_frequencies.items() if freq >= threshold}

    def get_title_chunk_frequencies(self, title_chunks: List[str]) -> Dict[str, int]:
        """Get frequencies specifically for title chunks."""
        return {chunk: self.word_frequencies.get(chunk, 0) for chunk in title_chunks}

    def get_title_chunk_positions(self, title_chunks: List[str]) -> Dict[str, List[int]]:
        """Get line positions specifically for title chunks."""
        return {chunk: self.chunk_line_positions.get(chunk, []) for chunk in title_chunks}

    def calculate_noise_threshold(self, title_chunks: List[str], buffer: int = 2) -> int:
        """
        Calculate noise threshold based on title chunk frequencies.

        This replaces the threshold calculation in FrequencyBasedFilter.
        """
        title_frequencies = [self.word_frequencies.get(chunk, 0) for chunk in title_chunks]
        max_title_freq = max(title_frequencies) if title_frequencies else 0
        return max_title_freq + buffer

    def meets_operation_criteria(self, word: str, target_count: int, operation: str) -> bool:
        """
        Check if word frequency meets operation criteria.

        Replaces the operation logic from TitleSearch.chunks_analysis method.
        """
        freq = self.word_frequencies.get(word, 0)

        operations_map = {'>=': freq >= target_count,
                          '>': freq > target_count,
                          '==': freq == target_count,
                          '<=': freq <= target_count,
                          '<': freq < target_count}

        if operation not in operations_map:
            raise ValueError(f"Unsupported operation: {operation}")

        return operations_map[operation]
