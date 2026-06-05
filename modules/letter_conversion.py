# Version 1.9
import langdetect as lang
from langdetect.lang_detect_exception import LangDetectException

from time import time as t2

start = t2()

sll = print
language = 'en'
accepted_ratio = False
ratio = 5


def eng_upper_letters():
	return ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',
			'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']


def gr_upper_letters():
	return ['Α', 'Β', 'Γ', 'Δ', 'Ε', 'Ζ', 'Η', 'Θ', 'Ι', 'Κ', 'Λ', 'Μ',
			'Ν', 'Ξ', 'Ο', 'Π', 'Ρ', 'Σ', 'Τ', 'Υ', 'Φ', 'Χ', 'Ψ', 'Ω']


def en2gr_full():
	return {'A':'Α', 'B':'Β', 'C':'Σ', 'D':'Δ', 'E':'Ε', 'F':'Φ',
			'G':'Γ', 'H':'Η', 'I':'Ι', 'J':'Θ', 'K':'Κ', 'L':'Λ',
			'M':'Μ', 'N':'Ν', 'O':'Ο', 'P':'Π', 'Q':'Κ', 'R':'Ρ',
			'S':'Σ', 'T':'Τ', 'U':'Υ', 'V':'Β', 'W':'Ω', 'X':'Χ',
			'Y':'Υ', 'Z':'Ζ'}


def gr2en_upper():
	return {'Α':'A', 'Β':'B', 'Ε':'E', 'Η':'H', 'Ι':'I', 'Κ':'K', 'Μ':'M',
			'Ν':'N', 'Ο':'O', 'Ρ':'P', 'Τ':'T', 'Χ':'X', 'Υ':'Y', 'Ζ':'Z'}


def en2gr_upper():
	return {'A':'Α', 'B':'Β', 'E':'Ε', 'H':'Η', 'I':'Ι', 'K':'Κ', 'M':'Μ',
			'N':'Ν', 'O':'Ο', 'P':'Ρ', 'T':'Τ', 'X':'Χ', 'Y':'Υ', 'Z':'Ζ'}


def en2gr_lower():
	return {'a':'α', 'b':'β', 'e':'ε', 'h':'η', 'i':'ι', 'k':'κ', 'm':'μ',
			'n':'ν', 'o':'ο', 'p':'ρ', 't':'τ', 'x':'χ', 'y':'υ', 'z':'ζ'}


def gr2en_lower():
	return {'α':'a', 'β':'b', 'ε':'e', 'η':'h', 'ι':'i', 'κ':'k', 'μ':'m',
			'ν':'n', 'ο':'o', 'ρ':'r', 'τ':'t', 'χ':'x', 'υ':'y', 'ζ':'z'}


def eng_lower_letters():
	return ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l',
			'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']


def gr_lower_letters():
	return ['α', 'β', 'γ', 'δ', 'ε', 'ζ', 'η', 'θ', 'ι', 'κ', 'λ', 'μ',
			'ν', 'ξ', 'ο', 'π', 'ρ', 'σ', 'ς', 'τ', 'υ', 'φ', 'χ', 'ψ', 'ω']


def gr_tones():
	return {'ά':'α', 'έ':'ε', 'ή':'η', 'ί':'ι', 'ό':'ο', 'ύ':'υ', 'ϋ':'υ', 'ώ':'ω'}


def unique_gr_char():
	return ['Δ', 'Λ', 'Ξ', 'Π', 'Σ', 'Φ', 'Ψ', 'Ω']


def unique_en_char():
	return ['C', 'D', 'F', 'G', 'J', 'L', 'Q', 'R', 'S', 'W']


def date2month():
	return {'Ιαν' :'01', 'Φεβ':'02', 'Μαρ':'03', 'Απρ':'04', 'Μαϊ':'05', 'Μαι':'05',
			'Ιουν':'06', 'Ιουλ':'07', 'Αυγ':'08', 'Σεπ':'09', 'Οκτ':'10', 'Νοε':'11', 'Δεκ':'12'}


def exclude():
	return [' ', '~', '`', '!', '@', '#', '$', '%', '^', '&', '*',
			'(', ')', '_', '-', '[', ']', '{', '}', '\\', '|', ':',
			';', '<', '>', '"', "'", '+', '=', '.', ',', '/', '?', '\n', '\t']


def transform(string, dct, key=True):
	# print(f'####### {"transform".upper()} ##########')
	# print(f'  arg({string}) type({type(string)})')
	return ''.join([conversion(i, dct, key) for i in string])


