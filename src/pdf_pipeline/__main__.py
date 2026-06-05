"""Package entry point: ``python -m pdf_pipeline {single|batch}``."""
import argparse

from .cli import batch_processor, single_file


def main() -> int:
    parser = argparse.ArgumentParser(prog="pdf_pipeline", description=__doc__)
    parser.add_argument("command", choices=["single", "batch"],
                        help="single: analyse one project's PDFs; batch: process a directory list")
    args = parser.parse_args()

    if args.command == "single":
        return single_file.main()
    return batch_processor.main()


if __name__ == "__main__":
    raise SystemExit(main())
