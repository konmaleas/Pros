from text_extractor import TextExtractor
from text_processor import TextProcessor
from frequency_analyzer import FrequencyAnalyzer
from adaptive_filter import AdaptiveFilter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import Counter, defaultdict
from string import punctuation
from datetime import datetime


@dataclass
class DistancePattern:
    """Represents distance patterns from anchor points to other chunks."""
    anchor_chunk: str
    anchor_line: int
    chunk_distances: Dict[str, int]
    chunk_lines: Dict[str, int]


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
    Supports multi-anchor scenarios where title chunks split across document areas.
    """
    title: str
    files: List[Path] = field(default_factory=list)
    max_distance_threshold: int = 15

    # NEW: Multi-anchor support
    anchor_chunk_assignments: Dict[Tuple[str, ...], Dict[str, int]] = field(default_factory=dict)
    viable_anchors: List[List[str]] = field(default_factory=list)

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

    # ==================== ORIGINAL METHODS ====================

    def analyze_all_files(self, extract_and_process_func) -> Dict[str, FileAnalysisResult]:
        """Main entry point: analyze all files using stable line anchors."""
        normalized_files = self._normalize_file_encodings()

        all_file_data = {}
        for file_path in normalized_files:
            raw_text, processed_lines = extract_and_process_func(file_path)

            frequency_analyzer = FrequencyAnalyzer()
            frequency_data = frequency_analyzer.analyze_text_frequencies(processed_lines)

            adaptive_filter = AdaptiveFilter(title_chunks=self.title_chunks)
            filtered_lines = adaptive_filter.filter_text_lines(processed_lines, frequency_data)

            self._save_filtered_text_to_file(str(file_path), filtered_lines)

            filtered_frequency_analyzer = FrequencyAnalyzer()
            filtered_frequency_data = filtered_frequency_analyzer.analyze_text_frequencies(filtered_lines)

            all_file_data[str(file_path)] = {'filtered_lines': filtered_lines,
                'chunk_positions'                            : filtered_frequency_data['chunk_line_positions']}

        stable_anchor_lines = self._find_stable_anchor_lines(all_file_data)
        print(f"STABLE ANCHOR SEARCH: Found {len(stable_anchor_lines)} stable lines")

        if not stable_anchor_lines:
            print("NO STABLE ANCHORS: Files may have completely different text content")
            return {filename: self._create_empty_result(filename) for filename in all_file_data.keys()}

        best_anchor = self._select_best_anchor(stable_anchor_lines, all_file_data)

        if not best_anchor:
            return {filename: self._create_empty_result(filename) for filename in all_file_data.keys()}

        results = {}
        for filename, file_data in all_file_data.items():
            result = self._analyze_single_file_with_anchor(filename, file_data['filtered_lines'],
                    file_data['chunk_positions'], best_anchor)
            results[filename] = result

        return results

    def _normalize_file_encodings(self) -> List[Path]:
        """Normalize file encodings for consistent character representation."""
        return self.files

    def _find_stable_anchor_lines(self, all_file_data: Dict) -> List[List[str]]:
        """Find lines that appear consistently across all files."""
        if not all_file_data:
            return []

        first_file = list(all_file_data.values())[0]
        candidate_lines = set()

        for line in first_file['filtered_lines']:
            if self._line_is_title_chunk_only(line):
                continue
            candidate_lines.add(tuple(line))

        stable_lines = []
        for line_tuple in candidate_lines:
            appears_in_all = True

            for file_data in all_file_data.values():
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
        """Check if a line consists entirely of title chunks."""
        if not line:
            return False

        line_text = ' '.join(line).lower().strip()

        for chunk in self.title_chunks:
            if line_text == chunk.lower().strip():
                return True

        line_words = [word.lower() for word in line if word.strip()]
        title_chunks_lower = [chunk.lower() for chunk in self.title_chunks]

        all_words_are_title_chunks = all(word in title_chunks_lower for word in line_words)

        return all_words_are_title_chunks

    def _select_best_anchor(self, stable_lines: List[List[str]], all_file_data: Dict) -> Optional[List[str]]:
        """Select the best stable line as anchor based on quality criteria."""
        if not stable_lines:
            return None

        scored_anchors = []

        for anchor_line in stable_lines:
            score = self._score_anchor_candidate(anchor_line, all_file_data)
            if score > 0:
                scored_anchors.append((score, anchor_line))

        if not scored_anchors:
            return None

        scored_anchors.sort(reverse=True)
        return scored_anchors[0][1]

    def _score_anchor_candidate(self, anchor_line: List[str], all_file_data: Dict) -> float:
        """Score an anchor candidate based on quality criteria."""
        score = 0.0

        if len(anchor_line) > 1:
            score += len(anchor_line) * 10

        total_occurrences = 0
        for file_data in all_file_data.values():
            occurrences = sum(1 for line in file_data['filtered_lines'] if line == anchor_line)
            total_occurrences += occurrences
            if occurrences > 1:
                score += occurrences * 5

        viable_files = 0
        for filename, file_data in all_file_data.items():
            if self._test_anchor_viability(anchor_line, file_data):
                viable_files += 1

        if viable_files < len(all_file_data):
            return 0

        score += viable_files * 20

        return score

    def _test_anchor_viability(self, anchor_line: List[str], file_data: Dict) -> bool:
        """
        Test if anchor can reach SOME chunks within max_distance_threshold.
        NEW: Aggregates ALL chunks reachable from ANY position of this anchor.
        """
        anchor_positions = []
        for line_num, line in enumerate(file_data['filtered_lines']):
            if line == anchor_line:
                anchor_positions.append(line_num)

        if not anchor_positions:
            return False

        validated_positions = self._validate_chunk_positions(file_data['filtered_lines'], file_data['chunk_positions'])

        anchor_key = tuple(anchor_line)
        aggregated_chunks = {}  # Collect ALL chunks from ALL anchor positions

        for anchor_pos in anchor_positions:
            for chunk in self.title_chunks:
                if chunk in validated_positions:
                    distances = [pos - anchor_pos for pos in validated_positions[chunk]]
                    closest_distance = min(distances, key=abs)

                    if abs(closest_distance) <= self.max_distance_threshold:
                        # If chunk not yet found OR this distance is closer, update it
                        if chunk not in aggregated_chunks or abs(closest_distance) < abs(aggregated_chunks[chunk]):
                            aggregated_chunks[chunk] = closest_distance

        if aggregated_chunks:
            # Merge across all files instead of overwriting
            if anchor_key not in self.anchor_chunk_assignments:
                self.anchor_chunk_assignments[anchor_key] = {}

            # Keep chunk if not exists OR if distance is closer
            for chunk, dist in aggregated_chunks.items():
                if chunk not in self.anchor_chunk_assignments[anchor_key] or abs(dist) < abs(
                        self.anchor_chunk_assignments[anchor_key][chunk]):
                    self.anchor_chunk_assignments[anchor_key][chunk] = dist

            return True

        return False

    def _validate_chunk_positions(self, filtered_lines: List[List[str]], chunk_positions: Dict[str, List[int]]) -> Dict[
        str, List[int]]:
        """Validate that chunk positions match actual content in filtered lines."""
        validated_positions = defaultdict(list)

        for chunk, positions in chunk_positions.items():
            for pos in positions:
                if pos < len(filtered_lines):
                    line_words = filtered_lines[pos]
                    if chunk in line_words:
                        validated_positions[chunk].append(pos)

        return dict(validated_positions)

    def _analyze_single_file_with_anchor(self, filename: str, filtered_lines: List[List[str]],
                                         chunk_positions: Dict[str, List[int]],
                                         anchor_line: List[str]) -> FileAnalysisResult:
        """Analyze a single file using the selected stable anchor."""
        anchor_positions = [i for i, line in enumerate(filtered_lines) if line == anchor_line]

        if not anchor_positions:
            return self._create_empty_result(filename)

        validated_positions = self._validate_chunk_positions(filtered_lines, chunk_positions)

        distance_pattern = None
        for anchor_pos in anchor_positions:
            chunk_distances = {}
            chunk_lines = {}

            for chunk in self.title_chunks:
                if chunk in validated_positions:
                    closest_pos = min(validated_positions[chunk], key=lambda p: abs(p - anchor_pos))
                    distance = closest_pos - anchor_pos

                    if abs(distance) <= self.max_distance_threshold:
                        chunk_distances[chunk] = distance
                        chunk_lines[chunk] = closest_pos

            if len(chunk_distances) == len(self.title_chunks):
                distance_pattern = DistancePattern(anchor_chunk=str(anchor_line), anchor_line=anchor_pos,
                        chunk_distances=chunk_distances, chunk_lines=chunk_lines)
                break

        if distance_pattern:
            return FileAnalysisResult(filename=filename, template_file=False, distance_patterns=[distance_pattern],
                    anchor_chunks=[str(anchor_line)], total_chunks_found=len(distance_pattern.chunk_distances))

        return self._create_empty_result(filename)

    def _create_empty_result(self, filename: str) -> FileAnalysisResult:
        """Create an empty result for files with no valid pattern."""
        return FileAnalysisResult(filename=filename, template_file=False, distance_patterns=[], anchor_chunks=[],
                total_chunks_found=0)

    def _save_filtered_text_to_file(self, original_file_path: str, filtered_lines: List[List[str]]) -> None:
        """Save the filtered text to a file for analysis."""
        original_path = Path(original_file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_dir = Path('filtered_texts')
        output_dir = base_dir / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)
        output_filename = output_dir / original_path.name

        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(f"=== FILTERED TEXT FOR: {original_path.name} ===\n\n")

                for line_num, line_list in enumerate(filtered_lines):
                    line_text = ' '.join(line_list)
                    f.write(f"Line {line_num:3d}: {line_text}\n")

                f.write(f"\n=== END OF FILTERED TEXT ===\n")
                f.write(f"Total lines: {len(filtered_lines)}\n")

        except Exception as e:
            print(f"Warning: Could not save filtered text for {original_path.name}: {e}")

    # ==================== NEW MULTI-ANCHOR METHODS ====================

    def find_multiple_anchors(self, all_file_data: Dict, max_anchors: int = 5) -> List[List[str]]:
        """
        Find multiple viable anchors to ensure complete chunk coverage.
        Iteratively finds anchors until all chunks are covered or max_anchors reached.
        """
        stable_lines = self._find_stable_anchor_lines(all_file_data)

        if not stable_lines:
            return []

        self.anchor_chunk_assignments.clear()
        self.viable_anchors.clear()

        scored_anchors = []
        for anchor_line in stable_lines:
            score = self._score_anchor_candidate(anchor_line, all_file_data)
            if score > 0:
                scored_anchors.append((score, anchor_line))

        if not scored_anchors:
            return []

        scored_anchors.sort(reverse=True)

        for score, anchor_line in scored_anchors:
            if len(self.viable_anchors) >= max_anchors:
                break

            self.viable_anchors.append(anchor_line)

            if self._validate_complete_coverage():
                print(f"Complete coverage achieved with {len(self.viable_anchors)} anchor(s)")
                break

        if not self._validate_complete_coverage():
            print("WARNING: Could not achieve complete chunk coverage with available anchors")

        return self.viable_anchors

    def _validate_complete_coverage(self) -> bool:
        """Verify that ALL title chunks are covered by at least one anchor."""
        all_covered_chunks = set()

        for chunk_map in self.anchor_chunk_assignments.values():
            all_covered_chunks.update(chunk_map.keys())

        required_chunks = set(self.title_chunks)
        missing_chunks = required_chunks - all_covered_chunks

        if missing_chunks:
            print(f"WARNING: Missing chunk coverage: {missing_chunks}")
            return False

        return True

    def get_anchor_coverage_report(self) -> str:
        """Generate a human-readable report of anchor coverage."""
        if not self.anchor_chunk_assignments:
            return "No anchor assignments found"

        report_lines = ["=== Anchor Coverage Report ===\n"]

        for anchor_key, chunk_map in self.anchor_chunk_assignments.items():
            anchor_str = " ".join(anchor_key)
            report_lines.append(f"\nAnchor: [{anchor_str}]")
            report_lines.append(f"  Covers {len(chunk_map)} chunk(s):")

            for chunk, distance in sorted(chunk_map.items(), key=lambda x: x[1]):
                sign = "+" if distance >= 0 else ""
                report_lines.append(f"    - {chunk}: {sign}{distance} lines")

        all_covered = set()
        for chunk_map in self.anchor_chunk_assignments.values():
            all_covered.update(chunk_map.keys())

        missing = set(self.title_chunks) - all_covered

        report_lines.append(f"\n=== Coverage Summary ===")
        report_lines.append(f"Total chunks: {len(self.title_chunks)}")
        report_lines.append(f"Covered: {len(all_covered)}")
        report_lines.append(f"Missing: {len(missing)}")

        if missing:
            report_lines.append(f"Missing chunks: {', '.join(missing)}")
        else:
            report_lines.append("✓ Complete coverage achieved!")

        return "\n".join(report_lines)
