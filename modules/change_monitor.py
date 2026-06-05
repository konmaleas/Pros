import asyncio
from watchfiles import awatch
from os import walk
from os.path import join
import time
from datetime import datetime as dt2
from watchfiles import watch, Change
from watchfiles.filters import PythonFilter


class Monitor:
	def __init__(self):
		self.path = r'D:\Users\Konstantinos\Documents\PyTests\Submission_process\dst\PDF\unbinded'


def time_convert(sec):
	mins = sec // 60
	sec = sec % 60
	hours = mins // 60
	mins = mins % 60
	print(f"Time Lapsed = {int(hours)}:{int(mins)}:{round(sec, 1)}")


def init(path):
	for r, p, f in walk(path):
		print(r)
		for file in f:
			print(join(r, file))


def only_added(change: Change, path: str):
	return change == Change.added


def only_modified(modified: Change, path: str) -> bool:
	return modified == Change.modified


async def main(path):
	start_time = time.time()
	print(f'\nStarted at {dt2.now()}\n')
	# init(path)
	# , watch_filter=only_added
	async for changes in awatch(path):
		for change in changes:
			print(f'\nStarted at {dt2.now()}')
			print(f'0) {change}')
			# time_lapsed = time.time() - start_time
			# time_convert(time_lapsed)
			for ch in change:
				if ch == 1:
					print(f' 1) {ch}')


if __name__ == '__main__':
	m = Monitor()

	asyncio.run(main(m.path))













# elif ch.__contains__('D:\\Users\\konstantinos\\Documents\\PyTests\\Watcher\\dst\\'):
# 	print(f' 1) {ch}')
# asyncio.run(main(r'D:\Users\konstantinos\Documents\PyTests\Watcher\Test'))
# asyncio.run(main(r'\\192.168.0.28\Public\File_Exchange'))
# r'\\192.168.0.28\Files\PROJECTS'
# for changes in watch(p, watch_filter=only_added):
# 	print(changes)
# print(PythonFilter)
