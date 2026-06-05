from modules.string_manipulation import clear, reconstruct_str, replacer_2
from modules.path_manipulation import path_sym, dst_exists
from modules.letter_conversion import letter_conversion
from modules.Log import logger
from title_name_scenarios.multi_line_table_title_2211 import au_2211
from title_name_scenarios.one_line_table_title_1910 import one_line_table_title as ncm_1910
from paths import Paths
from PyPDF2 import PdfFileReader
from PyPDF2 import PdfFileWriter
from os.path import join, isdir
from os import listdir
from subprocess import call
from platform import system
from datetime import datetime as dt2
from dataclasses import dataclass
from icecream import ic


def ict():
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


@dataclass
class PDFManipulation(Paths):
    file: str
    num: int = -1

    # workable
    def pdf_output_file(self):
        file = self.file.split(path_sym())[-1].split('.')[0]
        clear_file = letter_conversion(clear(file, [':']))
        return logger(string=clear_file, file=file, ts=True)

    # workable
    def find_pdf(self):
        pdf_output_file = self.pdf_output_file()
        ic(ict(), pdf_output_file)
        if str(self.file).endswith('pdf'):
            self.convert_pdf(pdf_output_file)
            try:
                test = au_2211(self.second_path, pdf_output_file)
                ic(ict(), test)

                new = replacer_2(test, '-', ' ')
                ic(ict(), new)

                return join(self.first_path, new)

            except TypeError as TE:
                print(TE)
                return join(self.first_path, self.file.split('.')[0])
            except AttributeError as AE:
                print(AE)
                return join(self.first_path, self.file.split('.')[0])

    # workable
    def convert_pdf(self, pdf_output_file):
        try:
            if system() == 'Windows':
                call(['pdftotext', self.file, pdf_output_file], shell=True, close_fds=True)
            elif system() == 'Linux':
                call(['pdftotext', self.file, pdf_output_file])
        except Exception as EX:
            print(EX)

    # workable
    def counting(self, num):
        self.num = self.num + 1
        return self.num if num < self.num else num

    # workable
    def unbind_iterator(self, files: list):
        num = list()
        for e, file in enumerate(listdir(self.first_path)):
            ic(e, file)
            #ToDo replace split with reconstruction_str
            if join(self.first_path, file).split(path_sym())[-2] not in files:
                if not isdir(join(self.first_path, file)):
                    ic(e, join(self.first_path, file))
                    with open(join(self.first_path, file), 'rb') as rb:
                        reader = PdfFileReader(rb, strict=False)
                        num.append(reader.getNumPages())
                        ic(e, num)
                        #ToDo make num to work with enumeration num[e]
                        for range_num in range(num[0]):
                            self.unbind(range_num)

    # workable
    def unbind(self, num):
        with open(self.file, 'rb') as read_binder:
            reader = PdfFileReader(read_binder, strict=False)
            writer = PdfFileWriter()
            writer.addPage(reader.getPage(num))
            num = self.counting(num)
            with open(f'{join(self.second_path, str(num))}.pdf', 'wb') as unique_pdf:
                print(
                    f'{num}) first_path({self.first_path})\n      second_path({join(self.second_path, str(num))}.pdf)')
                writer.write(unique_pdf)
