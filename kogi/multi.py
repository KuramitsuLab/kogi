from kogi.service import *
from .conversation import ConversationAI, set_chatbot
from .transform import model_transform, get_kvars
from .task.all import run_prompt


# def render_code(text, input_text=''):
#     doc = Doc()
#     doc.println('こんな感じはいかが？')
#     htext = tohtml(text)
#     vars = []
#     for kvar in get_kvars(htext):
#         var = kvar.replace('_', '')
#         var = html_color(var, color='blue')
#         htext = htext.replace(kvar, var)
#         vars.append(var)
#     doc.append(Doc.code(htext))
#     doc.add_button('@xcopy', 'コピー')
#     doc.likeit("@codepan", input_text, text)
#     return doc


class MultitaskAI(ConversationAI):

    def response(self, input_text):
        tag, generated_text = self.generate_transform(input_text)
        self.record('@model', input_text, f'{tag}{generated_text}')
        if tag.startswith('<status>'):
            return '@robot:AIモデルのロード中. しばらく待ってね'
        kwargs = dict(user_input=input_text,
                      generated_text=generated_text, **self.slots)
        if tag.startswith('<コード'):
            return run_prompt(self, '@translated_code', kwargs)
        if tag.startswith('<コマンド'):
            debug_print('TODO', tag, generated_text)
            return run_prompt(self, generated_text, kwargs)
        return generated_text


set_chatbot(MultitaskAI())
