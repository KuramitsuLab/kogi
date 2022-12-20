from kogi.transform import model_transform, get_kvars
from kogi.render import Doc, tohtml, html_color
from .common import model_generate, debug_print
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


@task('@translated_code')
def translated_code(bot, kwargs):
    doc = Doc()
    doc.println('こんなコードはいかが？')
    generated_code = add_import(kwargs['generated_text'])
    html_code = tohtml(generated_code)
    vars = []
    for kvar in get_kvars(html_code):
        var = kvar.replace('_', '')
        var = html_color(var, color='blue')
        html_code = html_code.replace(kvar, var)
        vars.append(var)
    doc.append(Doc.code(html_code))
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
    debug_print(tag, fixed)
    code = Doc.code()
    code.append(Doc.color(f'{eline}\n', color='red'))
    if tag != '<コード修正>' or eline == fixed:
        code.println('ごめんね。なんかうまく直せないよ！')
    else:
        code.append(Doc.color(f'{fixed}\n', background='#d0e2be'))
        code.add_likeit(recid)
    return code
