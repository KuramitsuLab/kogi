import re
import sys
from IPython import get_ipython

from .service import (
    model_generate, translate,
    record_log, debug_print
)

from .ui import google_colab
from .transform import model_generate, model_transform
from .task.all import run_prompt

from .ui.dialog_colab import start_dialog
# if google_colab:
#     from .ui.dialog_colab import start_dialog
# else:
#     pass
#     # try:
#     #     import ipywidgets
#     #     from .ui.dialog_ipywidgets import display_dialog
#     # except ModuleNotFoundError:
#     #     from .ui.dialog_colab import display_dialog

from .liberr import kogi_exc
from .ui.render import Doc


def split_tag(text):
    if isinstance(text, list) or isinstance(text, tuple):
        return [split_tag(str(t)) for t in text]
    if text.startswith('<'):
        tag, end_tag, text = text.partition('>')
        return tag+end_tag, text
    return '', text


class ConversationAI(object):
    slots: dict
    records: list

    def __init__(self, slots=None):
        self.slots = slots or {}
        self.records = []

    def get(self, key, value):
        return self.slots.get(key, value)

    def update(self, context: dict):
        if len(self.records) > 0:
            record_log(type='dialog', context=self.slots, records=self.records)
        self.records = []
        if context:
            self.slots = dict(context)
        else:
            self.slots = {}

    def record(self, task, input_text, output_text):
        rec_id = len(self.records)
        self.records.append((task, input_text, output_text))
        return rec_id

    def log_likeit(self, rec_id, score):
        if rec_id < len(self.records):
            task, input_text, output_text = self.records[rec_id]
            record_log(type='likeit', task=task, score=score,
                       input_text=input_text, output_text=output_text)

    def generate(self, input_text):
        output = model_generate(input_text)
        return split_tag(output)

    def generate_transform(self, input_text):
        output = model_transform(input_text)
        return split_tag(output)

    def exec(self, prompt, kwargs=None):
        kwargs = kwargs or dict(self.slots)
        return run_prompt(self, prompt, kwargs)

    def ask(self, input_text):
        message = self.response(input_text)
        self.record('@dialog', input_text, str(message))
        return message

    def response(self, input_text):
        tag, generated_text = self.generate_transform(input_text)
        if tag.startswith('<status>'):
            return '@robot:AIモデルのロード中. しばらく待ってね'
        return generated_text


_DefaultChatbot = ConversationAI()


def set_chatbot(chatbot):
    global _DefaultChatbot
    _DefaultChatbot = chatbot


def call_and_start_kogi(actions, code: str = None, context: dict = None):
    for user_text in actions:
        _DefaultChatbot.update(context)
        doc = _DefaultChatbot.ask(user_text)
        start_dialog(_DefaultChatbot, doc)
        return


def error_message(record):
    doc = Doc()
    if 'emsg_rewritten' in record:
        doc.println(record['emsg_rewritten'], bold=True)
        doc.println(record['emsg'], color='#888888')
    else:
        doc.println(record['emsg'])
        doc.println(record['_epat'], color='#888888')
    # print(record)
    if '_stacks' in record:
        for stack in record['_stacks'][::-1]:  # 逆順に
            if '-packages' in stack['filename']:
                continue
            doc.append(stack['_doc'])
    else:
        doc.append(record['_doc'])
    doc.add_button('@diagnosis', 'どうしたらいいの？')
    doc.add_button('@fix_code', '直してみて')

    # doc.add_button('@xcall', '先生を呼んで')
    return doc


_HIRA_PAT = re.compile('[あ-を]')


def is_kogi_call(record):
    if record.get('etype') == 'NameError':
        eparams = record['_eparams']
        return re.search(_HIRA_PAT, eparams[0])
    return False


def catch_and_start_kogi(exc_info=None, code: str = None, context: dict = None, exception=None, enable_dialog=True):
    if exc_info is None:
        exc_info = sys.exc_info()
    record = kogi_exc(code=code, exc_info=exc_info,
                      caught_ex=exception, translate=translate)
    if is_kogi_call(record):
        msg = record['_eparams'][0][1:-1]
        debug_print(msg)
        call_and_start_kogi([msg], code)
        return

    record_log(type='error2', **record)
    messages = error_message(record)
    if context:
        record.update(context)
    _DefaultChatbot.update(record)
    start_dialog(_DefaultChatbot, start=messages)
