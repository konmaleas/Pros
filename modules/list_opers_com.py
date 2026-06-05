# --- Imports ---
# These modules seem to be custom-built for this project.
from modules.string_manipulation import alpha_only, digit_only
from modules.dict_opers import sorted_counter
from modules.match_case import operations

# Standard library and third-party imports
from itertools import chain  # Used for flattening lists efficiently.
from curses.ascii import ispunct, isspace  # Used for character type checking.
from pathlib import Path  # Modern way to handle filesystem paths.
from typing import Any
from datetime import datetime as dt2  # Used for timestamping debug messages.
from icecream import ic  # A library for debugging, provides more context than print().


# --- Configuration ---

def ict():
    """Configures the 'icecream' debugger output format.

    This function sets the 'icecream' configuration to include the absolute
    path of the file where `ic()` is called and adds a timestamp prefix
    in the format 'HH:MM:SS.ffffff'. This is useful for tracing the
    execution flow and timing of debug prints.
    """
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


# --- Basic List & Type Manipulation ---

def list_appending(lst: list, arg):
    """Appends a given argument to the end of a list, modifying it in-place.

    Args:
        lst (list): The list to be modified.
        arg: The element to append to the list.
    """
    lst.append(arg)


def reverse_lists(lst0: list, lst1: list) -> tuple:
    """Swaps the variable assignments for two lists.

    Args:
        lst0 (list): The first list.
        lst1 (list): The second list.

    Returns:
        tuple: A tuple where the order of the original lists is swapped.
               The first element is the original `lst1`, and the second is the original `lst0`.
    """
    lst0, lst1 = lst1, lst0
    return lst0, lst1


def str_to_list(lst) -> list:
    """Ensures that the input variable is a list.

    If the provided argument `lst` is not already a list, this function
    will wrap it inside a new list. Otherwise, it returns the original list.

    Args:
        lst: The variable to check.

    Returns:
        list: The original list, or the input `lst` wrapped in a new list.
    """
    return [lst] if not isinstance(lst, list) else lst


def list_to_str(lst) -> str:
    """Extracts the first element from a list.

    If the input is a list, it returns its first element. If the input is not
    a list, it returns the input as is.

    NOTE: The `for` loop is designed to run only once and exit, effectively
    accessing only the first element (at index 0). Will raise an `IndexError`
    if an empty list is passed.

    Args:
        lst: The list or other variable to process.

    Returns:
        str: The first element if `lst` is a list, otherwise `lst` itself.
    """
    if isinstance(lst, list):
        for l in lst:
            return l
    return lst


# --- List Comparison & Analysis ---
def all_(l0: list | tuple | set,
         l1: list | tuple | set,
         from_left: bool = True,
         equal_len: bool = False) -> bool | tuple[bool, int]:
    """Checks if every element of a primary list exists in a secondary list.

    Args:
        l0 (list | tuple | set): The first collection.
        l1 (list | tuple | set): The second collection.
        from_left (bool, optional): If True (default), checks if all elements of `l0` are in `l1`.
                                    If False, swaps them to check if all elements of `l1` are in `l0`.
        equal_len (bool, optional): If True, an additional condition is that the lists must be of
                                    equal length for the function to return True. Defaults to False.

    Returns:
        bool | tuple[bool, int]: A tuple containing a boolean result and the count of found items.
                                 The boolean is True only if all items were found (and lengths match if `equal_len` is True).
    """
    if not from_left:
        l0, l1 = l1, l0
    l2 = [False for _ in l0]
    for e, i0 in enumerate(l0):
        # ic(e, i0, l1)
        if i0 in l1:
            l2[e] = True
    true_len = len([_ for _ in l2 if _ is True])

    if equal_len:
        if len(l1) == len(l2):
            ic(ict(), len(l1), l1, len(l2), l2)
            if all(l2):
                return True, true_len
        else:
            # ic(ict(), len(l1), l1, len(l2), l2, all(l2))
            return False, true_len
    if all(l2):
        return True, true_len
    return False, true_len


