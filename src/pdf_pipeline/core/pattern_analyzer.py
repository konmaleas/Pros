from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from datetime import datetime as dt2
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from icecream import ic

from ..models.patterns import ChunkPattern, DistancePattern, FileAnalysisResult
from .adaptive_filter import AdaptiveFilter
from .frequency_analyzer import FrequencyAnalyzer


def ict():
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


@dataclass
class MultiFilePatternAnalyzer:
    """
    Analyzes patterns across multiple files using stable line anchors.
    Supports multi-anchor scenarios where title chunks split across document areas.
    Uses pattern-based validation with adaptive offset learning.
    """
    title: str
    files: List[Path] = field(default_factory=list)
    max_distance_threshold: int = 15

    # Multi-anchor support
    anchor_chunk_assignments: Dict[Tuple[str, ...], Dict[str, int]] = field(default_factory=dict)
    viable_anchors: List[List[str]] = field(default_factory=list)

    # Pattern-based validation
    chunk_patterns: Dict[str, ChunkPattern] = field(default_factory=dict)

    # NEW: Learned offset storage (per-anchor, keyed by template chunk name)
    discovered_offsets: Dict[Tuple[str, ...], Dict[str, List[int]]] = field(default_factory=dict)

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
            is_alpha = chunk.isalpha()
            is_digit = chunk.isdigit()
            is_mixed = chunk.isalnum() and not is_alpha and not is_digit

            self.chunk_patterns[chunk] = ChunkPattern(original_value=chunk, length=len(chunk), is_alpha=is_alpha,
                    is_digit=is_digit, is_mixed=is_mixed)

    def _matches_chunk_pattern(self, candidate: str, template_chunk: str) -> bool:
        """
        Check if a candidate string matches the pattern of a template chunk.
        Uses EXCLUSIVE type checking to avoid ambiguity.
        """
        if template_chunk not in self.chunk_patterns:
            return False

        pattern = self.chunk_patterns[template_chunk]

        if len(candidate) != pattern.length:
            return False

        candidate_is_alpha = candidate.isalpha()
        candidate_is_digit = candidate.isdigit()
        candidate_is_mixed = candidate.isalnum() and not candidate_is_alpha and not candidate_is_digit

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

            self.save_filtered_text_to_file(str(file_path), filtered_lines)

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
        """
        print("NORMALIZING FILE ENCODINGS...")

        greek_to_latin = {'Α': 'A', 'Β': 'B', 'Γ': 'G', 'Δ': 'D', 'Ε': 'E', 'Ζ': 'Z', 'Η': 'H', 'Θ': 'T', 'Ι': 'I',
                          'Κ': 'K', 'Λ': 'L', 'Μ': 'M', 'Ν': 'N', 'Ξ': 'X', 'Ο': 'O', 'Π': 'P', 'Ρ': 'R', 'Σ': 'S',
                          'Τ': 'T', 'Υ': 'Y', 'Φ': 'F', 'Χ': 'C', 'Ψ': 'P', 'Ω': 'O', 'α': 'a', 'β': 'b', 'γ': 'g',
                          'δ': 'd', 'ε': 'e', 'ζ': 'z', 'η': 'h', 'θ': 't', 'ι': 'i', 'κ': 'k', 'λ': 'l', 'μ': 'm',
                          'ν': 'n', 'ξ': 'x', 'ο': 'o', 'π': 'p', 'ρ': 'r', 'σ': 's', 'τ': 't', 'υ': 'y', 'φ': 'f',
                          'χ': 'c', 'ψ': 'p', 'ω': 'o', 'ς': 's'}

        normalized_files = []

        for file_path in self.files:
            original_name = file_path.name
            normalized_name = original_name

            for greek_char, latin_char in greek_to_latin.items():
                if greek_char in normalized_name:
                    normalized_name = normalized_name.replace(greek_char, latin_char)
                    print(f"NORMALIZED: {greek_char} → {latin_char} in {file_path.name}")

            normalized_files.append(file_path)

            if hasattr(self, 'title') and any(greek_char in self.title for greek_char in greek_to_latin.keys()):
                original_title = self.title
                for greek_char, latin_char in greek_to_latin.items():
                    self.title = self.title.replace(greek_char, latin_char)
                if original_title != self.title:
                    print(f"TITLE NORMALIZED: '{original_title}' → '{self.title}'")
                    self.title_chunks = self._extract_title_chunks()

        print(f"NORMALIZATION COMPLETE: {len(normalized_files)} files processed")
        return normalized_files

    def _find_stable_anchor_lines(self, all_file_data: Dict) -> List[List[str]]:
        """Find lines that appear consistently across all files."""
        if not all_file_data:
            return []

        first_file = list(all_file_data.values())[0]
        candidate_lines = set()

        # CHANGED: processed_lines instead of filtered_lines
        for line in first_file['processed_lines']:
            if self._line_is_title_chunk_only(line):
                continue
            candidate_lines.add(tuple(line))

        stable_lines = []
        for line_tuple in candidate_lines:
            appears_in_all = True

            for file_data in all_file_data.values():
                line_found = False
                # CHANGED: processed_lines instead of filtered_lines
                for file_line in file_data['processed_lines']:
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
            occurrences = sum(1 for line in file_data['processed_lines'] if line == anchor_line)
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
        """Test if anchor can reach SOME chunks within max_distance_threshold."""
        anchor_positions = []
        # CHANGED: processed_lines instead of filtered_lines
        for line_num, line in enumerate(file_data['processed_lines']):
            if line == anchor_line:
                anchor_positions.append(line_num)

        if not anchor_positions:
            return False

        # CHANGED: processed_lines instead of filtered_lines
        validated_positions = self._validate_chunk_positions(file_data['processed_lines'], file_data['chunk_positions'])

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

    def save_filtered_text_to_file(self, original_file_path: str, filtered_lines: List[List[str]]) -> None:
        """Save the filtered text to a file for analysis."""
        original_path = Path(original_file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")[:-3]
        base_dir = Path('filtered_texts')
        output_dir = base_dir / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)

        # NEW: Use .txt suffix instead of keeping .pdf
        output_filename = output_dir / f"{original_path.stem}.txt"

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

    # ==================== MULTI-ANCHOR METHODS ====================

    def find_multiple_anchors(self, all_file_data: Dict) -> List[List[str]]:
        """Find all viable anchors needed for complete chunk coverage."""
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
        """Remove duplicate coverage and rank anchors by distance quality."""
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

    # ==================== TWO-PASS PATTERN-BASED VALIDATION ====================

    def validate_anchors_on_files(self, all_file_data: Dict) -> Dict:
        """
        Two-pass validation with adaptive offset learning.
        Pass 1: Validate with template offsets, discover new offsets
        Pass 2: Revalidate failed files with learned offsets
        """
        if not self.viable_anchors or not self.anchor_chunk_assignments:
            return {'error': 'No anchors to validate'}

        # Initialize discovered offsets storage
        for anchor in self.viable_anchors:
            anchor_key = tuple(anchor)
            if anchor_key not in self.discovered_offsets:
                self.discovered_offsets[anchor_key] = {}

            # Initialize with template offsets
            chunk_map = self.anchor_chunk_assignments.get(anchor_key, {})
            for template_chunk, offset in chunk_map.items():
                if template_chunk not in self.discovered_offsets[anchor_key]:
                    self.discovered_offsets[anchor_key][template_chunk] = [offset]

        print("\n=== PASS 1: Template Offset Validation ===")
        validation_results = self._run_validation_pass(all_file_data, pass_number=1)

        # If all files succeeded, no need for Pass 2
        if validation_results['failed_files'] == 0:
            print("✓ All files validated successfully in Pass 1")
            return validation_results

        print(f"\n=== PASS 2: Learned Offset Validation ===")
        print(f"Discovered {self._count_discovered_offsets()} new offset(s) from Pass 1")
        print(f"Revalidating {validation_results['failed_files']} failed file(s)...")

        # Run Pass 2 only on failed files
        pass2_results = self._run_validation_pass(all_file_data, pass_number=2, failed_files_only=True,
                                                  previous_results=validation_results)

        return pass2_results

    def _count_discovered_offsets(self) -> int:
        """Count total number of discovered offsets across all anchors."""
        total = 0
        for anchor_key, chunk_offsets in self.discovered_offsets.items():
            for template_chunk, offsets in chunk_offsets.items():
                total += len(offsets) - 1  # Subtract 1 for template offset
        return total

    def _run_validation_pass(self, all_file_data: Dict, pass_number: int, failed_files_only: bool = False,
                             previous_results: Dict = None) -> Dict:
        """Run a single validation pass."""
        if failed_files_only and previous_results:
            # Only process files that failed in previous pass
            files_to_process = {filename: file_data for filename, file_data in all_file_data.items() if
                not previous_results['per_file_results'][filename]['all_chunks_found']}
        else:
            files_to_process = all_file_data

        validation_results = {'total_files': len(all_file_data),
            'successful_files'             : 0 if not previous_results else previous_results['successful_files'],
            'failed_files'                 : 0,
            'per_file_results'             : previous_results['per_file_results'].copy() if previous_results else {},
            'anchor_success_rates'         : {}}

        # Initialize anchor statistics
        for anchor in self.viable_anchors:
            anchor_key = tuple(anchor)
            validation_results['anchor_success_rates'][anchor_key] = {'found_count': 0, 'chunks_matched': 0,
                'total_chunks'                                                     : len(
                    self.anchor_chunk_assignments.get(anchor_key, {}))}

        # Validate files
        for filename, file_data in files_to_process.items():
            file_result = self._validate_single_file_adaptive(filename, file_data, pass_number)
            validation_results['per_file_results'][filename] = file_result

            if file_result['all_chunks_found']:
                if failed_files_only:
                    # This was a failed file that now succeeded
                    validation_results['successful_files'] += 1
                elif not previous_results:
                    # Pass 1: count successful files
                    validation_results['successful_files'] += 1
            else:
                validation_results['failed_files'] += 1

            # Update anchor statistics
            for anchor_key, anchor_data in file_result['anchor_results'].items():
                if anchor_data['found']:
                    validation_results['anchor_success_rates'][anchor_key]['found_count'] += 1
                    validation_results['anchor_success_rates'][anchor_key]['chunks_matched'] += anchor_data[
                        'chunks_matched']

        # Recalculate failed files count if this is Pass 2
        if failed_files_only and previous_results:
            validation_results['failed_files'] = (
                    validation_results['total_files'] - validation_results['successful_files'])

        validation_results['success_rate'] = (
                validation_results['successful_files'] / validation_results['total_files'] * 100)

        return validation_results

    def _validate_single_file_adaptive(self, filename: str, file_data: Dict, pass_number: int) -> Dict:
        """Validate a single file with GREEDY ASSIGNMENT."""
        # CHANGED: processed_lines instead of filtered_lines
        processed_lines = file_data['processed_lines']

        file_result = {'filename': filename, 'anchor_results': {}, 'found_chunks': set(), 'missing_chunks': set(),
            'all_chunks_found'   : False}

        for anchor in self.viable_anchors:
            anchor_key = tuple(anchor)
            chunk_map = self.anchor_chunk_assignments.get(anchor_key, {})

            if not chunk_map:
                continue

            # Find anchor positions in PROCESSED lines
            anchor_positions = []
            for line_num, line in enumerate(processed_lines):
                if line == anchor:
                    anchor_positions.append(line_num)

            anchor_result = {'found': len(anchor_positions) > 0, 'positions': anchor_positions, 'chunks_matched': 0,
                'chunk_details'     : {}}

            if anchor_positions:
                anchor_pos = anchor_positions[0]

                # Collect ALL candidates for ALL templates
                candidates = {}

                for template_chunk, base_distance in chunk_map.items():
                    candidates[template_chunk] = []

                    if pass_number == 1:
                        # Pass 1: Search with window in PROCESSED lines
                        matches = self._search_with_window_all_matches(anchor_pos, base_distance, template_chunk,
                                processed_lines)
                    else:
                        # Pass 2: Search with learned offsets in PROCESSED lines
                        matches = self._search_with_learned_offsets_all_matches(anchor_pos, template_chunk, anchor_key,
                                base_distance, processed_lines)

                    candidates[template_chunk] = matches

                # Greedy assignment
                assignments = self._greedy_assign_chunks(candidates, chunk_map)

                # Store results
                for template_chunk, base_distance in chunk_map.items():
                    if template_chunk in assignments:
                        found_value, found_offset = assignments[template_chunk]

                        file_result['found_chunks'].add(template_chunk)
                        anchor_result['chunks_matched'] += 1

                        # Learn new offset if different from template
                        if pass_number == 1 and found_offset != base_distance:
                            self._store_discovered_offset(anchor_key, template_chunk, found_offset)

                        anchor_result['chunk_details'][template_chunk] = {'predicted_line': anchor_pos + base_distance,
                            'found'                                                       : True,
                            'found_value'                                                 : found_value,
                            'found_offset'                                                : found_offset}
                    else:
                        anchor_result['chunk_details'][template_chunk] = {'predicted_line': anchor_pos + base_distance,
                            'found'                                                       : False, 'found_value': None,
                            'found_offset'                                                : None}

            file_result['anchor_results'][anchor_key] = anchor_result

        file_result['missing_chunks'] = set(self.title_chunks) - file_result['found_chunks']
        file_result['all_chunks_found'] = len(file_result['missing_chunks']) == 0

        return file_result

    def _greedy_assign_chunks(self, candidates: Dict[str, List[Tuple]], chunk_map: Dict[str, int]) -> Dict[str, Tuple]:
        """
        Greedy assignment: Assign each found value to the template with closest offset.

        Args:
            candidates: {template_chunk: [(found_value, found_offset, offset_distance), ...]}
            chunk_map: {template_chunk: expected_offset}

        Returns:
            {template_chunk: (found_value, found_offset)}
        """
        assignments = {}
        used_values = set()

        # Build list of all possible (template, value, offset, distance) tuples
        all_matches = []
        for template_chunk, matches in candidates.items():
            for found_value, found_offset, offset_distance in matches:
                all_matches.append((template_chunk, found_value, found_offset, offset_distance))

        # Sort by offset distance (closest first)
        all_matches.sort(key=lambda x: x[3])

        # Greedy assignment: process closest matches first
        for template_chunk, found_value, found_offset, offset_distance in all_matches:
            # Skip if template already assigned or value already used
            if template_chunk in assignments or found_value in used_values:
                continue

            # Assign this value to this template
            assignments[template_chunk] = (found_value, found_offset)
            used_values.add(found_value)

        return assignments

    def _search_with_window_all_matches(self, anchor_pos: int, base_distance: int, template_chunk: str,
                                        filtered_lines: List[List[str]]) -> List[Tuple[str, int, int]]:
        """
        Search for ALL pattern matches in window around predicted position.
        Returns: [(found_value, found_offset, offset_distance), ...]
        """
        matches = []
        predicted_line = anchor_pos + base_distance

        # Try exact position first
        result = self._check_line_for_chunk_all_matches(predicted_line, template_chunk, filtered_lines)
        for found_value in result:
            matches.append((found_value, base_distance, 0))  # offset_distance = 0

        # Expand window
        for offset_delta in range(1, self.max_distance_threshold + 1):
            # Try negative offset
            search_offset = base_distance - offset_delta
            search_line = anchor_pos + search_offset
            result = self._check_line_for_chunk_all_matches(search_line, template_chunk, filtered_lines)
            for found_value in result:
                matches.append((found_value, search_offset, offset_delta))

            # Try positive offset
            search_offset = base_distance + offset_delta
            search_line = anchor_pos + search_offset
            result = self._check_line_for_chunk_all_matches(search_line, template_chunk, filtered_lines)
            for found_value in result:
                matches.append((found_value, search_offset, offset_delta))

        return matches

    def _search_with_learned_offsets_all_matches(self, anchor_pos: int, template_chunk: str, anchor_key: Tuple,
                                                 base_distance: int, filtered_lines: List[List[str]]) -> List[
        Tuple[str, int, int]]:
        """
        Search using all discovered offsets, return ALL matches.
        Returns: [(found_value, found_offset, offset_distance), ...]
        """
        matches = []

        if anchor_key not in self.discovered_offsets:
            return matches

        if template_chunk not in self.discovered_offsets[anchor_key]:
            return matches

        discovered_offsets = self.discovered_offsets[anchor_key][template_chunk]
        for offset in discovered_offsets:
            search_line = anchor_pos + offset
            result = self._check_line_for_chunk_all_matches(search_line, template_chunk, filtered_lines)
            offset_distance = abs(offset - base_distance)
            for found_value in result:
                matches.append((found_value, offset, offset_distance))

        return matches

    def _check_line_for_chunk_all_matches(self, line_num: int,
                                          template_chunk: str,
                                          filtered_lines: List[List[str]]) -> List[str]:
        """
        Check if a line contains ANY words matching the template pattern.
        Returns: List of all matching values (can be empty)
        """
        if line_num < 0 or line_num >= len(filtered_lines):
            return []

        line_content = filtered_lines[line_num]
        matches = []

        for word in line_content:
            if self._matches_chunk_pattern(word, template_chunk):
                matches.append(word)

        return matches

    def _search_with_window(self, anchor_pos: int, base_distance: int, template_chunk: str,
                            filtered_lines: List[List[str]], already_found: set) -> Tuple[Optional[str], Optional[int]]:
        """
        Search for chunk in expanding window around predicted position.
        Returns: (found_value, found_offset) or (None, None)
        """
        predicted_line = anchor_pos + base_distance

        # Try exact position first
        result = self._check_line_for_chunk(predicted_line, template_chunk, filtered_lines, already_found)
        if result:
            return result, base_distance

        # Expand window incrementally up to max_distance_threshold
        for offset_delta in range(1, self.max_distance_threshold + 1):
            # Try negative offset
            search_offset = base_distance - offset_delta
            search_line = anchor_pos + search_offset
            result = self._check_line_for_chunk(search_line, template_chunk, filtered_lines, already_found)
            if result:
                return result, search_offset

            # Try positive offset
            search_offset = base_distance + offset_delta
            search_line = anchor_pos + search_offset
            result = self._check_line_for_chunk(search_line, template_chunk, filtered_lines, already_found)
            if result:
                return result, search_offset

        return None, None

    def _search_with_learned_offsets(self, anchor_pos: int, template_chunk: str, anchor_key: Tuple,
                                     filtered_lines: List[List[str]], already_found: set) -> Tuple[Optional[str], Optional[int]]:
        """
        Search using all discovered offsets for this chunk.
        Returns: (found_value, found_offset) or (None, None)
        """
        if anchor_key not in self.discovered_offsets:
            return None, None

        if template_chunk not in self.discovered_offsets[anchor_key]:
            return None, None

        # Try all discovered offsets
        discovered_offsets = self.discovered_offsets[anchor_key][template_chunk]
        for offset in discovered_offsets:
            search_line = anchor_pos + offset
            result = self._check_line_for_chunk(search_line, template_chunk, filtered_lines, already_found)
            if result:
                return result, offset

        return None, None

    def _check_line_for_chunk(self, line_num: int, template_chunk: str,
                              filtered_lines: List[List[str]], already_found: set) -> Optional[str]:
        """
        Check if a specific line contains a chunk matching the template pattern.
        Returns the found chunk value or None.
        """
        if line_num < 0 or line_num >= len(filtered_lines):
            return None

        line_content = filtered_lines[line_num]

        for word in line_content:
            if word in already_found:
                continue

            if self._matches_chunk_pattern(word, template_chunk):
                return word

        return None

    def _store_discovered_offset(self, anchor_key: Tuple, template_chunk: str, offset: int):
        """Store a newly discovered offset for a template chunk."""
        if anchor_key not in self.discovered_offsets:
            self.discovered_offsets[anchor_key] = {}

        if template_chunk not in self.discovered_offsets[anchor_key]:
            self.discovered_offsets[anchor_key][template_chunk] = []

        # Only add if not already present
        if offset not in self.discovered_offsets[anchor_key][template_chunk]:
            self.discovered_offsets[anchor_key][template_chunk].append(offset)

    def print_validation_report(self, validation_results: Dict):
        """Print a human-readable validation report."""
        print(f"\n{'=' * 60}")
        print("ANCHOR VALIDATION REPORT (Two-Pass Pattern-Based)")
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
            print(
                f"    Chunks matched: {stats['chunks_matched']}/{stats['total_chunks'] * validation_results['total_files']} ({chunk_rate:.1f}%)")

        # Show learned offsets
        if self.discovered_offsets:
            print(f"\n{'=' * 60}")
            print("LEARNED OFFSETS")
            print(f"{'=' * 60}")
            for anchor_key, chunk_offsets in self.discovered_offsets.items():
                anchor_str = ' '.join(anchor_key)
                print(f"\nAnchor: [{anchor_str}]")
                for template_chunk, offsets in chunk_offsets.items():
                    if len(offsets) > 1:
                        offsets_str = ', '.join([f"{'+' if o >= 0 else ''}{o}" for o in sorted(offsets)])
                        print(f"  {template_chunk}: {offsets_str}")

        # Failed files section
        if validation_results['failed_files'] > 0:
            print(f"\nFailed Files:")
            for filename, result in validation_results['per_file_results'].items():
                if not result['all_chunks_found']:
                    print(f"  - {Path(filename).name}: Missing {result['missing_chunks']}")

        # NEW: Successful files section
        if validation_results['successful_files'] > 0:
            print(f"\nSuccessful Files:")
            for filename, result in validation_results['per_file_results'].items():
                if result['all_chunks_found']:
                    print(f"  - {Path(filename).name}")

        print(f"\n{'=' * 60}")

    def get_found_titles_dict(self, validation_results: Dict) -> Dict[str, str]:
        """
        Extract found title chunks and reconstruct titles in template format.

        Returns:
            Dict mapping filename to reconstructed title
            Example: {'NCM-DD-B2-DR-ARC-4404-P1.pdf': 'NCM-DD-B2-DR-ARC-4404-P1'}
        """
        found_titles = {}

        for filename, result in validation_results['per_file_results'].items():
            file_short_name = Path(filename).name

            if not result['all_chunks_found']:
                found_titles[file_short_name] = None
                continue

            # Collect found values for each template chunk in order
            chunk_values = {}

            for anchor_key, anchor_data in result['anchor_results'].items():
                if not anchor_data['found']:
                    continue

                for chunk, details in anchor_data['chunk_details'].items():
                    if details['found'] and chunk not in chunk_values:
                        chunk_values[chunk] = details['found_value']

            # Reconstruct title in template order
            reconstructed_parts = []
            for template_chunk in self.title_chunks:
                if template_chunk in chunk_values:
                    reconstructed_parts.append(chunk_values[template_chunk])
                else:
                    reconstructed_parts.append('???')  # Missing chunk placeholder

            found_titles[file_short_name] = '-'.join(reconstructed_parts)

        return found_titles
