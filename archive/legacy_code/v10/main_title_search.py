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
# from curses.ascii import ispunct, isspace
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
    # ic(ict(), start_time())
    # if self.active:
    file_write(file, ic.format(ict(), args, 'w'))
    # ic(ict(), end_time())


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

    return raw_text, processed_lines # Works perfectly for the template file


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


def get_filtering_data(filepath: Path, title: str) -> Dict:
    """
    Get all data needed for Stage 3 (AdaptiveFilter).

    This breaks the circular dependency by providing complete frequency analysis
    BEFORE any content filtering is applied.

    Args:
        filepath: Path to PDF file
        title: Document title (e.g., "4005-RES-VAP-DWG-233-IC-07020-0")

    Returns:
        Dict with all data needed for intelligent filtering
    """
    # Run complete analysis (Stages 1A, 1B, 2)
    processed_lines, frequency_data = full_text_analysis(filepath)

    # Extract title chunks for title-specific analysis
    title_chunks = title.split('-')  # Could use TitleAnalysis for more sophisticated parsing

    # Create analyzer instance to access title-specific methods
    analyzer = FrequencyAnalyzer()
    analyzer.word_frequencies = frequency_data['word_frequencies']
    analyzer.chunk_line_positions = frequency_data['chunk_line_positions']

    debug_file(debug_path / Path('3.0_analyzer_word_frequencies.txt'),
               analyzer.word_frequencies)
    debug_file(debug_path / Path('3.1_analyzer_chunk_line_positions.txt'),
               analyzer.chunk_line_positions)

    # Return comprehensive filtering data
    return {'processed_lines': processed_lines,
            'title_chunks': title_chunks,
            'title_chunk_frequencies': analyzer.get_title_chunk_frequencies(title_chunks),
            'title_chunk_positions': analyzer.get_title_chunk_positions(title_chunks),
            'noise_threshold': analyzer.calculate_noise_threshold(title_chunks),
            'all_word_frequencies': frequency_data['word_frequencies'],
            'high_frequency_words': frequency_data['high_frequency_words'],
            'total_lines': frequency_data['total_lines'],
            'total_unique_words': frequency_data['total_unique_words']}


# Updated integration function
def get_multi_file_analysis(files: List[Path], title: str, extract_and_process_func) -> Dict[str, FileAnalysisResult]:
    """
    Analyze multiple files using stable line anchors.

    Args:
        files: List of PDF files to analyze
        title: Document title for chunk extraction
        extract_and_process_func: External function for stages 1A+1B processing

    Returns:
        Dict mapping filename to analysis results
    """
    analyzer = MultiFilePatternAnalyzer(title=title, files=files)
    return analyzer.analyze_all_files(extract_and_process_func)


