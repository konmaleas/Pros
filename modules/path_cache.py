# Version 1.3
from modules.path_manipulation import slash_conv
from os.path import exists
from os.path import join


def num_file():
	return 'cache/paths/last_accessed.txt'


def log_path():
	return 'cache/paths/paths.txt'


def file_read(file):
	with open(file, 'r', encoding='utf8') as fr:
		return fr.readlines()


def file_write(file, string, mode='a'):
	with open(file, mode, encoding='utf8') as fw:
		fw.write(f'{string}\n')


def cache(string):
	'''
	:param string: is the new entry
	:return: if the new entry exists
	'''
	for e, fr in enumerate(file_read(log_path())):
		if fr.strip() == string:
			print(f'\nThe path file\n   {fr.strip()} \nIs already cached.')
			return False
	return True


def cache_limit():
	'''
	:return: False if the cache if full
	'''
	if len(file_read(log_path())) <= 10:
		return True
	return False


def fifo(lst_file: list, new_entry):
	'''
	stores the new entry and number of the replaced oldest entry
	:param lst_file: where cache entries are stored
	:param new_entry: just the new entry
	:return: the file as list
	'''
	lst_file[int(''.join(file_read(num_file())))] = new_entry
	file_write(num_file(), int(''.join(file_read(num_file()))) + 1, 'w')
	return lst_file


def cache_manipulation(entry, mode='a'):
	'''
	handles the cache alongside with fifo
	:param entry:
	:param mode:
	:return:
	'''
	if not cache(entry):
		if not cache_limit():
			lst = fifo(file_read(log_path()), entry)
			for e, fr in enumerate(lst):
				print(file_write(log_path(), fr.strip(), 'w' if e == 0 else 'a'))
	else:
		file_write(log_path(), entry, mode)


def cache_selection():
	'''
	prints the entries with num to help the user to select
	:return: the selection
	'''
	print('\nSelect the number of your selected path')
	for e, fr in enumerate(file_read(log_path())):
		print(f'\n[{e}] [{fr.strip()}]')
	npt = input('--->  ')
	for e, fr in enumerate(file_read(log_path())):
		if int(npt) == e:
			return fr.strip()


def el():
	'''
	collects the path and file which will be stored in cache
	:return: the cache selection of the user and True
				or False if something goes wrong
	'''
	path = slash_conv(input('\nGive me your path --->  '))
	file = slash_conv(input('\nGive me your file --->  '))
	try:
		cache_manipulation(join(path, file))
		return cache_selection(), True
	except FileNotFoundError as ffe:
		print(f'\n{ffe}')
		return False, False


def cli():
	'''
	prompt the user to choose
	between an existed entry and a new one
	:return: the path of the selection
	'''
	while True:
		if file_read(log_path()) != '':
			print(f'\nDo you want to work to the last path file')
			if input('\nY for yes ---> ').upper() == 'Y':
				cs = cache_selection()
				if exists(cs):
					print(f'\n{cs}')
					return cs
				print('The path is no longer there.')
		p, t = el()
		if t:
			print(f'\n{p}')
			return p
