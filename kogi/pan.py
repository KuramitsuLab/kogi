from kogi.service import *
from .conversation import ConversationAI, set_chatbot

kogi_set(
    model_id='myst7725/codepan1117_IN3'
)


def extract_tag(text):
    if text.startswith('<'):
        tag, end_tag, text = text.partition('>')
        return tag+end_tag, text
    return '', text


class PanAI(ConversationAI):
    def response(self, user_input):
        response_text = model_generate(user_input)
        if response_text is None:
            return 'ZZ.. zzz.. 眠む眠む..'
        tag, text = extract_tag(response_text)
        return text
