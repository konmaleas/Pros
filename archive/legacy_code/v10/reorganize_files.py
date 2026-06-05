from modules.path_manipulation import dst_exists, path_sym
from modules.list_opers import str_to_list
from os.path import join, exists, isfile
from os import listdir
from datetime import datetime as dt2
from shutil import copy, move
from pathlib import Path, PurePath
from icecream import ic


def ict():
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


def pdf_files():
    return ['unbounded', 'bkp_src', 'clean_files', 'raw_files', 'PDF']


def dwg_files():
    return ['DWG', 'bkp_src', 'XREF', 'Rest']


def transmittal_files():
    return ['ZIP']


# workable
def create_dst_dirs(path: str | Path, dst_dirs_list: list) -> list:
    # ic(ict(), path, dst_dirs_list)
    lst = []
    for e, dir_ in enumerate(str_to_list(dst_dirs_list)):
        dst_exists(join(path, dir_))
        # ic(ict(), join(path, dir_))
        if exists(join(path, dir_)):
            # if isfile(join(path, dir_)):
            lst.append(join(path, dir_))
            # ic(ict(), join(path, dir_))
    # ic(ict(), relative_paths)
    return lst


# workable
def if_exists_dst_dir(paths_list: list | set | tuple, dst_dirs_list: list | set | tuple) -> bool:
    paths_dirs = [pd.split(path_sym())[-1] for pd in paths_list]
    if paths_dirs == dst_dirs_list:
        # ic(paths_dirs, dst_dirs_list)
        return True
    return False


# workable
def reorganize_files(path: str | Path, dst_path_list: list | set | tuple):
    seen = set()
    for e, new_dir in enumerate(dst_path_list):
        for ef, file in enumerate(listdir(path)):
            # ic(e, new_dir, ef, file)
            if not isfile(join(path, file)):
                continue

            if file not in dst_path_list:
                # ic(ict(), file)
                if new_dir not in seen:
                    # ic(join(path, new_dir))

                    # workable
                    if PurePath(new_dir).name.lower() == 'bkp_src':
                        # ic(path, file, new_dir)
                        copy(Path(join(path, file)), Path(join(path, new_dir, file)))

                    # workable
                    if PurePath(new_dir).name.lower() == PurePath(file).suffix.lower().lstrip('.'):
                        if PurePath(file).suffix.lower() == '.pdf':
                            # ic(path, file, new_dir)
                            move(Path(join(path, file)), Path(join(path, new_dir, file)))
                            seen.add(path)

                    # workable
                    if PurePath(new_dir).name.lower() == PurePath(file).suffix.lower().lstrip('.'):
                        if PurePath(file).suffix.lower() == '.dwg':
                            # ic(path, file, new_dir)
                            move(Path(join(path, file)), Path(join(path, new_dir, file)))
                            seen.add(path)

                    # workable
                    if PurePath(new_dir).name == 'Rest':
                        if PurePath(file).suffix.lower() != '.dwg':
                            # if PurePath(file).suffix.lower() != '.pdf':
                                # ic(path, file, new_dir)
                            move(Path(join(path, file)), Path(join(path, new_dir, file)))
                            seen.add(path)

                    if PurePath(new_dir).name.lower() == PurePath(file).suffix.lower().lstrip('.'):
                        if PurePath(file).suffix.lower() == '.zip':
                            # ic(path, file, new_dir)
                            move(Path(join(path, file)), Path(join(path, new_dir, file)))
                            seen.add(path)
