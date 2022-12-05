import time
import traceback
from .content import ICON, JS, CSS
from ._google import google_colab

from IPython.display import display, HTML, JSON
from kogi.service import translate, model_generate, print_nop


RMT_HTML = '''
<div id="{id}" class="parent">
<div style="float: left; width: 48%; text-align: right;">
<label class="box24" for="input">{input}</label>
<textarea id="input" class="box16"></textarea>
</div>
<div style="float: left; width: 48%; text-align: right;">
<label class="box24" for="outout">{output}</label>
<textarea id="output" class="box18" readonly></textarea>
</div>
</div>
'''


def display_rmt(input='入力', output='出力', delay=600):
    data = dict(
        id=1,
        input=input,
        output=output,
        delay=600,
    )
    DHTML = RMT_HTML.format(**data)
    display(HTML(CSS('_rmt.css')+DHTML+JS('_rmt.js')))
    return id


class TransformWeaver(object):
    def before(self, text):
        return text

    def after(self, text):
        return text


TransformWeaverNone = TransformWeaver()

MODULES = [
    ('math.', 'import math'),
    ('os.', 'import os'),
    ('sys.', 'import sys'),
    ('collections.', 'import collections'),
    ('time.', 'import time'),
    ('datetime.', 'import datetime'),
    ('random.', 'import random'),
    ('np.', 'import numpy as np'),
    ('scipy.', 'import scipy'),
    ('plt.', 'import matplotlib.pyplot as plt'),
    ('pd.', 'import pandas as pd'),
]


def check_module(code, fmt='<tt>{}</tt> してから、'):
    for module, todo in MODULES:
        if code.startswith(module):
            return fmt.format(todo)
    return ''


def codegen(code, text=''):
    if '<nl>' in code:
        code = code.replace('<nl>', '\n').replace('<tab>', '\t')
    if text != '' or not text.isascii():
        text = translate(text, lang='ja_en')
        text = f'# {text}\n'
    code = check_module(code, fmt='{}\n') + text + code
    return code


_LOGS = []


def rmt(input='入力', output='予測', delay=600, print=print_nop,
        transform=TransformWeaverNone, generate=model_generate):
    display_rmt(input=input, output=output, delay=delay)

    cached = {'': ''}

    def convert(text):
        global _LOGS
        try:
            ss = []
            for line in text.splitlines():
                if line not in cached:
                    if line.isascii():
                        _line = translate(line, lang='en_ja')
                        _line = transform.before(_line)
                        print(line, '=>', _line)
                    else:
                        _line = transform.before(line)
                    s = time.time()
                    _translated = generate(_line)
                    e = time.time()
                    _translated = codegen(_translated, _line)
                    translated = transform.after(_translated)
                    print(f'{e-s:.3f}', line, '=>', translated)
                    if line == _line and translated == _translated:
                        _LOGS.append((line, translated))
                    else:
                        _LOGS.append((line, translated, _line, _translated))
                    cached[line] = translated
                else:
                    translated = cached[line]
                ss.append(translated)
            text = '\n'.join(ss)
            return JSON({'result': text})
        except:
            traceback.print_exc()

    def logger():
        global _LOGS
        if len(_LOGS) > 0:
            kogi_log('rmt', pairs=_LOGS)
            _LOGS = []

    if google_colab is not None:
        google_colab.register_callback('notebook.Convert', convert)
        google_colab.register_callback('notebook.Logger', logger)
