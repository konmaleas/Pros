# Version 3.0
from os import stat, makedirs
from platform import system
from pathlib import Path

from pathlib import Path


def dst_exists(path: str | Path, create: bool = True) -> str | Path:
    """
    Check if destination path exists and optionally create it.

    Args:
        path: Path to check / create
        create: If True, create the directory if it doesn't exist

    Returns:
        The path (same type as input)
    """
    path_obj = Path(path)

    if path_obj.exists():
        return path

    if create:
        path_obj.mkdir(parents=True, exist_ok=True)

    return path


def path_sym() -> str:
    '''
        :return: The path symbol for it's os
    '''
    return '\\' if system() == 'Windows' else '/'


def slash_conv(path: str) -> str:
    '''
        :param path:
        :return: a path with the right slash for every os
    '''
    return f'{path}{path_sym()}' if system() == 'Windows' else path.replace('/', path_sym())


def base_name(dr, path):
    '''
        :param dr: The part of the path that will be splitted fro left to write
        :param path: The whole path
        :return: The path without the splitted part
                i.e: dr='/home' path='/home/user/Documents/' return /user/Documents
    '''
    return slash_conv(path.split(dr)[-1])
