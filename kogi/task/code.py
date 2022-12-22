from kogi.transform import get_kvars
from .common import Doc, debug_print
from .runner import task
from .diagnosis import IMPORT


def add_import(code):
    ss = []
    for key, snippet in IMPORT.items():
        if f'{key}.' in code:
            ss.append(snippet)
    if len(ss) == 0:
        return code
    return '\n'.join(ss) + '\n' + code


def _split_kw(s, kw):
    ss = []
    while True:
        left, sp, right = s.partion(kw)
        ss.append(left)
        if kw != sp:
            break
        ss.append(sp)
    return ss


def split_keywords(s, keywords):
    keywords.sort(key=lambda x: -len(x))
    ss = [s]
    for kw in keywords:
        ss2 = []
        for s in ss[::2]:
            if kw in s:
                ss2.extend(_split_kw(s, kw))
            else:
                ss2.append(s)
        ss = ss2
    return ss


@task('@translated_code')
def translated_code(bot, kwargs):
    doc = Doc()
    doc.println('こんなコードはいかが？')
    generated_code = add_import(kwargs['generated_text'])
    # doc.append(typewriter_doc(generated_code))
    code_doc = doc.new(style='@code')
    kvars = get_kvars(generated_code)
    for t in split_keywords(generated_code, kvars):
        if t in kvars:
            code_doc.append(t.replace('_', ''), style='@zen')
        else:
            code_doc.append(t)
    recid = bot.record("@translate_code",
                       kwargs['user_input'], kwargs['generated_text'])
    doc.add_likeit(recid, copy=generated_code)
    return doc


@task('@fix_code')
def fix_code(bot, kwargs):
    if 'eline' not in kwargs:
        debug_print(kwargs)
        return 'エラーが見つからないよ！'

    eline = kwargs['eline']
    tag, fixed = bot.generate(f'<コード修正>{eline}')
    recid = bot.record('@fix_code', eline, fixed)
    doc = Doc('コギー、がんばってみる')
    code_doc = doc.new(f'{eline}\n', style='@code')
    if tag != '<コード修正>' or eline == fixed:
        doc.println('ごめんね。なんかうまく直せないよ！')
    else:
        doc.println('どう？')
        code_doc = doc.new(f'{fixed}\n', style='@code')
        doc.add_likeit(recid, copy=fixed)
    return doc
