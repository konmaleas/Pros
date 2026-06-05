import json
import csv
import pickle
import traceback
from modules.time_oper import start_time, end_time
from text_extractor import TextExtractor
from text_processor import TextProcessor
from frequency_analyzer import FrequencyAnalyzer
from adaptive_filter import AdaptiveFilter
from pattern_analyzer import MultiFilePatternAnalyzer
from utils import split_title_chunks
from os.path import expanduser as home
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from multiprocessing import Pool, cpu_count
from datetime import datetime as dt2
from icecream import ic


def ict():
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


def extract_and_process(filepath: Path) -> Tuple[str, List[List[str]]]:
    """Run Stages 1A and 1B together."""
    raw_text = TextExtractor.extract_raw_text(filepath)
    processed_lines = TextProcessor.process_text_to_lines(raw_text)
    return raw_text, processed_lines


def find_template_file(files: List[Path]) -> Optional[Path]:
    """
    Find template file using 'most complete title' strategy.
    Falls back to min() if strategy fails.

    Args:
        files: List of PDF file paths

    Returns:
        Template file path or None
    """
    if not files:
        return None

    # Strategy B: Most complete title (max chunks)
    try:
        max_chunks = 0
        template_file = None

        for file in files:
            title = file.stem
            chunk_count = len(split_title_chunks(title))

            if chunk_count > max_chunks:
                max_chunks = chunk_count
                template_file = file

        if template_file:
            print(f"  Template selected (most complete): {template_file.name} ({max_chunks} chunks)")
            return template_file

    except Exception as e:
        print(f"  Warning: Smart detection failed: {e}")

    # Fallback: min() alphabetical
    template_file = min(files)
    print(f"  Template selected (fallback min): {template_file.name}")
    return template_file


