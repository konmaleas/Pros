from text_extractor import TextExtractor
from text_processor import TextProcessor
from frequency_analyzer import FrequencyAnalyzer
from adaptive_filter import AdaptiveFilter
from pattern_analyzer import FileAnalysisResult
from pattern_analyzer import MultiFilePatternAnalyzer
from modules.path_manipulation import dst_exists
from modules.dict_opers import dict2list, sorted_dict_2, list_in_dict
from modules.file_opers import file_write, read_pickles
from modules.time_oper import start_time, end_time
from reorganize_files import create_dst_dirs, reorganize_files, pdf_files
from pathlib import Path, PurePath
from os.path import join, exists, expanduser as home
from os import listdir
import operator
from typing import List, Dict, Tuple
from platform import system
from datetime import datetime as dt2
from icecream import ic


def ict():
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


timestamp = dt2.now().strftime("%Y%m%d_%H%M%S")
debug_path = dst_exists(Path(home('~')) / Path('PycharmProjects/Pros/files/reports/v1.3.2') / Path(timestamp))


def debug_file(file: Path, *args):
    file_write(file, ic.format(ict(), args, 'w'))


# Utility functions for pipeline composition
def extract_and_process(filepath: Path) -> Tuple[str, List[List[str]]]:
    """
    Run Stages 1A and 1B together.

    Returns:
        Tuple of (raw_text, processed_lines)
    """
    # Stage 1A: Extract raw text
    raw_text = TextExtractor.extract_raw_text(filepath)
    debug_file(debug_path / Path('1a_raw_text.txt'), raw_text)

    # Stage 1B: Process to clean lines
    processed_lines = TextProcessor.process_text_to_lines(raw_text)
    debug_file(debug_path / Path('1b_processed_lines.txt'), processed_lines)

    return raw_text, processed_lines


def full_text_analysis(filepath: Path) -> Tuple[List[List[str]], Dict]:
    """
    Run Stages 1A, 1B, and 2 together.

    Returns:
        Tuple of (processed_lines, frequency_analysis)
    """
    # Stages 1A & 1B
    raw_text, processed_lines = extract_and_process(filepath)

    # Stage 2: Frequency analysis
    analyzer = FrequencyAnalyzer()
    frequency_data = analyzer.analyze_text_frequencies(processed_lines)
    debug_file(debug_path / Path('2_frequency_data.txt'), frequency_data)

    return processed_lines, frequency_data


