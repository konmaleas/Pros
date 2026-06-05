from modules.file_opers import file_write, file_read, read_pickles, save_pickles
from modules.dict_opers import list_in_dict


def cache_(file, string):
	'''
	:param file: where entries are stored
	:param string: is the new entry
	:return: if the new entry exists	'''
	for e, fr in enumerate(file_read(file)):
		if fr.strip() == string:
			print(f'\nThe path file\n   {fr.strip()} \nIs already cached.')
			return False
	return True


def cache(dct, key, value):
	try:
		print(dct, sep='\n')
		if key in dct:
			for v in dct.values():
				print(f'v({v})')
				if value not in v:
					dct[key].append(value)
					return True
				else:
					print(f'\n   {value}\n    Is already cashed')
					return False
		else:
			dct[key] = [value]
			return True

	except KeyError as ke:
		print(ke)


def cache_limit(file):
	'''
	:param file: where entries have been stored
	:return: False if the cache if full
	'''
	if len(file_read(file)) <= 10:
		return True
	return False


def fifo(lst_file: list, file, new_entry):
	'''
	:param lst_file: where cache entries are stored
	:param file: where entries have been stored
	:param new_entry: just the new entry
	:return: the file as list
	'''
	lst_file[int(''.join(file_read(file)))] = new_entry
	file_write(file, int(''.join(file_read(file))) + 1, 'w')
	return lst_file


def cache_manipulation(file, entry, mode='a'):
	'''
	handles the cache alongside with fifo
	by checking
		if the entry is already in the file
		if the entry exceedes the cache limit

	:param file: where entries have been stored
	:param new_entry: just the new entry
	:param mode:
	'''
	if not cache(file, entry):
		if not cache_limit(file):
			lst = fifo(file_read(file), file, entry)
			for e, fr in enumerate(lst):
				print(file_write(file, str(fr).strip(), 'w' if e == 0 else 'a'))
	else:
		file_write(file, entry, mode)


def cache_manipulation_(dct, key, value):
	'''
	handles the cache alongside with fifo
	by checking
		if the entry is already in the file
		if the entry exceedes the cache limit

	:param file: where entries have been stored
	:param new_entry: just the new entry
	:param mode:
	'''
	#ToDo dct replaces different files
	# key must be chosen earlier as files was
	# value replaces entry
	# no need for write file mode as dct will be writen in a file at the end
	if not cache(dct, key, value):
		if not cache_limit(value):
			lst = fifo(dct, key, value)
			for e, fr in enumerate(lst):
				print(file_write(dct, str(fr).strip(), 'w' if e == 0 else 'a'))
	else:
		file_write(dct, key, value)


def cache_selection(dct):
	'''
	prints the entries with num to help the user to select
	:param file:
	:return: the selection
	'''
	print('\nSelect the number of your selected path')
	for e, fr in enumerate(dct):
		print(f'\n[{e}] [{fr.strip()}]')
	npt = input('--->  ')
	for e, fr in enumerate(file_read(file)):
		if int(npt) == e:
			return fr.strip()
