from kogi.service import *
from .conversation import ConversationAI, set_chatbot
from .transform import model_transform, get_kvars
from .render import Doc, tohtml, html_color
from .task.loading import run_task

kogi_set(
    model_id='NaoS2/multi-kogi'
)


def render_code(text, input_text=''):
    doc = Doc()
    doc.println('えいやと')
    htext = tohtml(text)
    vars = []
    for kvar in get_kvars(htext):
        var = kvar.replace('_', '')
        var = html_color(var, color='blue')
        htext = htext.replace(kvar, var)
        vars.append(var)
    doc.append(Doc.code(htext))
    doc.add_button('@xcopy', 'コピー')
    doc.likeit("@codepan", input_text, text)
    return doc.get_message()


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

    def exec(self, prompt):
        return run_task(prompt, self.slots)

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
