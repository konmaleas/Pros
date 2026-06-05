# Complete Implementation Guide for Batch Processing Fix

## Files to Modify
1. `pattern_analyzer.py`
2. `batch_processor.py`

---

## pattern_analyzer.py Changes

### Change 1: Method Signature (around line 117)
**Find:**
```python
def analyze_all_files(self, extract_and_process_func) -> Dict[str, FileAnalysisResult]:
    """Main entry point: analyze all files using stable line anchors."""
```

**Replace with:**
```python
def analyze_all_files(self, extract_and_process_func) -> Tuple[Dict[str, FileAnalysisResult], Dict]:
    """Main entry point: analyze all files using stable line anchors.
    
    Returns:
        Tuple of (results, all_file_data) where:
        - results: Dict[filename, FileAnalysisResult]
        - all_file_data: Dict containing processed_lines, filtered_lines, chunk_positions for each file
    """
```

### Change 2: Add processed_lines (around line 136-137)
**Find:**
```python
all_file_data[str(file_path)] = {'filtered_lines' : filtered_lines,
                                 'chunk_positions': filtered_frequency_data['chunk_line_positions']}
```

**Replace with:**
```python
all_file_data[str(file_path)] = {'processed_lines': processed_lines,
                                 'filtered_lines' : filtered_lines,
                                 'chunk_positions': filtered_frequency_data['chunk_line_positions']}
```

### Change 3: Return Statement 1 (around line 144)
**Find:**
```python
return {filename: self._create_empty_result(filename) for filename in all_file_data.keys()}
```

**Replace with:**
```python
return {filename: self._create_empty_result(filename) for filename in all_file_data.keys()}, all_file_data
```

### Change 4: Return Statement 2 (around line 149)
**Find:**
```python
return {filename: self._create_empty_result(filename) for filename in all_file_data.keys()}
```

**Replace with:**
```python
return {filename: self._create_empty_result(filename) for filename in all_file_data.keys()}, all_file_data
```

### Change 5: Return Statement 3 (around line 157)
**Find:**
```python
return results
```

**Replace with:**
```python
return results, all_file_data
```

### Change 6: CRITICAL - Anchor Scoring Fix (around line 287-295)
**Find:**
```python
viable_files = 0
for filename, file_data in all_file_data.items():
    if self._test_anchor_viability(anchor_line, file_data):
        viable_files += 1

if viable_files < len(all_file_data):
    return 0

score += viable_files * 20
```

**Replace with:**
```python
viable_files = 0
for filename, file_data in all_file_data.items():
    if self._test_anchor_viability(anchor_line, file_data):
        viable_files += 1

# Anchor must be viable in at least ONE file (not all files)
# In multi-anchor scenarios, different anchors cover different files
if viable_files == 0:
    return 0

score += viable_files * 20
```

### Change 7: Add New Method (at end of class, after get_found_titles_dict)
**Add this complete method:**
```python
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
```

---

## batch_processor.py Changes

### Change 1: Import Dict (around line 5)
**Ensure this import includes Dict:**
```python
from typing import List, Dict, Tuple
```

### Change 2: Update CaseResult Dataclass (around line 17-30)
**Find:**
```python
@dataclass
class CaseResult:
    """Results from processing a single case."""
    case_path: str
    pdf_count: int
    success: bool
    error_message: str = ""
    inferred_title: str = ""
    template_file: str = ""
    total_files_analyzed: int = 0
    files_with_patterns: int = 0
    stable_anchors_found: int = 0
    processing_time: float = 0.0
```

**Replace with:**
```python
@dataclass
class CaseResult:
    """Results from processing a single case."""
    case_path: str
    pdf_count: int
    success: bool
    error_message: str = ""
    inferred_title: str = ""
    template_file: str = ""
    total_files_analyzed: int = 0
    files_with_patterns: int = 0
    stable_anchors_found: int = 0
    processing_time: float = 0.0
    found_titles: Dict[str, str] = field(default_factory=dict)  # filename -> reconstructed title
```

### Change 3: Update process_case Function (around line 155-175)
**Find:**
```python
try:
    # Run multi-file pattern analysis
    analyzer = MultiFilePatternAnalyzer(title=title, files=pdf_files)
    results = analyzer.analyze_all_files(extract_and_process)

    # Count successes
    template_file = ""
    files_with_patterns = 0

    for filename, result in results.items():
        if result.template_file:
            template_file = filename
        if result.total_chunks_found > 0:
            files_with_patterns += 1

    processing_time = (dt2.now() - start).total_seconds()

    return CaseResult(case_path=case_path, pdf_count=len(pdf_files), success=True, inferred_title=title,
            template_file=template_file, total_files_analyzed=len(results), files_with_patterns=files_with_patterns,
            stable_anchors_found=0,  # Not calculated in debug mode
            processing_time=processing_time)
```