def process_single_batch(batch_info: Tuple[str, Path, List[Path], int]) -> Dict:
    """
    Process a single batch of PDF files.

    Args:
        batch_info: Tuple of (batch_name, batch_path, files, min_files)

    Returns:
        Dict with batch results
    """
    batch_name, batch_path, files, min_files = batch_info
    start_time = dt2.now()

    result = {'batch_name'    : batch_name, 'batch_path': str(batch_path), 'status': 'unknown', 'files_processed': 0,
              'success_rate'  : 0.0, 'successful_files': 0, 'failed_files': 0, 'viable_anchors': 0,
              'template_file' : None, 'template_title': None, 'found_titles': {}, 'errors': [], 'duration_seconds': 0.0,
              'timestamp'     : start_time.isoformat()}

    try:
        print(f"\n{'=' * 80}")
        print(f"Processing: {batch_name}")
        print(f"Path: {batch_path}")
        print(f"{'=' * 80}")

        result['files_processed'] = len(files)

        # Check minimum files requirement
        if len(files) <= min_files:
            result['status'] = 'skipped'
            result['errors'].append(f"Insufficient files: {len(files)} <= {min_files}")
            print(f"  SKIPPED: Only {len(files)} files (minimum: {min_files + 1})")
            return result

        print(f"  Found {len(files)} PDF files")

        # Find template file
        template_file = find_template_file(files)
        if not template_file:
            result['status'] = 'failed'
            result['errors'].append("No template file found")
            return result

        result['template_file'] = template_file.name

        # Extract title from template filename
        title = template_file.stem
        result['template_title'] = title
        print(f"  Template title: {title}")

        # Extract title chunks using multi-delimiter split
        title_chunks = split_title_chunks(title)
        if len(title_chunks) < 2:
            result['status'] = 'failed'
            result['errors'].append(f"Invalid title format: {title}")
            return result

        print(f"  Title chunks: {title_chunks}")

        # Process all files - store PROCESSED lines
        print("  Processing files...")
        all_file_data = {}

        for file_path in files:
            try:
                file_raw, file_processed = extract_and_process(file_path)

                # Analyze frequencies
                file_freq_analyzer = FrequencyAnalyzer()
                file_freq_data = file_freq_analyzer.analyze_text_frequencies(file_processed)

                # Store processed lines for validation
                all_file_data[str(file_path)] = {'processed_lines': file_processed,
                                                 'chunk_positions': file_freq_data['chunk_line_positions']}

            except Exception as e:
                print(f"    Warning: Failed to process {file_path.name}: {e}")
                result['errors'].append(f"File processing error ({file_path.name}): {str(e)}")

        if not all_file_data:
            result['status'] = 'failed'
            result['errors'].append("All files failed to process")
            return result

        print(f"  Successfully processed {len(all_file_data)}/{len(files)} files")

        # Create pattern analyzer
        pattern_analyzer = MultiFilePatternAnalyzer(title=title, files=files)

        # Find multiple viable anchors
        print("  Finding viable anchors...")
        viable_anchors = pattern_analyzer.find_multiple_anchors(all_file_data)
        result['viable_anchors'] = len(viable_anchors)

        if not viable_anchors:
            result['status'] = 'failed'
            result['errors'].append("No viable anchors found")
            print("  ERROR: No viable anchors found")
            return result

        print(f"  Found {len(viable_anchors)} viable anchor(s)")

        # Validate anchors across all files
        print("  Validating anchors...")
        validation_results = pattern_analyzer.validate_anchors_on_files(all_file_data)

        result['success_rate'] = validation_results['success_rate']
        result['successful_files'] = validation_results['successful_files']
        result['failed_files'] = validation_results['failed_files']

        # Get reconstructed titles
        found_titles = pattern_analyzer.get_found_titles_dict(validation_results)
        result['found_titles'] = found_titles

        # Determine overall status
        if validation_results['success_rate'] == 100.0:
            result['status'] = 'success'
            print(f"  ✓ SUCCESS: 100% validation rate")
        elif validation_results['success_rate'] >= 80.0:
            result['status'] = 'partial'
            print(f"  ⚠ PARTIAL: {validation_results['success_rate']:.1f}% validation rate")
        else:
            result['status'] = 'failed'
            print(f"  ✗ FAILED: {validation_results['success_rate']:.1f}% validation rate")

        # Add failed file details
        for filename, file_result in validation_results['per_file_results'].items():
            if not file_result['all_chunks_found']:
                error_msg = f"{Path(filename).name}: Missing {file_result['missing_chunks']}"
                result['errors'].append(error_msg)

    except Exception as e:
        result['status'] = 'error'
        result['errors'].append(f"Exception: {str(e)}")
        result['errors'].append(traceback.format_exc())
        print(f"  ERROR: {e}")
        traceback.print_exc()

    finally:
        end_time = dt2.now()
        result['duration_seconds'] = (end_time - start_time).total_seconds()
        print(f"  Duration: {result['duration_seconds']:.2f}s")

    return result


def save_results_json(results: List[Dict], output_path: Path):
    """Save detailed results to JSON file."""
    # Convert Path objects to strings for JSON serialization
    serializable_results = []
    for result in results:
        result_copy = result.copy()
        # Convert batch_name if it's a Path
        if isinstance(result_copy.get('batch_name'), Path):
            result_copy['batch_name'] = str(result_copy['batch_name'])
        serializable_results.append(result_copy)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, indent=2, ensure_ascii=False)
    print(f"\nJSON results saved to: {output_path}")


def save_results_csv(results: List[Dict], output_path: Path):
    """Save summary results to CSV file."""
    fieldnames = ['batch_name', 'status', 'files_processed', 'success_rate', 'successful_files', 'failed_files',
                  'viable_anchors', 'template_title', 'duration_seconds', 'error_count', 'timestamp']

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for result in results:
            row = {'batch_name'      : result['batch_name'], 'status': result['status'],
                   'files_processed' : result['files_processed'], 'success_rate': result['success_rate'],
                   'successful_files': result['successful_files'], 'failed_files': result['failed_files'],
                   'viable_anchors'  : result['viable_anchors'], 'template_title': result['template_title'],
                   'duration_seconds': round(result['duration_seconds'], 2), 'error_count': len(result['errors']),
                   'timestamp'       : result['timestamp']}
            writer.writerow(row)

    print(f"CSV summary saved to: {output_path}")


def load_pdf_paths(pkl_path: Path) -> List[Path]:
    """
    Load PDF file paths from pickle file.

    Args:
        pkl_path: Path to pickle file containing PDF paths

    Returns:
        List of Path objects
    """
    with open(pkl_path, 'rb') as f:
        paths = pickle.load(f)
    return paths


