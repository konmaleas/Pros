# Version 3.0
from modules.path_manipulation import path_sym
from modules.dict_opers import sorted_counter
from curses.ascii import ispunct, isspace
from os.path import exists
from pathlib import Path


def digits():
    return ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']


def eng_upper_letters():
    return ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',
            'M', 'N', 'O', 'P', 'Q', 'R', 'T', 'S', 'U', 'V', 'W', 'X', 'Y', 'Z']


def eng_lower_letters():
    return ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l',
            'm', 'n', 'o', 'p', 'q', 'r', 't', 'u', 'v', 'w', 'x', 'y', 'z']


def gr_upper_letters():
    return ['Α', 'Β', 'Γ', 'Δ', 'Ε', 'Ζ', 'Η', 'Θ', 'Ι', 'Κ', 'Λ', 'Μ',
            'Ν', 'Ξ', 'Ο', 'Π', 'Ρ', 'Σ', 'Τ', 'Υ', 'Φ', 'Χ', 'Ψ', 'Ω']


def gr_lower_letters():
    return ['α', 'β', 'γ', 'δ', 'ε', 'ζ', 'η', 'θ', 'ι', 'κ', 'λ', 'μ',
            'ν', 'ξ', 'ο', 'π', 'ρ', 'σ', 'ς', 'τ', 'υ', 'φ', 'χ', 'ψ', 'ω']


def exclude_():
    return [path_sym(), ' ', '~', '`', '!', '@', '#', '$', '%', '^', '&', '*',
            '(', ')', '_', '-', '[', ']', '{', '}', '\\', '|', ':', '–',
            ';', '<', '>', '"', "'", '+', '=', '.', ',', '/', '?', '\n', '\t']


def extensions():
    return ['.ods', '.odt', '.xls', '.doc', '.xlsx', '.docx', '.pdf', '.dwg', '.rvt']


def clear(string: str, exclude: str | list = None, preserve: str | list = None):
    exclude = exclude if exclude is not None else exclude_()
    lst = list()
    # print(f'0) exclude({exclude})\n preserve({preserve})')
    if string is not None:
        for char in string:
            # print(f' 1) char({char})')
            if char not in exclude:
                lst.append(char)
            if preserve is not None:
                if char in preserve:
                    lst.append(char)
        # print(''.join(relative_paths))
        return ''.join(lst)
    return False


def singling_symbols(string: str) -> str:
    lst = list()
    if string is not None:
        for c, char in enumerate(string):
            if char in exclude_():
                if char != string[c - 1]:
                    lst.append(char)
            # print(f'{c}) char({char})')
            else:
                lst.append(char)
        # print(f'{c}) char({char})')
        return ''.join(lst)


def replacer(string: str, replacer_: str | list, replaced: str | list = None) -> str:
    replaced = replaced if replaced is not None else exclude_()
    lst = []
    if string is not None:
        for char in string:
            if char not in replaced:
                lst.append(char)
            else:
                lst.append(replacer_)
        return ''.join(lst)


def replacer_2(string: str,
               replacer_: str | list,
               replaced: str | list = None,
               preserve: str | list = None) -> str:
    replaced = replaced if replaced is not None else exclude_()
    lst = []
    if string is not None:
        for char in string:
            try:
                if char not in replaced:
                    lst.append(char)
                else:
                    if char in preserve:
                        lst.append(char)
                    else:
                        lst.append(replacer_)
            except TypeError as TE:
                lst.append(replacer_)
        return ''.join(lst)


def ansep(string: str) -> str:
    lst = list()
    for e, st in enumerate(string):
        lst.append(st)
        if e >= 1:
            if string[e - 1].isalpha() and st.isdigit():
                lst.insert(-1, ' ')
            elif string[e - 1].isdigit() and st.isalpha():
                lst.insert(-1, ' ')
    return ''.join(lst)


def spl(string: str, sym, pos: int = -1) -> str:
    sl = list()
    if pos == -1:
        return string.split(sym)[-1]
    elif pos == -2:
        pos = len(string.split(sym)) - 2
    elif pos == 0:
        pos = len(string.split(sym)) - 2
    for e, i in enumerate(string.split(sym), 1):
        if e <= pos:
            sl.append(f'{i}{sym}')
    return ''.join(sl)


def versioning(string: str) -> str:
    if exists(string):
        num = string.split("-")[-1].split('.')[0]
        print(f'0) num({num})')
        if num.isdigit():
            num = int(num) + 1
            return f'{string.split("-")[0]}-{num}'
    return string


def is_alnum(string: str) -> bool:
    if clear(string, exclude_()).isalnum():
        return True
    return False


def is_alpha(string: str) -> bool:
    if clear(string, exclude_()).isalpha():
        return True
    return False


def is_digit(string: str) -> bool:
    if clear(string, exclude_() + eng_upper_letters()).isdigit():
        return True
    return False


def is_float(string: str) -> bool:
    try:
        if clear(string, exclude_() + eng_upper_letters(), '.').isdigit():
            float(string)
        return True
    except ValueError:
        return False


def is_float_only(string: str) -> bool:
    try:
        for char in string:
            if char in ['.', ',']:
                pass
            elif not char.isdigit():
                return False
        return True
    except ValueError:
        return False


def alpha_only(string: str) -> bool:
    # ic(string)
    if string:
        return all(list(s.isalpha() for s in string))
    return False


def digit_only(string: str) -> bool:
    # ic(string)
    if string:
        return all(list(s.isdigit() for s in string))
    return False


def float_only(string):
    if string:
        return all(list(is_float_only(s) for s in string))
    return False


def reconstruct_str(string: str | Path, sym: str, start: int, end: int = 0) -> str:
    if isinstance(string, Path):
        string = str(string)
    if end == 0:
        return f'{sym}'.join(string.split(sym)[start:])
    return f'{sym}'.join(string.split(sym)[start:end])


def find_symbol(lst: list[Path | str]) -> str | None:
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
        print(VE)


def find_index_num(files: list, symbol: str) -> int:
    dct, seen, i, element = {}, set(), [], []
    try:
        for e, file in enumerate(files):
            for efn, fn in enumerate(Path(file).name.split(symbol)):
                seen.add(fn)
                i.append(efn)
                element.append(fn)
        key_ = sorted_counter(element)
        return element.index(min(key_, key=key_.get))
    except ValueError as VE:
        print(VE)