**Replace with:**
```python
try:
    # Run multi-file pattern analysis
    analyzer = MultiFilePatternAnalyzer(title=title, files=pdf_files)
    
    # Try single-anchor approach first
    results, all_file_data = analyzer.analyze_all_files(extract_and_process)
    
    # Check if single-anchor failed (no chunks found in any file)
    if all(r.total_chunks_found == 0 for r in results.values()):
        ic(ict(), "Single-anchor approach failed, trying multi-anchor approach...")
        
        # Try multi-anchor approach
        viable_anchors = analyzer.find_multiple_anchors(all_file_data)
        
        if viable_anchors:
            ic(ict(), f"Found {len(viable_anchors)} viable anchors for multi-anchor approach")
            
            # Validate with multi-anchor
            validation_results = analyzer.validate_anchors_on_files(all_file_data)
            
            # Convert validation results to FileAnalysisResult format
            results = analyzer.convert_validation_to_file_results(validation_results)
            
            # Get reconstructed titles
            found_titles = analyzer.get_found_titles_dict(validation_results)
            
            ic(ict(), f"Multi-anchor validation: {validation_results['successful_files']}/{validation_results['total_files']} files successful")
        else:
            ic(ict(), "Multi-anchor approach also failed - no viable anchors found")
            found_titles = {}
    else:
        # Single-anchor succeeded, no reconstructed titles available
        found_titles = {}

    # Count successes
    template_file = ""
    files_with_patterns = 0

    for filename, result in results.items():
        if result.template_file:
            template_file = filename
        if result.total_chunks_found > 0:
            files_with_patterns += 1

    processing_time = (dt2.now() - start).total_seconds()

    return CaseResult(case_path=case_path, pdf_count=len(pdf_files), success=True, inferred_title=title,
            template_file=template_file, total_files_analyzed=len(results), files_with_patterns=files_with_patterns,
            stable_anchors_found=0,  # Not calculated in debug mode
            processing_time=processing_time, found_titles=found_titles)
```

### Change 4: Update JSON Generation (around line 234-238)
**Find:**
```python
case_dict = {'case_path' : case.case_path, 'pdf_count': case.pdf_count, 'success': case.success,
    'error_message'      : case.error_message, 'inferred_title': case.inferred_title,
    'template_file'      : case.template_file, 'total_files_analyzed': case.total_files_analyzed,
    'files_with_patterns': case.files_with_patterns, 'processing_time': case.processing_time}
```

**Replace with:**
```python
case_dict = {'case_path' : case.case_path, 'pdf_count': case.pdf_count, 'success': case.success,
    'error_message'      : case.error_message, 'inferred_title': case.inferred_title,
    'template_file'      : case.template_file, 'total_files_analyzed': case.total_files_analyzed,
    'files_with_patterns': case.files_with_patterns, 'processing_time': case.processing_time,
    'found_titles'       : case.found_titles}
```

### Change 5: Update Report Generation (around line 288-295)
**Find:**
```python
if case.success:
    report_lines.append(
        f"    Template File: {Path(case.template_file).name if case.template_file else 'None'}")
    report_lines.append(f"    Files Analyzed: {case.total_files_analyzed}")
    report_lines.append(f"    Files with Patterns: {case.files_with_patterns}")
    report_lines.append(f"    Processing Time: {case.processing_time:.2f}s")
else:
    report_lines.append(f"    Error: {case.error_message}")
```

**Replace with:**
```python
if case.success:
    report_lines.append(
        f"    Template File: {Path(case.template_file).name if case.template_file else 'None'}")
    report_lines.append(f"    Files Analyzed: {case.total_files_analyzed}")
    report_lines.append(f"    Files with Patterns: {case.files_with_patterns}")
    report_lines.append(f"    Processing Time: {case.processing_time:.2f}s")
    
    # Add reconstructed titles if available
    if case.found_titles:
        report_lines.append("")
        report_lines.append("    " + "=" * 56)
        report_lines.append("    RECONSTRUCTED TITLES")
        report_lines.append("    " + "=" * 56)
        for filename, title in sorted(case.found_titles.items()):
            status = "✓" if title else "✗"
            short_name = Path(filename).name
            report_lines.append(f"    {status} {short_name}: {title}")
else:
    report_lines.append(f"    Error: {case.error_message}")
```

---

## Summary

**Most Critical Change:** Line ~292 in pattern_analyzer.py
```python
# OLD: if viable_files < len(all_file_data):
# NEW: if viable_files == 0:
```
This single change enables multi-anchor mode by allowing anchors that don't cover all files.

**Expected Result:**
- Batch processor will show "RECONSTRUCTED TITLES" section
- Each successful case will display found title chunks
- Format: ✓ filename.pdf: RECONSTRUCTED-TITLE-HERE
