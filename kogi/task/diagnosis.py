
import re
from .common import model_generate, debug_print, Doc
from .runner import model_parse, define_task

_DIC = {
    '構文エラー': '[<B>行目で]構文が間違っています。',
    '構文': '[<B>行目で]構文が間違っています。',
}

_SPECIAL = re.compile(r'\<([^\>]+)\>')
_OPTIONAL = re.compile(r'(\[[^\]]+\])')


def _extract_svars(text, pat):
    return text.findall(pat, text)


def _replace_svar(text, svar, kw):
    if svar in kw:
        return text.replace(f'<{svar}>', str(kw[svar]))
    svar2 = f'_{svar}'
    if svar2 in kw:
        return text.replace(f'<{svar}>', str(kw[svar2]))
    return text


def error_format(text, kw):
    for svar in _extract_svars(text, _SPECIAL):
        text = _replace_svar(text, svar, kw)
    for option in _extract_svars(text, _OPTIONAL):
        if '<' in option and '>' in option:
            text = text.replace(option, '')
        else:
            text = text.replace(option, option[1:-1])
    return text


def error_message(args, kw):
    doc = Doc()
    for w in args:
        if w in _DIC:
            doc.println(error_format(_DIC[w], kw))
        else:
            doc.println(w)
    return doc.get_message()


def error_classfy(args, kw):
    if 'emsg' in kw and 'eline' in kw:
        emsg = kw['emsg']
        eline = kw['eline']
        tag, fixed = model_generate(
            f'<エラー分類>{eline}<sep>{emsg}', split_tag=True)
        if tag != '<エラー分類>':
            return 'うまく分析できないよ。ごめんね。'
        args, kw, cmds = model_parse(fixed, kw)
        return error_message(args, kw)
    else:
        debug_print(args, kw)
        return 'エラーが見つからないよ！'


define_task('@root_cause_analysis @diagnosis', error_classfy)
