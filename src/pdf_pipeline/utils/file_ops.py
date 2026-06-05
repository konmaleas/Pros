# Version 1.3
from typing import Any, Generator

from .path_ops import path_sym
from .text_ops import reconstruct_str
from os.path import join, exists
from os import listdir
from platform import system
import pickle
from datetime import datetime as dt2
from pathlib import Path
from icecream import ic


def ict():
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


def debug(func):
    def wrapper(*args, **kwargs):
        # print the fucntion name and arguments
        print(f'Calling {func.__name__} with args: {args} kwargs: {kwargs}')
        # call the function
        result = func(*args, **kwargs)
        # print the results
        print(f'{func.__name__} returned: {result}')
        return result

    return wrapper


if system() == 'Windows':
    try:
        # pip install python-docx
        from docx import Document
    except Exception as e:
        print(f' ### docx ###\n   {e.__class__.__name__}')
        print(f'     Exception\n     {e}')


    def write_docx(file: str | Path, string: str):
        with open(f'{file}.docx', 'rb'):
            pass


    def read_docx(file: str | Path):
        doc = Document(file)
        text_ = []
        for line in doc.paragraphs:
            line.text.strip()
            text_.append(line.text)
            print(line.text)
        return text_


    def docx2txt(file: str | Path):
        file_write(file.replace('.docx', '.txt'), read_docx(file), 'w')
        return file.replace('.docx', '.txt')


def file_read(file: str | Path) -> None | list | list[Any]:
    if Path(file).suffix == '.pkl':
        return read_pickles(file)
    lst = []
    try:
        with open(file, 'r', encoding='utf8') as fr:
            for e, i in enumerate(fr.readlines()):
                lst.append(i.strip())
        return lst
    except Exception as e:
        print(f' ### file_read ###\n   {e.__class__.__name__}')
        print(f'     Exception\n     {e}')


def file_read_yield(file: str | Path) -> Generator[str, Any, None]:
    try:
        with open(file, 'r', encoding='utf8') as fr:
            for i in fr.readlines():
                yield i.strip()
    except Exception as E:
        print(f' ### file_read ###\n   {E.__class__.__name__}')
        print(f'     Exception\n     {E}')


def file_write(file: str | Path, string: str | int | float | bool | list | Any, mode='a'):
    if Path(file).suffix == '.pkl':
        return save_pickles(file, string)
    with open(file, mode, encoding='utf8') as fw:
        fw.write(f'{string}\n')


def save_pickles(file: str | Path, data, mode='wb'):
    with open(file, mode) as f:
        pickle.dump(data, f)
    if exists(file):
        # print(f'{file} has been saved.')
        return True
    return False


def read_pickles(file: str | Path) -> list:
    with open(file, 'rb') as rf:
        dct = rf.read()
    return pickle.loads(dct)


def read_pickles_yield(file: str | Path) -> str:
    with open(file, 'rb') as rf:
        dct = rf.read()
    for line in pickle.loads(dct):
        yield line


def differences_text(first: str, second:  str):
    return [i for i in first + second if i not in first or i not in second]


def compare_text(first: str, second: str):
    cnt = 0
    for i in first + second:
        if i not in first or i not in second:
            cnt += 1
    if cnt != 0:
        return False
    return True


def rename_file_before_saving(path_file: str | Path):
    '''Avoids overwriting same name file by
        replicating file with the next number at the end'''
    if exists(path_file):
        extension = path_file.split('.')[-1]
        ic(ict(), extension)

        path = reconstruct_str(path_file, path_sym(), 0, -1)
        ic(ict(), path)

        list_dir_len = len([ld for ld in listdir(path) if path_file in listdir(path)])
        ic(ict(), list_dir_len)

        file = reconstruct_str(path_file, path_sym(), -1, len(path_file.split(path_sym())))
        ic(ict(), file)

        file_name = reconstruct_str(file, '.', -1 * len(file.split(".")), len(file.split('.')) - 1)
        ic(ict(), file_name)

        new_file_name = f'{file_name}-{list_dir_len + 1}.{extension}'
        new_path_file = join(path, new_file_name)
        with open(new_path_file, 'w') as wf:
            wf.write('')

        return new_path_file
    else:
        return path_file


def txt2pkl(src_file: str | Path, dst_file: str | Path):
    save_pickles(dst_file, file_read(src_file))


def pkl2txt(src_file: str | Path, dst_file: str | Path):
    for esf, sf in enumerate(read_pickles(src_file)):
        file_write(dst_file, sf)


def byte_conversion(size: int, unit: str, round_=2):
    if unit.upper() == 'KB':
        return round(size / 1024, round_)
    elif unit.upper() == 'MB':
        return round(size / 1024 ** 2, round_)
    elif unit.upper() == 'GB':
        return round(size / 1024 ** 3, round_)
    elif unit.upper() == 'TB':
        return round(size / 1024 ** 4, round_)


def debug_file(file: str | Path, *args):
    file_write(file, ic.format(ict(), args, 'w'))
