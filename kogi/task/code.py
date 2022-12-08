from .common import model_generate, debug_print, Doc
from .runner import define_task


def fix_code(args, kw):
    if 'eline' in kw:
        eline = kw['eline']
        tag, fixed = model_generate(f'<コード修正>{eline}', split_tag=True)
        debug_print(tag, fixed)
        code = Doc.code()
        code.append(Doc.color(f'{eline}\n', color='red'))
        if tag != '<コード修正>' or eline == fixed:
            code.println('ごめんね。なんかうまく直せないよ！')
        else:
            code.append(Doc.color(f'{fixed}\n', background='#d0e2be'))
        doc_id = code.reg(eline, fixed)
        code.add_likeit(doc_id, '@fix_code')
        return code.get_message('コギーがコードを直してみたら..')
    else:
        debug_print(kw)
        return 'エラーが見つからないよ！'


define_task('@fix_code @fix @help', fix_code)
