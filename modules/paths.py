from dataclasses import dataclass
from pathlib import Path, PurePath


@dataclass
class Paths:
    first_path: Path
    second_path: Path
