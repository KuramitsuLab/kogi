import os
import base64
import warnings


_cache = {}


def load(file):
    file = f'{os.path.dirname(os.path.abspath(__file__))}/{file}'
    try:
        if file.endswith('.png'):
            file_data = open(file, "rb").read()
            return 'data:image/png;base64,' + base64.b64encode(file_data).decode('utf-8')
        else:
            with open(file) as f:
                return f.read()
    except:
        print(file)
        return


def ICON(file):
    if '/' in file:
        return file
    if file not in _cache:
        _cache[file] = load(file)
    return _cache[file]


def CSS(file):
    assert file.endswith('.css')
    if file not in _cache:
        _cache[file] = load(file)
    data = _cache[file]
    return f'<style>{data}</style>'


def JS(file):
    assert file.endswith('.js')
    if file not in _cache:
        _cache[file] = load(file)
    data = _cache[file]
    return f'<script>{data}</script>'