def conversion(dicts, char, key_=True):
	'''
		Returns key values or value keys from dictionaries
		Here it's used to convert EN to EL chars and vice versa
		key = True = en | key = False = el
		:param char: It's the chars to be converted
		:param dicts: You can give the dict of you choice
		:param key_: if key_ = True chooses the key else the value of the dict
		:return: The converted character if an opposite language character exists
											else the original characters
	'''
	# print(f'### {"conversion".upper()} ###')
	# print(f' key({key_})')
	for key, value in dicts.items():
		arg = key if key_ is True else value
		# print(f'0) key({key_}) arg({arg}) char({char.upper()})')
		if char.upper() == arg.upper():
			arg = value if key_ is True else key
			# print(f' 1) key({key_}) char({char}) arg({arg})')
			value = arg
			return value
	return char


def alter_dict():
	'''
		It initialize the default dict for word & language conversion
	'''
	if language == 'en':
		return gr2en_upper()
	return en2gr_upper()


def language_sorter(string):
	'''
		It initialize the default language for word & language conversion
	'''

	i = 0
	if preservation(string, unique_gr_char()):
		language = 'el'
		i += 1
	elif preservation(string, unique_en_char()):
		language = 'en'
		i += 1


def preservation(string, preserve_list):
	if string is not None:
		for i, char in enumerate(string):
			if char.upper() in preserve_list:
				return True
		return False


def word_conversion(string, dct=None, key=True):
	'''
		It converts words with mix languages into the preferred
		It also can choose by language ratio from characters
		ie: It chooses the lang which has > 50% of char in the word
		:param string: It's chars to be converted
		:param dct: You can give the dict of you choice or it'll get the default
		:param key: if key = True chooses the key else the value of the dict
		:return: The converted word
	'''

	dct = dct if dct is not None else alter_dict()
	lst = list()
	z, slg, rst = 0, 0, 0
	language = 'el'
	# ToDo Change Dicts when unique char are present
	if string is not None:
		language_sorter(string)

		for i, char in enumerate(str(string)):
			if not char.isdigit():
				if char not in exclude():
					z += 1
					if len(string) > 1:
						if i == 0:
							sll(f' i.{i}) string({string}) language({language})')
					while True:
						try:
							if lang.detect(char.lower()) == language:
								slg += 1
								sll(f'    3.1.{i}) {language} char({char}) z({z}) slg({slg}) rst({rst})')
								lst.append(conversion(dct, char, key))
								break
							else:
								rst += 1
								sll(f'     3.2.{i}) {language} char({char}) z({z}) slg({slg}) rst({rst})')
								lst.append(conversion(dct, char, key))
								break
						except Exception:
							sll(Exception)
							if lang.detect(char.lower()) == language:
								slg += 1
								sll(f'      3.3.{i}) {language} char({char}) z({z}) slg({slg}) rst({rst})')
								lst.append(conversion(dct, char, key))
								break
							else:
								rst += 1
								sll(f'       3.4.{i}) {language} char({char}) z({z}) slg({slg}) rst({rst})')
								lst.append(conversion(dct, char, key))
								break
				else:
					# print(f'     3.4.2) v({char})')
					lst.append(conversion(dct, char, key))
			else:
				# print(f'      3.4.3) char({char})')
				lst.append(conversion(dct, char, key))
		if z > 0:
			sll(f'        3.5) string({"".join(lst)}) z({z}) slg({slg}) rst({rst}) '
				f'current ratio rst({round((rst / z) * 100, 1)}) '
				f'slg({round((slg / z) * 100, 1)})')
			if accepted_ratio:
				sll(f'         3.6) accepted_ratio({accepted_ratio})')
				sll(f'         3.7) return({"".join(lst)})')
				return ''.join(lst)
			else:
				# print(f'         3.8) return({"".join(relative_paths)})')
				return ''.join(lst)
	return string


def letter_conversion(string, dct=None, key=True):
	'''
		# ToDo 	Convert letters
		It converts words with mix languages into the preferred
		It also can choose by language ratio from characters
		ie: It chooses the lang which has > 50% of char in the word
		:param string: It's chars to be converted
		:param dct: You can give the dict of you choice or it'll get the default
		:param key: if key = True chooses the key else the value of the dict
		:return: The converted word
	'''
	dct = dct if dct is not None else alter_dict()
	lst = list()
	z, slg, rst = 0, 0, 0
	language = 'el'
	# print(f'### {"letter_conversion".upper()} ###')
	if string is not None:
		# language_sorter(string)
		for i, char in enumerate(str(string)):
			if not char.isdigit():
				if char not in exclude():
					z += 1
					while True:
						try:
							if lang.detect(char) == language:
								slg += 1
								lst.append(conversion(dct, char, key))
								break
							else:
								rst += 1
								lst.append(conversion(dct, char, key))
								break
						except LangDetectException:
							slg += 1
							lst.append(conversion(dct, char, key))
							# sll(f'      3.3.{i}) {language} char({char}) z({z}) slg({slg}) rst({rst})')
							break
				else:
					lst.append(conversion(dct, char, key))
			else:
				lst.append(conversion(dct, char, key))
		if z > 0:
			if accepted_ratio:
				return ''.join(lst)
			else:
				return ''.join(lst)
	return string
