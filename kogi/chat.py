from .ui._google import google_colab
from .ui.render import Doc
from .liberr import kogi_exc
from .ui.message import display_dialog, append_message
import re
import sys
import traceback
import time
from IPython import get_ipython

from .service import (
    translate, model_prompt, kogi_get,
    record_log, debug_print
)

def remove_comment(code):
    ss = []
    for line in code.splitlines():
        if '"' in line or "'" in line:
            ss.append(line)
        else:
            line, _, _ = line.partition('#')
            ss.append(line)
    return '\n'.join(ss)


class ChatAI(object):
    slots: dict
    chats: dict

    def __init__(self, slots=None):
        self.slots = slots or {}
        self.chats = {}
        self.face_icon = '@kogi_plus'
        self.prev_time = time.time()

    def get(self, key, value):
        return self.slots.get(key, value)

    def update(self, context: dict):
        if context:
            self.slots = dict(context)
        else:
            self.slots = {}
        self.slots['rec_id'] = None

    def difftime(self):
        t = time.time()
        diff = int(t - self.prev_time)
        self.prev_time = t
        return diff

    # def record(self, task, input_text, output_text):
    #     rec_id = len(self.records)
    #     self.records.append((task, input_text, output_text))
    #     return rec_id

    def likeit(self, rec_id, score):
        if rec_id in self.chats:
            context, prompt, response, data = self.chats[rec_id]
            record_log(type='likeit', rec_id=rec_id, score=score,
                       context=context, prompt=prompt, response=response, data=data)
        self.slots['rec_id'] = None

    def face(self, text):
        return f'{self.face_icon}:{text}'

    def prompt(self, input_text, **kwargs):
        if self.slots['rec_id'] is not None:
            self.likeit(self.slots['rec_id'], 0)
            self.face_icon = '@kogi_minus'
        else:
            self.face_icon = '@kogi_plus'
        # 将来は分類モデルに置き換える
        if input_text == '直して' or 'コード' in input_text:
            kwargs['include_code'] = True
        if 'エラー' in input_text or 'どうしたら' in input_text:
            if 'eline' in self.slots:
                kwargs['include_eline'] = True
            else:
                kwargs['include_code'] = True
        if len(input_text) < 7: #コードを直して
            kwargs['detailed'] = True
        return self.dialog_with_context(input_text, **kwargs)

    def no_response(self):
        return 'AIが反応しない..'

    def get_context(self, **kwargs):
        ss = []
        if kwargs.get('include_code', False) and 'code' in self.slots:
            ss.append('コード:')
            ss.append('```')
            ss.append(remove_comment(self.slots['code']))
            ss.append('```')
        if 'emsg' in self.slots:
            emsg = self.slots['emsg']
            ss.append(f'発生したエラー: {emsg}')
        if kwargs.get('include_eline', False) and 'eline' in self.slots:
            eline = self.slots['eline']
            ss.append(f'エラーの発生した行: {eline}')
        if 'prev_input_text' in self.slots and kwargs.get('detailed', False):
            ss.append(self.slots['prev_input_text'])
        return '\n'.join(ss)

    def dialog_with_context(self, input_text, **kwargs):
        prompt = input_text
        context = self.get_context(**kwargs)
        response, tokens = model_prompt(prompt, context=context)
        if response == '':
            return self.no_response()
        self.slots['prev_input_text'] = input_text
        rec_id = record_log(type='prompt', prompt_type='auto', difftime=self.difftime(),
                            input_text=input_text,
                            context=context, prompt=prompt, response=response, tokens=tokens)
        self.chats[rec_id] = (context, prompt, response,
                              ('dialog_request', input_text, kwargs))
        self.slots['rec_id'] = rec_id
        return self.face(response), rec_id


_DefaultChatbot = ChatAI()


def set_chatbot(chatbot):
    global _DefaultChatbot
    _DefaultChatbot = chatbot


LIKEIT = [0, 0]


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
            global LIKEIT
            nonlocal bot
            try:
                if isinstance(user_text, str):
                    user_text = user_text.strip()
                debug_print(user_text)
                display_user(user_text)
                doc, rec_id = bot.prompt(user_text)
                doc = Doc.md(doc)
                doc.add_likeit(
                    rec_id, like=f'👍{LIKEIT[1]}', dislike=f'👎{LIKEIT[0]}')
                display_bot(doc)
            except:
                traceback.print_exc()
                display_bot('@robot:バグで処理に失敗しました。ごめんなさい')

        def like(docid, score):
            global LIKEIT
            nonlocal bot
            try:
                # debug_print(docid, score)
                bot.likeit(docid, score if score > 0 else -1)
                LIKEIT[score] += 1
            except:
                traceback.print_exc()
                display_bot('@robot:バグで処理に失敗しました。ごめんなさい')

        google_colab.register_callback('notebook.ask', ask)
        google_colab.register_callback('notebook.like', like)
        # if start != '':
        #     ask(start)
    return target


def call_and_start_kogi(actions, code: str = None, context: dict = None):
    for user_text in actions:
        _DefaultChatbot.update(context)
        _DefaultChatbot.slots['code']=code
        code = remove_comment(code)
        doc, rec_id = _DefaultChatbot.prompt(user_text, include_code=len(code) > 0)
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
    doc.set_mention('@kogi_minus')
    return doc


_HIRA_PAT = re.compile('[あ-を]')


def is_direct_kogi_call(record):
    if record.get('etype') == 'NameError':
        eparams = record['_eparams']
        return re.search(_HIRA_PAT, eparams[0])
    return False


def catch_and_start_kogi(exc_info=None, code: str = None, context: dict = None, exception=None, enable_dialog=True):
    if exc_info is None:
        exc_info = sys.exc_info()
    record = kogi_exc(code=code, exc_info=exc_info,
                      caught_ex=exception, translate=translate)
    if is_direct_kogi_call(record):
        msg = record['_eparams'][0][1:-1]
        debug_print(msg)
        call_and_start_kogi([msg], code)
        return

    record_log(type='error', **record)
    messages = error_message(record)
    if context:
        record.update(context)
    _DefaultChatbot.update(record)
    start_dialog(_DefaultChatbot, start=messages)
