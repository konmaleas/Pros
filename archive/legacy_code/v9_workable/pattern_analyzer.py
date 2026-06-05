from text_extractor import TextExtractor
from text_processor import TextProcessor
from frequency_analyzer import FrequencyAnalyzer
from adaptive_filter import AdaptiveFilter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from collections import Counter, defaultdict
from string import punctuation
from os import rename


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
            # Stages 1A + 1B: Extract and process text
            raw_text, processed_lines = extract_and_process_func(file_path)

            # Stage 2: Frequency analysis on original text (needed for filtering logic)
            frequency_analyzer = FrequencyAnalyzer()
            frequency_data = frequency_analyzer.analyze_text_frequencies(processed_lines)

            # Stage 3: Apply filtering
            adaptive_filter = AdaptiveFilter(title_chunks=self.title_chunks)
            filtered_lines = adaptive_filter.filter_text_lines(processed_lines, frequency_data)

            # SAVE FILTERED TEXT TO FILE FOR ANALYSIS
            self._save_filtered_text_to_file(str(file_path), filtered_lines)

            # Stage 2 REDUX: Run frequency analysis on FILTERED text to get correct positions
            filtered_frequency_analyzer = FrequencyAnalyzer()
            filtered_frequency_data = filtered_frequency_analyzer.analyze_text_frequencies(filtered_lines)

            all_file_data[str(file_path)] = {'filtered_lines' : filtered_lines,
                                             'chunk_positions': filtered_frequency_data['chunk_line_positions']
                                             # CORRECT POSITIONS!
                                             }

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
        Find line patterns that appear in ALL files, excluding title chunk lines.

        Returns:
            List of line patterns (List[str]) that exist across all files
            and do NOT consist entirely of title chunks
        """
        if not all_file_data:
            return []

        # Get all unique line patterns from first file
        first_file = list(all_file_data.values())[0]
        candidate_lines = set()

        for line in first_file['filtered_lines']:
            # EXCLUDE lines that consist entirely of title chunks
            if self._line_is_title_chunk_only(line):
                continue

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

    def _line_is_title_chunk_only(self, line: List[str]) -> bool:
        """
        Check if a line consists entirely of title chunks.

        Args:
            line: List of words in the line

        Returns:
            True if the line contains only title chunks (should be excluded as anchor)
        """
        if not line:
            return False

        # Convert line to text for comparison
        line_text = ' '.join(line).lower().strip()

        # Check if entire line matches any single title chunk
        for chunk in self.title_chunks:
            if line_text == chunk.lower().strip():
                return True

        # Check if line consists entirely of title chunks
        line_words = [word.lower() for word in line if word.strip()]
        title_chunks_lower = [chunk.lower() for chunk in self.title_chunks]

        # If all words in line are title chunks, exclude it
        all_words_are_title_chunks = all(word in title_chunks_lower for word in line_words)

        return all_words_are_title_chunks

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
        # Find ALL anchor positions in this file
        anchor_positions = []
        for line_num, line in enumerate(filtered_lines):
            if line == anchor_line:
                anchor_positions.append(line_num)

        if not anchor_positions:
            return self._create_empty_result(filename)

        # Validate chunk positions against filtered text
        validated_positions = self._validate_chunk_positions(filtered_lines, chunk_positions)

        # Determine if this is template file
        is_template = self._is_template_file(filename)

        if is_template:
            # Template file: use actual found positions
            found_chunks = {chunk: positions for chunk, positions in validated_positions.items() if
                            chunk in self.title_chunks}

            if not found_chunks:
                return self._create_empty_result(filename)

            # Find best anchor position and generate pattern
            best_anchor_pos = self._find_optimal_anchor_position(anchor_positions, found_chunks)
            distance_pattern = self._generate_anchor_distance_pattern(anchor_line, best_anchor_pos, found_chunks)

            # Store template pattern for other files to use
            self._template_distance_pattern = distance_pattern

            # ANALYZE TEMPLATE CHUNKS TO CREATE DYNAMIC VALIDATION RULES
            self._chunk_validation_rules = self._analyze_template_chunk_patterns(found_chunks.keys())

        else:
            # Non-template file: try each anchor position until ALL chunks are found
            if not hasattr(self, '_template_distance_pattern') or self._template_distance_pattern is None:
                return self._create_empty_result(filename)

            distance_pattern = None

            # Try each anchor position until we find ALL template chunks
            for anchor_pos in anchor_positions:
                attempted_pattern = self._generate_template_based_pattern(filename, anchor_line, anchor_pos,
                                                                          validated_positions, filtered_lines)

                # Check if ALL template chunks were found
                if self._validate_complete_pattern(attempted_pattern):
                    distance_pattern = attempted_pattern
                    break  # Success! Use this anchor position

            # If no anchor position yielded complete pattern, return empty result
            if distance_pattern is None:
                return self._create_empty_result(filename)

        return FileAnalysisResult(filename=filename, template_file=is_template,
                                  distance_patterns=[distance_pattern] if distance_pattern else [],
                                  anchor_chunks=[str(anchor_line)], total_chunks_found=sum(
                    len(positions) for positions in validated_positions.values() if
                    positions and any(chunk in str(positions) for chunk in self.title_chunks)))

    def _generate_template_based_pattern(self, filename: str, anchor_line: List[str], anchor_pos: int,
                                         validated_positions: Dict[str, List[int]], filtered_lines: List[List[str]]) -> \
    Optional[DistancePattern]:
        """
        Generate distance pattern using template's relative distances but reading actual chunks from THIS file's positions.
        """
        if not hasattr(self, '_template_distance_pattern') or self._template_distance_pattern is None:
            return None

        chunk_distances = {}
        chunk_lines = {}

        # Get the template's distance values (not the chunk names!)
        template_distances = self._template_distance_pattern.chunk_distances

        # For each template distance, find what chunk actually exists at that position in THIS file
        for template_chunk, distance in template_distances.items():
            predicted_line = anchor_pos + distance

            # Read what chunk actually exists at this line in the current file
            actual_chunk = self._find_chunk_at_line(predicted_line, filtered_lines)

            if actual_chunk:
                chunk_distances[actual_chunk] = distance
                chunk_lines[actual_chunk] = predicted_line

        return DistancePattern(anchor_chunk=str(anchor_line), anchor_line=anchor_pos, chunk_distances=chunk_distances,
                               chunk_lines=chunk_lines)

    def _analyze_template_chunk_patterns(self, template_chunks) -> List[dict]:
        """
        Analyze template file chunks to determine their type and length patterns.

        Args:
            template_chunks: Chunks found in template file

        Returns:
            List of validation rule dictionaries
        """
        patterns = []

        for chunk in template_chunks:
            chunk_clean = str(chunk).strip()
            if not chunk_clean:
                continue

            # Determine chunk characteristics
            pattern = {'length': len(chunk_clean), 'is_alpha': chunk_clean.isalpha(), 'is_digit': chunk_clean.isdigit(),
                'is_alnum'     : chunk_clean.isalnum(), 'example': chunk_clean}

            # Only add unique patterns
            if not any(p['length'] == pattern['length'] and p['is_alpha'] == pattern['is_alpha'] and p['is_digit'] ==
                       pattern['is_digit'] for p in patterns):
                patterns.append(pattern)

        return patterns

    def _validate_chunk_against_patterns(self, chunk: str) -> bool:
        """
        Validate if a chunk matches any of the discovered template patterns.

        Args:
            chunk: The chunk to validate

        Returns:
            True if chunk matches template patterns, False otherwise
        """
        if not hasattr(self, '_chunk_validation_rules') or not self._chunk_validation_rules:
            # Fallback: no rules available
            return False

        chunk_clean = chunk.strip()
        if not chunk_clean:
            return False

        # Check against each discovered pattern
        for pattern in self._chunk_validation_rules:
            if (len(chunk_clean) == pattern['length'] and chunk_clean.isalpha() == pattern[
                'is_alpha'] and chunk_clean.isdigit() == pattern['is_digit']):
                return True

        return False

    def _find_chunk_at_line(self, line_num: int, filtered_lines: List[List[str]]) -> Optional[str]:
        """
        Find what chunk actually exists at the specified line number in filtered text.
        Uses dynamic validation rules discovered from template file analysis.

        Args:
            line_num: The line number to check
            filtered_lines: The filtered text lines

        Returns:
            The chunk found at that line, or None if no valid chunk found
        """
        if line_num < 0 or line_num >= len(filtered_lines):
            return None

        line_content = filtered_lines[line_num]

        # Check each word in the line for chunks matching template patterns
        for word in line_content:
            word_clean = word.strip()
            if not word_clean:
                continue

            # Use dynamic validation based on template analysis
            if self._validate_chunk_against_patterns(word_clean):
                return word_clean

        return None

    def _validate_complete_pattern(self, pattern: Optional[DistancePattern]) -> bool:
        """
        Validate if a distance pattern contains ALL template chunks.

        Args:
            pattern: The distance pattern to validate

        Returns:
            True if pattern has chunks for ALL template distances, False otherwise
        """
        if pattern is None:
            return False

        if not hasattr(self, '_template_distance_pattern') or self._template_distance_pattern is None:
            return False

        template_distances = self._template_distance_pattern.chunk_distances
        found_distances = pattern.chunk_distances

        # Check if we found chunks for ALL template distances
        template_distance_values = set(template_distances.values())
        found_distance_values = set(found_distances.values())

        # ALL template distances must have corresponding chunks found
        return template_distance_values.issubset(found_distance_values)

    def _save_filtered_text_to_file(self, original_file_path: str, filtered_lines: List[List[str]]) -> None:
        """
        Save the filtered text to a file for analysis.

        Args:
            original_file_path: Path of the original PDF file
            filtered_lines: The filtered text lines from AdaptiveFilter
        """
        # Create output filename with timestamped directory
        from datetime import datetime
        original_path = Path(original_file_path)
        output_dir = Path('filtered_texts')
        output_dir.mkdir(parents=True, exist_ok=True)  # Create directory if it doesn't exist
        filename = Path(original_path.stem)
        output_filename = output_dir / filename.with_suffix('.txt')


        # Write filtered text to file
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(f"=== FILTERED TEXT FOR: {original_path.name} ===\n\n")

                for line_num, line_list in enumerate(filtered_lines):
                    # Convert line list back to readable text
                    line_text = ' '.join(line_list)
                    f.write(f"Line {line_num:3d}: {line_text}\n")

                f.write(f"\n=== END OF FILTERED TEXT ===\n")
                f.write(f"Total lines: {len(filtered_lines)}\n")

        except Exception as e:
            print(f"Warning: Could not save filtered text for {original_path.name}: {e}")

    def _extract_file_specific_title_chunks(self, filename: str) -> List[str]:
        """
        Extract title chunks from the specific filename being processed.

        Args:
            filename: The current file being processed (e.g., "4005-RES-VAP-DWG-234-DD-07130-1.pdf")

        Returns:
            List of chunks extracted from this specific filename
        """
        # Get just the filename without path and extension
        base_filename = Path(filename).stem

        # Use the same separator logic as the original title extraction
        separators = ['-', '_', '.', ' ']
        for sep in separators:
            if sep in base_filename:
                chunks = [chunk.strip() for chunk in base_filename.split(sep) if chunk.strip()]
                if len(chunks) > 1:
                    return chunks

        # If no separators found, return the whole filename as single chunk
        return [base_filename]

    def _validate_chunk_positions(self, filtered_lines: List[List[str]], chunk_positions: Dict[str, List[int]]) -> Dict[
        str, List[int]]:
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
