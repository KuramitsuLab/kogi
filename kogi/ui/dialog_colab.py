import traceback
from ._google import google_colab

from kogi.service import debug_print
from .message import display_dialog, append_message

# <div id="{target}" class="box" style="height: {height}px"></div>


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
                user_text = user_text.strip()
                debug_print(user_text)
                display_user(user_text)
                doc = bot.ask(user_text)
                display_bot(doc)
            except:
                traceback.print_exc()
                display_bot('@robot:バグで処理に失敗しました。ごめんなさい')

        def like(docid, score):
            nonlocal bot
            try:
                debug_print(docid, score)
                bot.log_likeit(docid, score)
            except:
                traceback.print_exc()
                display_bot('@robot:バグで処理に失敗しました。ごめんなさい')

        def say(prompt, text):
            nonlocal bot
            try:
                debug_print(text, prompt)
                display_user(text)
                doc = bot.exec(prompt)
                display_bot(doc)
            except:
                traceback.print_exc()
                display_bot('@robot:バグで処理に失敗しました。ごめんなさい')

        google_colab.register_callback('notebook.ask', ask)
        google_colab.register_callback('notebook.like', like)
        google_colab.register_callback('notebook.say', say)
    return target
