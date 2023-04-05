from kogi.service import kogi_get, debug_print
from .content import ICON, CSS, JS
from kogi.ui.render import Doc

from IPython.display import display, HTML
from ._google import google_colab

_ICON = {
    '@kogi': ('コギー', 'kogi_doya-fs8.png'),
    '@kogi_plus': ('コギー', 'kogi_doya-fs8.png'),
    '@kogi_minus': ('コギー', 'kogi_error-fs8.png'),
    '@robot': ('コギー', 'kogi_gaan-fs8.png'),
    '@ta': ('ももパン', 'ta-fs8.png'),
    '@you': ('あなた', 'girl-fs8.png'),
}

def get_icon(tag):
    return _ICON.get(tag, _ICON['@kogi'])


_BOT_HTML = '''\
<div class="sb-box">
<div class="icon-img icon-img-left"><img src="{icon}" width="60px"></div>
<div class="icon-name icon-name-left">{name}</div>
<div class="sb-side sb-side-left"><div class="sb-txt sb-txt-left">{content}</div></div>
</div>
'''

_USER_HTML = '''\
<div class="sb-box">
<div class="icon-img icon-img-right"><img src="{icon}" width="60px"></div>
<div class="icon-name icon-name-right">{name}</div>
<div class="sb-side sb-side-right"><div class="sb-txt sb-txt-right">{content}</div></div>
</div>
'''


def messagefy(doc, mention=None):
    if isinstance(doc, str):
        if doc.startswith('@'):
            mention, _, text = doc.partition(':')
            doc = Doc(text)
        else:
            doc = Doc(doc)
    if mention is None:
        mention = doc.get_mention('@kogi')
    name, icon = get_icon(mention)
    if mention == '@you':
        return _USER_HTML.format(
            icon=ICON(icon),
            name=kogi_get('uname', name),
            content=doc._repr_html_(),
        ), doc.get_script()
    return _BOT_HTML.format(
        icon=ICON(icon),
        name=name,
        content=doc._repr_html_(),
    ), doc.get_script()


_DIALOG_ID = 0


def replace_dialog_id(s):
    return s.replace('XYZ', str(_DIALOG_ID))


def display_dialog_css():
    display(HTML(CSS('dialog.css')))


def dialog_script():
    return JS('dialog.js')


def exec_js(script):
    if script != '':
        display(HTML(f'<script>\n{script}</script>'))


_DIALOG = '''\
<div id="dialogXYZ" class="box">{}</div>
'''

_DIALOG2 = '''\
<div id="dialogXYZ" class="box" style="height: {}px">{}</div>
'''

_TEXTAREA = '''\
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

_BLOCK = '''\
<div>
{}
{}
</div>
'''


def display_dialog(doc='', height=None, placeholder=None):
    global _DIALOG_ID
    _DIALOG_ID += 1
    display_dialog_css()
    if doc == '':
        html, script = '', ''
    else:
        html, script = messagefy(doc)
    if height:
        html = _DIALOG.format(html)
        ##html = _DIALOG2.format(height, html)
    else:
        html = _DIALOG.format(html)
    if placeholder:
        html = html+_TEXTAREA.replace('@placeholder@', placeholder)
    html = _BLOCK.format(dialog_script(), html)
    html = replace_dialog_id(html)
    script = replace_dialog_id(script)
    display(HTML(html))
    exec_js(script)
    return replace_dialog_id('#dialogXYZ')


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


def append_message(doc, target, mention=None):
    html, script = messagefy(doc, mention=mention)
    # if google_colab:
    #     with google_colab.redirect_to_element(target):
    #         display(HTML(replace_dialog_id(html)))
    # else:
    html = html.replace('\\', '\\\\')
    html = html.replace('`', '\\`')
    display(HTML(replace_dialog_id(APPEND_JS).format(html=html)))
    exec_js(replace_dialog_id(script))
    return target


def kogi_print(*args, **kwargs):
    height = kwargs.get('height', None)
    target = kwargs.get('target', None)
    placeholder = kwargs.get('placeholder', None)
    if len(args) > 0:
        if isinstance(args[0], Doc):
            if target:
                return append_message(args[0], target)
            else:
                return display_dialog(args[0], placeholder=placeholder, height=height)
    sep = kwargs.get('sep', ' ')
    text = sep.join(str(s) for s in args)
    if target:
        return append_message(text, target)
    else:
        return display_dialog(text, placeholder=placeholder, height=height)
