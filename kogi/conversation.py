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
from .render import Render


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
            if len(ms) == 3:
                return [
                    self.messagefy(ms[0], name='コギー', icon='kogi-fs8.png'),
                    self.messagefy(ms[1], name='ぱんち', icon='pan-fs8.png'),
                    self.messagefy(ms[2], name='OpenAI',
                                   icon='openai-fs8.png'),
                ]
            return [self.messagefy(m) for m in ms]
        return self.messagefy(self.response(input_text))

    def messagefy(self, message, name='コギー', icon='kogi-fs8.png'):
        if isinstance(message, str):
            message = dict(text=message)
        if 'name' not in message:
            message['name'] = name
        if 'icon' not in message:
            message['icon'] = icon
        if 'html' not in message:
            message['html'] = message['text']
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
    r = Render()
    if 'emsg_rewritten' in record:
        r.println(record['emsg_rewritten'], bold=True)
        r.println(record['emsg'], color='#888888')
    else:
        r.println(record['emsg'])
        r.println(record['_epat'])
    # print(record)
    if '_stacks' in record:
        for stack in record['_stacks']:
            if '-packages' in stack['filename']:
                continue
            r.extend(stack, div='<pre>{}</pre>')
    else:
        r.extend(record, div='<pre>{}</pre>')
    r.appendHTML('<button onlick="say(\'@diagnosis\')">どうしたらいいの？</button>')
    return r.get_message()


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
