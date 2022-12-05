import traceback
from .content import JS, CSS, ICON
from ._google import google_colab

from IPython.display import display, HTML
from kogi.service import kogi_get


_DIALOG_COLAB_HTML = '''
<div id="dialog">
    {script}
    <div id="{target}" class="box" style="height: {height}px">
    </div>
    <div style="text-align: right">
        <textarea id="input" placeholder="{placeholder}"></textarea>
    </div>
</div>
'''

_DIALOG_HTML = '''
<div id="dialog">
    {script}
    <div id="{target}" class="box" style="height: {height}px">
    </div>
</div>
'''


def display_main(target, placeholder=''):
    data = dict(
        script=JS('dialog.js'),
        placeholder=placeholder,
        target=target,
        height=str(kogi_get('chat_height', 300))
    )
    DHTML = _DIALOG_COLAB_HTML if google_colab else _DIALOG_HTML
    display(HTML(CSS('dialog.css') + DHTML.format(**data)))


_DIALOG_ID = 1


_BOT_HTML = '''
<div class="sb-box">
    <div class="icon-img icon-img-left">
        <img src="{icon}" width="60px">
    </div>
    <div class="icon-name icon-name-left">{name}</div>
    <div class="sb-side sb-side-left">
        <div class="sb-txt sb-txt-left">{html}</div>
    </div>
</div>
'''


def _htmlfy_bot(message, target=''):
    message['icon'] = ICON(message['icon'])
    return _BOT_HTML.format(**message)


_USER_HTML = '''
<div class="sb-box">
    <div class="icon-img icon-img-right">
        <img src="{icon}" width="60px">
    </div>
    <div class="icon-name icon-name-right">{name}</div>
    <div class="sb-side sb-side-right">
        <div class="sb-txt sb-txt-right">{text}</div>
    </div>
</div>
'''


def _htmlfy_user(message):
    message['icon'] = ICON(message['icon'])
    return _USER_HTML.format(**message)

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


def display_dialog(chatbot, start=None, placeholder='質問はこちらに'):
    global _DIALOG_ID
    target = f'output{_DIALOG_ID}'
    _DIALOG_ID += 1
    display_main(target, placeholder)

    def display_user(message):
        nonlocal chatbot, target
        message = chatbot.messagefy(message, name='あなた', icon='girl_think-fs8.png')
        message['target'] = target
        display_talk(_htmlfy_user(message), target)

    def display_bot_single(message):
        nonlocal chatbot, target
        message = chatbot.messagefy(message)
        message['target'] = target
        display_talk(_htmlfy_bot(message), target)

    def display_bot(messages):
        if isinstance(messages, list):
            for message in messages:
                display_bot_single(message)
        else:
            display_bot_single(messages)

    if google_colab:
        def ask(user_text):
            nonlocal chatbot
            try:
                user_text = user_text.strip()
                display_user(user_text)
                messages = chatbot.ask_message(user_text)
                display_bot(messages)
            except:
                display_bot('バグで処理に失敗しました。ごめんなさい')
                traceback.print_exc()

        def likeit(conversation_id, how):
            nonlocal chatbot
            try:
                chatbot.likeit(conversation_id, how)
            except:
                display_bot('バグで処理に失敗しました。ごめんなさい')
                traceback.print_exc()
        google_colab.register_callback('notebook.ask', ask)
        google_colab.register_callback('notebook.likeit', likeit)
    if start:
        display_bot(start)
    return display_bot, display_user
