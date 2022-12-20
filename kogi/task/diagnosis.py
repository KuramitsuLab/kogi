
import collections
import json
import re
from .common import model_generate, debug_print, Doc, status_message
from .runner import model_parse, task, run_prompt
from kogi.liberr.rulebase import extract_params, expand_eparams
from kogi.data.error_desc import get_error_desc

_SPECIAL = re.compile(r'\<([^\>]+)\>')
_OPTIONAL = re.compile(r'(\[[^\]]+\])')


def _extract_svars(text, pat):
    return re.findall(pat, text)


def _replace_svar(text, svar, kw):
    if svar in kw:
        return text.replace(f'<{svar}>', str(kw[svar]))
    svar2 = f'_{svar}'
    if svar2 in kw:
        return text.replace(f'<{svar}>', str(kw[svar2]))
    return text


def error_format(text, kwargs):
    for svar in _extract_svars(text, _SPECIAL):
        text = _replace_svar(text, svar, kwargs)
    for option in _extract_svars(text, _OPTIONAL):
        if '<' in option and '>' in option:
            text = text.replace(option, '')
        else:
            text = text.replace(option, option[1:-1])
    return Doc.md(text)


UNDEFINED = collections.Counter()


def generate_error_diagnosis_message(bot, args, kwargs):
    doc = Doc()
    for w in args:
        msg = get_error_desc(w)
        if msg == '':
            if bot:
                doc.println(w)
            else:
                UNDEFINED.update([w])
            continue
        cmd = None
        if '@' in msg:
            msg, _, cmd = msg.rpartition('@')
            cmd = f'@{cmd}'
            msg = msg.strip()
        doc.println(error_format(msg, kwargs))
        if bot and cmd:
            doc.append(run_prompt(bot, cmd, kwargs))
    return doc


def test_error_diagnosis_message(jsonl_filename):
    ss = []
    with open(jsonl_filename) as f:
        for line in f.readlines():
            d = json.loads(line)
            if 'eline' in d and 'emsg' in d and 'hint' in d:
                etype, epat, eparams = extract_params(d['emsg'], maxlen=None)
                d['_epat'] = epat
                d['_eparams'] = eparams
                args, kwargs = model_parse(d['hint'], d)
                doc = generate_error_diagnosis_message(None, args, kwargs)
                d2 = dict(
                    eline=d['eline'],
                    emsg=d['emsg'],
                    epat=epat,
                    eparams=eparams,
                    hint=d['hint'],
                    desc=doc.text().replace('\n', '')
                )
                ss.append(d2)
    outputfile = jsonl_filename.replace('.jsonl', '_shion.jsonl')
    with open(outputfile, 'w') as w:
        for d in ss:
            print(json.dumps(d, ensure_ascii=False), file=w)
    print(f'Wrote {outputfile} size={len(ss)}')
    print(UNDEFINED.most_common())


@task('@root_cause_analysis @diagnosis @error')
def error_classfy(bot, kwargs):
    if 'emsg' not in kwargs or 'eline' not in kwargs:
        debug_print(args, kwargs)
        return 'エラーが見つからないよ！'
    emsg = kwargs['emsg']
    eline = kwargs['eline']
    input_text = f'<エラー分類>{eline}<sep>{emsg}'
    tag, fixed = bot.generate(input_text)
    if tag == '<status>':
        return status_message(fixed)
    if tag != '<エラー分類>':
        return 'うまく分析できないよ。ごめんね。'
    args, kwargs = model_parse(fixed, kwargs)
    doc = generate_error_diagnosis_message(bot, args, kwargs)
    doc.likeit('@error', input_text, fixed)
    return doc


IMPORT = {
    'math': 'import math',
    'random': 'import random',
    'datetime': 'import datetime',
    'np': 'import numpy as np',
    'pd': 'import pandas as pd',
    'plt': 'import matplotlib.pyplot as plt',
    'sns': 'import seaborn as sns',
    'scipy.stats': 'import scipy.stats',
}


@task('@check_import')
def check_import(bot, kwargs):
    expand_eparams(kwargs)
    if 'A_' not in kwargs:
        return None
    x = kwargs['A_']
    if x in IMPORT:
        doc = Doc()
        doc.println('先に、次のインポートを実行しておきましょう')
        doc.append(Doc.code(IMPORT[x]))
        return doc
    else:
        return f'bot:「{x}をインポートするには？」'


@task('@xcopy')
def xcopy(args, kwargs):
    return '@ta:コピペは勉強にならないよ！'


@task('@xcall')
def xcall(bot, kwargs):
    return '先生は忙しいから、まずはTAさんに質問しましょう'
