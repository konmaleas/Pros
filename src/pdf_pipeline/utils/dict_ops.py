from datetime import datetime as dt2
from collections import Counter
from itertools import chain
from icecream import ic


def ict():
    ic.configureOutput(contextAbsPath=True, includeContext=True, prefix=f'{str(dt2.now()).split(" ")[-1]} | ')


def dict_creator(key: list, value: list) -> dict:
    return dict(zip(key, value))


def dicts(dct: dict, key, value):
    if key in dct:
        dct[key].append(value)
    else:
        dct[key] = value


def dicts_2(dct: dict, key, value):
    if key in dct:
        dct[key].append(value)
    else:
        dct[key] = value
    return dct


def dicts_3(dct: dict, key, value):
    dct.setdefault(key, value)
    return dct


def set_in_dict_2(dct: dict, key, value):
    return dct.setdefault(key, set()).add(value)


def set_in_dicts_in_dict_2(dct: dict, enum, key, value):
    return dct.setdefault(enum, {}).setdefault(key, set()).add(value)


def list_in_dict(dct: dict, key, value):
    try:
        if key in dct:
            dct[key].append(value)
        else:
            dct[key] = [value]
    except KeyError as ke:
        print(ke)
    return dct


def list_in_dict_2(dct: dict, key, value):
    return dct.setdefault(key, []).append(value)


def merge_list_in_dict(dct0: dict, dct1: dict) -> dict:
    merged = {}
    flat = []
    for e0, (key, value) in enumerate(dct0.items()):
        for e1, (key_, value_) in enumerate(dct1.items()):
            if key == key_:
                flat = list(chain(*[item if isinstance(item, list) else [item] for item in value+value_]))
                list_in_dict(merged, key, flat)
    return merged


def list_in_dicts_in_dict(dct: dict, enum, key, value):
    lst = []
    lst.append(value)
    if enum not in dct.keys():
        dct.update({enum: {key: lst}})
    else:
        dct[enum][key] = lst
    return dct


def list_in_dicts_in_dict_2(dct: dict, enum, key, value):
    return dct.setdefault(enum, {}).setdefault(key, []).append(value)


def yield_list_in_dict(dct):
    for e, (k, v) in enumerate(dct.items()):
        for ev, iv in enumerate(v):
            yield iv


def dicts_in_dict(dct: dict, enum, key, value):
    if enum not in dct.keys():
        dct.update({enum:{key:value}})
    else:
        dct[enum][key] = value
    return dct


def txt2dict(file) -> dict:
    import ast
    try:
        with open(file, 'r') as fr:
            return ast.literal_eval(fr.read())
    except SyntaxError:
        return {}


def print_dict(dct: dict):
    for e, (k, v) in enumerate(dct.items()):
        if k != '':
            print(f'{e}) k({k}) v({v})')


def sorted_counter_key(lst: list) -> dict:
    return {k:v for k, v in sorted(Counter(lst).items(), key=lambda item:item[0])}


def sorted_counter(lst: list) -> dict:
    return {k:v for k, v in sorted(Counter(lst).items(), key=lambda item: item[1])}


def sorted_dict_2(dct: dict, sort_by_key: bool) -> dict:
    if sort_by_key:
        return {i:dct[i] for i in sorted(dct.keys())}
    return dict(sorted(dct.items(), key=lambda kv:(kv[1], kv[0])))


def sorted_dict(dct: dict, by: str = 'key') -> dict:
    if by == 'key':
        return {k: v for k, v in sorted(dct.items(), key=lambda item: item[0])}
    elif by == 'value':
        return {k: v for k, v in sorted(dct.items(), key=lambda item: item[1])}
    else:
        raise ValueError("by parameter must be 'key' or 'value'")


def yielding_values(dct: dict, num: int) -> dict:
    for key, value in dct.items():
        if value >= num:
            yield key


def yielding_keys(dct: dict, num: int) -> dict:
    for key, value in dct.items():
        if key >= num:
            yield value


def dict2list(dct: dict,
              append_key: bool,
              dict_in_dict: bool = False,
              append_second_key: bool = False) -> list:
    lst = []
    for e, (key, value) in enumerate(dct.items()):
        if isinstance(key, tuple):
            for k in key:
                lst.append(k)
            continue
        if dict_in_dict:
            for key_, value_ in value.items():
                lst.append(key_ if append_second_key else value_)
        else:
            lst.append(key if append_key else value)
    return lst


def sort_list_in_dict(dct: dict) -> list:
    lst = []
    for e, value in enumerate(dct.values()):
        if len(value) > 1:
            lst.append(value[0])
        else:
            lst.append(value)
    return list(chain(*[item if isinstance(item, list) else [item] for item in lst]))


def invert_dict(dct: dict) -> dict:
    dct_ = {}
    for key, value in dct.items():
        if isinstance(value, list):
            for v in value:
                dicts_3(dct_, v, key)
        elif isinstance(value, dict):
            for v in value.items():
                dicts_3(dct_, v, key)
        elif isinstance(value, tuple):
            for v in value:
                dicts_3(dct_, v, key)
        else:
            dicts_3(dct_, value, key)
    return dct_


def invert_dict_list_in_dict(dct: dict) -> dict:
    dct1 = {}
    for key, value in dct.items():
        if isinstance(value, list):
            for v in tuple(value):
                dicts_3(dct1, v, key)
        elif isinstance(value, dict):
            for v in value.items():
                dicts_3(dct1, v, key)
        elif isinstance(value, tuple):
            for v in value:
                dicts_3(dct1, v, key)
        else:
            list_in_dict_2(dct1, value, key)
    return dct1


def invert_list_dict_dict(dct: dict) -> dict:
    dct1, key_ = {}, set()
    for e0, (key0, value0) in enumerate(dct.items()):
        for e1, (key1, value1) in enumerate(value0.items()):
            list_in_dicts_in_dict_2(dct1, tuple(value1), key1, key0)
            key_.add(tuple(value1))
    return dct1


def singling_values(dct: dict) -> dict:
    id_true = invert_dict(dct)
    id_false = invert_dict(id_true)
    return id_false
