from modules.string_manipulation import alpha_only, digit_only
from modules.dict_opers import sorted_counter
from modules.match_case import operations
from itertools import chain
from curses.ascii import ispunct, isspace
from datetime import datetime as dt2
from pathlib import Path
from icecream import ic


def ict():
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


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
         equal_len: bool = False) -> bool | tuple[bool | int]:
    if not from_left:
        l0, l1 = l1, l0
    l2 = [False for _ in l0]
    # ic(ict(), l0, l1, l2)
    for e, i0 in enumerate(l0):
        if i0 in l1:
            # ic(e, i0, l1)
            l2[e] = True
    # true_len = len([_ for _ in l2 if _ is True])

    if equal_len:
        if len(l1) == len(l2):
            # ic(ict(), len(l1), l1, len(l2), l2)
            if all(l2):
                return True
        else:
            # ic(ict(), len(l1), l1, len(l2), l2, all(l2))
            return False
    if all(l2):
        # ic(ict(), l2, all(l2))
        return True
    # ic(ict(), l2)
    return False


def all_1(l0: list | tuple | set,
          l1: list | tuple | set,
          from_left: bool = True,
          equal_len: bool = False) -> bool | tuple[bool, int]:
    # ic(ict(), l0, l1)
    if not from_left:
        l0, l1 = l1, l0
    l2 = [False for _ in l0]
    # l2 = []
    # ic(ict(), l0, l1, l2, len(l2))
    for e0, i0 in enumerate(l0):
        # ic(ict(), e, i0)
        for e1, i1 in enumerate(l1):
            # ic(ict(), e1, i1)
            if e0 == e1 and i0 == i1:
                # ic(ict(), e0, e1, i0, i1)
                l2[e0] = True

    true_len = len([_ for _ in l2 if _ is True])

    if equal_len:
        # ic(ict(), true_len, len(l2), l2)
        if true_len == len(l2):
            if all(l2):
                # ic(l2)
                return True, true_len
        else:
            # ic(ict(), len(l1), l1, len(l2), l2, all(l2))
            return False, true_len

    # ic(ict(), l1, l2)
    if l2 and all(l2):
        return True, true_len
    return False, true_len


def all_2(l0: list | tuple | set, l1: list | tuple | set) -> bool | None | tuple[bool, list]:
    l2 = [False for f in l1]
    for e, i1 in enumerate(l1):
        if i1 in l0:
            l2[e] = True

    if len(l1) == len(l2):
        ic(ict(), len(l1), l1, len(l2), l2)
        if all(l2):
            return True
    else:
        # ic(ict(), len(l1), l1, len(l2), l2, all(l2))
        return False


def any_(l0: list | tuple | set, l1: list | tuple | set) -> bool:
    l2 = [False for _ in l0]
    for e, i0 in enumerate(l0):
        if i0 in l1:
            l2[e] = True
    if any(l2):
        return True
    return False


def any_1(l0: list | tuple | set, l1: list | tuple | set) -> bool:
    l2 = [False for _ in l0]
    for e, i0 in enumerate(l0):
        if i0 in l1:
            l2[e] = i0
            return i0


def uniques(l0: list | tuple | set, l1: list | tuple | set) -> list:
    return list(set(l0).symmetric_difference(set(l1)))


def equals(l0: list | tuple, l1: list | tuple) -> list:
    if len(l0) <= len(l1):
        l0, l1 = l1, l0
    return [l for l in l0 if l in l1]


def difference(l0: list | tuple | set, l1: list | tuple | set, from_left: bool) -> list:
    if not from_left:
        l0, l1 = l1, l0
    return list(set(l0).difference(l1))


def operators():
    return ['==', '>', '<']


def is_set(l0: list | tuple | set, l1: list | tuple | set) -> list | tuple | bool:
    seen = set()
    operator_flag = []

    for e, operator in enumerate(operators()):
        if operations(len(l0), len(l1), operator):
            ic(ict(), len(l0), len(l1), operations(len(l0), len(l1), operator))
            operator_flag.append(operator)
    l2 = [False for _ in range(min(len(l0), len(l1)))]
    for e, operator in enumerate(operators()):
        for e0, i0 in enumerate(l0):
            if e0 <= len(l1)-1:
                if i0 == l1[e0]: #  operations(i0, l1[e0], operator)
                    l2[e0] = True
                    ic(ict(), i0, l1[e0], l2, operator)
                elif digit_only(i0) and digit_only(l1[e0]):
                    if operations(i0, l1[e0], operator):
                        l2[e0] = True
                        ic(ict(), i0, l1[e0], l2, operator)
    ic(l2)
    # if all(l2):
    #     return True
    return l2


def flatten(lst: list | tuple | set) -> list:
    # ic(ict(), lst)
    return list(chain(*[item if isinstance(item, list) else [item] for item in lst]))


def find_split_symbol(lst: list) -> str | None:
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
    except ValueError as VE:
        # ic(ict(), VE, lst)
        pass


def find_index_num(files_list: list, symbol: str) -> int | None:
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


def list_2d(lst: list, b: int = 1, c: int = 1) -> list:
    for ie in range(b):
        lst = list()
        lst.append([])
        for x in range(c):
            lst.append([])
        lst.append(lst)
    return lst


def create_3d_list(e, k, v):
    lst0 = []
    for ie in e:
        lst = list()
        lst.append([ie])
        for x in range(1):
            lst.append(k)
            for y in range(1):
                lst.append(v)
        # row_lst.append(relative_paths)


def print_2d_list(lst: list) -> None:
    for e, i in enumerate(lst):
        ic(ict(), '\n')
        for r in range(len(i)):
            for iw, w in enumerate(i[r]):
                ic(ict(), f' {e}.{r}.{iw}) arr({i[r][iw]})[{r}][{iw}]')


def find_closest_numbers(data):
    """
    Find the number closest to an automatically determined target in each list.
    The target is calculated as the median of all numbers in all lists.

    Args:
        data (dict): Dictionary with keys and lists of numbers as values

    Returns:
        dict: Dictionary with same keys but only the closest number in each list
    """
    # Collect all numbers from all lists
    all_numbers = []
    for numbers in data.values():
        all_numbers.extend(numbers)

    if not all_numbers:
        return {}

    # Calculate target as median of all numbers
    all_numbers.sort()
    n = len(all_numbers)
    if n % 2 == 0:
        target = (all_numbers[n // 2 - 1] + all_numbers[n // 2]) / 2
    else:
        target = all_numbers[n // 2]

    print(f"Calculated target: {target}")

    # Find closest number to target in each list
    result = {}
    for key, numbers in data.items():
        if numbers:  # Check if list is not empty
            closest = min(numbers, key=lambda x: abs(x - target))
            result[key] = [closest]
        else:
            result[key] = []  # Handle empty lists

    return result


def find_closest_numbers_mean(data):
    """
    Alternative version using mean instead of median as target.
    """
    # Collect all numbers from all lists
    all_numbers = []
    for numbers in data.values():
        all_numbers.extend(numbers)

    if not all_numbers:
        return {}

    # Calculate target as mean of all numbers
    target = sum(all_numbers) / len(all_numbers)

    print(f"Calculated target (mean): {target}")

    # Find closest number to target in each list
    result = {}
    for key, numbers in data.items():
        if numbers:  # Check if list is not empty
            closest = min(numbers, key=lambda x: abs(x - target))
            result[key] = [closest]
        else:
            result[key] = []  # Handle empty lists

    return result
