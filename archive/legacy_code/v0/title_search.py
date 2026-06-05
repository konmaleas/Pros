"""
Title Search and Pattern Analysis System

This module provides functionality for analyzing and extracting title patterns from text files.
It searches for consistent patterns across multiple files, identifies title templates, and
extracts structured information based on these patterns.

The main class TitleSearch performs:
1. File collection and preprocessing
2. Line chunk analysis (breaking lines into meaningful components)
3. Title pattern identification
4. Template generation based on frequently occurring patterns
5. Title extraction from all files based on the identified template

Author: [Konstantinos Maleas]
Date: [02/06/25]
Version: 1.3.2
"""

# Import statements with grouped categories
# Data structure operations
from modules.dict_opers import (sorted_counter, sorted_dict_2, list_in_dict, dict2list, dicts_3, dicts_in_dict,
                                invert_dict, singling_values)
# File operations
from modules.file_opers import debug, file_read, file_write, save_pickles, read_pickles, file_read_yield
# Pattern matching
from modules.match_case import operations
# List operations
from modules.list_opers import (any_, all_, difference, flatten, all_1, find_index_num, find_split_symbol)
# String manipulation
from modules.string_manipulation import replacer_2, is_float_only, is_float, singling_symbols
# Path operations
from modules.path_manipulation import dst_exists
# Time operations
from modules.time_oper import start_time, end_time

