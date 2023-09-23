import re
import html
import traceback
from IPython import get_ipython
from IPython.display import display, HTML
from .google_check import google_output
from .load_content import load_icon, load_css

import ipywidgets as widgets

from kogi import debug_print

########################

import re

def is_html(text):
    html_pattern = re.compile(r'<[^>]+>')
    return bool(html_pattern.search(text))

def replace_code_blocks_with_placeholders(text):
    placeholders = []
    code_blocks = re.findall(r'```[\s\S]*?```', text)
    for i, block in enumerate(code_blocks):
        placeholder = f"CODEBLOCK{i:02}_"
        block_modified = '\n'.join(block.splitlines()[1:-1])
        placeholders.append((placeholder, f'<pre></code>{block_modified}</code></pre>'))
        text = text.replace(block, placeholder)

    code_blocks = re.findall(r'`[^\`]*?`', text)
    for i, block in enumerate(code_blocks):
        placeholder = f"`CODE_{i:04}`"
        block_modified = html.escape(block[1:-1])
        placeholders.append((placeholder, f'<code>{block_modified}</code>'))
        text = text.replace(block, placeholder)

    code_blocks = re.findall(r'\$\$[\s\S]*?\$\$', text)
    for i, block in enumerate(code_blocks):
        placeholder = f"MATHBLOCK{i:04}_"
        placeholders.append((placeholder, block))
        text = text.replace(block, placeholder)

    code_blocks = re.findall(r'\$[\s\S]*?\$', text)
    for i, block in enumerate(code_blocks):
        placeholder = f"$MATH_{i:04}$"
        placeholders.append((placeholder, block))
        text = text.replace(block, placeholder)
    return text, placeholders

def restore_code_blocks(text, placeholders):
    for placeholder, block in placeholders:
        text = text.replace(placeholder, block)
    return text  


# URLの正規表現パターン。
# ここでは http または https で始まり、.jpg, .png, .gif, .jpeg のいずれかで終わるURLを対象としています。
img_url_pattern = re.compile(r'https?://[^\s]+?\.(jpg|jpeg|png|gif)')


def markdown_to_html(markdown_text):
    html_text = html.escape(markdown_text).replace('\n', '<br>')

    # 正規表現でマッチしたURLを<img>タグに変換
    html_text = img_url_pattern.sub(r'<img src="\g<0>" alt="image" />', html_text)

    # Headers
    # html_text = re.sub(r'###### (.*)', r'<h6>\1</h6>', html_text)
    # html_text = re.sub(r'##### (.*)', r'<h5>\1</h5>', html_text)
    # html_text = re.sub(r'#### (.*)', r'<h4>\1</h4>', html_text)
    # html_text = re.sub(r'### (.*)', r'<h3>\1</h3>', html_text)
    # html_text = re.sub(r'## (.*)', r'<h2>\1</h2>', html_text)
    # html_text = re.sub(r'# (.*)', r'<h1>\1</h1>', html_text)
    
    # Strong
    # html_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_text)
    # html_text = re.sub(r'__(.*?)__', r'<strong>\1</strong>', html_text)
    
    # Emphasis
    # html_text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html_text)
    # html_text = re.sub(r'_(.*?)_', r'<em>\1</em>', html_text)

    return html_text

def format_html(text):
    text, placeholders = replace_code_blocks_with_placeholders(text)
    if not is_html(text):
        text = markdown_to_html(text)
    text = restore_code_blocks(text, placeholders)
    return text



########################

MAIN_CSS = load_css('dialog.css')


BOT_HTML = '''\
<div class="sb-box">
<div class="icon-img icon-img-left"><img src="{icon}" width="60px"></div>
<div class="icon-name icon-name-left">{name}</div>
<div class="sb-side sb-side-left"><div class="sb-txt sb-txt-left">{content}</div></div>
</div>
'''

USER_HTML = '''\
<div class="sb-box">
<div class="icon-img icon-img-right"><img src="{icon}" width="60px"></div>
<div class="icon-name icon-name-right">{name}</div>
<div class="sb-side sb-side-right"><div class="sb-txt sb-txt-right">{content}</div></div>
</div>
'''

APPEND_JS = '''\
<script>
var target = document.getElementById("dialogXYZ");
var content = `{html}`;
if(target !== undefined) {{
    target.insertAdjacentHTML('beforeend', content);
    target.scrollTop = target.scrollHeight;
}}
</script>
'''

def exec_js(script):
    if script != '':
        if '<script>' not in script:
            script = f'<script>\n{script}</script>'
        display(HTML(script))

BOT_ICON = ('Bot', 'robot-fs8.png')
TA_ICON = ('TA', 'ta-fs8.png')
USER_ICON = ('You', 'girl-fs8.png')

