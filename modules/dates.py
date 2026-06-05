from modules.letter_conversion import conversion
from modules.string_manipulation import replacer
# from modules.path_manipulation import slash_conv
from modules.file_opers import file_read
from time import time, ctime, strptime, strftime
from os.path import join, exists, getctime, getmtime
from datetime import date, timedelta, datetime as dt2
import datetime as dt
from dateutil import relativedelta
from pathlib import Path
import calendar
from dateutil import parser
from icecream import ic


def ict():
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


# Version 1.6
def date_match(arg: str) -> bool:
    try:
        if dt2.strptime(date_format(arg), "%Y/%M/%d"):
            return True
    except ValueError as ve:
        print(ve)
        return False


def date_match_2(arg: str) -> bool:
    try:
        if bool(parser.parse(arg)):
            return True
    except ValueError:
        return False


def date_conv(arg, file):
    #ToDo It has to recognise every entry and format it accordingly
    return date_format(construct_date(conversion(arg, file_read(file), False)))


def date_format(dates):
    return replacer(str(dates).split(' ')[0], '/')


def construct_date(month):
    current_year = int(dt2.strftime(dt2.now(), '%Y'))
    return date(current_year, month, calendar.monthrange(current_year, month)[1])


def compare_dates(first_date: str, second_date: str) -> int:
    #ToDo Check if func is in the date module
    try:
        if first_date and second_date is not None:
            if dt2.strptime(first_date, "%Y/%m/%d") < dt2.strptime(second_date, "%Y/%m/%d"):
                return -1
            elif dt2.strptime(first_date, "%Y/%m/%d") > dt2.strptime(second_date, "%Y/%m/%d"):
                return 1
            else:
                return 0
    except ValueError as ve:
        print(ve)


def compare_date_time(first_date, second_date):
    #ToDo Check if func is in the date module
    try:
        if first_date and second_date is not None:
            if dt2.strptime(first_date, "%Y/%m/%d %H:%M:%S") < dt2.strptime(second_date, "%Y/%m/%d %H:%M:%S"):
                return -1
            elif dt2.strptime(first_date, "%Y/%m/%d %H:%M:%S") > dt2.strptime(second_date, "%Y/%m/%d %H:%M:%S"):
                return 1
            else:
                return 0
    except ValueError as ve:
        print(ve)


def is_date_time(string: str, fuzzy: bool = False) -> bool:
    from dateutil.parser import parse
    '''
        Return whether the string can be interpreted as a date.
        :param string: str, string to check for date
        :param fuzzy: bool, ignore unknown tokens in string if True
    '''
    try:
        parse(string, fuzzy=fuzzy)

        return True
    except ValueError:
        return False


def txt2date(string: str) -> str:
    if len(string) > 8:
        date_ = string.split('_')[0]
        time_ = string.split('_')[-1]
        return (f"{'/'.join([date_[:4], date_[4:6], date_[6:8]])} "
                f"{':'.join([time_[:2], time_[2:4], time_[4:]])}")
    date_ = string
    return '/'.join([date_[:4], date_[4:6], date_[6:8]])


def creation_date(path: Path):
    return getctime(path)


def modification_date(path: str):
    return getmtime(path)


def time_stamp(time_stamp_):
    return dt2.fromtimestamp(time_stamp_)


def c_time(date_):
    return ctime(date_)


def parse_time(date_: str):
    return strptime(date_)


def format_time(date_: time) -> str:
    return strftime('%Y/%m/%d %H:%M:%S', date_)


def get_q(date_: dt2, first: bool = True, last: bool = False) -> [dt2, dt]:
    q_month = [1, 4, 7, 10]
    if first:
        for i, v in enumerate(q_month):
            if (date_.today().month - 1) // 3 == i:
                return dt(date_.today().year, q_month[i], 1).strftime("%d-%m-%y")
    if last:
        return dt2.strptime(get_q(date_, first=True), "%d-%m-%y") + relativedelta(months=3, days=-1)


def end_of_month(date: dt2) -> dt2:
    if date.month == 12:
        return date.replace(day=31)
    return date.replace(month=date.month + 1, day=1) - timedelta(days=1)


def extend_days(date_: dt2, days: int = 29) -> dt2:
    return date_ + timedelta(days)


def extend_months(date_: dt, month: int) -> dt:
    return date_ + relativedelta(months=month, day=-1)
