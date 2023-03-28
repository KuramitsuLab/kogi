from .ui._google import google_colab
from .ui.render import Doc
from .liberr import kogi_exc
from .ui.message import display_dialog, append_message
import traceback
import re
import sys
from IPython import get_ipython

from .service import (
    translate,
    record_log, debug_print
)


def model_prompt(prompt):
    return 'ほげ', 3


class ChatAI(object):
    slots: dict
    chats: dict

    def __init__(self, slots=None):
        self.slots = slots or {}
        self.chats = {}

    def get(self, key, value):
        return self.slots.get(key, value)

    def update(self, context: dict):
        self.chats = {}
        if context:
            self.slots = dict(context)
        else:
            self.slots = {}

    def record(self, task, input_text, output_text):
        rec_id = len(self.records)
        self.records.append((task, input_text, output_text))
        return rec_id

    def prompt(self, prompt):
        if '@error_hint' in prompt:
            return self.error_hint(self.slots['emsg'], self.slots['eline'])
        if '@fix_code' in prompt:
            return self.fix_code(self.slots['emsg'], self.slots['code'])
        return self.dialog(prompt)

    def dialog(self, input_text):
        prompt = input_text
        response, tokens = model_prompt(prompt)
        rec_id = record_log(type='prompt_dialog',
                            prompt=prompt, response=response, tokens=tokens)
        self.chats[rec_id] = (prompt, response)
        return response, rec_id

    def error_hint(self, emsg, eline):
        prompt = f'コード`{eline}`で、`{emsg}`というエラーが出た。どうしたら良いの？'
        response, tokens = model_prompt(prompt)
        rec_id = record_log(type='prompt_error_hint',
                            prompt=prompt, response=response, tokens=tokens,
                            emsg=emsg, eline=eline)
        self.chats[rec_id] = (prompt, response, (emsg, eline))
        return response, rec_id

    def fix_code(self, emsg, code):
        prompt = f'`{emsg}`というエラーが出た。`{code}`を修正してください。'
        response, tokens = model_prompt(prompt)
        rec_id = record_log(type='prompt_fix_code',
                            prompt=prompt, response=response, tokens=tokens,
                            emsg=emsg, eline=code)
        self.chats[rec_id] = (prompt, response, (emsg, code))
        return response, rec_id

    def likeit(self, rec_id, score):
        if rec_id in self.chats:
            prompt, response, data = self.chats[rec_id]
            record_log(type='likeit', rec_id=rec_id, score=score,
                       prompt=prompt, response=response, data=data)


_DefaultChatbot = ChatAI()


def set_chatbot(chatbot):
    global _DefaultChatbot
    _DefaultChatbot = chatbot


def start_dialog(bot, start='', height=None, placeholder='質問はこちらに'):
    target = display_dialog(start, height, placeholder)

    def display_user(doc):
        nonlocal target
        append_message(doc, target, mention='@you')

    def display_bot_single(doc):
        nonlocal target
        append_message(doc, target)

    def display_bot(doc):
        if isinstance(doc, list):
            for d in doc:
                display_bot_single(d)
        else:
            display_bot_single(doc)

    if google_colab:
        def ask(user_text):
            nonlocal bot
            try:
                if isinstance(user_text, str):
                    user_text = user_text.strip()
                debug_print(user_text)
                display_user(user_text)
                doc, rec_id = bot.prompt(user_text)
                doc = Doc.md(doc)
                doc.add_likeit(rec_id)
                display_bot(doc)
            except:
                traceback.print_exc()
                display_bot('@robot:バグで処理に失敗しました。ごめんなさい')

        def like(docid, score):
            nonlocal bot
            try:
                debug_print(docid, score)
                bot.likeit(docid, score)
            except:
                traceback.print_exc()
                display_bot('@robot:バグで処理に失敗しました。ごめんなさい')

        # def say(prompt, text):
        #     nonlocal bot
        #     try:
        #         debug_print(text, prompt)
        #         display_user(text)
        #         doc = bot.exec(prompt)
        #         display_bot(doc)
        #     except:
        #         traceback.print_exc()
        #         display_bot('@robot:バグで処理に失敗しました。ごめんなさい')

        google_colab.register_callback('notebook.ask', ask)
        google_colab.register_callback('notebook.like', like)
        if start != '':
            ask(start)
    return target


def call_and_start_kogi(actions, code: str = None, context: dict = None):
    for user_text in actions:
        _DefaultChatbot.update(context)
        # doc = _DefaultChatbot.ask(user_text)
        start_dialog(_DefaultChatbot, user_text)
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
    doc.add_button('@error_hint', 'どうしたらいいの？')
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