def all_1(l0: list | tuple | set,
          l1: list | tuple | set,
          from_left: bool = True,
          equal_len: bool = False) -> bool | tuple[ bool, int]:
    """Checks for identical elements at identical indices in two lists.

    This function iterates through both lists simultaneously and checks if an element
    in the first list is the same as the element at the exact same index in the second list.

    Args:
        l0 (list | tuple | set): The first collection.
        l1 (list | tuple | set): The second collection.
        from_left (bool, optional): If False, the lists are swapped before comparison. Defaults to True.
        equal_len (bool, optional): If True, requires the lists to be of equal length. Defaults to False.

    Returns:
        bool | tuple[bool, int]: A tuple containing a boolean result and the count of matching elements.
    """
    if not from_left:
        l0, l1 = l1, l0
    l2 = [False for _ in l0]
    for e0, i0 in enumerate(l0):
        ic(e0, i0)
        if i0 == l1[e0]:
            l2[e0] = True
    true_len = len([_ for _ in l2 if _ is True])

    if equal_len:
        if len(l1) == len(l2):
            # ic(ict(), len(l1), l1, len(l2), l2)
            if all(l2):
                return True, true_len
        else:
            # ic(ict(), len(l1), l1, len(l2), l2, all(l2))
            return False, true_len
    if all(l2):
        return True, true_len
    return False, true_len


def all_2(l0: list | tuple | set, l1: list | tuple | set) -> bool | tuple[bool, list]:
    """Checks if all elements of `l1` are present in `l0`.

    NOTE: The logic `if len(l1) == len(l2):` is redundant because `l2` is
    initialized with the length of `l1`. The function effectively just checks
    if `set(l1)` is a subset of `set(l0)`.

    Args:
        l0 (list, tuple, set): The collection to search within.
        l1 (list, tuple, set): The collection whose elements are checked for presence in l0.

    Returns:
        bool: True if all elements of l1 are in l0, otherwise False.
    """
    # l2 = [False for f in l1]
    l2 = []
    for e, i1 in enumerate(l1):
        if i1 in l0:
            l2[e] = True

    # This condition will always be true since l2 is initialized based on l1's length.
    if len(l1) == len(l2):
        ic(ict(), len(l1), l1, len(l2), l2)
        if all(l2):
            return True
    else:
        # This branch is effectively unreachable.
        # ic(ict(), len(l1), l1, len(l2), l2, all(l2))
        return False


def any_(l0: list | tuple | set, l1: list | tuple | set) -> bool:
    """Checks if at least one element from `l0` is present in `l1`.

    Args:
        l0 (list, tuple, set): The collection of items to search for.
        l1 (list, tuple, set): The collection to be searched.

    Returns:
        bool: True if any element from `l0` is found in `l1`, otherwise False.
    """
    l2 = [False for _ in l0]
    for e, i0 in enumerate(l0):
        if i0 in l1:
            l2[e] = True
    if any(l2):
        return True
    return False


# --- Set-based List Operations ---

def uniques(l0: list | tuple | set, l1: list | tuple | set) -> list:
    """Finds elements that are in one list or the other, but not both.

    This is also known as the symmetric difference.

    Args:
        l0 (list | set | tuple): The first collection.
        l1 (list | set | tuple): The second collection.

    Returns:
        list: A list of unique elements found only in one of the collections.
    """
    return list(set(l0).symmetric_difference(set(l1)))


def difference(l0: list | tuple | set, l1: list | tuple | set, from_left: bool) -> list:
    """Returns elements that are in the first collection but not in the second.

    Args:
        l0 (list | set | tuple): The first collection.
        l1 (list | set | tuple): The second collection.
        from_left (bool): If True, returns elements from `l0` not in `l1`.
                          If False, returns elements from `l1` not in `l0`.

    Returns:
        list: A list containing the resulting different elements.
    """
    if not from_left:
        l0, l1 = l1, l0
    return list(set(l0).difference(l1))


def operators():
    """Returns a static list of comparison operator strings.

    Returns:
        list: A list containing '==', '>', '<'.
    """
    return ['==', '>', '<']


