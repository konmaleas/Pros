from os.path import expanduser as home
from os import walk
from modules.file_opers import file_read, file_write
from modules.string_manipulation import find_symbol, find_index_num
from modules.dict_opers import dict2list
from collections import Counter
from statistics import mean, median, median_low, median_high, median_grouped
from os import listdir
from pathlib import Path
from datetime import datetime as dt2
from icecream import ic


def ict():
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')
# output_dir = (Path.home() /
#               'PycharmProjects/Pros/claude/v19' /
#               Path(__file__).parent.stem /
#               dt2.now().strftime('%Y%m%d_%H%M%S'))


output_dir = (Path.home() /
              'PycharmProjects/Pros/claude' /
              Path(__file__).parent.name /
              'batch_debug' /
              dt2.now().strftime('%Y%m%d_%H%M%S'))
ic(output_dir)
