from os import listdir

from files.nikos.modules.file_opers import file_read
from modules.path_manipulation import dst_exists
from modules.dict_opers import dict2list, sorted_dict_2, list_in_dict
from modules.file_opers import file_write, read_pickles
from modules.time_oper import start_time, end_time
from reorganize_files import create_dst_dirs, reorganize_files, pdf_files
# from title_search_oop_commentary import TitleSearch
from title_search import TitleSearch
# from integrity import TitleAnalysis, NoiseCancellation, exclusions
# from enhancedNoiseCancellation import NoiseCancellation, apply_filters, exclusions
from heavy_text_processor_v2 import (process_pdf_with_adaptive_filtering,
                                     FrequencyBasedFilter as NoiseCancellation)
from pdf_to_text import PdfToText
from pathlib import Path, PurePath
from os.path import join, exists, expanduser as home
# from curses.ascii import ispunct, isspace
import operator
from platform import system
from datetime import datetime as dt2
from icecream import ic


def ict():
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


def debug_file(file: Path, *args):
    # ic(ict(), start_time())
    # if self.active:
    file_write(file, ic.format(ict(), args, 'w'))
    # ic(ict(), end_time())


def main_files_data(path: str | Path):
    ic(ict(), start_time())

    ic(ict(), path)

    # This class is responsible for the conversion
    pdf2txt = PdfToText(Path(''), Path(''))

    dst_path_list = create_dst_dirs(Path(path), pdf_files())  # Directories are created using this function.
    # Depending on their suffix, files from the main directory were placed into the folders.
    reorganize_files(path, dst_path_list)
    # These are the new paths
    pdf2txt.first_path = Path(join(path, 'PDF'))
    pdf2txt.second_path = Path(join(path, 'raw_files'))

    # ToDo Check if its returned values are useful
    # This function converts pdf into text
    pdf2txt.pdf_create_text_file()

    # This class is responsible for the conversion
    title_search = TitleSearch(path=pdf2txt.second_path, extension='.pkl', operation='>=')

    title_search.title = '4005-RES-VAP-DWG-233-IC-07020-0'
    # title_search.title = '4005-RES-VAP-DWG-234-DD-02000-C'
    # title_search.title = '4005-RES-VAP-DWG-233-CD-07201-B'
    # title_search.title = '4005-RES-VAP-DWG-233-CD-12100-A'
    # title_search.title = 'NCM-DD-B2-DR-ARC-4401-P1'

    # 0)
    noise_cancellation = NoiseCancellation([])
    new_filepath = Path
    title_frequency_data = {}
    for e, file in enumerate(listdir(pdf2txt.second_path)):
        if file.__contains__(title_search.title[6]):
            list_in_dict(title_frequency_data, )
            title_search.chunks_distances()

        filepath = Path(pdf2txt.second_path / file)
        text = '\n'.join(file_read(filepath))
        # text = file_read(filepath)
        new_filepath = filepath.parent.parent / 'clean_files' / filepath.with_suffix('.pkl').name

        title_chunks = title_search.title.split('-')
        title_alpha_chunks = [a for a in title_search.title.split('-') if a.isalpha()]
        title_digit_chunks = [d for d in title_search.title.split('-') if d.isdigit()]

        filtered = process_pdf_with_adaptive_filtering(text, title_search.title, )
        # file_write(filtered)
    # line_chunks = apply_filters(line_chunks, filters)
    # ic(ict(), len(line_chunks))

    ic(file_read(new_filepath))
    end_time(4)

    title_search.path = pdf2txt.second_path.parent / 'clean_files'

    title_search.repetitions = len(title_search.file_list)
    # ic(ict(), title_search.path, title_search.title, title_search.repetitions,
    #    title_search.file_list, len(title_search.file_list))
    store_path = title_search.pkl_path

    # 1)
    chunk_line_num, line_chunks = title_search.line_chunks_nums()
    debug_file(Path(join(store_path, '1.0.1.chunks_analysis.txt')), [_ for _ in chunk_line_num.items()])
    debug_file(Path(join(store_path, '1.0.2.chunks_analysis.txt')), line_chunks)
    file_write(Path(join(store_path, '1.0.2.chunks_analysis.pkl')), line_chunks)
    ic(ict(), len(line_chunks))

    # 2)
    constant_text_chunks = title_search.chunks_analysis(line_chunks)
    # ic(ict(), [_ for _ in constant_text_chunks.keys()], [len(_) for _ in constant_text_chunks.values()])
    debug_file(Path(join(store_path, '2.0.1.chunks_analysis.txt')), [_ for _ in constant_text_chunks.items()])
    # ic(ict(), constant_text_chunks)
    # ic(ict(), end_time())

    # 3)
    title_analysis = title_search.title_analysis(line_chunks)
    # title_line_num_chunk = title_analysis
    file_title_chunk_line_num = title_analysis
    debug_file(Path(join(store_path, '3.0.1.file_title_chunk_line_num.txt')),
               [_ for _ in file_title_chunk_line_num.items()])
    file_write(Path(join(store_path, '3.0.1.file_title_chunk_line_num.pkl')), file_title_chunk_line_num)
    # ic(ict(), file_title_chunk_line_num)
    ic(ict(), end_time())

    # Process template file and generate final template
    for e, file in enumerate(title_search.file_list):
        ic(ict(), str(Path(file).name), str(title_search.template_title_file))
        if str(Path(file).name) == str(title_search.template_title_file):
            ic(ict(), title_search.template_title_file)
            ic(ict(), title_search.title)

            # 4) Generate template distances (now stored internally)
            template_result = title_search.title_template(file, constant_text_chunks, file_title_chunk_line_num)
            if not template_result:
                ic(ict(), "Template generation failed")
                return False

            # Debug output for template generation
            debug_file(Path(join(store_path, '4.0.1.template_distances.txt')),
                       {k: v for k, v in title_search.template_distances.items()})
            file_write(Path(join(store_path, '4.0.1.template_distances.pkl')), title_search.template_distances)

            # 5) Extract closest chunks (REFORMED - no min_dif parameter needed)
            chunks_dif_dct = title_search.chunks_distances()

            # Debug output for final results
            debug_file(Path(join(store_path, '5.0.1.chunks_dif_dct.txt')), chunks_dif_dct)
            file_write(join(store_path, '5.1.0.chunks_dif_dct.pkl'), chunks_dif_dct)

            ic(ict(), "Template processing completed successfully")
            break  # Exit loop once template file is processed


if __name__ == '__main__':
    start_time()
    # title: {0: '4005', 1: 'RES', 2: 'VAP', 3: 'DWG', 4: '233', 5: 'IC', 6: '07020', 7: '0'}
    # In this path are pdf files to be converted into text
    home_0 = '/media/konstantinos/bkp/files/dst_small_group/PROJECTS'
    home_1 = join(home('~'), 'Documents/PyTests/Submission/Seek Title Template/dst/au1.5')
    home_2 = join(home('~'), 'PyTests')

    if system() == 'Windows':
        home_0 = 'D:/files/dst_small_group/PROJECTS'
        home_1 = 'D:/au1.5/20240628'
        home_2 = 'C:/PyTests'

    paths = [Path(join(home_2, 'Submission/Process/2211 au/dst/02xxx/PDF')),
             Path(join(home_2, 'Submission/Process/2211 au/dst/07xxx/PDF'))]

    # for e, path in enumerate(paths):
    if exists(Path(paths[1])):
        main_files_data(Path(paths[1]))
    else:
        ic(ict(), f'{Path(paths[1])} Does not exists!')
    # main_test_vars()
    ic(ict(), end_time())
