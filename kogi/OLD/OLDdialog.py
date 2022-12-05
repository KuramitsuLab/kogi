import traceback
from .content import ICON

# from kogi.settings import translate_ja, isEnglishDemo
# def cc(text):
#     if isEnglishDemo():
#         if len(text)==0:
#             return text
#         n_ascii = sum(1 for c in text if ord(c) < 128)
#         #print(text, n_ascii, len(text), n_ascii / len(text))
#         if (n_ascii / len(text)) < 0.4:  # 日本語
#             t = translate_ja(text)
#             # print(t)
#             if t is not None:
#                 return f'{text}<br><i>{t}</i>'
#     return text

# def htmlfy(text):
#     if isinstance(text, list):
#         text = '<br>'.join(cc(line) for line in text)
#     else:
#         text = cc(text)
#     return text


# DIALOG_BOT_HTML = '''
# <div class="sb-box">
#     <div class="icon-img icon-img-left">
#         <img src="{icon}" width="60px">
#     </div>
#     <div class="icon-name icon-name-left">{name}</div>
#     <div class="sb-side sb-side-left">
#         <div class="sb-txt sb-txt-left">{text}</div>
#     </div>
# </div>
# '''

# def htmlfy_bot(chat, text):
#     return DIALOG_BOT_HTML.format(
#         icon=ICON(chat.get('bot_icon', 'kogi-fs8.png')),
#         name=chat.get('bot_name', 'コギー'),
#         text=htmlfy(text)
#     )



# DIALOG_USER_HTML = '''
# <div class="sb-box">
#     <div class="icon-img icon-img-right">
#         <img src="{icon}" width="60px">
#     </div>
#     <div class="icon-name icon-name-right">{name}</div>
#     <div class="sb-side sb-side-right">
#         <div class="sb-txt sb-txt-right">{text}</div>
#     </div>
# </div>
# '''

# def htmlfy_user(chat, text):
#     return DIALOG_USER_HTML.format(
#         icon=ICON(chat.get('user_icon', 'girl_think-fs8.png')),
#         name=chat.get('name', 'あなた'),
#         text=htmlfy(text)
#     )
    

# _DIALOG_ID = 0

class Conversation(object):
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
        output_text = cc(output_text)
        return output_text

    def response(self, input_text):
        return 'わん'

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


