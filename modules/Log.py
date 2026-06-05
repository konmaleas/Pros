# Version 1.11
from modules.path_manipulation import dst_exists
from modules.string_manipulation import clear
from os.path import join
from datetime import datetime as dt2
from pathlib import PurePath
from sys import exit


extension: str = '.log'


def opj_(path: str, file: str, ts=True) -> str:
	return join(path, file_name_creator(file, ts))


def logger(string='', mode='a', path=None, file=None, ts=False):
	file = opj_(path, file, ts) if file is not None else file_name_creator(path)
	print(file)
	with open(file, mode, encoding='utf8') as log:
		try:
			log.write(f'{string}\n')
			return dst_exists(file)
		except FileNotFoundError as fnf:
			exit(fnf)
		except UnicodeEncodeError as uee:
			print(uee)


def timestamp(ts=False, mil_sec=False):
	if ts:
		if mil_sec:
			return ''.join(['_', clear(str(dt2.now()), ':')])
		return ''.join([clear(str(dt2.now()), ':').split(' ')[0]])
	return ''


def file_name_creator(path=None, file=None, ts=False, mil_sec=True) -> str:
	extension_ = extension
	file_ = file
	if file is not None:
		if len(file.split('.')) > 1:
			file_ = file.split('.')[0]
			extension_ = f'.{file.split(".")[-1]}'
		# print(PurePath(join(path, file)).suffix)
		# extension_ = PurePath(join(path, file)).suffix
		print(extension_, type(extension_))
	else:
		file_ = 'wc'
	timestamp_ = timestamp(ts, mil_sec)
	return ''.join([join(path, file_), timestamp_, extension_])
