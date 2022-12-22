from kogi.service import kogi_get
from .content import ICON, CSS
from kogi.ui.render import Doc, encode_md

from IPython.display import display, HTML

_ICON = {
    '@robot': ('システム', 'robot-fs8.png'),
    '@ta': ('TA', 'ta-fs8.png'),
    '@kogi': ('コギー', 'kogi-fs8.png'),
    '@you': ('あなた', 'girl-fs8.png'),
}


def get_icon(tag):
    return _ICON.get(tag, _ICON['@kogi'])


def messagefy(message, tag=None):
    if isinstance(message, str):
        if message.startswith('@'):
            tag, _, text = message.partition(':')
            message = dict(text=text)
        else:
            message = dict(text=message)
    elif isinstance(message, Doc):
        message, tag = message.get_message2(tag)
    elif not isinstance(message, dict):
        message = dict(text=str(message))
    name, icon = get_icon(tag)
    if tag == '@you':
        message['bot'] = False
        name = kogi_get('uname', name)
    if 'name' not in message:
        message['name'] = name
    if 'icon' not in message:
        message['icon'] = icon
    if 'html' not in message:
        message['html'] = encode_md(message['text'])
    return message


_BOT_HTML = '''\
<div class="sb-box">
<div class="icon-img icon-img-left"><img src="{icon}" width="60px"></div>
<div class="icon-name icon-name-left">{name}</div>
<div class="sb-side sb-side-left"><div class="sb-txt sb-txt-left">{html}</div></div>
</div>
'''

_USER_HTML = '''\
<div class="sb-box">
<div class="icon-img icon-img-right"><img src="{icon}" width="60px"></div>
<div class="icon-name icon-name-right">{name}</div>
<div class="sb-side sb-side-right"><div class="sb-txt sb-txt-right">{text}</div></div>
</div>
'''


def htmlfy_message(msg):
    msg['icon'] = ICON(msg['icon'])
    if msg.get('bot', True):
        return _BOT_HTML.format(**msg)
    else:
        return _USER_HTML.format(**msg)


_PRINT = '''<div class="box" style="height: {}px">{}</div>'''


def _kogi_print(m, tag, height=80):
    html = htmlfy_message(messagefy(m, tag))
    display(HTML(CSS('dialog.css')+_PRINT.format(height, html)))


def kogi_print(*args, **kwargs):
    tag = kwargs.get('tag', None)
    height = kwargs.get('height', 80)
    if len(args) > 0:
        if isinstance(args[0], dict):
            d = args[0]
            if 'name' in d and 'icon' in d and 'text' in d:
                _kogi_print(d, tag, height)
                return
        if isinstance(args[0], Doc):
            _kogi_print(args[0], tag, height)
            return
        if kwargs.get('html', True):
            m = {'html': str(args[0])}
            _kogi_print(m, tag, height)
            return
        if isinstance(args[0], Doc):
            _kogi_print(args[0], tag, height)
            return
    sep = kwargs.get('sep', ' ')
    _kogi_print(sep.join(str(s) for s in args), tag, height)
