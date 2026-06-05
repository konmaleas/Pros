from text_extractor import TextExtractor
from text_processor import TextProcessor
from frequency_analyzer import FrequencyAnalyzer
from adaptive_filter import AdaptiveFilter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from collections import Counter, defaultdict
from string import punctuation


@dataclass
class DistancePattern:
    """Represents distance patterns from anchor points to other chunks."""
    anchor_chunk: str
    anchor_line: int
    chunk_distances: Dict[str, int]  # chunk -> distance from anchor
    chunk_lines: Dict[str, int]  # chunk -> absolute line number


@dataclass
class FileAnalysisResult:
    """Results from analyzing a single file's title patterns."""
    filename: str
    template_file: bool
    distance_patterns: List[DistancePattern]
    anchor_chunks: List[str]
    total_chunks_found: int


@dataclass
class MultiFilePatternAnalyzer:
    """
    Analyzes patterns across multiple files using stable line anchors.

    Strategy:
    1. Process ALL files to find common stable line patterns
    2. Select best stable line as universal anchor content
    3. In each file, find where that anchor appears and calculate distances
    """
    title: str
    files: List[Path] = field(default_factory=list)
    max_distance_threshold: int = 15  # All title chunks must be within 15 lines of anchor

    def __post_init__(self):
        """Initialize derived fields after dataclass creation."""
        self.title_chunks = self._extract_title_chunks()

    def _extract_title_chunks(self) -> List[str]:
        """Extract individual chunks from the title string."""
        separators = ['-', '_', '.', ' ']
        for sep in separators:
            if sep in self.title:
                chunks = [chunk.strip() for chunk in self.title.split(sep) if chunk.strip()]
                if len(chunks) > 1:
                    return chunks
        return [self.title]

    def analyze_all_files(self, extract_and_process_func) -> Dict[str, FileAnalysisResult]:
        """
        Main entry point: analyze all files using stable line anchors.

        Args:
            extract_and_process_func: External function for stages 1A+1B

        Returns:
            Dict mapping filename to analysis results
        """
        # Step 1: Process all files and get their filtered lines + chunk positions
        all_file_data = {}
        for file_path in self.files:
            # Get filtered lines and chunk positions for this file
            raw_text, processed_lines = extract_and_process_func(file_path)

            # Run frequency analysis (Stage 2)
            frequency_analyzer = FrequencyAnalyzer()
            frequency_data = frequency_analyzer.analyze_text_frequencies(processed_lines)

            # Apply filtering
            adaptive_filter = AdaptiveFilter(title_chunks=self.title_chunks)
            filtered_lines = adaptive_filter.filter_text_lines(processed_lines, frequency_data)

            all_file_data[str(file_path)] = {'filtered_lines': filtered_lines,
                                             'chunk_positions': frequency_data['chunk_line_positions']}

        # Step 2: Find common stable lines across all files
        stable_anchor_lines = self._find_stable_anchor_lines(all_file_data)

        # Step 3: Select best anchor line
        best_anchor = self._select_best_anchor(stable_anchor_lines, all_file_data)

        if not best_anchor:
            # Fallback: no stable anchor found
            return {filename: self._create_empty_result(filename) for filename in all_file_data.keys()}

        # Step 4: Analyze each file using the selected stable anchor
        results = {}
        for filename, file_data in all_file_data.items():
            result = self._analyze_single_file_with_anchor(filename, file_data['filtered_lines'],
                    file_data['chunk_positions'], best_anchor)
            results[filename] = result

        return results

    def _find_stable_anchor_lines(self, all_file_data: Dict) -> List[List[str]]:
        """
        Find line patterns that appear in ALL files.

        Returns:
            List of line patterns (List[str]) that exist across all files
        """
        if not all_file_data:
            return []

        # Get all unique line patterns from first file
        first_file = list(all_file_data.values())[0]
        candidate_lines = set()

        for line in first_file['filtered_lines']:
            # Convert list to tuple for hashing
            line_tuple = tuple(line)
            candidate_lines.add(line_tuple)

        # Filter candidates: keep only lines that appear in ALL files
        stable_lines = []
        for line_tuple in candidate_lines:
            appears_in_all = True

            for file_data in all_file_data.values():
                # Check if this line pattern exists in current file
                line_found = False
                for file_line in file_data['filtered_lines']:
                    if tuple(file_line) == line_tuple:
                        line_found = True
                        break

                if not line_found:
                    appears_in_all = False
                    break

            if appears_in_all:
                stable_lines.append(list(line_tuple))

        return stable_lines

    def _select_best_anchor(self, stable_lines: List[List[str]], all_file_data: Dict) -> Optional[List[str]]:
        """
        Select the best stable line as anchor based on quality criteria.

        Criteria (in order of preference):
        1. Lines with multiple words (more unique/stable)
        2. Lines that appear multiple times per file
        3. Lines that keep all title chunks within max_distance_threshold
        """
        if not stable_lines:
            return None

        scored_anchors = []

        for anchor_line in stable_lines:
            score = self._score_anchor_candidate(anchor_line, all_file_data)
            if score > 0:  # Only consider viable anchors
                scored_anchors.append((score, anchor_line))

        if not scored_anchors:
            return None

        # Return highest scoring anchor
        scored_anchors.sort(reverse=True)
        return scored_anchors[0][1]

    def _score_anchor_candidate(self, anchor_line: List[str], all_file_data: Dict) -> float:
        """
        Score an anchor candidate based on quality criteria.

        Returns:
            Score (higher is better), 0 if anchor is invalid
        """
        score = 0.0

        # Criterion 1: Multi-word lines get bonus (more unique)
        if len(anchor_line) > 1:
            score += len(anchor_line) * 10

        # Criterion 2: Lines that appear multiple times (consistency bonus)
        total_occurrences = 0
        for file_data in all_file_data.values():
            occurrences = sum(1 for line in file_data['filtered_lines'] if line == anchor_line)
            total_occurrences += occurrences
            if occurrences > 1:
                score += occurrences * 5

        # Criterion 3: Check if anchor keeps title chunks within threshold
        viable_files = 0
        for filename, file_data in all_file_data.items():
            if self._test_anchor_viability(anchor_line, file_data):
                viable_files += 1

        # Anchor must work in ALL files
        if viable_files < len(all_file_data):
            return 0  # Invalid anchor

        score += viable_files * 20  # Big bonus for universal viability

        return score

    def _test_anchor_viability(self, anchor_line: List[str], file_data: Dict) -> bool:
        """
        Test if using this anchor keeps all title chunks within max_distance_threshold.

        Returns:
            True if anchor is viable for this file
        """
        # Find anchor positions in this file
        anchor_positions = []
        for line_num, line in enumerate(file_data['filtered_lines']):
            if line == anchor_line:
                anchor_positions.append(line_num)

        if not anchor_positions:
            return False

        # Validate title chunk positions
        validated_positions = self._validate_chunk_positions(file_data['filtered_lines'], file_data['chunk_positions'])

        # Check if any anchor position keeps all title chunks within threshold
        for anchor_pos in anchor_positions:
            max_distance = 0

            for chunk in self.title_chunks:
                if chunk in validated_positions:
                    min_chunk_distance = min(abs(pos - anchor_pos) for pos in validated_positions[chunk])
                    max_distance = max(max_distance, min_chunk_distance)

            # If this anchor position works, the anchor is viable
            if max_distance <= self.max_distance_threshold:
                return True

        return False

    def _analyze_single_file_with_anchor(self, filename: str, filtered_lines: List[List[str]],
                                         chunk_positions: Dict[str, List[int]],
                                         anchor_line: List[str]) -> FileAnalysisResult:
        """
        Analyze a single file using the selected stable anchor.
        """
        # Find anchor positions in this file
        anchor_positions = []
        for line_num, line in enumerate(filtered_lines):
            if line == anchor_line:
                anchor_positions.append(line_num)

        if not anchor_positions:
            return self._create_empty_result(filename)

        # Validate chunk positions against filtered text
        validated_positions = self._validate_chunk_positions(filtered_lines, chunk_positions)

        # Find title chunks in this file
        found_chunks = {chunk: positions for chunk, positions in validated_positions.items() if
                        chunk in self.title_chunks}

        if not found_chunks:
            return self._create_empty_result(filename)

        # Find best anchor position that minimizes max distance
        best_anchor_pos = self._find_optimal_anchor_position(anchor_positions, found_chunks)

        # Generate distance pattern
        distance_pattern = self._generate_anchor_distance_pattern(anchor_line, best_anchor_pos, found_chunks)

        # Determine if this is template file
        is_template = self._is_template_file(filename)

        return FileAnalysisResult(filename=filename,
                                  template_file=is_template,
                                  distance_patterns=[distance_pattern] if distance_pattern else [],
                                  anchor_chunks=[str(anchor_line)],
                                  # Store anchor line as string
                                  total_chunks_found=sum(len(positions) for positions in found_chunks.values()))

    def _validate_chunk_positions(self,
                                  filtered_lines: List[List[str]],
                                  chunk_positions: Dict[str, List[int]]) -> Dict[str, List[int]]:
        """
        Validate chunk positions against filtered text, recalculate if needed.
        """
        validated_positions = {}

        for chunk, original_positions in chunk_positions.items():
            valid_positions = []

            # Try original positions first
            for line_num in original_positions:
                if line_num < len(filtered_lines):
                    line_text = ' '.join(filtered_lines[line_num]).lower()
                    if chunk.lower() in line_text:
                        valid_positions.append(line_num)

            # If original positions failed, search in filtered text
            if not valid_positions:
                valid_positions = self._find_chunk_in_filtered_text(chunk, filtered_lines)

            if valid_positions:
                validated_positions[chunk] = valid_positions

        return validated_positions

    def _find_chunk_in_filtered_text(self, chunk: str, filtered_lines: List[List[str]]) -> List[int]:
        """Find chunk occurrences in filtered text."""
        positions = []
        chunk_lower = chunk.lower()

        for line_num, line_list in enumerate(filtered_lines):
            line_text = ' '.join(line_list).lower()
            if chunk_lower in line_text:
                import re
                pattern = r'\b' + re.escape(chunk_lower) + r'\b'
                if re.search(pattern, line_text):
                    positions.append(line_num)

        return positions

    def _find_optimal_anchor_position(self, anchor_positions: List[int], found_chunks: Dict[str, List[int]]) -> int:
        """
        Find anchor position that minimizes maximum distance to any title chunk.
        """
        best_pos = anchor_positions[0]
        best_max_distance = float('inf')

        for anchor_pos in anchor_positions:
            max_distance = 0

            for chunk_positions in found_chunks.values():
                min_chunk_distance = min(abs(pos - anchor_pos) for pos in chunk_positions)
                max_distance = max(max_distance, min_chunk_distance)

            if max_distance < best_max_distance:
                best_max_distance = max_distance
                best_pos = anchor_pos

        return best_pos

    def _generate_anchor_distance_pattern(self, anchor_line: List[str], anchor_pos: int,
                                          found_chunks: Dict[str, List[int]]) -> Optional[DistancePattern]:
        """
        Generate distance pattern using stable line anchor.
        """
        chunk_distances = {}
        chunk_lines = {}

        for chunk, positions in found_chunks.items():
            # Find closest position to anchor
            closest_pos = min(positions, key=lambda pos: abs(pos - anchor_pos))
            distance = closest_pos - anchor_pos  # Positive = after, negative = before

            chunk_distances[chunk] = distance
            chunk_lines[chunk] = closest_pos

        return DistancePattern(anchor_chunk=str(anchor_line),  # Store full line as anchor identifier
                anchor_line=anchor_pos, chunk_distances=chunk_distances, chunk_lines=chunk_lines)

    def _create_empty_result(self, filename: str) -> FileAnalysisResult:
        """Create empty result for files with no valid analysis."""
        return FileAnalysisResult(filename=filename, template_file=False, distance_patterns=[], anchor_chunks=[],
                total_chunks_found=0)

    def _is_template_file(self, filename: str) -> bool:
        """Determine if file is the template file."""
        # Use existing template identification logic
        symbol = self._find_split_symbol([str(f) for f in self.files])
        index = self._find_index_num([str(f) for f in self.files], symbol)

        try:
            file_chunks = Path(filename).name.split(symbol)
            return index < len(file_chunks) and file_chunks[index] in self.title
        except:
            return False

    def _find_split_symbol(self, files: List[str]) -> str:
        """Find the most common punctuation/space symbol in filenames."""
        symbols = []
        for filename in files:
            for char in Path(filename).name:
                if char in punctuation or char.isspace():
                    symbols.append(char)

        if not symbols:
            return '-'

        counter = Counter(symbols)
        return counter.most_common(1)[0][0]

    def _find_index_num(self, files: List[str], symbol: str) -> int:
        """Find the index position where title chunks typically appear."""
        all_elements = []
        for filename in files:
            chunks = Path(filename).name.split(symbol)
            all_elements.extend(chunks)

        if not all_elements:
            return 0

        counter = Counter(all_elements)
        least_common = counter.most_common()[-1][0]

        for filename in files:
            chunks = Path(filename).name.split(symbol)
            try:
                return chunks.index(least_common)
            except ValueError:
                continue
        return 0
