import traceback
from ._google import google_colab

from kogi.service import debug_print
from .message import display_dialog, append_message

# <div id="{target}" class="box" style="height: {height}px"></div>

"""
if google_colab:
    _DIALOG_HTML = '''\
<div id="dialog">
    <div id="{target}" class="box" style="height: {height}px"></div>
    <div style="text-align: right"><textarea id="input" placeholder="{placeholder}"></textarea></div>
</div>'''
else:
    _DIALOG_HTML = '''\
<div id="dialog">
    <div id="{target}" class="box" style="height: {height}px"></div>
</div>'''


def display_dialog_js():
    display(JS('dialog.js'))


def display_main(target, placeholder=''):
    data = dict(
        script=JS('dialog.js'),
        placeholder=placeholder,
        target=target,
        height=kogi_get('dialog_height', 300)
    )
    display(HTML(CSS('dialog.css') + _DIALOG_HTML.format(**data)))


_DIALOG_ID = 1

###
APPEND_JS = '''
<script>
var target = document.getElementById('{target}');
var content = `{html}`;
if(target !== undefined) {{
    target.insertAdjacentHTML('beforeend', content);
    target.scrollTop = target.scrollHeight;
}}
</script>
'''


def display_talk(html, dialog_target=None):

    if dialog_target:
        html = html.replace('\\', '\\\\')
        html = html.replace('`', '\\`')
        display(HTML(APPEND_JS.format(target=dialog_target, html=html)))
    else:
        display(HTML(CSS('dialog.css') + html))


def display_dialog(bot, start=None, placeholder='質問はこちらに'):
    global _DIALOG_ID
    target = f'output{_DIALOG_ID}'
    _DIALOG_ID += 1
    display_main(target, placeholder)

    def display_user(message):
        nonlocal target
        message = messagefy(message, tag='@you')
        display_talk(htmlfy_message(message), target)

    def display_bot_single(message):
        nonlocal target
        message = messagefy(message)
        display_talk(htmlfy_message(message), target)

    def display_bot(messages):
        if isinstance(messages, list):
            for message in messages:
                display_bot_single(message)
        else:
            display_bot_single(messages)

    if google_colab:
        def ask(user_text):
            nonlocal bot
            try:
                user_text = user_text.strip()
                display_user(user_text)
                messages = bot.ask(user_text)
                display_bot(messages)
            except:
                display_bot('@robot:バグで処理に失敗しました。ごめんなさい')
                traceback.print_exc()

        def like(docid, score):
            nonlocal bot
            try:
                debug_print(docid, score)
                bot.log_likeit(docid, score)
            except:
                display_bot('@robot:バグで処理に失敗しました。ごめんなさい')
                traceback.print_exc()

        def say(prompt, text):
            nonlocal bot
            try:
                display_user(text)
                messages = bot.exec(prompt)
                display_bot(messages)
            except:
                display_bot('バグで処理に失敗しました。ごめんなさい')
                traceback.print_exc()
        google_colab.register_callback('notebook.ask', ask)
        google_colab.register_callback('notebook.like', like)
        google_colab.register_callback('notebook.say', say)
    if start:
        display_bot(start)
    return display_bot, display_user
"""


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
            display_bot_single(d)

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
