import os
import base64

_cache = {}

def load_from_this_dir(file):
    file = f'{os.path.dirname(os.path.abspath(__file__))}/{file}'
    try:
        if file.endswith('.png'):
            file_data = open(file, "rb").read()
            return 'data:image/png;base64,' + base64.b64encode(file_data).decode('utf-8')
        else:
            with open(file) as f:
                return f.read()
    except:
        print('Cannot load', file)
        return ''


def load_icon(file):
    if file.startswith('https://') or file.startswith('http://'):
        return file
    if file not in _cache:
        _cache[file] = load_from_this_dir(file)
    return _cache[file]


def load_css(file):
    assert file.endswith('.css')
    if file not in _cache:
        _cache[file] = load_from_this_dir(file)
    data = _cache[file]
    return f'<style>{data}</style>'


def load_js(file):
    assert file.endswith('.js')
    if file not in _cache:
        _cache[file] = load_from_this_dir(file)
    data = _cache[file]
    return f'<script>{data}</script>'