def get_complete_analysis(filepath: Path,
                          title: str,
                          files: List[Path], extract_and_process_func) -> Dict:
    """
    Run complete pipeline analysis (Stages 1A through 4).

    This breaks the circular dependency by providing complete frequency analysis
    BEFORE any content filtering, then applies filtering and pattern analysis.

    Args:
        filepath: Path to PDF file
        title: Document title (e.g., "4005-RES-VAP-DWG-233-IC-07020-0")
        files: List of all files for template identification
        extract_and_process_func: External function for stages 1A+1B processing

    Returns:
        Dict with all analysis data including pattern analysis
    """
    # Run Stages 1A, 1B, 2 (Text extraction and frequency analysis)
    processed_lines, frequency_data = full_text_analysis(filepath)

    # Extract title chunks for title-specific analysis
    title_chunks = title.split('-')  # Could use more sophisticated parsing

    # Create frequency analyzer instance
    analyzer = FrequencyAnalyzer()
    analyzer.word_frequencies = frequency_data['word_frequencies']
    analyzer.chunk_line_positions = frequency_data['chunk_line_positions']

    # Get filtering data for Stage 3
    filtering_data = {'processed_lines' : processed_lines,
                      'title_chunks': title_chunks,
                      'title_chunk_frequencies': analyzer.get_title_chunk_frequencies(title_chunks),
                      'title_chunk_positions': analyzer.get_title_chunk_positions(title_chunks),
                      'noise_threshold': analyzer.calculate_noise_threshold(title_chunks),
                      'word_frequencies': frequency_data['word_frequencies'],  # all_word_frequencies
                      'high_frequency_words': frequency_data['high_frequency_words'],
                      'total_lines': frequency_data['total_lines'],
                      'total_unique_words': frequency_data['total_unique_words']}

    # Stage 3: Apply adaptive filtering
    adaptive_filter = AdaptiveFilter(title_chunks=title_chunks, noise_threshold=filtering_data['noise_threshold'])
    # debug_file(debug_path / Path('4.0_adaptive_filter.txt'), adaptive_filter)

    filtered_lines = adaptive_filter.filter_text_lines(processed_lines, frequency_data)
    # debug_file(debug_path / Path('4.1_filtered_lines.txt'), filtered_lines)

    # Stage 4: Pattern analysis (multi-file analysis)
    pattern_analyzer = MultiFilePatternAnalyzer(title=title, files=files)
    # debug_file(debug_path / Path('4.2_pattern_analyzer.txt'), pattern_analyzer)

    # Get results for all files
    all_files_results = pattern_analyzer.analyze_all_files(extract_and_process_func)
    debug_file(debug_path / Path('3_pattern_result.txt'), all_files_results)

    # Get results for the current file being analyzed
    current_file_result = all_files_results.get(str(filepath))

    # If current file result exists, use its data; otherwise create empty defaults
    if current_file_result:
        distance_patterns = current_file_result.distance_patterns
        anchor_chunks = current_file_result.anchor_chunks
        is_template_file = current_file_result.template_file
        chunks_found = current_file_result.total_chunks_found
    else:
        distance_patterns = []
        anchor_chunks = []
        is_template_file = False
        chunks_found = 0

    # Return complete analysis
    return {**filtering_data,
            'filtered_lines': filtered_lines,
            'pattern_analysis': all_files_results,
            # All files results
            'current_file_analysis': current_file_result,  # Current file specific
            'distance_patterns': distance_patterns,
            'anchor_chunks': anchor_chunks,
            'is_template_file': is_template_file,
            'chunks_found': chunks_found}


if __name__ == '__main__':
    start_time()
    # title: {0: '4005', 1: 'RES', 2: 'VAP', 3: 'DWG', 4: '233', 5: 'IC', 6: '07020', 7: '0'}
    # title = '4005-RES-VAP-DWG-233-IC-07020-0'
    title = 'NCM-DD-B1-DR-ARC-4408-P1'
    # In this path are pdf files to be converted into text
    home_0 = '/media/konstantinos/bkp/files/dst_small_group/PROJECTS'
    home_1 = join(home('~'), 'Documents/PyTests/Submission/Seek Title Template/dst/au1.5')
    home_2 = Path(home('~')) / Path('PyTests')

    if system() == 'Windows':
        home_0 = 'D:/files/dst_small_group/PROJECTS'
        home_1 = 'D:/au1.5/20240628'
        home_2 = Path('C:/PyTests')

    path = home_2 / Path('Submission/Process/1910 ncm/dst/44xx')

    # dst_path_list = create_dst_dirs(path, pdf_files())  # Directories are created using this function.
    # Depending on their suffix, files from the main directory were placed into the folders.
    # reorganize_files(path, dst_path_list)

    pdf_file = path / min(listdir(path))
    ic(ict(), pdf_file)

    files = [Path(path / f) for f in listdir(path)
             if Path(path / f).is_file() and
             Path(path / f).exists()]

    if exists(Path(path)):

        pattern = get_complete_analysis(pdf_file, title, files, extract_and_process)
        for e, key in enumerate(pattern.keys()):
            debug_file(debug_path / Path(f'4.{e}_{key}.txt'), pattern[key])

    else:
        ic(ict(), f'{Path(path)} Does not exists!')
    ic(ict(), end_time())
























