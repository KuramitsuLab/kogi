import os


def _abspath(file):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), file)


def load_data(file, DATA, default_first=True):
    if not os.path.exists(file):
        file = _abspath(file)

    with open(file) as f:
        for line in f.readlines():
            if line.startswith('#'):
                continue
            kw, _, data = line.partition(': ')
            if data != '':
                kw = kw.strip()
                data = data.strip()
                if default_first:
                    DATA.setdefault(kw, data)
                else:
                    DATA[kw] = data
