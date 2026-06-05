from modules.file_opers import file_write, file_read_yield
from datetime import datetime as dt2
from time import time
from icecream import ic


def ict():
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


def time_convert(sec: float = 0.0, round_: int = 1):
    mins = sec // 60
    sec = sec % 60
    hours = mins // 60
    mins = mins % 60
    ic(f"Time Lapsed = {int(hours)}:{int(mins)}:{round(sec, round_)}")
    return f'{int(hours)}:{int(mins)}:{round(sec, round_)}'


def start_time():
    ic(f'Start Time({dt2.now().strftime("%H:%M:%S")})')
    file_write('start_time.txt', time(), 'w')


def end_time(round_: int = 1):
    ic(f'End Time({dt2.now().strftime("%H:%M:%S")})')
    time_convert(time() - float(''.join(file_read_yield('start_time.txt'))), round_=3)
