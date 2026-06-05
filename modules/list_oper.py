# --- Imports ---
# These modules seem to be custom-built for this project.
from modules.string_manipulation import alpha_only, digit_only
from modules.dict_opers import sorted_counter
from modules.match_case import operations

# Standard library and third-party imports
from itertools import chain  # Used for flattening lists efficiently.
from curses.ascii import ispunct, isspace  # Used for character type checking.
from datetime import datetime as dt2  # Used for timestamping debug messages.
from pathlib import Path  # Modern way to handle filesystem paths.
from icecream import ic  # A library for debugging, provides more context than print().


# --- Configuration ---

def ict():
    """Configures the 'icecream' debugger output.

    Sets the output to include the absolute path of the file and a timestamp prefix.
    This helps in tracing when and where a debug message was generated.
    """
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


# --- List Manipulation Functions ---

def list_appending(lst: list, arg):
    """Appends an element to a list.

    Args:
        lst (list): The list to which the element will be added.
        arg: The element to append.
    """
    lst.append(arg)


def reverse_lists(lst0: list, lst1: list) -> tuple:
    """Swaps the contents of two lists.

    Args:
        lst0 (list): The first list.
        lst1 (list): The second list.

    Returns:
        tuple: A tuple containing the two lists in swapped order (lst1, lst0).
    """
    lst0, lst1 = lst1, lst0
    return lst0, lst1


def str_to_list(item) -> list:
    """Ensures the returned value is a list.

    If the input `item` is not a list, it wraps it in a new list.
    If it's already a list, it returns it unchanged.

    Args:
        item: The variable to process.

    Returns:
        list: The original list or the item wrapped in a new list.
    """
    return [item] if not isinstance(item, list) else item


def list_to_str(item) -> str:
    """Extracts the first element from a list.

    If the input is a list, it returns its first element.
    If it's not a list, it returns the item as is.
    Note: This will raise an IndexError for an empty list.

    Args:
        item: The variable to process.

    Returns:
        str: The first element of the list or the original item.
    """
    if isinstance(item, list):
        for l in item:
            return l  # Returns on the first element.
    return item


def flatten(lst: [list, tuple, set]) -> list:
    """Flattens a list of lists into a single list.

    Example: [[1, 2], [3], [4, 5]] -> [1, 2, 3, 4, 5]

    Args:
        lst (list | tuple | set): A list that may contain other lists as elements.

    Returns:
        list: A new, one-dimensional list.
    """
    return list(chain(*[item if isinstance(item, list) else [item] for item in lst]))


# --- List Comparison Functions ---

def all_(l0: [list, tuple, set], l1: [list, tuple, set], from_left: bool = True, equal_len: bool = False) -> tuple[
    bool, int]:
    """Checks if all elements of one list are present in another.

    Args:
        l0 (list | tuple | set): The list of items to check for.
        l1 (list | tuple | set): The list to be checked against.
        from_left (bool, optional): If True, checks if all l0 items are in l1.
                                    If False, checks if all l1 items are in l0. Defaults to True.
        equal_len (bool, optional): If True, both lists must also have the same length. Defaults to False.

    Returns:
        tuple[bool, int]: A tuple where the first element is True if all items match
                          (and lengths are equal if required), and the second element
                          is the count of matching items.
    """
    if not from_left:
        l0, l1 = l1, l0  # Swap lists if checking from right to left.

    # Check for presence of each item from l0 in l1.
    presence_flags = [item in l1 for item in l0]
    true_count = sum(presence_flags)

    if equal_len and len(l0) != len(l1):
        return False, true_count

    # Return True only if all flags are True.
    return all(presence_flags), true_count


def all_1(l0: [list, tuple, set], l1: [list, tuple, set], from_left: bool = True, equal_len: bool = False) -> tuple[
    bool, int]:
    """Checks if two lists have identical elements at the same indices.

    This function performs an element-wise comparison at each index.

    Args:
        l0 (list | tuple | set): The first list.
        l1 (list | tuple | set): The second list.
        from_left (bool, optional): If False, the lists are swapped before comparison. Defaults to True.
        equal_len (bool, optional): If True, the check only passes if the lists have equal length. Defaults to False.

    Returns:
        tuple[bool, int]: A tuple containing a boolean for the overall match and the count of matching elements.
    """
    if not from_left:
        l0, l1 = l1, l0

    # Compare elements at the same index in both lists.
    presence_flags = [item0 == l1[i] for i, item0 in enumerate(l0) if i < len(l1)]
    true_count = sum(presence_flags)

    if equal_len and len(l0) != len(l1):
        return False, true_count

    # The final result depends on the length of `l0`, as `presence_flags` length is tied to `l0`.
    return len(presence_flags) == true_count and true_count > 0, true_count


def any_(l0: [list, tuple, set], l1: [list, tuple, set]) -> bool:
    """Checks if any element from the first list exists in the second list.

    Args:
        l0 (list | tuple | set): The list of items to search for.
        l1 (list | tuple | set): The list to be searched in.

    Returns:
        bool: True if at least one element from l0 is found in l1, otherwise False.
    """
    # A more concise way to write this is: return any(item in l1 for item in l0)
    for item in l0:
        if item in l1:
            return True
    return False


# --- Set-like Operations on Lists ---

def uniques(l0: [list, set, tuple], l1: [list, set, tuple]) -> list:
    """Finds elements that are unique to either list (symmetric difference).

    Args:
        l0 (list | set | tuple): The first collection.
        l1 (list | set | tuple): The second collection.

    Returns:
        list: A list of elements present in one list but not both.
    """
    return list(set(l0).symmetric_difference(set(l1)))


