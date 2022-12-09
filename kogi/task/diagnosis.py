
import re
from .common import model_generate, debug_print, Doc, status_message
from .runner import model_parse, define_task
from kogi.liberr.rulebase import expand_eparams

_DIC = {
    '構文エラー': '[<B>行目で]構文が間違っています。',
    '構文': '[<B>行目で]構文が間違っています。',
    '未定義変数': '変数[<A_>]はまだ値が代入されていません。[<A_> = ... のように先に代入してみましょう。]',
    'インポート忘れ': 'インポートをし忘れています。@check_import',
}

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


def error_format(text, kw):
    expand_eparams(kw)
    debug_print(kw)
    for svar in _extract_svars(text, _SPECIAL):
        text = _replace_svar(text, svar, kw)
    for option in _extract_svars(text, _OPTIONAL):
        if '<' in option and '>' in option:
            text = text.replace(option, '')
        else:
            text = text.replace(option, option[1:-1])
    return text


def error_message(doc, args, kw):
    for w in args:
        if w in _DIC:
            doc.println(error_format(_DIC[w], kw))
        else:
            doc.println(w)


def error_classfy(args, kw):
    if 'emsg' in kw and 'eline' in kw:
        emsg = kw['emsg']
        eline = kw['eline']
        input_text = f'<エラー分類>{eline}<sep>{emsg}'
        tag, fixed = model_generate(input_text, split_tag=True)
        if tag == '<status>':
            return status_message(fixed)
        if tag != '<エラー分類>':
            return 'うまく分析できないよ。ごめんね。'
        args, kw = model_parse(fixed, kw)
        doc = Doc()
        error_message(doc, args, kw)
        doc.likeit('@error', input_text, fixed)
        return doc.get_message()
    else:
        debug_print(args, kw)
        return 'エラーが見つからないよ！'


define_task('@root_cause_analysis @diagnosis @error', error_classfy)

IMPORT = {
    'np': 'import numpy as np',
    'pd': 'import pandas as pd',
    'plt': 'import matplotlib.pyplot as plt',
}


def check_import(args, kw):
    expand_eparams(kw)
    if 'A_' not in kw:
        return ''
    x = kw['A_']
    if x in IMPORT:
        doc = Doc()
        doc.println('先に')
        doc.append(Doc.code(IMPORT[x]))
        doc.println('を実行するようにしよう')
        return doc.get_message()
    else:
        return f'「{x}をインポートするには？」'


define_task('@check_import', check_import)
