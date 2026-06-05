from modules.string_manipulation import singling_symbols, reconstruct_str, replacer, replacer_2
from modules.path_manipulation import paths, dst_paths, path_files, path_sym, dst_exists
# from file_name_2211 import au_2011
from PyPDF2 import PdfFileReader as rpf
from PyPDF2 import PdfFileWriter as wpf
from os.path import expanduser as home
from datetime import datetime as dt2
from zipfile import ZipFile as zf
from os.path import join as opj
from os.path import join, exists
from os import listdir
from modules.string_manipulation import singling_symbols
import subprocess as sub
from icecream import ic
import platform
import shutil
import time
import sys
import os
import re

ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


def ict():
	ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


# Version 1.8
class Log:
	def __init__(self):
		self.sm = StringManipulation()
		self.pm = PathManipulation()
		self.path = self.pm.slash_conv(opj(home('~'), 'Documents/Logs/ath'))
		self.extension = '.log'
		self.file = self.file_name_creator()

	def path_exists(self, path=None):
		path = path if path is not None else self.path
		try:
			os.stat(path)
			return path
		except Exception:
			os.makedirs(path)
			print(f'Path({path}) has just created.')
			return path

	def opj_(self, file):
		return os.path.join(self.path, self.file_name_creator(file))

	def logger(self, file=None, string='', mode='a'):
		file = self.opj_(file) if file is not None else self.file
		try:
			with open(file, mode, encoding='utf8') as log:
				log.write(f'{string}\n')
			return self.path_exists(file)
		except FileNotFoundError:
			sys.exit(FileNotFoundError)

	def timestamp(self, mil_sec=False):
		if mil_sec:
			return ''.join(['_', self.sm.clear(str(dt2.now()), ':')])
		return ''.join(['_', self.sm.clear(str(dt2.now()), ':').split(".")[0]])

	def file_name_creator(self, file=None, mil_sec=False):
		return ''.join([opj(self.path, file if file is not None else 'wc'), self.timestamp(mil_sec), self.extension])


# Version 2.6
class PathManipulation:
	def __init__(self):
		pass

	@staticmethod
	def split_sym():
		return '/' if platform.system() == 'Linux' else '\\'

	@staticmethod
	def splitas(arg):
		return str(arg).split('.')[0]

	def slash_conv(self, path):
		if path is not None:
			path = f'{path}{self.split_sym()}'
			return path if platform.system() == 'Linux' else path.replace('/', '\\')
		return False

	def base_name(self, dr, path):
		return self.slash_conv(path.split(dr)[-1])


# Version 2.3
class StringManipulation:
	def __init__(self):
		pass

	@staticmethod
	def digits():
		return ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

	@staticmethod
	def eng_upper_letters():
		return ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',
		        'M', 'N', 'O', 'P', 'Q', 'R', 'T', 'S', 'U', 'V', 'W', 'X', 'Y', 'Z']

	@staticmethod
	def eng_lower_letters():
		return ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l',
		        'm', 'n', 'o', 'p', 'q', 'r', 't', 'u', 'v', 'w', 'x', 'y', 'z']

	@staticmethod
	def gr_upper_letters():
		return ['Α', 'Β', 'Γ', 'Δ', 'Ε', 'Ζ', 'Η', 'Θ', 'Ι', 'Κ', 'Λ', 'Μ',
		        'Ν', 'Ξ', 'Ο', 'Π', 'Ρ', 'Σ', 'Τ', 'Υ', 'Φ', 'Χ', 'Ψ', 'Ω']

	@staticmethod
	def gr_lower_letters():
		return ['α', 'β', 'γ', 'δ', 'ε', 'ζ', 'η', 'θ', 'ι', 'κ', 'λ', 'μ',
		        'ν', 'ξ', 'ο', 'π', 'ρ', 'σ', 'ς', 'τ', 'υ', 'φ', 'χ', 'ψ', 'ω']

	@staticmethod
	def exclude():
		return [' ', '_', '~', '!', '@', '#', '$', '%', '^', '&', '*',
		        '(', ')', '[', ']', '{', '}', '<', '>', ':', ';',
		        '"', "'", '-', '+', '=', '.', ',', '/']

	@staticmethod
	def extensions():
		return ['.ods', '.odt', '.xls', '.doc', '.xlsx', '.docx', '.pdf', '.dwg', '.rvt']

	def clear(self, string, exclude=None, preserve=None):
		exclude = exclude if exclude is not None else self.exclude
		lst = list()
		# print(f'0) exclude({exclude})\n preserve({preserve})')
		if string is not None:
			for char in string:
				# print(f' 1) char({char})')
				if char not in exclude:
					lst.append(char)
				if preserve is not None:
					if char in preserve:
						lst.append(char)
			# print(''.join(relative_paths))
			return ''.join(lst)
		return False

	@staticmethod
	def file_association_splitter(string):
		# Works ONLY Without '.' in the rest of the string
		return string.split('.')[0]

	def is_alnum(self, string):
		if self.clear(string, self.exclude()).isalnum():
			return True
		return False

	def is_digit(self, string):
		if self.clear(string, self.exclude() + self.eng_upper_letters()).isdigit():
			return True
		return False

	def is_float(self, string):
		try:
			if self.clear(string, self.exclude() + self.eng_upper_letters(), '.').isdigit():
				float(string)
			return True
		except ValueError:
			return False


