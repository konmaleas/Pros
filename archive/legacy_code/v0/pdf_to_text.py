from dataclasses import dataclass
from os import listdir
from os.path import join, isfile, isdir
from pathlib import PurePath, Path
import fitz
from datetime import datetime as dt2
from modules.dict_opers import dicts
from modules.file_opers import file_read, file_write
from modules.string_manipulation import singling_symbols, clear, replacer_2
from modules.paths import Paths
from icecream import ic


def ict():
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


@dataclass
class PdfToText(Paths):
    @staticmethod
    def pdf_extract_text(file: str | Path) -> str:
        # ic(ict(), file)
        with fitz.open(file) as doc:
            text = ''.join([page.get_text() for page in doc])
        return text

    @staticmethod
    def check_file_length(file: Path, length: len = 500) -> Path:
        if len(str(file)) > length:
            reduce_char = len(str(file)) - length
            file_ = Path(f'{join(PurePath(file).parent, PurePath(file).stem[reduce_char:])}{PurePath(file).suffix}')
            ic(ict(), file_)
            return file_
        return file

    # same as pdf_output_file
    def pdf_create_text_file(self) -> dict:
        # ic(ict())
        dct = {}
        cnt = 0
        for e, file in enumerate(listdir(self.first_path)):
            if isdir(join(self.first_path, file)):
                ic(ict(), join(self.first_path, file))
                continue
            dt2_now = dt2.now()

            # ToDo files have to be cleared
            text = self.pdf_extract_text(join(self.first_path, file))
            # ic(text, type(text))

            # text = self.clear_file_(text)
            # ic(text, type(text))

            # filename = self.check_file_length(
            #     Path(join(self.second_path,
            #               f'{PurePath(file).stem}_{clear(str(dt2_now).split(" ")[-1])}')))
            # pkl_filename = Path(join(self.second_path, f'{filename}.pkl'))

            # pkl_filename = self.check_file_length(
            #     Path(join(self.second_path,
            #               f'{PurePath(file).stem}_{clear(str(dt2_now).split(" ")[-1])}.pkl')))
            # file_write(pkl_filename, self.clear_file_(text), mode='w')
            # ic(pkl_filename)

            txt_filename = self.check_file_length(
                    Path(join(self.second_path,
                              f'{PurePath(file).stem}_{clear(str(dt2_now).split(" ")[-1])}.txt')))
            file_write(txt_filename, text, mode='w')
            # ic(ict(), txt_filename)

            dicts(dct, join(self.first_path, file), txt_filename)
            # dicts(dct, join(self.first_path, file), txt_filename)

        return dct

    # def clear_file(self, path: Path = None):
    #     if path is None:
    #         path = self.second_path
    #     for e, file in enumerate(listdir(path)):
    #         ic(ict(), path, file)
    #         if isfile(join(path, file)):
    #             for ef, line in enumerate(file_read(join(path, file))):
    #                 # line = letter_conversion(clear(singling_symbols(line), ['\t']).strip('\n'))
    #                 line = clear(singling_symbols(line), ['\t']).strip('\n')
    #
    #                 if line != '\n':
    #                     file_write(join(path, file), line, mode='a')
    #                     ic(ict(), path, file)
    #
    # @classmethod
    # def clear_file_(cls, text: str) -> list:
    #     lst = []
    #     for line in text.split('\n'):
    #         # Assuming replacer_2 cleans the line and returns a string
    #         # For demonstration, let's assume replacer_2 removes extra spaces
    #         # and keeps specified punctuation. You'll need to define this.
    #         # Example placeholder for replacer_2:
    #         # line = re.sub(r'\s+', ' ', line).strip() # Replace multiple spaces with one, remove leading/trailing
    #
    #         processed_line_str = singling_symbols(replacer_2(line, ' ', preserve=[',', '.']))
    #
    #         # Split the processed string by space
    #         words = processed_line_str.split(' ')
    #
    #         # Filter out empty strings from the 'words' list
    #         # A common way to remove empty strings is using a list comprehension with a truthiness check
    #         filtered_words = [word for word in words if word.strip()]
    #
    #         # Append to lst only if the filtered_words list is not empty
    #         if filtered_words:
    #             lst.append(filtered_words)
    #     return lst
    #
    # @classmethod
    # def _clear_file_(cls, text: str) -> list:
    #     lst = []
    #     # ic(ict(), text)
    #     for ef, line in enumerate(text.split('\n')):
    #         # line = letter_conversion(clear(singling_symbols(line), ['\t']).strip('\n'))
    #         # line = replacer_2(line, ' ', preserve=[',', '.']).split(' ')
    #         # line = clear(singling_symbols(line), preserve=[' ']).strip('\n')
    #
    #         # ToDo Check if replacer and preserve may be dynamic
    #         line = replacer_2(line, ' ', preserve=[',', '.']).split(' ')
    #         # for l in line:
    #         if line != '\n' and line != '':
    #             lst.append(line)
    #         # ic(ict(), text, line)
    #     return lst
