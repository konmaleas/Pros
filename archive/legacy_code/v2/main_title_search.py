from files.nikos.modules.file_opers import file_read
from modules.dict_opers import dict2list, sorted_dict_2, list_in_dict
from modules.file_opers import file_write, read_pickles
from modules.time_oper import start_time, end_time
from reorganize_files import create_dst_dirs, reorganize_files, pdf_files
from title_search import TitleSearch
from heavy_text_processor_v2 import (process_pdf_with_adaptive_filtering,
                                     FrequencyBasedFilter as NoiseCancellation)
from pdf_to_text import PdfToText
from pathlib import Path
from os import listdir
from os.path import join, exists, expanduser as home
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

    # 0) File processing and filtering
    new_filepath = Path
    title_frequency_data = {}
    for e, file in enumerate(listdir(pdf2txt.second_path)):
        if file.__contains__(title_search.title[6]):
            list_in_dict(title_frequency_data, )  # Note: chunks_distances() call removed - now handled by pipeline

        filepath = Path(pdf2txt.second_path / file)
        text = '\n'.join(file_read(filepath))
        new_filepath = filepath.parent.parent / 'clean_files' / filepath.with_suffix('.pkl').name

        # title_chunks = title_search.title.split('-')
        filtered = process_pdf_with_adaptive_filtering(text, title_search.title, )
        # file_write(filtered)

    ic(file_read(new_filepath))
    end_time(4)

    # Update path to clean files
    title_search.path = pdf2txt.second_path.parent / 'clean_files'
    title_search.repetitions = len(title_search.file_list)

    store_path = title_search.pkl_path

    # REFORMED: Single master pipeline call replaces all individual steps
    try:
        ic(ict(), "Starting reformed template generation pipeline...")

        # Execute the complete pipeline in one call
        final_template = title_search.generate_full_template(anchor_selection_strategy='cluster', max_distance=100,
                min_cluster_size=3, max_chunks=5, save_intermediate=True  # Save debug files during processing
        )

        ic(ict(), "Template generation completed successfully!")
        ic(ict(), f"Final template contains {len(final_template)} title chunks")

        # Optional: Display pipeline summary
        pipeline_summary = title_search.get_step_summary()
        ic(ict(), "Pipeline Summary:", pipeline_summary)

        return final_template

    except ValueError as e:
        ic(ict(), f"Template generation failed: {e}")
        return False


# ALTERNATIVE: Step-by-step approach (for debugging or custom control)
def main_files_data_step_by_step(path: str | Path):
    """
    Alternative main function using individual pipeline steps.
    Useful for debugging or when you need custom control over each step.
    """
    ic(ict(), start_time())

    # ... [same initialization code as above] ...

    # This approach gives you full control over each step
    title_search = TitleSearch(path=Path(path) / 'clean_files',  # Assuming clean_files already processed
                               extension='.pkl', operation='>=')

    title_search.title = '4005-RES-VAP-DWG-233-IC-07020-0'

    store_path = title_search.pkl_path

    try:
        # Step 1: Extract line chunks
        ic(ict(), "Step 1: Extracting line chunks...")
        if not title_search.line_chunks_nums():
            raise ValueError("Step 1 failed")

        # Save intermediate results
        debug_file(Path(join(store_path, '1.0.1.chunks_analysis.txt')),
                   [_ for _ in title_search.chunk_line_num.items()])
        debug_file(Path(join(store_path, '1.0.2.chunks_analysis.txt')), title_search.line_chunks)
        file_write(Path(join(store_path, '1.0.2.chunks_analysis.pkl')), title_search.line_chunks)

        ic(ict(), f"Step 1 complete: {len(title_search.line_chunks)} chunks found")

        # Step 2: Analyze constant chunks
        ic(ict(), "Step 2: Analyzing constant chunks...")
        if not title_search.chunks_analysis():
            raise ValueError("Step 2 failed")

        debug_file(Path(join(store_path, '2.0.1.chunks_analysis.txt')),
                   [_ for _ in title_search.constant_text_chunks.items()])

        ic(ict(), f"Step 2 complete: {len(title_search.constant_text_chunks)} files analyzed")

        # Step 3: Title analysis
        ic(ict(), "Step 3: Analyzing title chunks...")
        if not title_search.title_analysis():
            raise ValueError("Step 3 failed")

        debug_file(Path(join(store_path, '3.0.1.file_title_chunk_line_num.txt')),
                   [_ for _ in title_search.file_title_chunk_line_num.items()])
        file_write(Path(join(store_path, '3.0.1.file_title_chunk_line_num.pkl')),
                   title_search.file_title_chunk_line_num)

        ic(ict(), f"Step 3 complete: {len(title_search.file_title_chunk_line_num)} files with title chunks")

        # Step 4: Generate template for the specific template file
        template_file = None
        for file in title_search.file_list:
            if str(Path(file).name) == str(title_search.template_title_file):
                template_file = file
                break

        if template_file is None:
            raise ValueError(f"Template file {title_search.template_title_file} not found")

        ic(ict(), "Step 4: Generating template distances...")
        if not title_search.title_template(template_file):
            raise ValueError("Step 4 failed")

        debug_file(Path(join(store_path, '4.0.1.template_distances.txt')),
                   {k: v for k, v in title_search.template_distances.items()})
        file_write(Path(join(store_path, '4.0.1.template_distances.pkl')), title_search.template_distances)

        ic(ict(), f"Step 4 complete: {len(title_search.template_distances)} title chunks processed")

        # Step 5: Extract final chunks
        ic(ict(), "Step 5: Extracting closest chunks...")
        final_result = title_search.chunks_distances()

        debug_file(Path(join(store_path, '5.0.1.chunks_dif_dct.txt')), final_result)
        file_write(join(store_path, '5.1.0.chunks_dif_dct.pkl'), final_result)

        ic(ict(), f"Step 5 complete: {len(final_result)} title chunks with distances")

        return final_result

    except Exception as e:
        ic(ict(), f"Step-by-step processing failed: {e}")
        return False


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

    # Main execution with reformed pipeline
    if exists(Path(paths[1])):
        # Use the reformed single-call approach
        result = main_files_data(Path(paths[1]))

        # Or use step-by-step approach for debugging
        # result = main_files_data_step_by_step(Path(paths[1]))

        if result:
            ic(ict(), "Processing completed successfully")
        else:
            ic(ict(), "Processing failed")
    else:
        ic(ict(), f'{Path(paths[1])} Does not exist!')

    ic(ict(), end_time())
