from modules.file_opers import file_read, file_write
from modules.path_manipulation import dst_exists, path_sym
from modules.string_manipulation import clear, singling_symbols, reconstruct_str, replacer_2
from modules.dict_opers import list_in_dict
from os.path import expanduser as home
from os import walk
from pathlib import Path
from shutil import copy2
from collections import Counter
from platform import system
from datetime import datetime as dt2
from icecream import ic


def ict():
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


def projects(path: str | Path) -> list[str | Path]:
    lst = []
    for e, (root, dirs, files) in enumerate(walk(path)):
        if root.lower().__contains__('sub'):
            for file in files:
                filepath = Path(root) / Path(file)
                if filepath.suffix == '.pdf':
                    lst.append(filepath)
    return lst


def in_interest(filepaths: list[str | Path],
                start: int,
                end: int,
                uid: int) -> dict[str | Path, list[str | Path]]:
    dct = {}
    for filepath in filepaths:
        project = reconstruct_str(filepath, path_sym(), 7, 0)
        project_name = reconstruct_str(filepath, path_sym(), 6, 7)
        project_uid = reconstruct_str(filepath, path_sym(), 6, 7) .split(' ')[0]

        try:
            if isinstance(uid, int):
                if int(project_uid) >= uid:
                    list_in_dict(dct, Path(project_name), Path(project))
        except ValueError:
            pass

    return dct


def _copy(src: str | Path, dst: str | Path, files: dict[str | Path, list[str | Path]]):
    dct = {}
    dst_filepath = Path
    for project_name, files in files.items():
        for f, file in enumerate(files):

            try:

                filepath = src / project_name / file

                dst_file = Path(singling_symbols(replacer_2(file.stem, '_', preserve='-')))
                base_dir = file.parent.stem
                dst_filepath = dst_exists(dst / project_name / base_dir ) / f'{dst_file}.pdf'

                copy2(filepath, dst_filepath)

                if dst_file.exists():
                    list_in_dict(dct, 'copied', dst_filepath)

            except FileNotFoundError:
                list_in_dict(dct, 'FileNotFoundError', dst_filepath)
                continue
            except PermissionError:
                list_in_dict(dct, 'FileNotFoundError', dst_filepath)
                continue
            except OSError:
                list_in_dict(dct, 'FileNotFoundError', dst_filepath)
                continue
    return dct


if __name__ == '__main__':

    src_path = Path('/media/konstantinos/8T/files/PROJECTS')
    dst_path = dst_exists(Path('/media/konstantinos/8T/Projects'))

    home_1 = dst_exists(Path(home('~')) / Path('PycharmProjects/Pros/claude/files/pkl'))
    home_2 = Path(home('~')) / Path('PyTests')

    if system() == 'Windows':
        home_2 = Path('C:/PyTests/Submission/Process')

    # path = home_2 / Path('1910 ncm/dst/44xx')

    # successful_files_path = home_1 / Path('successful_file.txt')
    # original_files = home_2 / Path('1910 ncm/dst/44xx')

    projects_ = projects(src_path)
    ic(file_write(home_1 / 'projects_files.pkl'))


    # # projects_in_interest = in_interest(projects, 1301)
    # # file_write(home_1 / 'projects_in_interest.pkl', projects_in_interest)
    # projects_in_interest = dict(file_read(home_1 / 'projects_in_interest.pkl'))
    #
    # # copied_files = _copy(src_path, dst_path, projects_in_interest)
    # # ic(file_write(home_1 / 'copied_files.pkl', copied_files))
    # copied_files = dict(file_read(home_1 / 'copied_files.pkl'))
    #
    # ic(copied_files.values())

    # projects_ = projects(dst_path)

    uids = []
    submissions_directories = {}
    submissions_stems = {}
    project_uid = ''
    seen = set()
    projects_ = file_read(home_1 / 'copied_files.pkl')

    # projects_ = file_read(home_1 / 'projects_files.pkl')

    for p, filepath in enumerate(projects):

        project = reconstruct_str(filepath, path_sym(), 6, 0)
        project_name = reconstruct_str(filepath, path_sym(), 5, 6)
        project_submission = reconstruct_str(filepath, path_sym(), 6, 7)

        if project not in seen:
            seen.add(project_submission)
            list_in_dict(submissions_directories, project_name, project)

        list_in_dict(submissions_stems, Path(project_name) / Path(project_submission), filepath.stem)

    ic(file_write(home_1 / 'submissions_stem.pkl', submissions_stems))
    ic(file_write(home_1 / 'submissions_directories.pkl', submissions_directories))

    # '20220117_FINAL BIG SUBMISSION'

    submissions_stems = file_read(home_1 / 'submissions_stem.pkl')
    ic(submissions_stems)

    submissions_directories = file_read(home_1 / 'submissions_directories.pkl')
    ic(submissions_directories)


