def difference(l0: [list, set, tuple], l1: [list, set, tuple], from_left: bool) -> list:
    """Finds elements present in one list but not the other.

    Args:
        l0 (list | set | tuple): The first collection.
        l1 (list | set | tuple): The second collection.
        from_left (bool): If True, returns items in l0 but not in l1.
                          If False, returns items in l1 but not in l0.
    Returns:
        list: A list containing the difference.
    """
    if not from_left:
        l0, l1 = l1, l0
    return list(set(l0).difference(l1))


def find_duplicates(lst: [list, tuple, set]) -> list:
    """Finds all duplicate elements in a list.

    Args:
        lst (list | tuple | set): The list to check for duplicates.

    Returns:
        list: A list of elements that appear more than once.
    """
    seen = set()
    duplicates = set()
    for item in lst:
        if item in seen:
            duplicates.add(item)
        else:
            seen.add(item)
    return list(duplicates)


# --- Complex/Specialized Functions ---

def find_split_symbol(lst: list) -> str | None:
    """Analyzes a list of filenames to find the most common delimiter.

    It scans all punctuation and whitespace characters in the filenames and
    returns the character that appears most frequently.

    Args:
        lst (list): A list of strings, typically file paths.

    Returns:
        str | None: The most common symbol, or None if no symbols are found.
    """
    symbols = []
    try:
        for file in lst:
            # Look at the filename part of the path only
            for char in Path(file).name:
                if ispunct(char) or isspace(char):
                    symbols.append(char)

        if not symbols:
            return None

        # Count frequencies and find the most common symbol.
        max_key = sorted_counter(symbols)
        return max(max_key, key=max_key.get)
    except (ValueError, TypeError):
        # Handle cases where the input list is invalid or empty.
        return None


def find_index_num(files_list: list, symbol: str) -> int | None:
    """Finds the index of the least common part of filenames when split by a symbol.

    This function is complex. It splits filenames by a given symbol, counts the
    frequency of all resulting parts, and then returns the list index of the part
    that occurred least frequently.

    Args:
        files_list (list): A list of file paths.
        symbol (str): The character to split filenames by.

    Returns:
        int | None: The index of the least common filename part, or None on error.
    """
    all_parts = []
    try:
        for file in files_list:
            # Split the filename (not the full path) by the symbol.
            parts = Path(file).name.split(symbol)
            all_parts.extend(parts)

        if not all_parts:
            return None

        # Count the frequency of each part.
        part_counts = sorted_counter(all_parts)
        # Find the part that appears the least number of times.
        least_common_part = min(part_counts, key=part_counts.get)

        # Return the first index where this part appears.
        return all_parts.index(least_common_part)
    except (ValueError, TypeError):
        # Handle empty lists or other errors.
        return None


# --- Incomplete or Potentially Buggy Functions ---
# NOTE: The functions in this section appear to be experimental, incomplete, or have bugs.
# They are documented based on their current implementation, with warnings.

def is_set(l0: [list, set, tuple], l1: [list, set, tuple]) -> list | bool:
    """
    [Experimental] Attempts to perform complex element-wise comparisons.

    WARNING: The function name `is_set` is misleading as it does not check
    if inputs are sets. Its logic is complex and appears to be for debugging or
    a very specific, unfinished use case. It compares list lengths and then
    compares elements at the same indices.

    Args:
        l0 (list | set | tuple): The first collection.
        l1 (list | set | tuple): The second collection.

    Returns:
        list | bool: A list of booleans indicating matching elements at each index.
    """
    l2 = [False] * min(len(l0), len(l1))
    operators_to_check = ['==', '>', '<']

    for operator in operators_to_check:
        for i, item0 in enumerate(l0):
            # Only compare if the index exists in both lists.
            if i < len(l1):
                item1 = l1[i]
                # Direct equality check.
                if item0 == item1:
                    l2[i] = True
                # If both are digits, perform numeric comparison.
                elif digit_only(item0) and digit_only(item1):
                    if operations(item0, item1, operator):
                        l2[i] = True
    return l2


def list_2d(lst: list, b: int = 1, c: int = 1) -> list:
    """
    WARNING: This function does not work as expected.
    It attempts to create a 2D list but contains logic errors, including
    re-initializing the list in a loop and creating a self-referential
    list with `lst.append(lst)`. It should not be used in production.
    """
    for ie in range(b):
        lst = list()  # This re-creates the list in every iteration.
        lst.append([])
        for x in range(c):
            lst.append([])
        lst.append(lst)  # This creates a recursive list that refers to itself.
    return lst


def create_3d_list(e, k, v):
    """
    WARNING: This function is incomplete.
    It constructs a list but does not return it or use it. It appears to be
    unfinished placeholder code.
    """
    lst0 = []
    for ie in e:
        lst = list()
        lst.append([ie])
        for x in range(1):
            lst.append(k)
            for y in range(1):
                lst.append(v)  # The created `lst` is not stored or returned.


def print_2d_list(lst: list) -> None:
    """Prints the contents of a 2D list with detailed indices using 'icecream'.

    Args:
        lst (list): A 2D list (list of lists).
    """
    # Outer loop for rows.
    for e, i in enumerate(lst):
        ic(ict(), '\n')  # Print a newline for spacing between rows.
        # Inner loop for columns in the current row.
        for r in range(len(i)):
            for iw, w in enumerate(i[r]):
                ic(ict(), f' {e}.{r}.{iw}) arr({i[r][iw]})[{r}][{iw}]')
