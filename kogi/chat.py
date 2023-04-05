from .ui._google import google_colab
from .ui.render import Doc
from .liberr import kogi_exc
from .ui.message import display_dialog, append_message
import traceback
import re
import sys
from IPython import get_ipython

from .service import (
    translate, model_prompt, kogi_get,
    record_log, debug_print
)


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
        self.slots['assistant'] = None

    def record(self, task, input_text, output_text):
        rec_id = len(self.records)
        self.records.append((task, input_text, output_text))
        return rec_id


    def prompt(self, prompt):
        # 将来は分類モデルに置き換える
        if 'どうしたら' in prompt or 'どしたら' in prompt:
            if 'emsg' not in self.slots:
                return '@kogi:何をしたいの？'
            return self.error_hint(prompt)
        if '直して' in prompt or 'たすけて' in prompt or '助けて' in prompt:
            if 'emsg' not in self.slots:
                return '@kogi:何を？？'
            return self.fix_code(self.slots['code'])
        if prompt.startswith('+') or prompt.startswith('＋'):
            prompt = prompt[1:]
            if 'again' in self.slots:
                return self.dialog_again(prompt)
        return self.dialog(prompt)

    def no_response(self):
        return '@robot:ChatGPTが反応しないんだけど..'

    def dialog(self, input_text):
        prompt = input_text
        response, tokens = model_prompt(prompt)
        if response == '':
            return self.no_response()
        rec_id = record_log(type='prompt_dialog',
                            prompt=prompt, response=response, tokens=tokens)
        self.chats[rec_id] = (prompt, response, ('dialog', input_text))
        self.slots['again'] = ('', prompt, response)
        return response, rec_id

    def dialog_again(self, input_text):
        if 'again' in self.slots:
            context, prompt, response = self.slots['again']
        response, tokens = model_prompt(prompt, context=context, post_prompt=input_text)
        if response == '':
            return self.no_response()
        prompt=f'{context}\n{prompt}\n{input_text}'
        rec_id = record_log(type='prompt_again',prompt=prompt, response=response, tokens=tokens)
        self.chats[rec_id] = (prompt, response, ('dialog_again', input_text))
        #self.slots['again'] = ('', prompt, response)
        return response, rec_id


    def get_context(self, include_eline=False, include_code=False):
        ss=[]
        if 'emsg' in self.slots:
            emsg = self.slots['emsg']
            ss.append(f'エラーの発生: {emsg}')
        if include_eline and 'eline' in self.slots:
            eline = self.slots['eline']
            ss.append(f'エラーの発生した行: {eline}')
        if include_code and 'code' in self.slots:
            ss.append('コード:')
            ss.append('```')
            for line in self.slots['code'].splitlines():
                if '"' in line or "'" in line:
                    ss.append(line)
                else:
                    line, _, _ = line.partition('#')
                    ss.append(line)
            ss.append('```')
        return '\n'.join(ss)

    def error_hint(self, prompt):
        emsg = self.slots['emsg']
        eline = self.slots['eline']
        context = self.get_context(include_eline=True)
        prompt = '原因と解決のヒントを簡単に説明してください。'
        response, tokens = model_prompt(prompt, context=context)
        if response == '':
            return self.no_response()
        rec_id = record_log(type='prompt_error_hint',
                            prompt=prompt, response=response, tokens=tokens,
                            emsg=emsg, eline=eline)
        self.chats[rec_id] = (prompt, response, ('error_hint', emsg, eline))
        self.slots['again'] = (context, prompt, response)
        return response, rec_id

    def fix_code(self, code):
        emsg = self.slots['emsg']
        code = self.slots['code']
        if len(code) > 512:
            return '@kogi:直すべきコードがちょっと長すぎるね', 0
        context = self.get_context(include_code=True)
        prompt = f'上記のコードを修正してください。'
        response, tokens = model_prompt(prompt, context=context)
        if response == '':
            return self.no_response()
        rec_id = record_log(type='prompt_fix_code',
                            prompt=prompt, response=response, tokens=tokens,
                            emsg=emsg, code=code)
        self.chats[rec_id] = (prompt, response, ('fix_code', emsg, code))
        self.slots['again'] = (context, prompt, response)
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
    height = kogi_get('height', height)
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
        # if start != '':
        #     ask(start)
    return target


def call_and_start_kogi(actions, code: str = None, context: dict = None):
    for user_text in actions:
        _DefaultChatbot.update(context)
        doc, rec_id = _DefaultChatbot.dialog(user_text)
        doc = Doc.md(doc)
        doc.add_likeit(rec_id)
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
    # doc.add_button('@error_hint', 'どうしたらいいの？')
    # doc.add_button('@fix_code', '直してみて')
    # doc.add_button('@xcall', '先生を呼んで')
    return doc


# _HIRA_PAT = re.compile('[あ-を]')


# def is_kogi_call(record):
#     if record.get('etype') == 'NameError':
#         eparams = record['_eparams']
#         return re.search(_HIRA_PAT, eparams[0])
#     return False


def catch_and_start_kogi(exc_info=None, code: str = None, context: dict = None, exception=None, enable_dialog=True):
    if exc_info is None:
        exc_info = sys.exc_info()
    record = kogi_exc(code=code, exc_info=exc_info,
                      caught_ex=exception, translate=translate)
    # if is_kogi_call(record):
    #     msg = record['_eparams'][0][1:-1]
    #     debug_print(msg)
    #     call_and_start_kogi([msg], code)
    #     return

    record_log(type='error', **record)
    messages = error_message(record)
    if context:
        record.update(context)
    _DefaultChatbot.update(record)
    start_dialog(_DefaultChatbot, start=messages)
