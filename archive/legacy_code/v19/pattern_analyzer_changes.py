# This file contains the specific changes needed for pattern_analyzer.py
# Apply these changes to your existing pattern_analyzer.py file

# CHANGE 1: Line ~6 - Ensure Tuple is imported
from typing import Dict, List, Optional, Tuple

# CHANGE 2: Line ~117 - Update method signature
def analyze_all_files(self, extract_and_process_func) -> Tuple[Dict[str, FileAnalysisResult], Dict]:
    """Main entry point: analyze all files using stable line anchors.
    
    Returns:
        Tuple of (results, all_file_data) where:
        - results: Dict[filename, FileAnalysisResult]
        - all_file_data: Dict containing processed_lines, filtered_lines, chunk_positions for each file
    """

# CHANGE 3: Line ~142 - Add processed_lines to all_file_data
all_file_data[str(file_path)] = {'processed_lines': processed_lines,
                                 'filtered_lines' : filtered_lines,
                                 'chunk_positions': filtered_frequency_data['chunk_line_positions']}

# CHANGE 4: Line ~151 - Update return statement
return {filename: self._create_empty_result(filename) for filename in all_file_data.keys()}, all_file_data

# CHANGE 5: Line ~156 - Update return statement
return {filename: self._create_empty_result(filename) for filename in all_file_data.keys()}, all_file_data

# CHANGE 6: Line ~164 - Update return statement
return results, all_file_data

# CHANGE 7: Line ~292-295 - CRITICAL FIX: Relax anchor viability requirement
viable_files = 0
for filename, file_data in all_file_data.items():
    if self._test_anchor_viability(anchor_line, file_data):
        viable_files += 1

# Anchor must be viable in at least ONE file (not all files)
# In multi-anchor scenarios, different anchors cover different files
if viable_files == 0:
    return 0

score += viable_files * 20

# CHANGE 8: Add new method at the end of the class (after get_found_titles_dict)
def convert_validation_to_file_results(self, validation_results: Dict) -> Dict[str, FileAnalysisResult]:
    """
    Convert validation results from multi-anchor validation to FileAnalysisResult format.
    
    Args:
        validation_results: Results from validate_anchors_on_files()
        
    Returns:
        Dict mapping filename to FileAnalysisResult
    """
    file_results = {}
    
    for filename, file_result in validation_results['per_file_results'].items():
        distance_patterns = []
        anchor_chunks = []
        
        # Build distance patterns from each anchor that found chunks
        for anchor_key, anchor_data in file_result['anchor_results'].items():
            if not anchor_data['found'] or anchor_data['chunks_matched'] == 0:
                continue
                
            anchor_str = str(list(anchor_key))
            anchor_chunks.append(anchor_str)
            
            # Get anchor position
            if anchor_data['positions']:
                anchor_pos = anchor_data['positions'][0]
                
                # Build chunk_distances and chunk_lines
                chunk_distances = {}
                chunk_lines = {}
                
                for chunk, details in anchor_data['chunk_details'].items():
                    if details['found']:
                        chunk_distances[chunk] = details['found_offset']
                        chunk_lines[chunk] = anchor_pos + details['found_offset']
                
                if chunk_distances:
                    pattern = DistancePattern(
                        anchor_chunk=anchor_str,
                        anchor_line=anchor_pos,
                        chunk_distances=chunk_distances,
                        chunk_lines=chunk_lines
                    )
                    distance_patterns.append(pattern)
        
        # Create FileAnalysisResult
        result = FileAnalysisResult(
            filename=filename,
            template_file=False,  # We don't identify template files in multi-anchor mode
            distance_patterns=distance_patterns,
            anchor_chunks=anchor_chunks,
            total_chunks_found=len(file_result['found_chunks'])
        )
        
        file_results[filename] = result
    
    return file_results
