from os import walk, rmdir, remove
from os.path import isfile, join
from pathlib import Path

from modules.string_manipulation import find_symbol
from modules.file_opers import file_read, file_write, delete_empty_directories
from modules.dict_opers import list_in_dict, dicts_in_dict
from modules.time_oper import start_time, end_time
from modules.path_manipulation import dst_exists, path_sym

from collections import Counter
from string import punctuation
import re
from typing import List, Optional, Callable

from datetime import datetime as dt2
from icecream import ic


def ict():
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


def separate(path: Path, excluded: list[Path | str]) -> dict[str, list]:
    dct = {}
    delimiter = ''
    for e, (root, dirs, files) in enumerate(walk(path)):
        if len(files) < 3:
            list_in_dict(dct, 'excluded', Path(root))
        root = Path(root)
        if root not in excluded:
            list_in_dict(dct, 'included', Path(root))

    return dct


def remove_(files: list[Path]) -> None:
    for file in files:
        remove(file)


if __name__ == "__main__":
    start_time()

    p = Path('/media/konstantinos/8T/Projects/2206 BLP TEMES')
    new_dir = dst_exists(Path('files') / Path('separated') / Path(p.stem.split(' ')[0]) / '1')

    base = Path('~/PycharmProjects/Pros/claude').expanduser()
    mid_dir = Path('files/non_acceptable')

    separated = separate(p, file_read(base / mid_dir / Path('projects.txt')))

    if separated.get('included'):
        ic(file_write(new_dir / 'included.pkl', separated['included']))
        included = file_read(new_dir / 'included.pkl')

    if separated.get('excluded'):
        ic(file_write(new_dir / 'excluded.pkl', separated['excluded']))
        excluded = file_read(new_dir / 'excluded.pkl')
        ic(excluded, len(excluded))
        ic(delete_empty_directories(p))

    end_time(4)




















