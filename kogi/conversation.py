import sys
from IPython import get_ipython

from .settings import (
    model_generate, translate_en, translate_ja,
    isEnglishDemo, send_slack, kogi_get, kogi_log, kogi_print
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

from .liberr import kogi_print_exc, replace_eparams

def english_subtitle(text):
    if isEnglishDemo():
        if len(text)==0:
            return text
        n_ascii = sum(1 for c in text if ord(c) < 128)
        #print(text, n_ascii, len(text), n_ascii / len(text))
        if (n_ascii / len(text)) < 0.4:  # 日本語
            t = translate_ja(text)
            # print(t)
            if t is not None:
                return f'{text}<br><i>{t}</i>'
    return text


class ConversationAI(object):
    slots: dict
    records: list

    def __init__(self, slots=None):
        # global _DIALOG_ID
        # self.cid= _DIALOG_ID
        # DIALOG_ID += 1
        self.slots = slots or {}
        self.records = []

    def get(self, key, value):
        return self.slots.get(key, value)

    def update(self, context: dict):
        return self.slots.update(context)

    def ask(self, input_text):
        output_text = self.response(input_text)
        self.records.append((input_text, output_text))
        # output_text = cc(output_text)
        return output_text

    def response(self, user_input):
        response_text = model_generate(user_input)
        if response_text is None:
            return 'ZZ.. zzz.. 眠む眠む..'
        return response_text

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
        return self.messagefy(self.response(input_text), is_user=False)

    def messagefy(self, message, is_user=False):
        if isinstance(message, str):
            message = dict(text=message)
        if is_user:
            if 'name' not in message:
                message['name'] = 'あなた'
            if 'icon' not in message:
                message['icon'] = 'girl_think-fs8.png'
        else:
            if 'name' not in message:
                message['name'] = 'コギー'
            if 'icon' not in message:
                message['icon'] = 'kogi-fs8.png'
        if 'html' not in message:
            # message['html'] = #htmlfy(message['text'])
            message['html'] = message['text']
        return message




class Chatbot(ConversationAI):



_DefaultChatbot = ConversationAI()

def set_chatbot(chatbot):
    global _DefaultChatbot
    _DefaultChatbot = chatbot
    

def call_and_start_dialog(actions):
    for user_text in actions:
        #_DefaultChatbot.update(context)
        messages = _DefaultChatbot.ask_message(user_text)
        display_dialog(_DefaultChatbot, messages)
        return 


def catch_and_start_dialog(exc_info=None, code: str = None, context: dict = None, exception=None, enable_dialog=True):
    if exc_info is None:
        exc_info = sys.exc_info()
    slots = kogi_print_exc(code=code, exc_info=exc_info, caught_ex=exception, translate_en=translate_en)
    if context is not None:
        slots.update(context)
    if enable_dialog:
        start = slots.get('translated', 'おはよう')
        _DefaultChatbot.update(slots)
        if context is not None:
            _DefaultChatbot.update(context)
        display_dialog(_DefaultChatbot, start)
