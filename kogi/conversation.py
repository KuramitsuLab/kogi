import sys
from IPython import get_ipython

from .service import (
    model_generate, translate, isEnglishDemo, slack_send
)

from .ui import google_colab

if google_colab:
    from .ui.dialog_colab import display_dialog
else:
    try:
        import ipywidgets
        from .ui.dialog_ipywidgets import display_dialog
    except ModuleNotFoundError:
        from .ui.dialog_colab import display_dialog

from .liberr import kogi_exc
from .render import Doc, encode_md

_ICON = {
    '@robot': ('システム', 'robot-fs8.png'),
    '@ta': ('TA', 'ta-fs8.png'),
    '@kogi': ('コギー', 'kogi-fs8.png'),
    '@you': ('あなた', 'girl-fs8.png'),
}


def get_icon(tag):
    return _ICON.get(tag, _ICON['@kogi'])


class ConversationAI(object):
    slots: dict
    records: list

    def __init__(self, slots=None):
        self.slots = slots or {}
        self.records = []

    def get(self, key, value):
        return self.slots.get(key, value)

    def update(self, context: dict):
        if context:
            self.slots = context
        else:
            self.slots = {}

    def exec(self, prompt):
        return ''

    def ask(self, input_text):
        output_text = self.response(input_text)
        self.records.append((input_text, output_text))
        # output_text = cc(output_text)
        return output_text

    def response(self, user_input):
        response_text = model_generate(user_input)
        if response_text is None:
            return 'ZZ.. zzz.. 眠む眠む..'
        return [response_text]*3

    def record(self, input_text, message):
        response_id = len(self.records)
        message['response_id'] = response_id
        self.records.append((input_text, message))

    def get_record(self, response_id):
        return self.records[response_id]

    def ask_message(self, input_text):
        messages = self.response_message(input_text)
        if isinstance(messages, list):
            for message in messages:
                self.record(input_text, message)
        else:
            self.record(input_text, messages)
        return messages

    def response_message(self, input_text):
        ms = self.response(input_text)
        if isinstance(ms, list) or isinstance(ms, tuple):
            return [self.messagefy(m) for m in ms]
        return self.messagefy(self.response(input_text))

    def messagefy(self, message, tag=None, name='コギー', icon='kogi-fs8.png'):
        if isinstance(message, str):
            if message.startswith('@'):
                tag, _, text = message.partition(':')
                message = dict(text=text)
            else:
                message = dict(text=message)
        elif isinstance(message, Doc):
            message, tag = message.get_message2(tag)
        elif not isinstance(message, dict):
            message = dict(text=str(message))
        name, icon = get_icon(tag)
        if 'name' not in message:
            message['name'] = name
        if 'icon' not in message:
            message['icon'] = icon
        if 'html' not in message:
            message['html'] = encode_md(message['text'])
        return message


_DefaultChatbot = ConversationAI()


def set_chatbot(chatbot):
    global _DefaultChatbot
    _DefaultChatbot = chatbot


def call_and_start_kogi(actions, code: str = None, context: dict = None):
    for user_text in actions:
        _DefaultChatbot.update(context)
        # print('@', actions)
        messages = _DefaultChatbot.ask_message(user_text)
        # print('@@', messages)
        display_dialog(_DefaultChatbot, messages)
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
        for stack in record['_stacks']:
            if '-packages' in stack['filename']:
                continue
            doc.append(stack['_doc'])
    else:
        doc.append(record['_doc'])
    doc.add_button('@diagnosis', 'どうしたらいいの？')
    doc.add_button('@fix_code', '直してみて')
    #doc.add_button('@xcall', '先生を呼んで')
    return doc


def catch_and_start_kogi(exc_info=None, code: str = None, context: dict = None, exception=None, enable_dialog=True):
    if exc_info is None:
        exc_info = sys.exc_info()
    record = kogi_exc(code=code, exc_info=exc_info,
                      caught_ex=exception, translate=translate)
    messages = error_message(record)
    if context:
        record.update(context)
    _DefaultChatbot.update(record)
    display_dialog(_DefaultChatbot, start=messages)