# Version 1.1
class PDF:
	def __init__(self):
		self.log = Log()
		self.sll = self.log.logger
		self.pm = PathManipulation()
		self.sm = StringManipulation()
		self.src_path = self.paths()
		self.src_files = self.files()
		print(f'0) self.src({self.src_files})')

		self.nmp = int()
		self.num = -1
		self.rnm = False

		self.extension = self.extensions()
		print(f' 0.1) self.extension({self.extension}) type({type(self.extension)})')

		self.search = str()
		self.fn = str()

	def paths(self):
		while True:
			print('\nGive me path or...\n\nI will continue with mine.')
			try:
				return self.paths_exists(input('--->  '))
			except FileNotFoundError:
				return self.src_paths()

	def src_paths(self):
		return self.pm.slash_conv('/home/konstantinos/Documents/PyTests/Unbind/dst/a3 700')

	def dst_paths(self):
		return self.pm.slash_conv('//192.168.1.253/Shared/dst')

	def files(self, src=None):
		src = src if src is not None else self.src_path
		return [ld for ld in os.listdir(src) if os.path.isfile(opj(src, ld))]

	@staticmethod
	def extensions():
		lst = list()
		while True:
			print(f'\nGive me extensions to look for OR press Enter \n ')
			npt = input('---> ').lower()
			if npt != '':
				print(f'Extensions input({npt})')
				lst.append(npt)
			else:
				return lst

	@staticmethod
	def paths_exists(path):
		if os.path.exists(path):
			print(f'0.1) Path ({path})')
			return path
		print(f'Path ({path}) does not exists so the program had to stop.')
		sys.exit()

	@staticmethod
	def listing(lst):
		return [lst] if not isinstance(lst, list) else lst

	@staticmethod
	def unlist(lst):
		if isinstance(lst, list):
			for l in lst:
				return l
		return lst

	@staticmethod
	def check_folders(path):
		if os.path.exists(path):
			print(f'3.0) Directory -> {path} Already Exists')
			return True
		else:
			os.makedirs(path)
			print(f'3.1.1) Just created Directory -> {path}')
			return True

	@staticmethod
	def check_file(path, file):
		pf = os.path.join(path, file)
		if os.path.exists(pf):
			print(f'4.1) File on Path-> {pf} Already Exists')
			return True
		else:
			print(f'4.0) File on Path-> {pf} has to be moved')
			return False

	@staticmethod
	def compare_strings(str1, str2):
		pattern = re.compile(str1)
		sp = pattern.match(str2, -1)
		#sp1 = sp.group()
		return True if sp is not False else False

	def pdf_output_file(self, file):
		print(f'pdf_output_file file({file})')
		return self.sll(file=self.sm.clear(file.split(self.pm.split_sym())[-1].split(".")[0], [":"]))

	@staticmethod
	def convert_pdf(file, pdf_output_file):
		print(f'convert_pdf file({file})')
		try:
			if platform.system() == 'Windows':
				sub.call(['pdftotext', file, pdf_output_file], shell=True, close_fds=True)
			elif platform.system() == 'Linux':
				sub.call(['pdftotext', file, pdf_output_file])
		except Exception:
			print(Exception)

	def find_pdf(self, path, file):
		pdf_output_file = self.pdf_output_file(opj(path, file))
		print(f'0) file({opj(path, file)})')
		if str(file).endswith('pdf'):
			self.convert_pdf(opj(path, file), pdf_output_file)
			try:
				print(f' 0.1) path({path}) self.read_txt_file(pdf_output_file({self.read_txt_file(pdf_output_file)}))')
				# au_2011 func working only with au1.5
				# for ncm & ath3 need to use read_txt_file func
				return opj(path, self.read_txt_file(pdf_output_file).replace(" ", "-"))
			except TypeError:
				print(TypeError)
				return opj(path, file.split('.')[0])
			except AttributeError:
				print(AttributeError)
				return opj(path, file.split('.')[0])

	def read_txt_file(self, file):
		print(f'read_txt_file file({file})')
		try:
			with open(file, 'r', encoding='utf8') as fr:
				for line in fr.readlines():
					if line != '\n':
						line = singling_symbols(self.sm.clear(line.strip('\n'), ' '))
						search = singling_symbols(self.search)
						if line.__contains__(search):
							print(f' 1) line({line})')
							return line
						elif line.__contains__(search.lower()):
							print(f'  1.1) line({line})')
							return line
		except PermissionError:
			print(PermissionError)

	def complex_pdf_name(self, src_file, index_num, extension):
		# ToDo Totally unworkable
		sf_lst = list()
		for sf in src_file:
			if sf.endswith(extension):
				print(f'src_file.split({sf.split(".")[0].split("-")})')
				sf_lst = sf.split(".")[0].split("-")
				print(f' sf_lst len({len(sf_lst)})')
		for e, sfl in enumerate(sf_lst):
			if self.sm.clear(sfl, ' ').isdigit():
				print(f"  {e}) sfl sm.clear({self.sm.clear(sfl, ' ')})")
		if index_num is None:
			return opj(f"{self.src_path}{self.sm.clear(src_file.split('-')[9], ' ')}")
		return f"{self.src_path}NCM-DD-A-{index_num}-P0.{extension}"

	def opi_(self, file):
		if os.path.isfile(file):
			return file
		pass

	def counting(self, num):
		self.num = self.num + 1
		return self.num if num < self.num else num

	def unbind_iterator(self, pdf_src=None):
		pdf_src = pdf_src if pdf_src is not None else self.src_path
		print(f'pdf_src({pdf_src})')
		print(f'os.listdir({self.files(pdf_src)})')
		num = list()
		for e, ps in enumerate(self.files(pdf_src)):
			if not os.path.isdir(opj(pdf_src, ps)):
				self.reorganize_files(self.et_files()[0])
				print(f'e({e}) unbind_iterator {opj(pdf_src, ps)}')
				with open(opj(pdf_src, ps), 'rb') as rb:
					reader = rpf(rb, strict=False)
					num.append(reader.getNumPages())
					for rn in range(num[e]):
						self.unbind(rn, opj(self.src_path, ps),
						            self.log.path_exists(opj(self.src_path, 'unbinded')))

	def unbind(self, num, pdf_src, pdf_dst):
		with open(pdf_src, 'rb') as rb:
			reader = rpf(rb, strict=False)
			writer = wpf()
			writer.addPage(reader.getPage(num))
			num = self.counting(num)
			with open(f'{opj(pdf_dst, str(num))}.pdf', 'wb') as wb:
				print(f'{num})   pdf_src({pdf_src})\n     pdf_dst({opj(pdf_dst, str(num))}.pdf)')
				writer.write(wb)

	@staticmethod
	def et_files():
		return ['bkp-src', 'DWG', 'Rest', 'ZIP']

	def reorganize_files(self, dr=None):
		dr = dr if dr is not None else self.et_files()
		seen = set()
		for e, sef in enumerate(self.listing(dr)):
			self.log.path_exists(opj(self.src_path, sef))
			for en, ss in enumerate(self.files()):
				if ss not in seen:
					if sef == 'bkp-src':
						shutil.copy(opj(self.src_path, ss), opj(self.src_path, sef, ss))
						if self.rnm:
							self.renaming(self.src_path, ss)
					elif sef == ss.split('.')[-1].upper():
						shutil.move(opj(self.src_path, ss), opj(self.src_path, sef, ss))
						seen.add(ss)
					elif sef != 'DWG':
						shutil.move(opj(self.src_path, ss), opj(self.src_path, sef, ss))
						seen.add(ss)

	def e_transmit(self):
		self.create_zip(opj(self.src_path, 'ZIP'), opj(self.src_path, 'DWG'), opj(self.src_path, 'Rest'))

	def copy_(self, src_path_: str, dst_path: str):
		dst_exists(dst_path)

		if exists(join(src_path_, self.et_files()[3])):
			src_path_ = join(src_path_, self.et_files()[3])

		for ed, sp in enumerate(listdir(src_path_)):
			ict()
			ic(join(src_path_, sp), join(dst_path, sp))
			shutil.copy(join(src_path_, sp), join(dst_path, sp))

	def split(self, file):
		return file.split('.')[0].split('-')[self.nmp]

	def dst_fn(self, path, file, ext):
		'''
			Check which func sends the wrong path
			and if this var is necessary or
			it can be replaced by split / reconstruct file.split[0]
		'''
		ict()
		ic(path, file)
		file = file.split(path_sym())[-1]
		spc = ' '
		if file.endswith('dwg'):
			if self.fn == '':
				exit('No filename was given')
			elif self.nmp != 0:  # returns a given filename with the number contained in the original long filename
				return join(path,
				            f"{self.fn.format(self.split(singling_symbols(replacer(reconstruct_str(file, '.', 0), '-'))))}.{ext}")
			else:  # returns a given filename with the number contained in the original single number filename
				return join(path, f'{singling_symbols(self.fn.format(self.sm.clear(file.split(".")[0], " ")))}.{ext}')

		elif file.endswith('pdf'):
			if self.fn == '':
				#ToDo pdf has to be converted to text before calling au_2211 func
				ic(path, file)
				return join(path, f'{self.find_pdf(path, file)}.{ext}')
			elif self.nmp != 0:  # returns a given filename with the number contained in the original long filename
				return join(path,
					f"{self.fn.format(self.split(singling_symbols(replacer(reconstruct_str(file, '.', 0), '-'))))}"
					f".{ext}")
			else:
				# returns a given filename with the number contained in the original single number filename
				return join(path, f'{singling_symbols(self.fn.format(self.sm.clear(file.split(".")[0], " ")))}.{ext}')

	def renaming(self, path=None, file=None, extension=None):
		path = path if path is not None else self.src_path
		file = file if file is not None else self.files(path)
		extension = extension if extension is not None else self.extension
		for e, ss in enumerate(self.listing(file)):
			for ext in self.listing(extension):
				try:
					print(f'  2) src_file({ss})')
					if ss.endswith(ext):
						print(f'   3) path({path}) ss({ss}) ext({ext})')
						os.rename(opj(path, ss), self.dst_fn(path, ss, ext))
				except FileExistsError:
					print(FileExistsError)
				except FileNotFoundError:
					print(FileNotFoundError)
				except IndexError:
					print(IndexError)
				except PermissionError:
					print(PermissionError)
				except OSError as ose:
					print(ose)

	@staticmethod
	def create_zip(zipped, dwg, rest):
		for f in os.listdir(dwg):
			print(f"zipped({zipped}) f({f})")
			with zf(f'{opj(zipped, f.split(".")[0])}.zip', 'w') as zp:
				zp.write(opj(dwg, f), os.path.basename(f))
				for i in os.listdir(rest):
					print(f' 1) i({i})')
					zp.write(opj(rest, i), os.path.basename(i))
