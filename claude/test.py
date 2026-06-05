from os.path import expanduser as home
from os import walk
from modules.file_opers import file_read, file_write
from modules.string_manipulation import find_symbol, find_index_num
from modules.dict_opers import list_in_dict
from collections import Counter
from statistics import mean, median, median_low, median_high, median_grouped
from os import listdir
from pathlib import Path
from datetime import datetime as dt2
from icecream import ic


def ict():
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


