import os

_EDESC = {}


def _abspath(file):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), file)


def load_error(file='error.tsv'):
    if not os.path.exists(file):
        file = _abspath(file)

    with open(file) as f:
        for line in f.readlines():
            if line.startswith('#'):
                continue
            kw, _, edesc = line.partition(': ')
            if edesc != '':
                kw = kw.strip()
                edesc = edesc.strip()
                _EDESC[kw] = edesc
                #print(kw, edesc)


load_error('error.txt')


def get_error_desc(kw):
    if kw in _EDESC:
        return _EDESC[kw]
    return ''
