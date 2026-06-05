from modules.dict_opers import (dict_creator, dicts_3, list_in_dict_2, invert_dict,
                                sorted_dict_2, dicts_in_dict, dict2list)
from modules.file_opers import debug, file_read, file_write, save_pickles, read_pickles, file_read_yield, debug_file
from modules.match_case import operations
from modules.list_opers import any_, all_, all_1, difference, flatten, uniques
from modules.string_manipulation import clear, reconstruct_str, replacer_2, is_float, singling_symbols
from modules.path_manipulation import dst_exists, path_sym
from modules.time_oper import start_time, end_time
from pdf_to_text import PdfToText
from collections import OrderedDict, Counter
from os import listdir, walk, remove
from os.path import getsize, exists, join, isfile, relpath, expanduser as home
from curses.ascii import ispunct, isspace
from pathlib import Path, PurePath
from copy import deepcopy
from shutil import copy2, rmtree
from functools import cache
from typing import Dict, Any
from dataclasses import dataclass, field
from openpyxl import Workbook, load_workbook
from datetime import datetime as dt2
from itertools import islice
from platform import system
from icecream import ic


def ict():
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


def collect_files(src_path: str | Path) -> list:
    files_list = []
    for e, file in enumerate(listdir(src_path)):
        if isfile(Path(join(src_path, file))):
            files_list.append(Path(file))
    return files_list


def copy(lst: list, src_path: Path, dst_path: Path):
    for e, file in enumerate(lst):
        copy2(Path(join(src_path, file)), Path(join(dst_path, file)))


def delete(lst: list, src_path: Path, dst_path: Path):
    # ic(ict(), [join(dst_path, _) for _ in lst])
    l0, l1 = [], []
    undeletables = [Path(join(dst_path, _)) for _ in lst]
    ic(ict(), undeletables)
    for e, (root, dirs, files) in enumerate(walk(dst_path)):
        # for file in files:
        #     l0.append(Path(join(root, file)))
        #     if Path(join(root, file)) not in undeletables:
        #         ic(ict(), Path(join(root, file)))
        #         remove(Path(join(root, file)))
        for dir_ in dirs:
            ic(ict(), Path(join(root, dir_)), Path(root))
            rmtree(Path(join(root, dir_)))


if __name__ == '__main__':
    home_0 = '/media/konstantinos/bkp/files/dst_small_group/PROJECTS'
    home_1 = join(home('~'), 'Documents/PyTests/Submission/Seek Title Template/dst/au1.5')
    home_2 = join(home('~'), 'PyTests')

    if system() == 'Windows':
        home_0 = 'D:/files/dst_small_group/PROJECTS'
        home_1 = 'D:/au1.5/20240628'
        home_2 = 'C:/PyTests'

    paths = [join(home_2, 'Submission/Process/2211 au/dst/02xxx/PDF/bkp_src'),
             join(home_2, 'Submission/Process/2211 au/dst/07xxx/PDF/bkp_src')]

    src_path_ = Path(paths[1])
    dst_path_ = Path(src_path_).parent
    ic(ict(), src_path_, dst_path_)
    if Path(src_path_).stem != 'bkp_src':
        exit('The given path is in correct.')
    if exists(src_path_):

        files_list_ = collect_files(src_path_)
        ic(ict(), files_list_)

        copy(files_list_, src_path_, dst_path_)

        delete(files_list_, src_path_, dst_path_)
    else:
        ic(ict(), src_path_, 'Does not exist!')
