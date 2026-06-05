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
class PatternAnalyzer:
    """
    Stage 4: Analyzes spatial patterns of title chunks using template-based approach.

    Takes filtered text from Stage 3 and maps title chunks to line positions,
    using template file as reference for dynamic vs static chunk identification.
    """
    title: str
    files: List[Path] = field(default_factory=list)
    # Anchor selection parameters
    max_cluster_distance: int = 100
    min_cluster_size: int = 3
    density_window: int = 50

    def __post_init__(self):
        """Initialize derived fields after dataclass creation."""
        self.title_chunks = self._extract_title_chunks()
        self.template_file = self._find_template_file()

    def _extract_title_chunks(self) -> List[str]:
        """Extract individual chunks from the title string."""
        # Find the most common separator in the title
        separators = ['-', '_', '.', ' ']
        for sep in separators:
            if sep in self.title:
                chunks = [chunk.strip() for chunk in self.title.split(sep) if chunk.strip()]
                if len(chunks) > 1:
                    return chunks
        return [self.title]  # Fallback if no separator found

    def _find_template_file(self) -> Path:
        """
        Identify which file contains the complete title template.
        Uses the provided template identification logic.
        """
        # Find the symbol used to split chunks
        symbol = self._find_split_symbol([str(f) for f in self.files])

        # Find the index where title chunks typically appear
        index = self._find_index_num([str(f) for f in self.files], symbol)

        title_file = ''
        for file in self.files:
            filename = Path(file).name
            try:
                file_chunks = str(filename).split(symbol)
                if index < len(file_chunks) and file_chunks[index] in self.title:
                    title_file = filename
                    break
            except IndexError:
                continue

        return Path(title_file) if title_file else self.files[0]

    def _find_split_symbol(self, files: List[str]) -> str:
        """Find the most common punctuation/space symbol in filenames."""
        symbols = []
        for filename in files:
            for char in Path(filename).name:
                if char in punctuation or char.isspace():
                    symbols.append(char)

        if not symbols:
            return '-'  # Default fallback

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
        # Find the least common element (likely the variable part)
        least_common = counter.most_common()[-1][0]

        # Find its typical index position
        for filename in files:
            chunks = Path(filename).name.split(symbol)
            try:
                return chunks.index(least_common)
            except ValueError:
                continue
        return 0

    def analyze_file_patterns(self,
                              filename: str,
                              chunk_line_positions: Dict[str, List[int]]) -> FileAnalysisResult:
        """
        Analyze title patterns in a single file.

        Args:
            filtered_lines: Clean, filtered text lines from Stage 3
            filename: Name of the file being analyzed
            chunk_line_positions: Map of chunks to their line positions from Stage 2
        """
        is_template = Path(filename).name == self.template_file.name

        # Find all title chunks present in this file
        found_chunks = {chunk: positions for chunk, positions in chunk_line_positions.items() if
                        chunk in self.title_chunks}

        if not found_chunks:
            return FileAnalysisResult(filename=filename, template_file=is_template, distance_patterns=[],
                    anchor_chunks=[], total_chunks_found=0)

        # Select anchor chunks using multiple strategies
        anchor_chunks = self._select_anchor_chunks(found_chunks)

        # Generate distance patterns for each anchor
        distance_patterns = []
        for anchor_chunk in anchor_chunks:
            pattern = self._generate_distance_pattern(anchor_chunk, found_chunks)
            if pattern:
                distance_patterns.append(pattern)

        return FileAnalysisResult(filename=filename,
                                  template_file=is_template,
                                  distance_patterns=distance_patterns,
                                  anchor_chunks=anchor_chunks,
                                  total_chunks_found=sum(len(positions) for positions in found_chunks.values()))

    def _select_anchor_chunks(self, found_chunks: Dict[str, List[int]]) -> List[str]:
        """
        Select optimal anchor chunks using multiple strategies.
        Prefers single anchor but can select multiple if needed.
        """
        if not found_chunks:
            return []

        # Strategy 1: Cluster-based selection
        cluster_anchors = self._cluster_strategy(found_chunks)
        if cluster_anchors:
            return cluster_anchors[:1]  # Prefer single anchor from clustering

        # Strategy 2: Density-based selection
        density_anchors = self._density_strategy(found_chunks)
        if density_anchors:
            return density_anchors[:1]  # Prefer single anchor from density

        # Strategy 3: Fallback to first/most frequent
        return self._fallback_strategy(found_chunks)

    def _cluster_strategy(self, found_chunks: Dict[str, List[int]]) -> List[str]:
        """
        Find anchors by clustering title chunks within max_cluster_distance.
        Returns chunks that are centers of the largest clusters.
        """
        clusters = defaultdict(list)

        # For each chunk, find all other chunks within cluster distance
        for chunk, positions in found_chunks.items():
            for pos in positions:
                cluster_members = [chunk]

                # Find nearby chunks
                for other_chunk, other_positions in found_chunks.items():
                    if other_chunk != chunk:
                        for other_pos in other_positions:
                            if abs(pos - other_pos) <= self.max_cluster_distance:
                                cluster_members.append(other_chunk)

                if len(set(cluster_members)) >= self.min_cluster_size:
                    clusters[f"{chunk}_{pos}"] = cluster_members

        if not clusters:
            return []

        # Find the largest cluster
        largest_cluster = max(clusters.items(), key=lambda x: len(set(x[1])))
        anchor_chunk = largest_cluster[0].split('_')[0]

        return [anchor_chunk]

    def _density_strategy(self, found_chunks: Dict[str, List[int]]) -> List[str]:
        """
        Find anchors based on density - positions with highest concentration
        of other title chunks within density_window.
        """
        density_scores = {}

        for chunk, positions in found_chunks.items():
            for pos in positions:
                # Count other chunks within density window
                nearby_count = 0
                for other_chunk, other_positions in found_chunks.items():
                    if other_chunk != chunk:
                        nearby_count += sum(
                                1 for other_pos in other_positions if abs(pos - other_pos) <= self.density_window)

                density_scores[f"{chunk}_{pos}"] = nearby_count

        if not density_scores:
            return []

        # Return chunk with highest density score
        best_anchor = max(density_scores.items(), key=lambda x: x[1])
        anchor_chunk = best_anchor[0].split('_')[0]

        return [anchor_chunk]

    def _fallback_strategy(self, found_chunks: Dict[str, List[int]]) -> List[str]:
        """
        Fallback strategy: select chunk with most occurrences,
        or first chunk if tied.
        """
        if not found_chunks:
            return []

        # Select chunk with most positions
        best_chunk = max(found_chunks.items(), key=lambda x: len(x[1]))
        return [best_chunk[0]]

    def _generate_distance_pattern(self,
                                   anchor_chunk: str,
                                   found_chunks: Dict[str, List[int]]) -> Optional[DistancePattern]:
        """
        Generate distance pattern from anchor chunk to all other chunks.
        Uses bidirectional distances (positive = after anchor, negative = before).
        """
        if anchor_chunk not in found_chunks:
            return None

        anchor_positions = found_chunks[anchor_chunk]
        # Use the first occurrence as the reference point
        anchor_line = anchor_positions[0]

        chunk_distances = {}
        chunk_lines = {}

        for chunk, positions in found_chunks.items():
            if chunk == anchor_chunk:
                chunk_distances[chunk] = 0
                chunk_lines[chunk] = anchor_line
            else:
                # Find closer position to anchor
                closest_pos = min(positions, key=lambda pos: abs(pos - anchor_line))
                distance = closest_pos - anchor_line  # Positive = after, negative = before

                chunk_distances[chunk] = distance
                chunk_lines[chunk] = closest_pos

        return DistancePattern(anchor_chunk=anchor_chunk, anchor_line=anchor_line, chunk_distances=chunk_distances,
                chunk_lines=chunk_lines)

    def compare_with_template(self,
                              current_pattern: DistancePattern,
                              template_pattern: DistancePattern) -> Dict[str, int]:
        """
        Compare current file's pattern with template to identify dynamic chunks.
        Returns differences in distances for each chunk.
        """
        differences = {}

        for chunk in current_pattern.chunk_distances:
            if chunk in template_pattern.chunk_distances:
                current_dist = current_pattern.chunk_distances[chunk]
                template_dist = template_pattern.chunk_distances[chunk]
                difference = current_dist - template_dist

                if difference != 0:  # Only track chunks that moved
                    differences[chunk] = difference

        return differences

    def _validate_and_recalculate_positions(self, filtered_lines: List[str],
                                            chunk_line_positions: Dict[str, List[int]]) -> Dict[str, List[int]]:
        """
        Validate chunk positions from Stage 2 against filtered text from Stage 3.
        Recalculate positions if chunks moved or disappeared due to filtering.

        Args:
            filtered_lines: Clean, filtered text from Stage 3
            chunk_line_positions: Original positions from Stage 2

        Returns:
            Updated chunk positions that are valid in filtered text
        """
        validated_positions = {}

        for chunk, original_positions in chunk_line_positions.items():
            valid_positions = []

            # First, try to validate original positions
            for line_num in original_positions:
                if (line_num < len(filtered_lines) and chunk.lower() in filtered_lines[line_num].lower()):
                    valid_positions.append(line_num)

            # If original positions are invalid, search for chunk in filtered text
            if not valid_positions:
                valid_positions = self._find_chunk_in_filtered_text(chunk, filtered_lines)

            # Only keep chunks that exist in filtered text
            if valid_positions:
                validated_positions[chunk] = valid_positions

        return validated_positions

    def _find_chunk_in_filtered_text(self, chunk: str, filtered_lines: List[str]) -> List[int]:
        """
        Find all occurrences of a chunk in the filtered text.

        Args:
            chunk: Text chunk to find
            filtered_lines: Filtered text lines to search

        Returns:
            List of line numbers where chunk appears
        """
        positions = []
        chunk_lower = chunk.lower()

        for line_num, line in enumerate(filtered_lines):
            if chunk_lower in line.lower():
                # Additional validation: check if it's a whole word match
                import re
                pattern = r'\b' + re.escape(chunk_lower) + r'\b'
                if re.search(pattern, line.lower()):
                    positions.append(line_num)

        return positions