def group_files_by_batch(pdf_paths: List[Path]) -> Dict[Path, List[Path]]:
    """
    Group PDF files by their parent directory (batch).

    Args:
        pdf_paths: List of PDF file paths

    Returns:
        Dict mapping batch_dir -> list of files in that batch
    """
    batches = {}
    for filepath in pdf_paths:
        batch_dir = Path(filepath.parent).stem
        if batch_dir not in batches:
            batches[batch_dir] = []
        batches[batch_dir].append(filepath)

    return batches


def process_all_batches(pdf_paths_pkl: Path, min_files: int = 2, num_workers: int = None):
    """
    Process all submission batches using multiprocessing.

    Args:
        pdf_paths_pkl: Path to pickle file containing all PDF paths
        min_files: Minimum number of files required (skip if <= this)
        num_workers: Number of parallel workers (default: CPU count - 1)
    """
    if num_workers is None:
        num_workers = max(1, cpu_count() - 1)

    print(f"{'=' * 80}")
    print(f"BATCH PROCESSOR - Starting")
    print(f"{'=' * 80}")
    print(f"PDF paths file: {pdf_paths_pkl}")
    print(f"Min files threshold: {min_files}")
    print(f"Parallel workers: {num_workers}")

    # Load PDF paths
    print("Loading PDF paths...")
    pdf_paths = load_pdf_paths(pdf_paths_pkl)
    print(f"Loaded {len(pdf_paths)} PDF files")

    # Group by batch (parent directory)
    print("Grouping files by batch...")
    batches = group_files_by_batch(pdf_paths)
    print(f"Found {len(batches)} batches")

    # Create batch_list for processing
    batch_list = []
    for batch_dir, files in sorted(batches.items()):
        batch_dir = Path(batch_dir)
        # Create batch name: Project/Submission
        batch_name = Path(batch_dir.parent.name) / Path(batch_dir.name)
        batch_list.append((batch_name, batch_dir, files, min_files))

    print(f"Prepared {len(batch_list)} batches for processing")
    print(f"{'=' * 80}\n")

    # Process batches in parallel
    start_time = dt2.now()

    with Pool(processes=num_workers) as pool:
        results = pool.map(process_single_batch, batch_list)

    end_time = dt2.now()
    total_duration = (end_time - start_time).total_seconds()

    # Print summary
    print(f"\n{'=' * 80}")
    print(f"BATCH PROCESSOR - Complete")
    print(f"{'=' * 80}")

    status_counts = {'success': 0, 'partial': 0, 'failed': 0, 'skipped': 0, 'error': 0}

    for result in results:
        status = result['status']
        if status in status_counts:
            status_counts[status] += 1

    print(f"Total batches: {len(results)}")
    print(f"Success: {status_counts['success']}")
    print(f"Partial: {status_counts['partial']}")
    print(f"Failed: {status_counts['failed']}")
    print(f"Skipped: {status_counts['skipped']}")
    print(f"Errors: {status_counts['error']}")
    print(f"Total duration: {total_duration:.2f}s ({total_duration / 60:.1f} min)")
    print(f"{'=' * 80}\n")

    # Save results
    timestamp = dt2.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path('batch_results')
    output_dir.mkdir(exist_ok=True)

    json_path = output_dir / f'results_{timestamp}.json'
    csv_path = output_dir / f'summary_{timestamp}.csv'

    save_results_json(results, json_path)
    save_results_csv(results, csv_path)

    return results


if __name__ == '__main__':
    # Configuration
    home = Path(home('~'))
    base_dir = Path('PycharmProjects/Pros/claude/files/pkl')
    paths_file = Path('copied_files.pkl')  # Your pickle file with PDF paths
    pdf_paths_file = home / base_dir / paths_file
    min_files_threshold = 2
    num_workers = 3  # Adjust based on CPU cores

    start_time()
    # Run batch processing
    results_ = process_all_batches(pdf_paths_pkl=pdf_paths_file, min_files=min_files_threshold, num_workers=num_workers)
    end_time(4)

    print("\nProcessing complete!")
