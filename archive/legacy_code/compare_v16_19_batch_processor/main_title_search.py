from text_extractor import TextExtractor
from text_processor import TextProcessor
from frequency_analyzer import FrequencyAnalyzer
from adaptive_filter import AdaptiveFilter
from pattern_analyzer import MultiFilePatternAnalyzer
from modules.path_manipulation import dst_exists
from modules.file_opers import file_write, read_pickles
from modules.time_oper import start_time, end_time
from pathlib import Path
from os.path import expanduser as home
from os import listdir
from typing import List, Dict, Tuple
from platform import system
from datetime import datetime as dt2
from icecream import ic


def ict():
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


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


def get_complete_analysis_multi_anchor(filepath: Path,
                                       title: str,
                                       files: List[Path],
                                       extract_and_process_func) -> Dict:
    """
    Run complete pipeline analysis with MULTI-ANCHOR support (Stages 1A through 4).

    NEW: Uses processed_lines for validation instead of filtered_lines.
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
    filtering_data = {'processed_lines': processed_lines,
                      'title_chunks': title_chunks,
                      'title_chunk_frequencies': analyzer.get_title_chunk_frequencies(title_chunks),
                      'title_chunk_positions': analyzer.get_title_chunk_positions(title_chunks),
                      'noise_threshold': analyzer.calculate_noise_threshold(title_chunks),
                      'word_frequencies': frequency_data['word_frequencies'],
                      'high_frequency_words': frequency_data['high_frequency_words'],
                      'total_lines': frequency_data['total_lines'],
                      'total_unique_words': frequency_data['total_unique_words']}

    debug_file(debug_path / Path('4.2_title_chunk_frequencies.txt'), filtering_data['title_chunk_frequencies'])
    debug_file(debug_path / Path('4.3_title_chunk_positions.txt'), filtering_data['title_chunk_positions'])

    # Stage 3: Apply adaptive filtering (for analysis only, not for validation)
    adaptive_filter = AdaptiveFilter(title_chunks=title_chunks, noise_threshold=filtering_data['noise_threshold'])
    filtered_lines = adaptive_filter.filter_text_lines(processed_lines, frequency_data)
    debug_file(debug_path / Path('4.1_filtered_lines.txt'), filtered_lines)

    # Stage 4: Multi-Anchor Pattern Analysis
    print("\n" + "=" * 60)
    print("STARTING MULTI-ANCHOR PATTERN ANALYSIS")
    print("=" * 60)

    pattern_analyzer = MultiFilePatternAnalyzer(title=title, files=files)

    # Print learned chunk patterns
    print("\nLearned Chunk Patterns:")
    for chunk, pattern in pattern_analyzer.chunk_patterns.items():
        print(f"  {chunk}: length={pattern.length}, "
              f"alpha={pattern.is_alpha}, "
              f"digit={pattern.is_digit}, "
              f"mixed={pattern.is_mixed}")

    # CRITICAL: Calculate ONE noise threshold for ALL files
    global_noise_threshold = filtering_data['noise_threshold']
    print(f"\nUsing global noise threshold: {global_noise_threshold}")

    # NEW: Process all files - store PROCESSED lines for validation
    all_file_data = {}
    for file_path in files:
        file_raw, file_processed = extract_and_process_func(file_path)

        # Analyze frequencies on processed lines to find chunks
        file_freq_analyzer = FrequencyAnalyzer()
        file_freq_data = file_freq_analyzer.analyze_text_frequencies(file_processed)

        # NEW: Store PROCESSED lines instead of filtered
        all_file_data[str(file_path)] = {'processed_lines': file_processed,
                                         'chunk_positions': file_freq_data['chunk_line_positions']}

        # Optional: Still save filtered lines for debugging
        file_filter = AdaptiveFilter(title_chunks=title_chunks, noise_threshold=global_noise_threshold)
        file_filtered = file_filter.filter_text_lines(file_processed, file_freq_data)
        pattern_analyzer.save_filtered_text_to_file(str(file_path), file_filtered)

    # Find multiple viable anchors for complete coverage
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

    # Print coverage report
    coverage_report = pattern_analyzer.get_anchor_coverage_report()
    # print(f"\n{coverage_report}")

    # Validate anchors across all files using PATTERN MATCHING on PROCESSED LINES
    print("\n" + "=" * 60)
    print("VALIDATING ANCHORS ACROSS ALL FILES (Pattern-Based on Processed Lines)")
    print("=" * 60)

    validation_results = pattern_analyzer.validate_anchors_on_files(all_file_data)
    pattern_analyzer.print_validation_report(validation_results)

    # Print discovered offsets
    if pattern_analyzer.discovered_offsets:
        print("\n" + "=" * 60)
        print("DISCOVERED OFFSETS SUMMARY")
        print("=" * 60)
        for anchor_key, chunk_offsets in pattern_analyzer.discovered_offsets.items():
            anchor_str = ' '.join(anchor_key)
            print(f"\nAnchor: [{anchor_str}]")
            for template_chunk, offsets in chunk_offsets.items():
                if len(offsets) > 1:
                    print(f"  {template_chunk}: learned {len(offsets) - 1} new offset(s)")

    # Print detailed validation results per file
    print("\n" + "=" * 60)
    print("DETAILED VALIDATION RESULTS")
    print("=" * 60)

    for filename, result in validation_results['per_file_results'].items():
        file_short_name = Path(filename).name
        status = "✓ SUCCESS" if result['all_chunks_found'] else "✗ FAILED"

        print(f"\n{file_short_name}: {status}")

        if result['all_chunks_found']:
            for anchor_key, anchor_data in result['anchor_results'].items():
                if anchor_data['found'] and anchor_data['chunks_matched'] > 0:
                    anchor_str = ' '.join(anchor_key)[:30]
                    print(f"  Anchor: [{anchor_str}...] matched {anchor_data['chunks_matched']} chunk(s)")

                    for chunk, details in anchor_data['chunk_details'].items():
                        if details['found']:
                            found_val = details['found_value']
                            found_off = details['found_offset']
                            predicted = details['predicted_line']

                            if found_off != (predicted - anchor_data['positions'][0]):
                                print(f"    {chunk} → found '{found_val}' at offset {found_off:+d} (learned)")
                            else:
                                print(f"    {chunk} → found '{found_val}' at offset {found_off:+d}")
        else:
            print(f"  Missing chunks: {result['missing_chunks']}")

    # Save debug files
    debug_file(debug_path / Path('5.4_discovered_offsets.txt'), pattern_analyzer.discovered_offsets)
    debug_file(debug_path / Path('5.0_anchor_coverage_report.txt'), coverage_report)
    debug_file(debug_path / Path('5.2_validation_results.txt'), validation_results)

    # Save anchor assignments
    anchor_assignments_readable = {" ".join(anchor): chunks for anchor, chunks in
                                   pattern_analyzer.anchor_chunk_assignments.items()}
    debug_file(debug_path / Path('5.1_anchor_chunk_assignments.txt'), anchor_assignments_readable)

    chunk_patterns_readable = {chunk:
                                   {'length': p.length,
                                    'is_alpha': p.is_alpha,
                                    'is_digit': p.is_digit,
                                    'is_mixed': p.is_mixed}
                               for chunk, p in pattern_analyzer.chunk_patterns.items()}

    debug_file(debug_path / Path('5.3_chunk_patterns.txt'), chunk_patterns_readable)

    # Get reconstructed titles
    found_titles = pattern_analyzer.get_found_titles_dict(validation_results)
    # Print them
    print("\n" + "=" * 60)
    print("RECONSTRUCTED TITLES")
    print("=" * 60)
    for filename, title in found_titles.items():
        status = "✓" if title else "✗"
        print(f"{status} {filename}: {title}")

    # Save to debug file
    debug_file(debug_path / Path('6.0_found_titles.txt'), found_titles)

    # Return complete analysis
    return {**filtering_data, 'filtered_lines': filtered_lines,
            'viable_anchors': viable_anchors,
            'anchor_chunk_assignments': pattern_analyzer.anchor_chunk_assignments,
            'chunk_patterns': pattern_analyzer.chunk_patterns,
            'coverage_complete': pattern_analyzer.validate_complete_coverage(),
            'coverage_report': coverage_report,
            'validation_results': validation_results,
            'found_titles': found_titles}


if __name__ == '__main__':
    start_time()

    timestamp = dt2.now().strftime("%Y%m%d_%H%M%S")
    debug_path = dst_exists(Path(home('~')) /
                            Path('PycharmProjects/Pros/files/reports/claude') /
                            Path(timestamp))

    # Title with known split-chunk scenario
    # title = 'NCM-DD-B1-DR-ARC-4408-P1'
    title = 'ATH1-DC03-CAP-20302-PLN-2-011-AL-00-T00_4-SECTIONS_DC3'

    # Path configuration
    home_2 = Path(home('~')) / Path('PyTests')

    if system() == 'Windows':
        home_2 = Path('C:/PyTests')

    path = Path('/media/konstantinos/DATA/PyTests/Submission/Process/2502 DATA4-DC02+DC03/PDF')
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
    pdf_file = path / Path(f'{title}.pdf')
    print(f"\nAnalyzing: {pdf_file.name}")
    print(f"Title: {title}\n")

    # Run multi-anchor analysis with pattern-based validation
    result = get_complete_analysis_multi_anchor(pdf_file, title, files, extract_and_process)

    # Print summary
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"Coverage complete: {result['coverage_complete']}")
    print(f"Number of anchors: {len(result['viable_anchors'])}")
    print(f"Validation success rate: {result['validation_results']['success_rate']:.1f}%")
    print(f"Successful files: "
          f"{result['validation_results']['successful_files']}/"
          f"{result['validation_results']['total_files']}")
    print(f"Results saved to: {debug_path}")

    ic(ict(), end_time())
