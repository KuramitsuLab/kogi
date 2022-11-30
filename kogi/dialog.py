import sys
import traceback
from IPython import get_ipython

from .settings import (
    model_generate, translate_en, translate_ja,
    send_slack, kogi_get, kogi_log, kogi_print
)

from .diagnosis import run_diagnosis
from .dialog_desc import get_desc

from .ui import Conversation, google_colab

if google_colab:
    from .ui.dialog_colab import display_dialog
else:
    try:
        import ipywidgets
        from .ui.dialog_ipywidgets import display_dialog
    except ModuleNotFoundError:
        from .ui.dialog_colab import display_dialog

from .liberr import kogi_print_exc, replace_eparams
from .logger import add_lazy_logger

import kogi.fake_nlp as nlp

MODULES = [
    ('math.', 'import math'),
    ('os.', 'import os'),
    ('sys.', 'import sys'),
    ('collections.', 'import collections'),
    ('time.', 'import time'),
    ('datetime.', 'import datetime'),
    ('random.', 'import random'),
    ('np.', 'import numpy as np'),
    ('plt.', 'import matplotlib.pyplot as plt'),
    ('pd.', 'import pandas as pd'),
]


def check_module(code):
    for module, todo in MODULES:
        if code.startswith(module):
            return f'<tt>{todo}</tt> してから、'
    return ''


def response_codegen(text: str):
    response = model_generate(text)
    if response is None:
        return 'kogi.set(...)を再実行しよう'
    code = response.replace('<nl>', '\n').replace('<tab>', '    ')
    return check_module(code) + f'<pre>{code}</pre>'


def response_hint(slots: dict):
    if 'ekey' in slots and 'eparams' in slots:
        ekey = slots['ekey']
        eparams = ' '.join(slots['eparams'])
        eline = slots.get('eline', '')
        text = f'{ekey}<tab>{eparams}<tab>{eline}'
        ans = model_generate(text)
        if ans:
            # kogi_print(ans, slots['eparams'])
            return replace_eparams(ans, slots['eparams'])
            # return f'{ans}<br>{translate_ja(ans)}'
    return None


def response_talk(text: str):
    response = model_generate(f'talk: {text}')
    if response is None:
        return 'ZZ.. zzz.. 眠む眠む..'
    return response


def response_desc(text: str):
    response = get_desc(text)
    if response is None:
        return response_talk(text)
    return response


class Chatbot(Conversation):

    def response(self, user_input):
        text = user_input
        if 'user_inputs' not in self.slots:
            self.slots['user_inputs'] = []
        self.slots['user_inputs'].append(text)
        # if nlp.startswith(text, ('質問')):
        #     return self.response_question(text)
        text = nlp.normalize(user_input)
        # if nlp.startswith(text, ('デバッグ', '助けて', 'たすけて', '困った', '分析', '調べて')):
        #     if 'fault_vars' in self.slots:
        #         return self.slots['fault_vars']
        #     else:
        #         return 'コギーも助けて...'
        if text.endswith('には'):
            text = text[:-2]
            return response_codegen(text)
        if text.endswith('たい'):
            text = nlp.remove_tai(text)
            return response_codegen(text)
        if text.endswith('って') or text.endswith('とは'):
            text = text[:-2]
            return response_desc(text)
        if nlp.startswith(text, ('原因', '理由', 'なぜ', 'なんで', 'どう')):
            response = response_hint(self.slots)
            if response is None:
                if 'reason' in self.slots:
                    return self.slots['reason']
                if 'solution' in self.slots:
                    return self.slots['solution']
                if 'maybe' in self.slots:
                    return 'ひょっとしたら、' + self.slots['maybe']
                if 'ekey' in self.slots:
                    return 'エラーメッセージを検索してみたら？'
                return 'エラーなくない？'
            return response
        if nlp.startswith(text, ('ヒント', '助けて', 'たすけて')):
            if 'hint' in self.slots:
                return self.slots['hint']
            else:
                return 'ヒントなし'
        return response_talk(text)


global_slots = {
    'bot_name': 'コギー',
    'your_name': 'あなた',
}

def set_global_slots(**kwargs):
    for key, value in kwargs.items():
        global_slots[key] = value


PREV_CHAT = None
CHAT_CNT = 0


def record_dialog():
    global PREV_CHAT, CHAT_CNT
    if PREV_CHAT is None:
        return
    chat = PREV_CHAT
    PREV_CHAT = None
    CHAT_CNT += 1
    user = kogi_get('name', 'ユーザ')
    data = {'type': 'kogi_chat'}
    data.update(chat.slots)
    data['chat'] = chat.records
    kogi_log('kogi_chat', right_now=True, **data)
    # Slack レポート
    lines = [f'*{user}({CHAT_CNT})より*']
    if 'code' in data:
        lines.extend(['```', data['code'], '```'])
    if 'emsg' in data:
        lines.extend([data['emsg'], ''])
    if 'start' in data:
        lines.extend([data['start']])
    #print(chat.records, data)
    if len(chat.records) > 0:
        for user_text, bot_text in chat.records:
            lines.extend([f'> {user_text}', bot_text])
    send_slack('\n'.join(lines))


add_lazy_logger(record_dialog)


def start_dialog(slots: dict):
    global PREV_CHAT
    record_dialog()
    dialog_slots = global_slots.copy()
    dialog_slots.update(slots)
    dialog_slots['your_name'] = kogi_get('name', 'あなた')
    if 'start' not in dialog_slots:
        dialog_slots['start'] = dialog_slots.get('translated', 'おはよう')
    PREV_CHAT = Chatbot(slots=dialog_slots)
    display_dialog(PREV_CHAT, dialog_slots['start'])
    return PREV_CHAT

def kogi_ask(text:str):
    global PREV_CHAT
    if PREV_CHAT is not None:
        print(PREV_CHAT.ask(text))

def kogi_catch(exc_info=None, code: str = None, context: dict = None, exception=None, enable_dialog=True):
    if exc_info is None:
        exc_info = sys.exc_info()
    slots = kogi_print_exc(code=code, exc_info=exc_info, caught_ex=exception, translate_en=translate_en)
    if context is not None:
        slots.update(context)
    run_diagnosis(slots)
    if enable_dialog:
        start_dialog(slots)

## 

class Chatbot2(Conversation):

    def response(self, user_input):
        text = user_input
        if 'user_inputs' not in self.slots:
            self.slots['user_inputs'] = []
        self.slots['user_inputs'].append(text)
        response = model_generate(text)
        if response is None:
            return 'ZZ.. zzz.. 眠む眠む..'
        return response

CHATBOT = Chatbot2()

def start_dialog2(context: dict):
    display_dialog(CHATBOT)


def call_and_start_dialog(actions):
    for say in actions:
        CHATBOT.ask(say)


if __name__ == '__main__':
    start_dialog({})