def get_complete_analysis_multi_anchor(filepath: Path, title: str, files: List[Path], extract_and_process_func) -> Dict:
    """
    Run complete pipeline analysis with MULTI-ANCHOR support (Stages 1A through 4).

    NEW: Uses find_multiple_anchors() for split-title scenarios.

    Args:
        filepath: Path to PDF file being analyzed
        title: Document title (e.g., "NCM-DD-B1-DR-ARC-4408-P1")
        files: List of all files for multi-file pattern analysis
        extract_and_process_func: Function for stages 1A+1B processing

    Returns:
        Dict with all analysis data including multi-anchor assignments
    """
    # Run Stages 1A, 1B, 2 (Text extraction and frequency analysis)
    processed_lines, frequency_data = full_text_analysis(filepath)

    # Extract title chunks for title-specific analysis
    title_chunks = title.split('-')
    debug_file(debug_path / Path('4.1_title_chunks.txt'), title_chunks)

    # Create frequency analyzer instance
    analyzer = FrequencyAnalyzer()
    analyzer.word_frequencies = frequency_data['word_frequencies']
    analyzer.chunk_line_positions = frequency_data['chunk_line_positions']

    # Get filtering data for Stage 3
    filtering_data = {'processed_lines': processed_lines, 'title_chunks': title_chunks,
        'title_chunk_frequencies'      : analyzer.get_title_chunk_frequencies(title_chunks),
        'title_chunk_positions'        : analyzer.get_title_chunk_positions(title_chunks),
        'noise_threshold'              : analyzer.calculate_noise_threshold(title_chunks),
        'word_frequencies'             : frequency_data['word_frequencies'],
        'high_frequency_words'         : frequency_data['high_frequency_words'],
        'total_lines'                  : frequency_data['total_lines'],
        'total_unique_words'           : frequency_data['total_unique_words']}

    debug_file(debug_path / Path('4.2_title_chunk_frequencies.txt'), filtering_data['title_chunk_frequencies'])
    debug_file(debug_path / Path('4.3_title_chunk_positions.txt'), filtering_data['title_chunk_positions'])

    # Stage 3: Apply adaptive filtering
    adaptive_filter = AdaptiveFilter(title_chunks=title_chunks, noise_threshold=filtering_data['noise_threshold'])

    filtered_lines = adaptive_filter.filter_text_lines(processed_lines, frequency_data)
    debug_file(debug_path / Path('4.1_filtered_lines.txt'), filtered_lines)

    # Stage 4: Multi-Anchor Pattern Analysis
    print("\n" + "=" * 60)
    print("STARTING MULTI-ANCHOR PATTERN ANALYSIS")
    print("=" * 60)

    pattern_analyzer = MultiFilePatternAnalyzer(title=title, files=files)

    # CRITICAL: Calculate ONE noise threshold for ALL files (use from first file analysis)
    global_noise_threshold = filtering_data['noise_threshold']
    print(f"Using global noise threshold: {global_noise_threshold}")

    # NEW: Process all files to build data for anchor detection
    all_file_data = {}
    for file_path in files:
        file_raw, file_processed = extract_and_process_func(file_path)
        file_freq_analyzer = FrequencyAnalyzer()
        file_freq_data = file_freq_analyzer.analyze_text_frequencies(file_processed)

        # CRITICAL: Use SAME noise_threshold for ALL files
        file_filter = AdaptiveFilter(title_chunks=title_chunks, noise_threshold=global_noise_threshold
                # Use global threshold
        )
        file_filtered = file_filter.filter_text_lines(file_processed, file_freq_data)

        # Re-analyze filtered text to get correct chunk positions
        file_filtered_freq = FrequencyAnalyzer()
        file_filtered_freq_data = file_filtered_freq.analyze_text_frequencies(file_filtered)

        all_file_data[str(file_path)] = {'filtered_lines': file_filtered,
            'chunk_positions'                            : file_filtered_freq_data['chunk_line_positions']
            # Correct positions
        }

    # NEW: Find all viable anchors for complete coverage (no limit)
    viable_anchors = pattern_analyzer.find_multiple_anchors(all_file_data)

    print(f"\n{'=' * 60}")
    print("DEDUPLICATED & RANKED ANCHORS (by distance quality)")
    print(f"{'=' * 60}")

    for i, anchor in enumerate(viable_anchors, 1):
        anchor_key = tuple(anchor)
        chunks = pattern_analyzer.anchor_chunk_assignments.get(anchor_key, {})

        if chunks:
            distances = [abs(d) for d in chunks.values()]
            avg_dist = sum(distances) / len(distances)
            max_dist = max(distances)

            print(f"\n{i}. Anchor: [{' '.join(anchor)}]")
            print(f"   Avg distance: {avg_dist:.2f} | Max distance: {max_dist}")
            print(f"   Covers {len(chunks)} chunk(s):")

            for chunk, distance in sorted(chunks.items(), key=lambda x: abs(x[1])):
                sign = '+' if distance >= 0 else ''
                print(f"     - {chunk}: {sign}{distance} lines")

    print(f"\n{'=' * 60}")
    print(f"Total viable anchors: {len(viable_anchors)}")

    # NEW: Print coverage report
    coverage_report = pattern_analyzer.get_anchor_coverage_report()
    print(f"\n{coverage_report}")
    debug_file(debug_path / Path('5.0_anchor_coverage_report.txt'), coverage_report)

    # NEW: Save anchor assignments
    anchor_assignments_readable = {" ".join(anchor): chunks for anchor, chunks in
        pattern_analyzer.anchor_chunk_assignments.items()}
    debug_file(debug_path / Path('5.1_anchor_chunk_assignments.txt'), anchor_assignments_readable)

    # Return complete analysis with multi-anchor data
    return {**filtering_data, 'filtered_lines': filtered_lines, 'viable_anchors': viable_anchors,
        'anchor_chunk_assignments'            : pattern_analyzer.anchor_chunk_assignments,
        'coverage_complete'                   : pattern_analyzer._validate_complete_coverage(),
        'coverage_report'                     : coverage_report}


if __name__ == '__main__':
    start_time()

    # Title with known split-chunk scenario
    title = 'NCM-DD-B1-DR-ARC-4408-P1'

    # Path configuration
    home_2 = Path(home('~')) / Path('PyTests')

    if system() == 'Windows':
        home_2 = Path('C:/PyTests')

    path = home_2 / Path('Submission/Process/1910 ncm/dst/44xx')

    if not path.exists():
        print(f"ERROR: Path does not exist: {path}")
        exit(1)

    # Get all PDF files in directory
    files = [Path(path / f) for f in listdir(path) if
             Path(path / f).is_file() and Path(path / f).exists() and str(f).endswith('.pdf')]

    print(f"\nFound {len(files)} PDF file(s) in {path}")

    if not files:
        print("ERROR: No PDF files found")
        exit(1)

    # Use first file (alphabetically sorted for consistency)
    pdf_file = min(files)
    print(f"\nAnalyzing: {pdf_file.name}")
    print(f"Title: {title}\n")

    # Run multi-anchor analysis
    result = get_complete_analysis_multi_anchor(pdf_file, title, files, extract_and_process)

    # Print summary
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"Coverage complete: {result['coverage_complete']}")
    print(f"Number of anchors: {len(result['viable_anchors'])}")
    print(f"Results saved to: {debug_path}")

    ic(ict(), end_time())
