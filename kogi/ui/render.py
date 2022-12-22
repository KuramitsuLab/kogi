import re

# mini md

_CODE = re.compile(r'(`[^`]+`)')
_BOLD = re.compile(r'(__[^_]+__)')


def encode_md(s):
    s = s.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
    for t in re.findall(_CODE, s):
        t2 = f'<code>{t[1:-1]}</code>'
        s = s.replace(t, t2)
    for t in re.findall(_BOLD, s):
        t2 = f'<b>{t[2:-2]}</b>'
        s = s.replace(t, t2)
    return s


def encode_md_text(s):
    for t in re.findall(_CODE, s):
        t2 = t[1:-1]
        s = s.replace(t, t2)
    for t in re.findall(_BOLD, s):
        t2 = t[2:-2]
        s = s.replace(t, t2)
    return s


TERM = {
    'code': '\033[35m{}\033[0m',
    'glay': '\033[07m{}\033[0m',
    'red': '\033[31m{}\033[0m',
    'green': '\033[32m{}\033[0m',
    'yellow': '\033[33m{}\033[0m',
    'blue': '\033[34m{}\033[0m',
    'magenta': '\033[35m{}\033[0m',
    'cyan': '\033[36m{}\033[0m',
}


def _term_div_color(color=None, background=None, bold=False):
    div = '{}'
    if color and color in TERM:
        div = TERM[color].format(div)
    if bold:
        div = '\033[01m{}\033[0m'.format(div)
    return div


def encode_md_term(s):
    for t in re.findall(_CODE, s):
        t2 = _term_div_color('code').format(t[1:-1])
        s = s.replace(t, t2)
    for t in re.findall(_BOLD, s):
        t2 = _term_div_color('bold').format(t[2:-2])
        s = s.replace(t, t2)
    return s


def _html_div_color(color=None, background=None, bold=False):
    div = '{}'
    if bold:
        div = f'<b>{div}</b>'
    if color and background:
        div = f'<span style="color: {color}; background: {background};">{div}</span>'
    elif color:
        div = f'<span style="color: {color};">{div}</span>'
    elif background:
        div = f'<span style="background: {background};">{div}</span>'
    return div


def _term(x):
    return x.term() if hasattr(x, 'term') else str(x)


_BUTTON_ID = 1000

_DEFAULT_STYLE = ('{}', '{}')

_STYLE_MAP = {
    '@pre': ('<pre>{}</pre>', '{}'),
    '@code': ('<pre class="code">{}</pre>', '{}'),
    '@zen': ('<span class="zen">{}</span>', '{}'),
}


def _get_style(style=None):
    if isinstance(style, str) and style.startswith('<'):
        return style, '{}'
    return _STYLE_MAP.get(style, _DEFAULT_STYLE)


def _tohtml(text):
    if '</' in text or '<br>' in text:
        return text.replace('</>', '')
    return text.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')


def _html(x):
    return x._repr_html_() if hasattr(x, '_repr_html_') else _tohtml(str(x))


class Doc(object):
    def __init__(self, doc=None, style=None):
        self.texts = []
        self.htmls = []
        self.terms = []
        self.style_format = _get_style(style)
        if doc:
            self.append(doc)

    def new(self, doc=None, style=None):
        doc = Doc(doc=doc, style=style)
        self.append(doc)
        return doc

    def __str__(self):
        content = ''.join(str(x) for x in self.texts)
        return content

    def term(self):
        content = ''.join(_term(x) for x in self.terms)
        return self.style_format[1].format(content)

    def __repr__(self):
        return self.term()

    def _repr_html_(self):
        content = ''.join(_html(x) for x in self.htmls)
        return self.style_format[0].format(content)

    def append(self, doc, style=None):
        if style is not None:
            doc = Doc(doc, style)
        if isinstance(doc, Doc):
            self.texts.append(doc)
            self.terms.append(doc)
            self.htmls.append(doc)
        elif doc is not None:
            self.texts.append(str(doc))
            self.terms.append(str(doc))
            self.htmls.append(_html(doc))

    def print(self, doc=None, style=None, color=None, background=None, bold=None):
        if style is not None:
            self.append(doc, style=style)
            return
        if isinstance(doc, Doc):
            self.texts.append(doc)
            self.terms.append(doc)
            self.htmls.append(doc)
        if isinstance(doc, str):
            doc = str(doc)
            self.texts.append(doc)
            div = _term_div_color(
                color=color, background=background, bold=bold)
            self.terms.append(div.format(doc))
            div = _html_div_color(
                color=color, background=background, bold=bold)
            self.htmls.append(div.format(_tohtml(doc)))

    def println(self, doc=None, style=None, color=None, background=None, bold=None):
        if doc:
            self.print(doc, style=style, color=color,
                       background=background, bold=bold)
        self.texts.append('\n')
        self.terms.append('\n')
        self.htmls.append('<br>')

    def add_likeit(self, recid, copy=None, like='いいね', dislike='残念'):
        global _BUTTON_ID
        if copy:
            _BUTTON_ID += 1
            textarea = f'<textarea id="t{_BUTTON_ID}" style="display: none">{{}}</textarea>'
            self.htmls.append(Doc(f'</>{copy}', style=textarea))
            button = f'<button id="b{_BUTTON_ID}" class="likeit" onclick="copy({_BUTTON_ID});like({recid},1)">{{}}</button>'
            self.htmls.append(Doc(f'コピー({like})', style=button))
        else:
            button = f'<button class="likeit" onclick="like({recid},1)">{{}}</button>'
            self.htmls.append(Doc(like, style=button))
        button = f'<button class="likeit" onclick="like({recid},0)">{{}}</button>'
        self.htmls.append(Doc(dislike, style=button))

    def add_button(self, cmd, message):
        global _BUTTON_ID
        _BUTTON_ID += 1
        cmd = f"'{cmd}'"
        button = f'<button id="b{_BUTTON_ID}" onclick="say({cmd},{_BUTTON_ID})">{{}}</button>'
        self.htmls.append(Doc(message, style=button))

    def get_message2(self, tag):
        m = {}
        m['text'] = str(self)
        m['term'] = self.term()
        m['html'] = self._repr_html_()
        return m, tag

    @classmethod
    def md(cls, s, style=None):
        doc = Doc(style=style)
        doc.htmls.append(encode_md(s))
        doc.terms.append(encode_md_term(s))
        doc.texts.append(encode_md_text(s))
        return doc

    @classmethod
    def HTML(cls, html, text, css=None, script=None):
        global _BUTTON_ID
        _BUTTON_ID += 1
        doc = Doc()
        html = html.replace('XYZ', f'X{_BUTTON_ID}')
        if css:
            if script:
                html = css+script+html
            else:
                html = css+html
        doc.htmls.append(html)
        doc.terms.append(encode_md_term(text))
        doc.texts.append(encode_md_text(text))
        return doc
