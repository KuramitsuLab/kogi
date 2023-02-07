import os
from .common_loader import load_data

_KWDATA = {}
load_data('diagnosis_ja.txt', _KWDATA)


def kwconv_diagnosis(kw, default=''):
    if kw in _KWDATA:
        return _KWDATA[kw]
    return default


def reload(filename):
    global _KWDATA
    _KWDATA = {}
    load_data(filename, _KWDATA)