# Standard library imports
from collections import OrderedDict, Counter
from os import listdir
from os.path import exists, join, isfile, expanduser as home
from curses.ascii import ispunct, isspace
from pathlib import Path
from copy import deepcopy
from functools import cache
from typing import Dict, Any
from dataclasses import dataclass, field
from itertools import islice
from platform import system
import re
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
class TitleSearch:
    """
    Main class for searching and analyzing title patterns in text files.

    This class processes a directory of text files to:
    1. Identify common patterns (title templates)
    2. Extract title chunks and their positions
    3. Generate a template for title identification
    4. Apply the template to extract titles from all files

    Attributes:
        path (Path): Directory path containing files to analyze
        extension (str): File extension to filter (e.g., '.txt')
        operation (str): Comparison operation for filtering ('==', '>=', etc.)
        title (str): Extracted title template (set after initialization)
        repetitions (int): Number of files in the directory
        template_title_file (Path): File containing the title template
        file_list (list[Path]): Sorted list of files to process
        pkl_path (Path): Path for saving pickle/report files
    """

    # Initialize debug output
    ic(ict(), start_time())

    # Required fields
    path: Path
    extension: str  # File extension filter (e.g., '.txt', '.pkl')
    operation: str  # Comparison operation for chunk repetition analysis

    # Fields initialized in __post_init__
    title: str = field(init=False)  # Title template extracted from files
    repetitions: int = field(init=False)  # Number of files to process
    template_title_file: Path = field(init=False)  # File containing the template
    file_list: list[Path] = field(init=False, default_factory=list)  # List of files to analyze
    pkl_path: Path = field(init=False)  # Path for saving analysis reports

    def __post_init__(self):
        """
        Post-initialization setup for the TitleSearch instance.

        This method:
        1. Collects and sorts all files matching the extension
        2. Extracts the title from the first file
        3. Sets up the report directory structure
        4. Identifies the template title file
        """
        # Collect all files matching the extension and sort them
        self.file_list = sorted(self.collect_files())

        # Exit early if no files found
        if not self.file_list:
            return False

        # Extract title from the first file
        # TODO: Make this more flexible - currently hardcoded
        title = replacer_2(str(self.file_list[0]), '-', preserve='.')
        # self.title = Path(self.file_list[0]).stem.split('_')[0]
        # self.title = '4005-RES-VAP-DWG-233-CD-05000-D'
        # self.title = '4005-RES-VAP-DWG-234-DD-02000-C'  # Hardcoded for testing
        self.title = '4005-RES-VAP-DWG-233-IC-07020-0'

        # Set repetitions as the number of files found
        self.repetitions = len(self.file_list)

        # Find the file that contains the template title
        self.template_title_file = self.find_template_title_file()
        ic(ict(), self.template_title_file)

        # Set up report directory with timestamp
        self.pkl_path = Path(dst_exists(join(home('~'), 'PycharmProjects/Pros/files/reports/v1.3.2')))
        timestamp = dt2.now().strftime("%Y%m%d_%H%M%S")
        self.pkl_path = dst_exists(join(self.pkl_path, timestamp))

    @staticmethod
    def debug_file(file: Path, *args):
        """
        Write debug information to a file.

        Args:
            file (Path): Path to the debug file
            *args: Variable arguments to write to the file
        """
        file_write(file, ic.format(ict(), args), 'a')

    def find_template_title_file(self) -> Path | str:
        """
        Identify which file contains the complete title template.

        This method:
        1. Finds the common symbol used to split title chunks (e.g., '-')
        2. Determines the index position where the title appears
        3. Returns the file that contains the title pattern

        Returns:
            Path: The file containing the title template
        """
        # Find the symbol used to split chunks (e.g., '-', '_')
        symbol = find_split_symbol(self.file_list)

        # Find the index where numeric values typically appear
        index = find_index_num(self.file_list, symbol)

        title_file = ''
        for file in self.file_list:
            file = Path(file).name
            # Check if this file's chunk at the index position is in our title
            if str(file).split(symbol)[index] in self.title:
                title_file = file

        return Path(title_file)

    def title_dict(self, sort_by_key: bool = True) -> dict:
        """
        Convert the title string into an enumerated dictionary.

        Args:
            sort_by_key (bool): Whether to sort the dictionary by keys

        Returns:
            dict: Dictionary with index as key and title chunk as value
                  e.g., {0: '4005', 1: 'RES', 2: 'VAP', ...}
        """
        # Split title by '-' and enumerate the chunks
        return sorted_dict_2(dict(enumerate(self.title.split('-'))), sort_by_key)

    @staticmethod
    def title_chunk_value(l0: list | tuple, l1: list | tuple) -> bool:
        """
        Check if there's a difference between two lists of title chunks.

        Args:
            l0: First list/tuple of chunks
            l1: Second list/tuple of chunks

        Returns:
            bool: True if lists differ, False if identical
        """
        return True if difference(l0, l1, False) else False

    @staticmethod
    def title_chunks_type(dct: dict) -> dict:
        """
        Classify each title chunk by its type (alpha, digit, alnum, punct).

        Args:
            dct (dict): Dictionary of title chunks

        Returns:
            dict: Dictionary with chunk index as key and nested dict containing
                  chunk value and type classification
                  e.g., {0: {'4005': 'digit'}, 1: {'RES': 'alpha'}}
        """
        title_types = {}
        for e, value in enumerate(dct.values()):
            if value.isalpha():
                dicts_in_dict(title_types, e, value, 'alpha')
            elif value.isdigit():
                dicts_in_dict(title_types, e, value, 'digit')
            elif value.isalnum():
                dicts_in_dict(title_types, e, value, 'alnum')
            else:
                dicts_in_dict(title_types, e, value, 'puncts')
        return title_types

    @staticmethod
    def title_chunks_len(dct: dict) -> dict:
        """
        Calculate the length of each title chunk.

        Args:
            dct (dict): Dictionary of title chunks

        Returns:
            dict: Dictionary with chunk index as key and nested dict containing
                  chunk value and its length
                  e.g., {0: {'4005': 4}, 1: {'RES': 3}}
        """
        title_lengths = {}
        for e, value in enumerate(dct.values()):
            dicts_in_dict(title_lengths, e, value, len(value))
        return title_lengths

    @staticmethod
    def integrity_check(lst0: list, lst1: list, integrity):
        """
        Verify integrity between two lists using a provided integrity function.

        Args:
            lst0: First list to compare
            lst1: Second list to compare
            integrity: Function to apply for integrity checking

        Returns:
            Result of all_1 function applied to both integrity checks
        """
        return all_1(integrity(lst0), integrity(lst1), from_left=True)

    def collect_files(self, path: Path = None) -> list:
        """
        Collect all files with the specified extension from a directory.

        Args:
            path (Path, optional): Directory path to search. Uses self.path if None.

        Returns:
            list: List of full file paths matching the extension
        """
        if path is None:
            path = self.path

        ic(ict(), self.path)

        lst = []
        # Iterate through directory and filter by extension
        for e, file in enumerate(listdir(path)):
            if isfile(join(path, file)):
                if Path(file).suffix == self.extension:
                    lst.append(join(path, file))
        return lst

    # 1) First analysis step
    def line_chunks_nums(self) -> tuple:
        """
        Extract and analyze all line chunks from the text files.

        This function:
        1. Reads all lines from each file
        2. Splits lines into chunks (words, numbers, alphanumeric)
        3. Collects all chunks and tracks which line numbers they appear on

        Returns:
            tuple: (chunk_line_num, line_chunks)
                - chunk_line_num: Dict mapping chunks to line numbers where found
                - line_chunks: List of all chunks found
        """

        chunk_line_num, line_chunks = {}, []

        # Process each file in the file list
        for ef, file in enumerate(self.file_list):
            # Read and process each line in the file
            for line_num, line in enumerate(file_read(Path(file))):
                for e, line_chunk in enumerate(line):

                    # Classify and collect chunks

                    if line_chunk.isdigit():  # Numeric chunks
                        line_chunks.append(line_chunk)
                        list_in_dict(chunk_line_num, line_chunk, line_num)

                    elif line_chunk.isalpha():  # Alphabetic chunks
                        line_chunks.append(line_chunk)
                        list_in_dict(chunk_line_num, line_chunk, line_num)

                    elif not is_float_only(replacer_2(line_chunk, '.')):  # Non-float chunks
                        line_chunks.append(line_chunk)
                        list_in_dict(chunk_line_num, line_chunk, line_num)

        return chunk_line_num, line_chunks

    # 2) Second analysis step
    def chunks_analysis(self, line_chunks: list) -> dict:
        """
        Analyze chunks to find constants across files.

        This function identifies chunks that appear in multiple files
        (equal to or greater than the number of files based on operation).

        Args:
            line_chunks (list): List of all chunks from step 1

        Returns:
            dict: Nested dictionary structure:
                  {filename: {line_num: [chunks_found_on_this_line]}}
        """
        constant_text_chunks, line_chunk_list = {}, []

        # Count repetitions of each chunk across all files
        chunk_repetition = sorted_counter(line_chunks)

        for ef, file in enumerate(self.file_list):
            for emk, (line_chunk, repetition_times) in enumerate(chunk_repetition.items()):
                # Check if chunk meets repetition criteria
                if operations(repetition_times, self.repetitions, self.operation):
                    # Find all occurrences of this chunk in the file
                    for line_num, line in enumerate(file_read(join(Path(self.path), Path(file)))):
                        line_chunk_list.clear()
                        try:
                            for e, line_chunk_ in enumerate(line):
                                if line_chunk == line_chunk_:
                                    file_ = Path(file).name

                                    # Store chunk location information
                                    if file_ not in constant_text_chunks.keys():
                                        line_chunk_list.append(line_chunk)
                                        constant_text_chunks.update({file_: {line_num: [line_chunk]}})
                                    else:
                                        if line_num not in constant_text_chunks[file_]:
                                            line_chunk_list.append(line_chunk)
                                            constant_text_chunks[file_].update({line_num: [line_chunk]})
                                        else:
                                            line_chunk_list.append(line_chunk)
                                            # Merge with existing chunks on same line
                                            value_list_ = list(
                                                    v for (k, v0) in constant_text_chunks[file_].items()
                                                    for v in v0 if k == line_num)
                                            constant_text_chunks[file_][line_num] = deepcopy(
                                                    [*value_list_, *line_chunk_list])

                        except ValueError as VE:
                            print(VE)

        return constant_text_chunks

    # 3) Third analysis step
    def title_analysis(self, line_chunks: list) -> dict:
        """
        Analyze which title chunks appear in which files and on which lines.

        This function specifically looks for chunks that match the title template
        and records their positions in each file.

        Args:
            line_chunks (list): List of all chunks from step 1

        Returns:
            dict: Nested dictionary structure:
                  {filename: {title_chunk: [line_numbers_where_found]}}
        """
        ic(ict(), len(line_chunks))
        pkl_file = Path(join(self.pkl_path, '3.0.title_analysis.txt'))

        # Count chunk repetitions
        chunk_repetition = sorted_counter(line_chunks)

        # Get title chunks as enumerated dictionary
        title = self.title_dict(sort_by_key=True)
        ic(ict(), title)

        file_list_len = len(self.file_list)
        title_line_num_chunk, seen = {}, set()
        file_title_chunk_line_num = {}
        seen = set()

        # Process each file
        for ef, file in enumerate(listdir(self.path)):
            # Read file content from /clean_files
            file_list = file_read(join(self.path, file))

            # Check each chunk against title chunks
            for emk, (line_chunk, repetition_times) in enumerate(chunk_repetition.items()):
                # ic(ict(), line_chunk, repetition_times)

                if line_chunk in self.title.split('-'):

                    for et, (title_num, title_chunk) in enumerate(title.items()):
                        # ToDo check if enumeration works with 0
                        # if title_num not in seen:
                        #     seen.add(title_num)

                        # Search for title chunks in file lines
                        for line_num, line in enumerate(file_list):
                            split_line = line

                            if line_chunk == title_chunk:
                                if title_chunk in split_line:
                                    self.debug_file(pkl_file, '0)', line_num, line_chunk, file, split_line)
                                    # Store findings in both dictionary structures
                                    title_line_num_chunk.setdefault(line_chunk, {}) \
                                        .setdefault(file, []).append(line_num)
                                    file_title_chunk_line_num \
                                        .setdefault(file, {}) \
                                        .setdefault(title_chunk, []).append(line_num)

        return file_title_chunk_line_num

    # 4) Fourth analysis step
    def title_template(self, file: Path,
                       constant_text_chunks: dict,
                       file_title_chunk_line_num: dict,
                       anchor_selection_strategy: str = 'cluster',
                       max_distance: int = 100,
                       min_cluster_size: int = 3) -> dict | bool:
        """
        Create an enhanced template with bidirectional distances, smart anchor selection, and pattern filtering.

        Args:
            file (Path): Current file being analyzed
            constant_text_chunks (dict): Constant chunks from step 2
            file_title_chunk_line_num (dict): Title chunk positions from step 3
            anchor_selection_strategy (str): 'cluster', 'density', or 'first'
            max_distance (int): Maximum distance to consider for patterns
            min_cluster_size (int): Minimum size for title chunk clusters

        Returns:
            dict: Enhanced chunk distances with bidirectional patterns
        """
        filename = Path(file).name

        try:
            line_num_chunk = constant_text_chunks[filename]
            title_num_chunk_ = file_title_chunk_line_num[filename]
        except KeyError as e:
            return False

        # 1. SMART ANCHOR SELECTION
        selected_anchors = self._select_optimal_anchors(title_num_chunk_, anchor_selection_strategy, min_cluster_size)

        if not selected_anchors:
            return False

        # Convert to working format
        line_num_list = list(line_num_chunk.keys())
        line_chunk_list = list(line_num_chunk.values())

        # 2. BIDIRECTIONAL DISTANCE CALCULATION
        enhanced_distances = {}

        for title_chunk, anchor_line in selected_anchors.items():
            chunk_distances = {}

            # Calculate distances to all line chunks
            for line_num, line_chunks in line_num_chunk.items():
                distance = line_num - anchor_line  # Positive = after, Negative = before

                # Skip if distance exceeds maximum or chunk is title chunk
                if abs(distance) > max_distance or distance == 0:
                    continue

                # Skip if line chunk is in title chunks (avoid self-reference)
                if not self.title_chunk_value(self.title.split('-'), line_chunks):
                    continue

                chunk_distances[distance] = line_chunks

            if chunk_distances:
                enhanced_distances[title_chunk] = chunk_distances

        # 3. PATTERN FILTERING
        filtered_distances = self._filter_patterns(enhanced_distances, selected_anchors, max_distance)

        return filtered_distances

    def _select_optimal_anchors(self, title_positions: dict,
                                strategy: str,
                                min_cluster_size: int) -> dict:
        """
        Select the best anchor positions for each title chunk.

        Args:
            title_positions: {title_chunk: [line_numbers]}
            strategy: Selection method
            min_cluster_size: Minimum cluster size for 'cluster' strategy

        Returns:
            dict: {title_chunk: selected_line_number}
        """
        selected_anchors = {}

        for title_chunk, positions in title_positions.items():
            if not positions:
                continue

            if strategy == 'first':
                # Simply use first occurrence
                selected_anchors[title_chunk] = min(positions)

            elif strategy == 'density':
                # Select position with highest density of other title chunks nearby
                best_position = self._find_highest_density_position(positions, title_positions)
                selected_anchors[title_chunk] = best_position

            elif strategy == 'cluster':
                # Find the largest cluster of title chunks
                cluster_anchor = self._find_cluster_anchor(positions, title_positions, min_cluster_size)
                if cluster_anchor:
                    selected_anchors[title_chunk] = cluster_anchor

        return selected_anchors

    def _find_highest_density_position(self, positions: list, all_title_positions: dict) -> int:
        """Find position with highest density of other title chunks within ±50 lines."""
        best_position = positions[0]
        max_density = 0

        for pos in positions:
            density = 0
            # Count other title chunks within ±50 lines
            for other_title, other_positions in all_title_positions.items():
                for other_pos in other_positions:
                    if abs(other_pos - pos) <= 50 and other_pos != pos:
                        density += 1

            if density > max_density:
                max_density = density
                best_position = pos

        return best_position

    def _find_cluster_anchor(self, positions: list,
                             all_title_positions: dict,
                             min_cluster_size: int) -> int:
        """Find anchor position within the largest cluster of title chunks."""
        # Collect all title positions
        all_positions = []
        for title_positions in all_title_positions.values():
            all_positions.extend(title_positions)

        all_positions.sort()

        # Find clusters (groups of positions within 100 lines of each other)
        clusters = []
        current_cluster = [all_positions[0]] if all_positions else []

        for pos in all_positions[1:]:
            if pos - current_cluster[-1] <= 100:
                current_cluster.append(pos)
            else:
                if len(current_cluster) >= min_cluster_size:
                    clusters.append(current_cluster)
                current_cluster = [pos]

        if len(current_cluster) >= min_cluster_size:
            clusters.append(current_cluster)

        if not clusters:
            return positions[0]  # Fallback to first position

        # Find largest cluster
        largest_cluster = max(clusters, key=len)

        # Return the position from our title chunk that's closest to cluster center
        cluster_center = sum(largest_cluster) / len(largest_cluster)
        return min(positions, key=lambda x: abs(x - cluster_center))

    def _filter_patterns(self, enhanced_distances: dict,
                         selected_anchors: dict,
                         max_distance: int) -> dict:
        """
        Filter patterns to remove noise and keep only consistent relationships.

        Args:
            enhanced_distances: Raw distance calculations
            selected_anchors: Selected anchor positions
            max_distance: Maximum distance considered

        Returns:
            dict: Filtered patterns with confidence scores
        """
        filtered_patterns = {}

        # Track chunk relationships across all title chunks
        chunk_relationships = {}  # {chunk_tuple: {distances: [], titles: []}}

        for title_chunk, distances in enhanced_distances.items():
            for distance, chunks in distances.items():
                chunk_key = tuple(chunks) if isinstance(chunks, list) else (chunks,)

                if chunk_key not in chunk_relationships:
                    chunk_relationships[chunk_key] = {'distances': [], 'titles': []}

                chunk_relationships[chunk_key]['distances'].append(distance)
                chunk_relationships[chunk_key]['titles'].append(title_chunk)

        # Filter each title chunk's patterns
        for title_chunk, distances in enhanced_distances.items():
            filtered_distances = {}

            for distance, chunks in distances.items():
                chunk_key = tuple(chunks) if isinstance(chunks, list) else (chunks,)
                relationship = chunk_relationships[chunk_key]

                # Calculate confidence metrics
                consistency = len(set(relationship['distances'])) == 1  # Same distance across titles
                frequency = len(relationship['distances'])  # How often this chunk appears

                # Keep chunks that appear consistently or frequently
                if consistency or frequency >= 2:
                    # Add confidence score
                    confidence = frequency / len(selected_anchors) if len(selected_anchors) > 0 else 0

                    filtered_distances[distance] = {'chunks': chunks,
                                                    'confidence': confidence,
                                                    'frequency': frequency,
                                                    'consistent': consistency}

            if filtered_distances:
                filtered_patterns[title_chunk] = filtered_distances

        return filtered_patterns

    # 5) Fifth analysis step
    def chunks_distances(self, min_dif: dict, max_chunks: int = 5) -> dict:
        """
        Extract the closest chunks to each title chunk based on distance.

        This function sorts and filters the chunk distances to find the closest
        chunks to each title chunk position, avoiding duplicate chunk values.
        Handles both old format (direct chunks) and new format (metadata dicts).

        Args:
            min_dif (dict): Distance dictionary from step 4
            max_chunks (int): Maximum number of closest chunks to return (default: 5)

        Returns:
            dict: Dictionary with title chunks as keys and their closest chunks
                  {title_chunk: {distance: chunk_value}}
        """
        closest_sorted_chunks = {}
        debug_file_path = Path(join(self.pkl_path, '5.0.final_template_.txt'))

        for title_key, idx_distance_chunks in min_dif.items():
            self.debug_file(debug_file_path, '0)', title_key, idx_distance_chunks)

            # Sort chunks by distance (ascending)
            sorted_chunks = sorted_dict_2(idx_distance_chunks, True)
            closest_chunks = {}
            seen_values = set()  # Track already seen chunk values

            for distance, chunks in sorted_chunks.items():
                # Handle both old format (list) and new format (dict with metadata)
                if isinstance(chunks, dict) and 'chunks' in chunks:
                    actual_chunks = chunks['chunks']  # Extract the actual chunk list
                    metadata = chunks  # Keep metadata for potential use
                else:
                    actual_chunks = chunks  # Old format - chunks is already the list
                    metadata = None

                # Convert chunks to tuple for hashable comparison
                chunks_tuple = tuple(actual_chunks) if isinstance(actual_chunks, list) else actual_chunks

                # Only add if we haven't seen this exact chunk list before
                if chunks_tuple not in seen_values:
                    closest_chunks[distance] = actual_chunks  # Store actual chunks
                    seen_values.add(chunks_tuple)

                    self.debug_file(debug_file_path, '1)', title_key, distance, actual_chunks, len(closest_chunks))

                    # Stop when we have enough unique chunks
                    if len(closest_chunks) >= max_chunks:
                        break

            if closest_chunks:
                closest_sorted_chunks[title_key] = closest_chunks

                self.debug_file(debug_file_path,
                                '2)', closest_chunks, max_chunks, len(closest_chunks))
                self.debug_file(Path(join(self.pkl_path, '5.1.final_template_.txt')),
                                '2.1)', closest_chunks, title_key)
                self.debug_file(Path(join(self.pkl_path, '5.2.final_template_.txt')),
                                '2.2)', closest_sorted_chunks, len(closest_chunks))

        return closest_sorted_chunks

    def chunks_distances_(self, min_dif: dict, max_chunks: int = 5) -> dict:
        """
        Extract the closest chunks to each title chunk based on distance.

        This function sorts and filters the chunk distances to find the closest
        chunks to each title chunk position, avoiding duplicate chunk values.
        Handles both old format (direct chunks) and new format (metadata dicts).

        Args:
            min_dif (dict): Distance dictionary from step 4
            max_chunks (int): Maximum number of closest chunks to return (default: 5)

        Returns:
            dict: Dictionary with title chunks as keys and their closest chunks
                  {title_chunk: {distance: chunk_value}}
        """
        closest_sorted_chunks = {}
        debug_file_path = Path(join(self.pkl_path, '5.0.final_template_.txt'))

        for title_key, idx_distance_chunks in min_dif.items():
            self.debug_file(debug_file_path, '0)', title_key, idx_distance_chunks)

            # Sort chunks by distance (ascending)
            sorted_chunks = sorted_dict_2(idx_distance_chunks, True)
            closest_chunks = {}
            seen_values = set()  # Track already seen chunk values

            for distance, chunks in sorted_chunks.items():
                # Handle both old format (list) and new format (dict with metadata)
                if isinstance(chunks, dict) and 'chunks' in chunks:
                    actual_chunks = chunks['chunks']  # Extract the actual chunk list
                    metadata = chunks  # Keep metadata for potential use
                else:
                    actual_chunks = chunks  # Old format - chunks is already the list
                    metadata = None

                # Convert chunks to tuple for hashable comparison
                chunks_tuple = tuple(actual_chunks) if isinstance(actual_chunks, list) else actual_chunks

                # Only add if we haven't seen this exact chunk list before
                if chunks_tuple not in seen_values:
                    closest_chunks[distance] = actual_chunks  # Store actual chunks
                    seen_values.add(chunks_tuple)

                    self.debug_file(debug_file_path, '1)', title_key, distance, actual_chunks, len(closest_chunks))

                    # Stop when we have enough unique chunks
                    if len(closest_chunks) >= max_chunks:
                        break

            if closest_chunks:
                closest_sorted_chunks[title_key] = closest_chunks

                self.debug_file(debug_file_path,
                                '2)', closest_chunks, max_chunks, len(closest_chunks))
                self.debug_file(Path(join(self.pkl_path, '5.1.final_template_.txt')),
                                '2.1)', closest_chunks, title_key)
                self.debug_file(Path(join(self.pkl_path, '5.2.final_template_.txt')),
                                '2.2)', closest_sorted_chunks, len(closest_chunks))

        return closest_sorted_chunks
