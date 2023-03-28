from kogi.service import *
from ..OLDconversation import ConversationAI, set_chatbot
from .common import status_message
from .all import run_prompt


class MultitaskAI(ConversationAI):

    def response(self, input_text):
        tag, generated_text = self.generate_transform(input_text)
        # debug_print(input_text, tag, generated_text)
        if tag.startswith('<status>'):
            return status_message(generated_text)
        self.record('@model', input_text, f'{tag}{generated_text}')
        kwargs = dict(user_input=input_text,
                      generated_text=generated_text, **self.slots)
        if tag.startswith('<コード'):
            return run_prompt(self, '@translated_code', kwargs)
        if tag.startswith('<コマンド'):
            debug_print('TODO', tag, generated_text)
            return run_prompt(self, generated_text, kwargs)
        return generated_text


set_chatbot(MultitaskAI())
