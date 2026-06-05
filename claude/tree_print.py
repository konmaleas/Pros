import os
from pathlib import Path
from icecream import ic


def print_tree(directory, prefix='', max_depth=4, current_depth=0):
    if current_depth >= max_depth:
        return
    
    try:
        paths = sorted(Path(directory).iterdir(), key=lambda p: (not p.is_dir(), p.name))
    except PermissionError:
        return
    
    for i, path in enumerate(paths):
        is_last = i == len(paths) - 1
        current_prefix = '└── ' if is_last else '├── '
        print(f'{prefix}{current_prefix}{path.name}')
        
        if path.is_dir() and not path.name.startswith('.'):
            extension = '    ' if is_last else '│   '
            print_tree(path, prefix + extension, max_depth, current_depth + 1)


# Run from project directory
print('/n/home/konstantinos/PycharmProjects/Pros')
print_tree('/home/konstantinos/PycharmProjects/Pros')