class Dialog(object):
    def __init__(self, target, context):
        self.target = target
        if 'icons' not in context:
            context['icons'] = {
                '@system': BOT_ICON,
                '@user': USER_ICON,
                '@ta': TA_ICON,
                '@bot': BOT_ICON,
            }
        self.context = context

    def check_speech(self, speech, is_user=False):
        if isinstance(speech, str) or isinstance(speech, list):
            speech = {'content': speech, 'is_user': is_user}
        if 'is_user' not in speech:
            speech['is_user'] = is_user
        if speech['is_user']:
            name = speech.get('whoami', '@user')
            name, icon = self.context['icons'].get(name, USER_ICON)
        else:
            name = speech.get('whoami', '@bot')
            name, icon = self.context['icons'].get(name, BOT_ICON)
        if not icon.startswith('data:'):
            icon = load_icon(icon)
        speech['name'] = name
        speech['icon'] = icon
        if isinstance(speech['content'], list):
            speech['content'] = '<br>'.join(format_html(d) for d in speech['content'])
        else:
            speech['content'] = format_html(speech['content'])
        return speech

    def fix(self, s: str):
        return s.replace('XYZ', str(self.target))

    def display(self, s: str):
        display(HTML(self.fix(s)))

    def append_message(self, speech, is_user=False):
        speech = self.check_speech(speech, is_user=is_user)
        format_html = USER_HTML if speech.get('is_user', False) else BOT_HTML
        html = format_html.format(**speech)
        html = html.replace('\\', '\\\\').replace('`', '\\`')
        script = self.fix(APPEND_JS.format(html=html))
        exec_js(script)
        if 'script' in speech:
            exec_js(speech['script'])

    def print(self, speech, is_user=False):
        self.append_message(speech, is_user=is_user)


_DIALOG_HTML = '''\
<div id="dialogXYZ" class="box"></div>
'''

_TEXTAREA_HTML = '''\
<div style="text-align: right">
<textarea id="inputXYZ" placeholder="@placeholder@"></textarea>
<script>
let timeout = 3*60*1000;
var tm = setTimeout(()=>{document.getElementById("inputXYZ").remove();}, timeout);
document.getElementById("inputXYZ").addEventListener('keydown', (e) => {
    if (e.keyCode == 13) {
        const pane = document.getElementById("inputXYZ");
        clearTimeout(tm);
        tm = setTimeout(()=>{pane.remove();}, timeout*2);
        google.colab.kernel.invokeFunction('notebook.ask', [pane.value], {});
        pane.value = '';
    }
});
</script>
</div>
'''

_DIALOG_ID=111

def display_main(context, css=MAIN_CSS, placeholder=None):
    """
    """
    global _DIALOG_ID
    _DIALOG_ID += 1
    dialog = Dialog(_DIALOG_ID, context)
    if '<style>' not in css:
        css = f'<style>{css}</style>'
    html = css + _DIALOG_HTML
    if placeholder is not None and google_output is not None:
        html = html+_TEXTAREA_HTML.replace('@placeholder@', str(placeholder))
    dialog.display(html)
    return dialog


def default_chat(user_input, context=None):
    return 'おはよう'

def perform_chat(dialog, chat_fn, user_input, context):
    try:
        if isinstance(user_input, str):
            user_input = user_input.strip()
        debug_print(user_input)
        dialog.append_message(user_input, is_user=True)
        response = chat_fn(user_input, context)
        if isinstance(response, list):
            for res in response:
                dialog.append_message(res, is_user=False)
        else:
            dialog.append_message(response, is_user=False)
    except:
        traceback.print_exc()
        dialog.append_message({
            'name': '開発者',
            'icon': load_icon('robot.png'),
            'content': 'バグで処理に失敗しました。ごめんなさい',
        })


def start_chat(context=None, chat=default_chat, css=MAIN_CSS, placeholder=None):
    if context is None:
        context = {}
    
    dialog = display_main(context, placeholder=placeholder)
    dialog.context = context

    if google_output:
        def ask(user_input):
            nonlocal dialog, context, chat
            perform_chat(dialog, chat, user_input.strip(), context)
        google_output.register_callback('notebook.ask', ask)
    elif placeholder is not None:
        text = widgets.Text(
            value='',
            placeholder=placeholder,
            description='',
            layout=widgets.Layout(width='90%'),
            disabled=False
        )
        # enter キーが押されたときに呼び出される関数
        def on_enter(sender):
            nonlocal dialog, context, chat
            perform_chat(dialog, chat, f'{sender.value}', context)
            sender.value=''
        # on_submit イベントに関数をバインド
        text.on_submit(on_enter)
        # ウィジェットを表示
        display(text)

    return dialog

def kogi_print(text:str, css=MAIN_CSS):
    dialog = start_chat(css=css)
    dialog.print(text)
