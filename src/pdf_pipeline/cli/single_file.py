"""CLI entry point: run multi-anchor analysis on a single project's PDFs."""
from datetime import datetime as dt2
from os import listdir
from os.path import expanduser as home
from pathlib import Path
from platform import system

from icecream import ic

from ..pipeline.reorganize import create_dst_dirs, pdf_files, reorganize_files  # noqa: F401 (stubs)
from ..pipeline.single import get_complete_analysis_multi_anchor
from ..pipeline.stages import extract_and_process
from ..utils.path_ops import dst_exists
from ..utils.time_ops import end_time, start_time


def ict():
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


def main() -> int:
    start_time()

    timestamp = dt2.now().strftime("%Y%m%d_%H%M%S")
    debug_path = dst_exists(Path(home('~')) /
                            Path('PycharmProjects/Pros/files/reports/claude') /
                            Path(timestamp))

    # Title with known split-chunk scenario
    title = 'ATH1-DC03-CAP-20302-PLN-2-011-AL-00-T00_4-SECTIONS_DC3'

    # Path configuration
    path = Path('/media/konstantinos/DATA/PyTests/Submission/Process/2502 DATA4-DC02+DC03/PDF')
    if system() == 'Windows':
        path = Path('C:/PyTests')

    if not path.exists():
        print(f"ERROR: Path does not exist: {path}")
        return 1

    # Get all PDF files in directory
    files = [Path(path / f) for f in listdir(path) if
             Path(path / f).is_file() and Path(path / f).exists() and str(f).endswith('.pdf')]

    print(f"\nFound {len(files)} PDF file(s) in {path}")

    if not files:
        print("ERROR: No PDF files found")
        return 1

    pdf_file = path / Path(f'{title}.pdf')
    print(f"\nAnalyzing: {pdf_file.name}")
    print(f"Title: {title}\n")

    # Run multi-anchor analysis with pattern-based validation
    result = get_complete_analysis_multi_anchor(pdf_file, title, files, extract_and_process, debug_path)

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
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
