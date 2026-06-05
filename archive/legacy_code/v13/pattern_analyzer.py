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
class ChunkPattern:
    """Pattern characteristics for a title chunk."""
    original_value: str
    length: int
    is_alpha: bool
    is_digit: bool
    is_mixed: bool  # Mixed alphanumeric (not pure alpha, not pure digit)


@dataclass
class MultiFilePatternAnalyzer:
    """
    Analyzes patterns across multiple files using stable line anchors.
    Supports multi-anchor scenarios where title chunks split across document areas.
    Uses pattern-based validation for dynamic chunk detection.
    """
    title: str
    files: List[Path] = field(default_factory=list)
    max_distance_threshold: int = 15

    # NEW: Multi-anchor support
    anchor_chunk_assignments: Dict[Tuple[str, ...], Dict[str, int]] = field(default_factory=dict)
    viable_anchors: List[List[str]] = field(default_factory=list)

    # NEW: Pattern-based validation
    chunk_patterns: Dict[str, ChunkPattern] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize derived fields after dataclass creation."""
        self.title_chunks = self._extract_title_chunks()
        self._learn_chunk_patterns()

    def _extract_title_chunks(self) -> List[str]:
        """Extract individual chunks from the title string."""
        separators = ['-', '_', '.', ' ']
        for sep in separators:
            if sep in self.title:
                chunks = [chunk.strip() for chunk in self.title.split(sep) if chunk.strip()]
                if len(chunks) > 1:
                    return chunks
        return [self.title]

    def _learn_chunk_patterns(self):
        """
        Learn the pattern characteristics of each title chunk from the template title.
        Uses EXCLUSIVE type checking: alpha XOR digit XOR mixed.
        """
        for chunk in self.title_chunks:
            # Determine chunk type EXCLUSIVELY
            is_alpha = chunk.isalpha()
            is_digit = chunk.isdigit()
            is_mixed = chunk.isalnum() and not is_alpha and not is_digit

            self.chunk_patterns[chunk] = ChunkPattern(original_value=chunk, length=len(chunk), is_alpha=is_alpha,
                    is_digit=is_digit, is_mixed=is_mixed)

    def _matches_chunk_pattern(self, candidate: str, template_chunk: str) -> bool:
        """
        Check if a candidate string matches the pattern of a template chunk.
        Uses EXCLUSIVE type checking to avoid ambiguity.

        Args:
            candidate: The string found in the file at predicted position
            template_chunk: The original chunk from the template title

        Returns:
            True if candidate matches the pattern characteristics
        """
        if template_chunk not in self.chunk_patterns:
            return False

        pattern = self.chunk_patterns[template_chunk]

        # Length must match exactly
        if len(candidate) != pattern.length:
            return False

        # Determine candidate type EXCLUSIVELY
        candidate_is_alpha = candidate.isalpha()
        candidate_is_digit = candidate.isdigit()
        candidate_is_mixed = candidate.isalnum() and not candidate_is_alpha and not candidate_is_digit

        # Match based on pattern type (EXCLUSIVE)
        if pattern.is_alpha:
            return candidate_is_alpha
        elif pattern.is_digit:
            return candidate_is_digit
        elif pattern.is_mixed:
            return candidate_is_mixed

        return False

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

            all_file_data[str(file_path)] = {'filtered_lines' : filtered_lines,
                                             'chunk_positions': filtered_frequency_data['chunk_line_positions']}

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
        """
        Normalize file encodings for consistent character representation.
        Fastest strategy: Direct character replacement without ML detection.

        Returns:
            List of normalized file paths (original paths, normalization applied internally)
        """
        print("NORMALIZING FILE ENCODINGS...")

        # Greek to Latin character mappings for common lookalikes
        greek_to_latin = {'Α': 'A', 'Β': 'B', 'Γ': 'G', 'Δ': 'D', 'Ε': 'E', 'Ζ': 'Z', 'Η': 'H', 'Θ': 'T', 'Ι': 'I',
                          'Κ': 'K', 'Λ': 'L', 'Μ': 'M', 'Ν': 'N', 'Ξ': 'X', 'Ο': 'O', 'Π': 'P', 'Ρ': 'R', 'Σ': 'S',
                          'Τ': 'T', 'Υ': 'Y', 'Φ': 'F', 'Χ': 'C', 'Ψ': 'P', 'Ω': 'O',  # Include lowercase versions
                          'α': 'a', 'β': 'b', 'γ': 'g', 'δ': 'd', 'ε': 'e', 'ζ': 'z', 'η': 'h', 'θ': 't', 'ι': 'i',
                          'κ': 'k', 'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'x', 'ο': 'o', 'π': 'p', 'ρ': 'r', 'σ': 's',
                          'τ': 't', 'υ': 'y', 'φ': 'f', 'χ': 'c', 'ψ': 'p', 'ω': 'o', 'ς': 's'}

        normalized_files = []

        for file_path in self.files:
            original_name = file_path.name
            normalized_name = original_name

            # Apply character normalization
            for greek_char, latin_char in greek_to_latin.items():
                if greek_char in normalized_name:
                    normalized_name = normalized_name.replace(greek_char, latin_char)
                    print(f"NORMALIZED: {greek_char} → {latin_char} in {file_path.name}")

            # Create normalized path (keeping original file, just tracking the normalization)
            normalized_files.append(file_path)

            # Update title chunks if they contain Greek characters
            if hasattr(self, 'title') and any(greek_char in self.title for greek_char in greek_to_latin.keys()):
                original_title = self.title
                for greek_char, latin_char in greek_to_latin.items():
                    self.title = self.title.replace(greek_char, latin_char)
                if original_title != self.title:
                    print(f"TITLE NORMALIZED: '{original_title}' → '{self.title}'")
                    # Re-extract title chunks with normalized title
                    self.title_chunks = self._extract_title_chunks()

        print(f"NORMALIZATION COMPLETE: {len(normalized_files)} files processed")
        return normalized_files

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
        aggregated_chunks = {}

        for anchor_pos in anchor_positions:
            for chunk in self.title_chunks:
                if chunk in validated_positions:
                    distances = [pos - anchor_pos for pos in validated_positions[chunk]]
                    closest_distance = min(distances, key=abs)

                    if abs(closest_distance) <= self.max_distance_threshold:
                        if chunk not in aggregated_chunks or abs(closest_distance) < abs(aggregated_chunks[chunk]):
                            aggregated_chunks[chunk] = closest_distance

        if aggregated_chunks:
            if anchor_key not in self.anchor_chunk_assignments:
                self.anchor_chunk_assignments[anchor_key] = {}

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
                                      anchor_chunks=[str(anchor_line)],
                                      total_chunks_found=len(distance_pattern.chunk_distances))

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

    def find_multiple_anchors(self, all_file_data: Dict) -> List[List[str]]:
        """
        Find all viable anchors needed for complete chunk coverage.
        Evaluates multiple candidate combinations and picks the best by distance quality.
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

        coverage_options = []
        temp_anchors = []

        max_candidates = min(30, len(scored_anchors))

        for score, anchor_line in scored_anchors[:max_candidates]:
            temp_anchors.append(anchor_line)

            temp_covered = set()
            for anchor in temp_anchors:
                anchor_key = tuple(anchor)
                if anchor_key in self.anchor_chunk_assignments:
                    temp_covered.update(self.anchor_chunk_assignments[anchor_key].keys())

            if temp_covered == set(self.title_chunks):
                coverage_options.append(temp_anchors.copy())

        if not coverage_options:
            print("WARNING: Could not achieve complete chunk coverage with available anchors")
            return []

        best_option = min(coverage_options, key=lambda anchors: self._calculate_option_distance(anchors))
        self.viable_anchors = best_option

        print(f"Complete coverage achieved with {len(self.viable_anchors)} anchor(s)")
        print(f"Evaluated {len(coverage_options)} coverage options, selected best by distance")

        self.viable_anchors = self._deduplicate_and_rank_anchors(self.viable_anchors)

        return self.viable_anchors

    def _calculate_option_distance(self, anchors: List[List[str]]) -> float:
        """Calculate average distance metric for a set of anchors."""
        total_distance = 0
        total_chunks = 0

        for anchor in anchors:
            anchor_key = tuple(anchor)
            if anchor_key in self.anchor_chunk_assignments:
                chunk_map = self.anchor_chunk_assignments[anchor_key]
                for dist in chunk_map.values():
                    total_distance += abs(dist)
                    total_chunks += 1

        return total_distance / total_chunks if total_chunks > 0 else float('inf')

    def _validate_coverage_from_selected(self) -> bool:
        """Check coverage only from anchors in viable_anchors list."""
        all_covered = set()
        for anchor in self.viable_anchors:
            anchor_key = tuple(anchor)
            if anchor_key in self.anchor_chunk_assignments:
                all_covered.update(self.anchor_chunk_assignments[anchor_key].keys())

        missing = set(self.title_chunks) - all_covered
        if missing:
            print(f"DEBUG: Missing from selected anchors: {missing}")
        return len(missing) == 0

    def _deduplicate_and_rank_anchors(self, anchors: List[List[str]]) -> List[List[str]]:
        """
        Remove duplicate coverage and rank anchors by distance quality.

        Strategy:
        1. Group anchors by the chunk-set they cover
        2. Within each group, keep only the anchor with best (shortest) distances
        3. Sort final list by average distance for reliability fallback
        """
        anchor_metadata = []
        for anchor in anchors:
            anchor_key = tuple(anchor)
            chunk_map = self.anchor_chunk_assignments.get(anchor_key, {})

            if not chunk_map:
                continue

            distances = list(chunk_map.values())
            avg_distance = sum(abs(d) for d in distances) / len(distances)
            max_distance = max(abs(d) for d in distances)
            chunk_set = frozenset(chunk_map.keys())

            anchor_metadata.append(
                    {'anchor'      : anchor, 'anchor_key': anchor_key, 'chunk_set': chunk_set, 'chunk_map': chunk_map,
                     'avg_distance': avg_distance, 'max_distance': max_distance, 'coverage_count': len(chunk_map)})

        coverage_groups = {}
        for meta in anchor_metadata:
            chunk_set = meta['chunk_set']
            if chunk_set not in coverage_groups:
                coverage_groups[chunk_set] = []
            coverage_groups[chunk_set].append(meta)

        deduplicated = []
        for chunk_set, group in coverage_groups.items():
            group.sort(key=lambda x: (x['avg_distance'], x['max_distance']))
            best = group[0]
            deduplicated.append(best)

        deduplicated.sort(key=lambda x: (x['avg_distance'], -x['coverage_count']))

        result = [meta['anchor'] for meta in deduplicated]

        print(f"\nDeduplicated {len(anchor_metadata)} anchors down to {len(result)}")

        return result

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

    # ==================== PATTERN-BASED VALIDATION ====================

    def validate_anchors_on_files(self, all_file_data: Dict) -> Dict:
        """
        Validate discovered anchors across all files using PATTERN MATCHING.
        Tests if anchors can be found and if chunks matching the PATTERN exist at predicted positions.

        Returns:
            Dict with validation statistics and per-file results
        """
        if not self.viable_anchors or not self.anchor_chunk_assignments:
            return {'error': 'No anchors to validate'}

        validation_results = {'total_files': len(all_file_data), 'successful_files': 0, 'failed_files': 0,
            'per_file_results'             : {}, 'anchor_success_rates': {}}

        for anchor in self.viable_anchors:
            anchor_key = tuple(anchor)
            validation_results['anchor_success_rates'][anchor_key] = {'found_count': 0, 'chunks_matched': 0,
                'total_chunks'                                                     : len(
                    self.anchor_chunk_assignments.get(anchor_key, {}))}

        for filename, file_data in all_file_data.items():
            file_result = self._validate_single_file_pattern_based(filename, file_data)
            validation_results['per_file_results'][filename] = file_result

            if file_result['all_chunks_found']:
                validation_results['successful_files'] += 1
            else:
                validation_results['failed_files'] += 1

            for anchor_key, anchor_data in file_result['anchor_results'].items():
                if anchor_data['found']:
                    validation_results['anchor_success_rates'][anchor_key]['found_count'] += 1
                    validation_results['anchor_success_rates'][anchor_key]['chunks_matched'] += anchor_data[
                        'chunks_matched']

        validation_results['success_rate'] = (
                validation_results['successful_files'] / validation_results['total_files'] * 100)

        return validation_results

    def _validate_single_file_pattern_based(self, filename: str, file_data: Dict) -> Dict:
        """
        Validate anchors and chunk predictions for a single file using PATTERN MATCHING.
        Instead of looking for exact chunk values, checks if something matching the pattern exists.
        """
        filtered_lines = file_data['filtered_lines']

        file_result = {'filename': filename, 'anchor_results': {}, 'found_chunks': set(), 'missing_chunks': set(),
            'all_chunks_found'   : False}

        for anchor in self.viable_anchors:
            anchor_key = tuple(anchor)
            chunk_map = self.anchor_chunk_assignments.get(anchor_key, {})

            if not chunk_map:
                continue

            anchor_positions = []
            for line_num, line in enumerate(filtered_lines):
                if line == anchor:
                    anchor_positions.append(line_num)

            anchor_result = {'found': len(anchor_positions) > 0, 'positions': anchor_positions, 'chunks_matched': 0,
                'chunk_details'     : {}}

            if anchor_positions:
                anchor_pos = anchor_positions[0]

                for template_chunk, distance in chunk_map.items():
                    predicted_line = anchor_pos + distance

                    found = False
                    found_value = None

                    if 0 <= predicted_line < len(filtered_lines):
                        line_content = filtered_lines[predicted_line]

                        # Check each word in the line for pattern match
                        for word in line_content:
                            if template_chunk == 'B1':  # Focus on the problematic chunk
                                print(f"\n[DEBUG B1] File: {Path(filename).name}")
                                print(f"  Predicted line {predicted_line}: {line_content}")
                                print(f"  Checking word: '{word}'")
                                print(f"  Pattern for B1: {self.chunk_patterns[template_chunk]}")

                                # Check candidate characteristics
                                candidate_is_alpha = word.isalpha()
                                candidate_is_digit = word.isdigit()
                                candidate_is_mixed = (word.isalnum() and not
                                candidate_is_alpha and not
                                candidate_is_digit)

                                print(f"  Candidate '{word}': len={len(word)}, "
                                      f"alpha={candidate_is_alpha}, "
                                      f"digit={candidate_is_digit}, "
                                      f"mixed={candidate_is_mixed}")
                                print(f"  Match result: {self._matches_chunk_pattern(word, template_chunk)}")
                            if self._matches_chunk_pattern(word, template_chunk):
                                found = True
                                found_value = word
                                file_result['found_chunks'].add(template_chunk)
                                anchor_result['chunks_matched'] += 1
                                break

                    anchor_result['chunk_details'][template_chunk] = {'predicted_line': predicted_line, 'found': found,
                        'found_value'                                                 : found_value}

            file_result['anchor_results'][anchor_key] = anchor_result

        file_result['missing_chunks'] = set(self.title_chunks) - file_result['found_chunks']
        file_result['all_chunks_found'] = len(file_result['missing_chunks']) == 0

        return file_result

    def print_validation_report(self, validation_results: Dict):
        """Print a human-readable validation report."""
        print(f"\n{'=' * 60}")
        print("ANCHOR VALIDATION REPORT (Pattern-Based)")
        print(f"{'=' * 60}")

        print(f"\nOverall Statistics:")
        print(f"  Total files tested: {validation_results['total_files']}")
        print(f"  Successful: {validation_results['successful_files']} ({validation_results['success_rate']:.1f}%)")
        print(f"  Failed: {validation_results['failed_files']}")

        print(f"\nPer-Anchor Success Rates:")
        for anchor_key, stats in validation_results['anchor_success_rates'].items():
            anchor_str = ' '.join(anchor_key)
            found_rate = stats['found_count'] / validation_results['total_files'] * 100
            if stats['total_chunks'] > 0:
                chunk_rate = stats['chunks_matched'] / (stats['total_chunks'] * validation_results['total_files']) * 100
            else:
                chunk_rate = 0

            print(f"\n  [{anchor_str}]")
            print(f"    Found in files: {stats['found_count']}/{validation_results['total_files']} ({found_rate:.1f}%)")
            print(f"    Chunks matched: {stats['chunks_matched']}/{stats['total_chunks'] * validation_results['total_files']} ({chunk_rate:.1f}%)")

        if validation_results['failed_files'] > 0:
            print(f"\nFailed Files:")
            for filename, result in validation_results['per_file_results'].items():
                if not result['all_chunks_found']:
                    print(f"  - {Path(filename).name}: Missing {result['missing_chunks']}")

        print(f"\n{'=' * 60}")
