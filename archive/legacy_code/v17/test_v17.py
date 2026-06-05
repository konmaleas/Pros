from modules.file_opers import file_read
from os.path import expanduser as home
from pathlib import Path
from datetime import datetime as dt2
from icecream import ic


def ict():
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


home = Path(home('~'))
base_dir = Path('PycharmProjects/Pros/claude/files/pkl')
paths_file = Path('copied_files.pkl')  # Your pickle file with PDF paths
pdf_paths_file = home / base_dir / paths_file

ic(file_read(pdf_paths_file))
