from kogi.service import *
from .conversation import ConversationAI, set_chatbot
from .transform import model_transform, get_kvars
from .render import Render, tohtml, html_color
from .task.loading import run_task

kogi_set(
    model_id='NaoS2/multi-kogi'
)


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
        tag, text = model_transform(user_input, split_tag=True)
        if tag.startswith('<status>'):
            return 'AIモデルのロード中. しばらく待ってね'
        if tag.startswith('<コード'):
            return render_code(text, input_text=user_input)
        if tag.startswith('<コマンド'):
            return run_task(text, self.slots)
        return text


set_chatbot(MultitaskAI())
