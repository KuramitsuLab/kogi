
import re
from .common import model_generate, debug_print, Doc, status_message
from .runner import model_parse, define_task, run_command
from kogi.liberr.rulebase import expand_eparams
from kogi.data.error_desc import get_error_desc

# _DIC = {
#     '構文エラー': '[<B>行目で]構文が間違っています。',
#     '構文': '[<B>行目で]構文が間違っています。',
#     '未定義変数': '変数[<A_>]はまだ値が代入されていません。[<A_> = ... のように先に代入してみましょう。]',
#     'インポート忘れ': 'インポートをし忘れています。@check_import',
# }

_SPECIAL = re.compile(r'\<([^\>]+)\>')
_OPTIONAL = re.compile(r'(\[[^\]]+\])')
_CODE = re.compile(r'(`[^`]+`)')
_BOLD = re.compile(r'(__[^_]+__)')


def _extract_svars(text, pat):
    return re.findall(pat, text)


def _replace_svar(text, svar, kw):
    if svar in kw:
        return text.replace(f'<{svar}>', str(kw[svar]))
    svar2 = f'_{svar}'
    if svar2 in kw:
        return text.replace(f'<{svar}>', str(kw[svar2]))
    return text


def replace_md(s):
    for t in re.findall(_CODE, s):
        t2 = f'<code>{t[1:-1]}</code>'
        s = s.replace(t, t2)
    for t in re.findall(_BOLD, s):
        t2 = f'<b>{t[2:-2]}</b>'
        s = s.replace(t, t2)
    return s


def error_format(text, kw):
    for svar in _extract_svars(text, _SPECIAL):
        text = _replace_svar(text, svar, kw)
    for option in _extract_svars(text, _OPTIONAL):
        if '<' in option and '>' in option:
            text = text.replace(option, '')
        else:
            text = text.replace(option, option[1:-1])
    return replace_md(text)


def error_message(args, kw):
    doc = Doc()
    for w in args:
        msg = get_error_desc(w)
        if msg != '':
            cmd = None
            if '@' in msg:
                msg, _, cmd = msg.rpartition('@')
                cmd = f'@{cmd}'
                msg = msg.strip()
            doc.println(error_format(msg, kw))
            if cmd:
                doc.append(run_command(cmd, args, kw))
        else:
            doc.println(w)
    return doc


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
        expand_eparams(kw)
        doc = error_message(args, kw)
        doc.likeit('@error', input_text, fixed)
        return doc
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
        return doc
    else:
        return f'「{x}をインポートするには？」'


define_task('@check_import', check_import)


def xcopy(args, kw):
    return '@pan:コピペは勉強にならないよ！'


define_task('@xcopy', xcopy)


def xcall(args, kw):
    return '先生は忙しいから、まずはTAさんに質問しましょう'


define_task('@xcall', xcall)
