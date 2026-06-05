from itertools import chain
from curses.ascii import ispunct, isspace
from pathlib import Path
from typing import Any
from datetime import datetime as dt2
from icecream import ic

from .text_ops import alpha_only, digit_only
from .dict_ops import sorted_counter


def ict():
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


def operations(x: int, y: int, operators: str) -> bool:
    match operators:
        case '>':
            return x > y
        case '>=':
            return x >= y
        case '<':
            return x < y
        case '<=':
            return x <= y
        case '==':
            return x == y


def list_appending(lst: list, arg):
    lst.append(arg)


def reverse_lists(lst0: list, lst1: list) -> tuple:
    lst0, lst1 = lst1, lst0
    return lst0, lst1


def str_to_list(lst) -> list:
    return [lst] if not isinstance(lst, list) else lst


def list_to_str(lst) -> str:
    if isinstance(lst, list):
        for l in lst:
            return l
    return lst


def all_(l0: list | tuple | set,
         l1: list | tuple | set,
         from_left: bool = True,
         equal_len: bool = False) -> bool | tuple[bool, int]:
    if not from_left:
        l0, l1 = l1, l0
    l2 = [False for _ in l0]
    for e, i0 in enumerate(l0):
        if i0 in l1:
            l2[e] = True
    true_len = len([_ for _ in l2 if _ is True])
    if equal_len:
        if len(l1) == len(l2):
            if all(l2):
                return True, true_len
        else:
            return False, true_len
    if all(l2):
        return True, true_len
    return False, true_len


def all_1(l0: list | tuple | set,
          l1: list | tuple | set,
          from_left: bool = True,
          equal_len: bool = False) -> bool | tuple[bool, int]:
    if not from_left:
        l0, l1 = l1, l0
    l2 = [False for _ in l0]
    for e0, i0 in enumerate(l0):
        if i0 == l1[e0]:
            l2[e0] = True
    true_len = len([_ for _ in l2 if _ is True])
    if equal_len:
        if len(l1) == len(l2):
            if all(l2):
                return True, true_len
        else:
            return False, true_len
    if all(l2):
        return True, true_len
    return False, true_len


def any_(l0: list | tuple | set, l1: list | tuple | set) -> bool:
    l2 = [False for _ in l0]
    for e, i0 in enumerate(l0):
        if i0 in l1:
            l2[e] = True
    if any(l2):
        return True
    return False


def uniques(l0: list | tuple | set, l1: list | tuple | set) -> list:
    return list(set(l0).symmetric_difference(set(l1)))


def difference(l0: list | tuple | set, l1: list | tuple | set, from_left: bool) -> list:
    if not from_left:
        l0, l1 = l1, l0
    return list(set(l0).difference(l1))


def is_set(l0: list | tuple | set, l1: list | tuple | set) -> list:
    operator_flag = []
    for e, operator in enumerate(['==', '>', '<']):
        if operations(len(l0), len(l1), operator):
            operator_flag.append(operator)
    l2 = [False for _ in range(min(len(l0), len(l1)))]
    for e, operator in enumerate(['==', '>', '<']):
        for e0, i0 in enumerate(l0):
            if e0 <= len(l1) - 1:
                if i0 == l1[e0]:
                    l2[e0] = True
                elif digit_only(i0) and digit_only(l1[e0]):
                    if operations(i0, l1[e0], operator):
                        l2[e0] = True
    return l2


def flatten(lst: list | tuple | set) -> list:
    return list(chain(*[item if isinstance(item, list) else [item] for item in lst]))


def find_split_symbol(lst: list[Any]) -> str:
    symbols = []
    try:
        for ef, file in enumerate(lst):
            for e, char in enumerate(Path(file).name):
                if ispunct(char):
                    symbols.append(char)
                elif isspace(char):
                    symbols.append(char)
        max_key = sorted_counter(symbols)
        return max(max_key, key=max_key.get)
    except ValueError:
        pass


def find_index_num(files_list: list, symbol: str) -> int:
    dct, seen, i, element = {}, set(), [], []
    try:
        for e, file in enumerate(files_list):
            for efn, fn in enumerate(Path(file).name.split(symbol)):
                seen.add(fn)
                i.append(efn)
                element.append(fn)
        key_ = sorted_counter(element)
        return element.index(min(key_, key=key_.get))
    except ValueError as VE:
        ic(ict(), VE)


def find_duplicates(lst: list | tuple | set) -> list:
    seen = set()
    seen_add = seen.add
    return list(set(x for x in lst if x in seen or seen_add(x)))
