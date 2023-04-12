import re

# mini md

_CODE = re.compile(r'(`[^`]+`)')
_BOLD = re.compile(r'(__[^_]+__)')


def replace_pre(s):
    while '```' in s:
        s = s.replace('```', '<pre>', 1).replace('```', '</pre>', 1)
    return s


def encode_md(s):
    s = s.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
    s = replace_pre(s)
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


# try:
#     import markdown

#     def encode_md(s):
#         return markdown.markdown(s)
# except ModuleNotFoundError:
#     pass


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


_FRAMEID = 1000


def frameid(frmid=None):
    global _FRAMEID
    if frmid:
        return frmid
    _FRAMEID += 1
    return _FRAMEID


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

    # def add_likeit(self, recid, frmid=None, copy=None, like='👍', dislike='👎'):
    #     frmid = frameid(frmid)
    #     if copy:
    #         textarea = f'<textarea id="t{frmid}" style="display: none">{{}}</textarea>'
    #         self.htmls.append(Doc(f'</>{copy}', style=textarea))
    #         button = f'<button id="b{frmid}" class="likeit" onclick="copy({frmid});like({recid},1)">{{}}</button>'
    #         self.htmls.append(Doc(f'コピー({like})', style=button))
    #     else:
    #         button = f'<button class="likeit" onclick="like({recid},1)">{{}}</button>'
    #         self.htmls.append(Doc(like, style=button))
    #     button = f'<button class="likeit" onclick="like({recid},0)">{{}}</button>'
    #     self.htmls.append(Doc(dislike, style=button))

    def add_likeit(self, recid, frmid=None, copy=None, like='👍1', dislike='👎0'):
        frmid = frameid(frmid)
        button = f'''\
<span id="b{frmid}">
<button class="likeit" onclick="like({recid},1,'b{frmid}')">{like}</button>
<button class="likeit" onclick="like({recid},0,'b{frmid}')">{{}}</button>
</span>'''
        self.htmls.append(Doc(dislike, style=button))

    def add_button(self, cmd, message, frmid=None):
        frmid = frameid(frmid)
        cmd = f"'{cmd}'"
        button = f'<button id="b{frmid}" onclick="say({cmd},{frmid})">{{}}</button>'
        self.htmls.append(Doc(message, style=button))

    def set_mention(self, mention: str):
        if mention.startswith('@'):
            mention, _, text = mention.partition(':')
            self.mention = mention
            return text
        return mention

    def get_mention(self, default=None):
        if hasattr(self, 'mention'):
            return self.mention
        for d in self.htmls:
            if isinstance(d, Doc):
                mention = d.get_mention()
                if mention:
                    return mention
        return default

    def get_script(self):
        script = ''
        if hasattr(self, 'script'):
            script = self.script
        for d in self.htmls:
            if isinstance(d, Doc):
                s = d.get_script()
                if s != '':
                    script += s
        return script

    @classmethod
    def md(cls, s, style=None):
        doc = Doc(style=style)
        s = doc.set_mention(s)
        doc.htmls.append(encode_md(s))
        doc.terms.append(encode_md_term(s))
        doc.texts.append(encode_md_text(s))
        return doc

    @classmethod
    def HTML(cls, html, text=None, css=None, script=None):
        doc = Doc()
        frmid = frameid()
        html = html.replace('ZYX', str(frmid))
        if css:
            html = css+html
        doc.htmls.append(html)
        if text:
            doc.terms.append(encode_md_term(text))
            doc.texts.append(encode_md_text(text))
        if script:
            script = script.replace('ZYX', str(frmid))
            doc.script = script
        return doc
