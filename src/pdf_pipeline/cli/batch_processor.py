"""CLI entry point: batch-process a list of project directories into reports."""
from datetime import datetime as dt2
from pathlib import Path

from icecream import ic

from ..pipeline.batch import (
    generate_report,
    group_by_projects,
    load_directory_list,
    process_all_projects,
)


def ict():
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


def main() -> int:
    ict()
    start = dt2.now()

    # Input file with directory list
    input_file = Path.home() / 'PycharmProjects/Pros/data/project_dirs.txt'

    # Output directory for reports
    output_dir = (Path.home() /
                  'PycharmProjects/Pros/output/batch_debug' /
                  dt2.now().strftime('%Y%m%d_%H%M%S'))
    output_dir.mkdir(parents=True, exist_ok=True)

    ic(ict(), "Starting batch debug processor")
    ic(ict(), f"Input file: {input_file}")
    ic(ict(), f"Output directory: {output_dir}")

    if not input_file.exists():
        print(f"ERROR: Input file does not exist: {input_file}")
        return 1

    # Load and group directories
    dir_list = load_directory_list(input_file)
    ic(ict(), f"Loaded {len(dir_list)} directory entries")

    projects = group_by_projects(dir_list)
    ic(ict(), f"Grouped into {len(projects)} projects")

    # Process all projects
    results = process_all_projects(projects)

    # Generate reports
    generate_report(results, output_dir)

    elapsed = (dt2.now() - start).total_seconds()
    ic(ict(), f"Total processing time: {elapsed:.2f}s ({elapsed / 60:.1f} minutes)")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
