"""Stub for the removed ``reorganize_files`` module.

The original implementation (which created destination directories and moved
PDF files into them) was deleted during the repository cleanup. These stubs
exist so dependent modules import cleanly; restore the real logic to use them.
"""
from pathlib import Path
from typing import List


def create_dst_dirs(*args, **kwargs):
    raise NotImplementedError("reorganize_files.create_dst_dirs was removed during cleanup.")


def reorganize_files(*args, **kwargs):
    raise NotImplementedError("reorganize_files.reorganize_files was removed during cleanup.")


def pdf_files(directory: Path) -> List[Path]:
    """Return all PDF files directly under ``directory`` (best-effort replacement)."""
    directory = Path(directory)
    if not directory.exists():
        return []
    return [f for f in directory.iterdir() if f.is_file() and f.suffix.lower() == ".pdf"]
