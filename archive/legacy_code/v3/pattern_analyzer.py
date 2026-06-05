from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import Counter, defaultdict
import statistics


@dataclass
class PatternAnalyzer:
    """
    Stage 4: Template-first pattern analysis for dynamic title chunk detection.

    Uses template file to establish baseline spatial relationships, then analyzes
    other files to detect dynamic chunks and their positional variations.

    Template-first approach:
    1. Process template file to establish anchor and baseline distances
    2. Process each file against template to detect dynamic chunks
    3. Track positional variations for auto-completion
    """

    # Core configuration
    title_chunks: List[str] = field(default_factory=list)
    template_file_name: str = ""
    max_distance: int = 100
    min_cluster_size: int = 3

    # Template baseline data
    template_anchor: Optional[str] = None
    template_anchor_position: int = 0
    template_distances: Dict[str, int] = field(default_factory=dict)  # {chunk: distance_from_anchor}

    # Multi-file analysis results
    file_patterns: Dict[str, Dict] = field(default_factory=dict)  # {filename: pattern_data}
    dynamic_chunks: Dict[str, List[int]] = field(default_factory=dict)  # {chunk: [positions_across_files]}
    static_chunks: Dict[str, int] = field(default_factory=dict)  # {chunk: consistent_distance}

    # Confidence and consistency tracking
    chunk_consistency: Dict[str, float] = field(default_factory=dict)  # {chunk: consistency_score}

    def analyze_template_patterns(self, template_filtered_lines: List[List[str]],
                                  template_frequency_data: Dict) -> bool:
        """
        Step 1: Analyze the template file to establish baseline spatial relationships.

        Args:
            template_filtered_lines: Filtered text from Stage 3 for template file
            template_frequency_data: Frequency data from Stage 2 for template file

        Returns:
            bool: True if template analysis successful
        """
        try:
            # Get title chunk positions in template file
            title_positions = self._extract_title_positions(template_filtered_lines)

            if not title_positions:
                return False

            # Select optimal anchor using semantic clustering
            self.template_anchor = self._select_semantic_anchor(title_positions)
            if not self.template_anchor:
                return False

            self.template_anchor_position = title_positions[self.template_anchor][0]  # Use first occurrence

            # Calculate baseline distances from anchor to all other chunks
            self.template_distances = self._calculate_baseline_distances(template_filtered_lines, title_positions)

            return True

        except Exception as e:
            print(f"Error in template analysis: {e}")
            return False

    def analyze_file_patterns(self, filename: str, filtered_lines: List[List[str]], frequency_data: Dict) -> Dict:
        """
        Step 2: Analyze individual file against template baseline.

        Args:
            filename: Name of file being analyzed
            filtered_lines: Filtered text from Stage 3
            frequency_data: Frequency data from Stage 2

        Returns:
            Dict: Pattern analysis results for this file
        """
        try:
            # Get title chunk positions in current file
            title_positions = self._extract_title_positions(filtered_lines)

            if not title_positions or self.template_anchor not in title_positions:
                return {}

            # Find anchor position in current file
            current_anchor_position = title_positions[self.template_anchor][0]

            # Calculate distances from anchor in current file
            current_distances = {}
            for line_num, words in enumerate(filtered_lines):
                for word in words:
                    if word in self.title_chunks:
                        distance = line_num - current_anchor_position
                        if abs(distance) <= self.max_distance and distance != 0:
                            if word not in current_distances:
                                current_distances[word] = []
                            current_distances[word].append(distance)

            # Compare against template to detect dynamic chunks
            pattern_analysis = self._analyze_pattern_differences(current_distances, filename)

            # Store file pattern data
            self.file_patterns[filename] = pattern_analysis

            return pattern_analysis

        except Exception as e:
            print(f"Error analyzing file {filename}: {e}")
            return {}

    def _extract_title_positions(self, filtered_lines: List[List[str]]) -> Dict[str, List[int]]:
        """Extract positions of title chunks from filtered text."""
        title_positions = {}

        for line_num, words in enumerate(filtered_lines):
            for word in words:
                if word in self.title_chunks:
                    if word not in title_positions:
                        title_positions[word] = []
                    title_positions[word].append(line_num)

        return title_positions

    def _select_semantic_anchor(self, title_positions: Dict[str, List[int]]) -> Optional[str]:
        """
        Select anchor using semantic clustering logic.

        Prioritizes chunks that represent semantic categories like:
        ["High", "Rise", "Residential", "Development"] over technical codes.
        """
        # Score each title chunk for semantic anchor suitability
        anchor_scores = {}

        for chunk, positions in title_positions.items():
            score = 0

            # Semantic scoring based on chunk characteristics
            if chunk.isalpha():
                score += 10  # Alphabetic chunks are more stable anchors

                # Longer words tend to be more descriptive (semantic)
                if len(chunk) >= 4:
                    score += 5

                # Common architectural/engineering terms get higher scores
                semantic_terms = ['HIGH', 'RISE', 'RESIDENTIAL', 'DEVELOPMENT', 'BUILDING', 'TOWER', 'COMPLEX',
                                  'CENTER', 'OFFICE', 'COMMERCIAL', 'INDUSTRIAL']
                if chunk.upper() in semantic_terms:
                    score += 15

            # Consistency scoring - fewer position variations = better anchor
            position_variance = len(set(positions))
            if position_variance == 1:
                score += 20  # Perfect consistency
            elif position_variance <= 3:
                score += 10  # Good consistency

            # Position stability - chunks that appear early tend to be more stable
            avg_position = sum(positions) / len(positions)
            if avg_position < 50:  # Appears in first 50 lines
                score += 5

            anchor_scores[chunk] = score

        # Select chunk with highest score
        if anchor_scores:
            return max(anchor_scores, key=anchor_scores.get)

        return None

    def _calculate_baseline_distances(self, template_lines: List[List[str]], title_positions: Dict[str, List[int]]) -> \
    Dict[str, int]:
        """Calculate baseline distances from anchor to all other chunks in template."""
        baseline_distances = {}

        for line_num, words in enumerate(template_lines):
            for word in words:
                if word in self.title_chunks and word != self.template_anchor:
                    distance = line_num - self.template_anchor_position
                    if abs(distance) <= self.max_distance:
                        # Use first occurrence as baseline
                        if word not in baseline_distances:
                            baseline_distances[word] = distance

        return baseline_distances

    def _analyze_pattern_differences(self, current_distances: Dict[str, List[int]], filename: str) -> Dict:
        """
        Compare current file distances against template baseline.

        Identifies static vs dynamic chunks based on positional consistency.
        """
        pattern_analysis = {'filename': filename, 'static_chunks': {}, 'dynamic_chunks': {}, 'missing_chunks': [],
            'extra_chunks'            : {}, 'anchor_position': None}

        # Find current anchor position
        if self.template_anchor in current_distances:
            pattern_analysis['anchor_position'] = current_distances[self.template_anchor][0] if current_distances[
                self.template_anchor] else None

        # Analyze each title chunk
        for chunk in self.title_chunks:
            if chunk == self.template_anchor:
                continue

            template_distance = self.template_distances.get(chunk)
            current_distance_list = current_distances.get(chunk, [])

            if not current_distance_list:
                # Chunk missing in current file
                pattern_analysis['missing_chunks'].append(chunk)
                continue

            # Use most common distance (mode) or first occurrence
            current_distance = Counter(current_distance_list).most_common(1)[0][0]

            if template_distance is not None:
                # Compare with template
                distance_diff = abs(current_distance - template_distance)

                if distance_diff <= self.static_distance_tolerance:  # Within tolerance = static
                    pattern_analysis['static_chunks'][chunk] = {'template_distance': template_distance,
                                                                'current_distance': current_distance,
                                                                'variation': distance_diff}
                    # Update global static chunk tracking
                    if chunk not in self.static_chunks:
                        self.static_chunks[chunk] = template_distance

                else:  # Significant difference = dynamic
                    pattern_analysis['dynamic_chunks'][chunk] = {'template_distance': template_distance,
                                                                 'current_distance': current_distance,
                                                                 'variation': distance_diff,
                                                                 'all_positions': current_distance_list}
                    # Update global dynamic chunk tracking
                    if chunk not in self.dynamic_chunks:
                        self.dynamic_chunks[chunk] = []
                    self.dynamic_chunks[chunk].extend(current_distance_list)
            else:
                # Chunk not in template (shouldn't happen with proper title chunks)
                pattern_analysis['extra_chunks'][chunk] = current_distance_list

        return pattern_analysis

    def calculate_consistency_scores(self) -> Dict[str, float]:
        """
        Calculate consistency scores for all chunks across files.

        Returns:
            Dict: {chunk: consistency_score} where 1.0 = perfectly consistent, 0.0 = completely random
        """
        for chunk in self.title_chunks:
            if chunk == self.template_anchor:
                self.chunk_consistency[chunk] = 1.0  # Anchor is always consistent
                continue

            if chunk in self.static_chunks:
                # Static chunks get high consistency scores
                variations = []
                for file_data in self.file_patterns.values():
                    if chunk in file_data.get('static_chunks', {}):
                        variations.append(file_data['static_chunks'][chunk]['variation'])

                if variations:
                    avg_variation = sum(variations) / len(variations)
                    consistency = max(0.0, 1.0 - (avg_variation / 10))  # Normalize to 0-1
                else:
                    consistency = 1.0

                self.chunk_consistency[chunk] = consistency

            elif chunk in self.dynamic_chunks:
                # Dynamic chunks get lower consistency scores based on position variance
                positions = self.dynamic_chunks[chunk]
                if len(positions) > 1:
                    position_variance = statistics.variance(positions)
                    consistency = max(0.0, 1.0 - (position_variance / 100))  # Normalize
                else:
                    consistency = 0.5  # Single occurrence = medium consistency

                self.chunk_consistency[chunk] = consistency
            else:
                self.chunk_consistency[chunk] = 0.0  # Chunk never found

        return self.chunk_consistency

    def get_auto_completion_patterns(self) -> Dict:
        """
        Generate patterns for auto-completion system.

        Returns:
            Dict: Comprehensive pattern data for auto-completion
        """
        return {'template_anchor': self.template_anchor,
                'template_anchor_position': self.template_anchor_position,
                'static_patterns':
                    {chunk: {'expected_distance': distance,
                             'consistency_score': self.chunk_consistency.get(chunk, 0.0),
                             'is_reliable': self.chunk_consistency.get(chunk, 0.0) > 0.8}
                     for chunk, distance in self.static_chunks.items()},
                'dynamic_patterns':
                    {chunk: {'template_distance': self.template_distances.get(chunk),
                             'observed_positions': positions,
                             'position_variance': statistics.variance(positions) if len(positions) > 1 else 0,
                             'consistency_score': self.chunk_consistency.get(chunk, 0.0),
                             'common_distances': Counter(positions).most_common(3)}
                     for chunk, positions in self.dynamic_chunks.items()},
                'file_analysis_summary':
                    {'total_files_analyzed': len(self.file_patterns),
                     'static_chunk_count': len(self.static_chunks),
                     'dynamic_chunk_count': len(self.dynamic_chunks),
                     'average_consistency': sum(self.chunk_consistency.values()) / len(self.chunk_consistency)
                     if self.chunk_consistency else 0.0}}

    def analyze_multiple_files(self, file_data_list: List[Dict]) -> Dict:
        """
        Master method: Analyze template + multiple files in sequence.

        Args:
            file_data_list: List of dicts with format:
                [
                    {
                        'filename': str,
                        'filtered_lines': List[List[str]],
                        'frequency_data': Dict,
                        'is_template': bool
                    },
                    ...
                ]

        Returns:
            Dict: Complete auto-completion patterns
        """
        # Step 1: Find and process template file
        template_processed = False
        for file_data in file_data_list:
            if file_data.get('is_template', False):
                if self.analyze_template_patterns(file_data['filtered_lines'], file_data['frequency_data']):
                    self.template_file_name = file_data['filename']
                    template_processed = True
                    break

        if not template_processed:
            raise ValueError("Template file analysis failed or no template file found")

        # Step 2: Process all non-template files
        for file_data in file_data_list:
            if not file_data.get('is_template', False):
                self.analyze_file_patterns(file_data['filename'],
                                           file_data['filtered_lines'],
                                           file_data['frequency_data'])

        # Step 3: Calculate consistency scores
        self.calculate_consistency_scores()

        # Step 4: Generate final auto-completion patterns
        return self.get_auto_completion_patterns()