def is_set(l0: list | tuple | set, l1: list | tuple | set) -> list | tuple | bool:
    """
    Performs a complex, index-based comparison of two lists.

    WARNING: The function name `is_set` is misleading; it operates on lists,
    not sets, and performs element-wise comparisons rather than checking for set properties.
    Its behavior is highly specific and appears geared towards debugging or a specialized task.

    Args:
        l0 (list | set | tuple): The first collection.
        l1 (list | set | tuple): The second collection.

    Returns:
        list: A list of booleans, where each boolean corresponds to an index and
              indicates if a match was found for that index based on the internal logic.
    """
    seen = set()
    operator_flag = []

    for e, operator in enumerate(operators()):
        if operations(len(l0), len(l1), operator):
            ic(ict(), len(l0), len(l1), operations(len(l0), len(l1), operator))
            operator_flag.append(operator)
    l2 = [False for _ in range(min(len(l0), len(l1)))]
    for e, operator in enumerate(operators()):
        for e0, i0 in enumerate(l0):
            if e0 <= len(l1) - 1:
                if i0 == l1[e0]:  #  operations(i0, l1[e0], operator)
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


# --- Advanced & Specialized Functions ---

def flatten(lst: list | tuple | set) -> list:
    """Converts a list that may contain other lists as elements into a single, flat list.

    Args:
        lst (list | tuple | set): The collection to flatten.

    Returns:
        list: A new one-dimensional list.
    """
    # ic(ict(), lst)
    return list(chain(*[item if isinstance(item, list) else [item] for item in lst]))


def find_split_symbol(lst: list[Any]) -> str:
    """Finds the most frequently occurring delimiter (punctuation or space) in a list of filenames.

    Args:
        lst (list): A list of strings, expected to be file paths.

    Returns:
        str: The most common symbol character. Returns None if an error occurs or no symbols are found.
    """
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
        # This exception can occur if `symbols` is empty, meaning no punctuation/spaces were found.
        # ic(ict(), VE, lst)
        pass


def find_index_num(files_list: list, symbol: str) -> int:
    """Finds the list index of the least common part from filenames split by a symbol.

    This function first splits all filenames by the given `symbol`. It then counts
    the occurrences of all these resulting parts. Finally, it identifies the
    part that occurred least often and returns the index of its first appearance
    in the flattened list of all parts.

    Args:
        files_list (list): A list of file paths.
        symbol (str): The delimiter character to split filenames by.

    Returns:
        int: The index of the first occurrence of the least frequent filename part.
    """
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
    """Identifies and returns all elements that appear more than once in a list.

    Args:
        lst (list | tuple | set): The collection to check for duplicates.

    Returns:
        list: A list containing each duplicate element once.
    """
    seen = set()
    seen_add = seen.add
    # An element `x` is a duplicate if it's already in the `seen` set.
    # The expression `x in seen or seen_add(x)` ensures that `seen_add(x)`
    # is only called for new elements, adding them to the set.
    return list(set(x for x in lst if x in seen or seen_add(x)))


# --- Incomplete or Potentially Unintended Behavior ---

def list_2d(lst: list, b: int = 1, c: int = 1) -> list:
    """
    WARNING: This function does not create a standard 2D list. Due to its
    implementation (`lst = list()` inside the loop and `lst.append(lst)`),
    it returns a self-referencing list created during the *final* iteration
    of the outer loop. Its output is likely not what is intended.
    """
    for ie in range(b):
        lst = list()
        lst.append([])
        for x in range(c):
            lst.append([])
        # This line makes the list contain a reference to itself.
        lst.append(lst)
    return lst


def create_3d_list(e, k, v):
    """
    WARNING: This function is incomplete. It initializes and populates a
    local list variable `lst` within a loop but never uses it, stores it,
    or returns it. As written, this function has no observable effect.
    """
    lst0 = []
    for ie in e:
        lst = list()
        lst.append([ie])
        for x in range(1):
            lst.append(k)
            for y in range(1):
                lst.append(v)
                # The created `lst` is not appended to `lst0` or returned.  # row_lst.append(relative_paths)


def print_2d_list(lst: list) -> None:
    """Prints a nested list structure with detailed indices for each element.

    This function assumes `lst` is a list of lists, and that each of those
    sub-lists also contains iterable elements. It is designed for a specific
    (potentially 3D) data structure.

    Args:
        lst (list): A nested list.
    """
    for e, i in enumerate(lst):
        ic(ict(), '\n')
        # This loop iterates through the elements of the sub-list `i`.
        for r in range(len(i)):
            # This loop iterates through the elements of the sub-sub-list `i[r]`.
            for iw, w in enumerate(i[r]):
                ic(ict(), f' {e}.{r}.{iw}) arr({i[r][iw]})[{r}][{iw}]')
