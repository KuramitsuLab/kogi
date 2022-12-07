from kogi.service import *
from .conversation import ConversationAI, set_chatbot
from .transform import model_transform
from .render import Render

kogi_set(
    model_id='NaoS2/multi-kogi'
)


def extract_tag(text):
    if text.startswith('<'):
        tag, end_tag, text = text.partition('>')
        return tag+end_tag, text
    return '', text


def render_code(text):
    r = Render(div='<pre>{}</pre>')
    r.println(text)
    return r.get_message('ざっくりいうと')


def fix_code(args, kw):
    if 'eline' in kw:
        eline = kw['eline']
        fixed = model_generate(f'<コード修正>{eline}')
        r = Render(div='<pre>{}</pre>')
        r.println(eline, color='red')
        r.println(fixed, color='green')
        return r.get_message('直してみたよ')
    else:
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
        return 'あわわわ ' + ' '.join(commands)
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
            return render_code(text)
        return text


set_chatbot(MultitaskAI())
