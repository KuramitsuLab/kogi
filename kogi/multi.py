from kogi.service import *
from .conversation import ConversationAI, set_chatbot
from .transform import model_transform, get_kvars
from .render import Render, tohtml, html_color

kogi_set(
    model_id='NaoS2/multi-kogi'
)


def extract_tag(text):
    if text.startswith('<'):
        tag, end_tag, text = text.partition('>')
        return tag+end_tag, text
    return '', text


def render_code(text, input_text=''):
    eid = Render.new_pairid(input_text, text)
    r = Render()
    text = tohtml(text)
    vars = []
    for kvar in get_kvars(text):
        var = kvar.replace('_', '')
        var = html_color(var, color='blue')
        text = text.replace(kvar, var)
        vars.append(var)
    r.appendHTML(Render.create_code(eid, text))
    return r.get_message('こんな感じかな？')


def fix_code(args, kw):
    if 'eline' in kw:
        eline = kw['eline']
        fixed = model_generate(f'<コード修正>{eline}')
        tag, fixed = extract_tag(fixed)
        if eline == fixed:
            return '直せないよ。ごめんね'
        r = Render(div='<pre style="background: #fff2b8">{}</pre>')
        r.println(eline, color='red')
        r.println(fixed, color='green')
        return r.get_message('直してみたよ')
    else:
        debug_print(kw)
        return 'エラーが見つからないよ！'


TASK = {
    '@help': fix_code,
    '@fix_code': fix_code,
}


def run_task(commands, args, kw):
    global TASK
    ms = []
    for command in commands:
        if command in TASK:
            ms.append(TASK[command](args, kw))
    if len(ms) == 0:
        debug_print(commands)
        return 'あわわわ'
    return ms


class MultitaskAI(ConversationAI):

    def argparse(self, text, commands=None):
        ss = text.split()
        commands = commands or []
        kw = dict(self.slots)
        args = []
        for s in ss:
            if s.startswith('@'):
                commands.append(s)
            elif '=' in s:
                kv = s.split('=')
                if len(kv) == 2:
                    kw[kv[0]] = kv[1]
            elif '_' in s:
                kv = s.split('_')
                if len(kv) == 2:
                    kw[kv[0]] = kv[1]
            else:
                args.append(s)
        return commands, args, kw

    def response(self, user_input):
        response_text = model_transform(user_input)
        tag, text = extract_tag(response_text)
        if tag.startswith('<status>'):
            return 'AIモデルのロード中. しばらく待ってね'
        if tag.startswith('<コマンド'):
            commands, args, kw = self.argparse(text)
            return run_task(commands, args, kw)
        if tag.startswith('<コード'):
            return render_code(text, input_text=user_input)
        return text


set_chatbot(MultitaskAI())
