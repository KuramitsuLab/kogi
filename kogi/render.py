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


TERM = {
    'glay': '\033[07m{}\033[0m',
    'red': '\033[31m{}\033[0m',
    'green': '\033[32m{}\033[0m',
    'yellow': '\033[33m{}\033[0m',
    'blue': '\033[34m{}\033[0m',
    'cyan': '\033[36m{}\033[0m',
}


def _term_div_color(color=None, background=None, bold=False):
    div = '{}'
    if color and color in TERM:
        div = TERM[color].format(div)
    if bold:
        div = '\033[01m{}\033[0m'.format(div)
    return div


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


def _text(x):
    return x.html() if hasattr(x, 'html') else str(x)


def _term(x):
    return x.term() if hasattr(x, 'term') else str(x)


def _html(x):
    return x.html() if hasattr(x, 'html') else str(x)


def _tohtml(text):
    if '</' in text or '<br>' in text:
        return text
    return text.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')


_BUTTON_ID = 1000


class Doc(object):
    def __init__(self, text='', html_div='{}', term_div='{}'):
        self.html_div = html_div
        self.term_div = term_div
        self.texts = []
        self.htmls = []
        self.terms = []
        if text:
            self.append(text)

    def text(self):
        content = ''.join(_text(x) for x in self.texts)
        return content

    def html(self):
        content = ''.join(_html(x) for x in self.htmls)
        return self.html_div.format(content)

    def term(self):
        content = ''.join(_term(x) for x in self.terms)
        return self.term_div.format(content)

    def __getitem__(self, key):
        if key == '_text' or key == 'text':
            return self.html()
        if key == '_term' or key == 'term':
            return self.term()
        return self.html()

    def append(self, doc, div='{}'):
        if isinstance(doc, Doc):
            self.texts.append(doc)
            self.terms.append(doc)
            doc.html_div = div.format(doc.html_div)
            self.htmls.append(doc)
        elif isinstance(doc, dict):
            self.texts.append(doc['_text'])
            self.terms.append(doc['_term'])
            self.htmls.append(div.format(doc['_html']))
        elif doc is not None:
            self.texts.append(str(doc))
            self.terms.append(str(doc))
            if hasattr(doc, '_repr_html_'):
                doc = doc._repr_html_()
                self.htmls.append(div.format(doc))
            else:
                self.htmls.append(div.format(_tohtml(str(doc))))

    def print(self, doc=None, color=None, background=None, bold=None):
        if isinstance(doc, str):
            doc = str(doc)
            self.texts.append(doc)
            div = _term_div_color(
                color=color, background=background, bold=bold)
            self.terms.append(div.format(doc))
            div = _html_div_color(
                color=color, background=background, bold=bold)
            self.htmls.append(div.format(_tohtml(doc)))

    def println(self, doc=None, color=None, background=None, bold=None):
        if doc:
            self.print(doc, color=color, background=background, bold=bold)
        self.texts.append('\n')
        self.terms.append('\n')
        self.htmls.append('<br>')

    def add_likeit(self, recid, copy=None, like='いいね👍', dislike='残念😞'):
        global _BUTTON_ID
        if copy:
            _BUTTON_ID += 1
            textarea = f'<textarea id="t{_BUTTON_ID}" style="display: none">{{}}</textarea>'
            self.htmls.append(Doc(copy, html_div=textarea))
            button = f'<button id="b{_BUTTON_ID}" class="likeit" onclick="copy({_BUTTON_ID});like({recid},1)">{{}}</button>'
            self.htmls.append(Doc(f'コピー({like})', html_div=button))
        else:
            button = f'<button class="likeit" onclick="like({recid},1)">{{}}</button>'
            self.htmls.append(Doc(like, html_div=button))
        button = f'<button class="likeit" onclick="like({recid},0)">{{}}</button>'
        self.htmls.append(Doc(dislike, html_div=button))

    def add_button(self, cmd, message):
        global _BUTTON_ID
        _BUTTON_ID += 1
        cmd = f"'{cmd}'"
        button = f'<button id="b{_BUTTON_ID}" onclick="say({cmd},{_BUTTON_ID})">{{}}</button>'
        self.htmls.append(Doc(message, html_div=button))

    def get_message2(self, tag):
        m = {}
        m['text'] = self.text()
        m['term'] = self.term()
        m['html'] = self.html()
        return m, tag

    @classmethod
    def md(cls, s):
        return encode_md(s)

    @classmethod
    def color(cls, text, color=None, background=None, bold=False):
        return Doc(text,
                   html_div=_html_div_color(color, background, bold),
                   term_div=_term_div_color(color, background, bold))

    @classmethod
    def code(cls, text=''):
        return Doc(text, html_div='<pre>{}</pre>')


def tohtml(text):
    return text.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')


def textfy(doc):
    if isinstance(doc, Doc):
        return doc.text()
    return str(doc)

# def term_color(text, color=None, background=None, bold=False):
#     if color and color in TERM:
#         text = TERM[color].format(text)
#     if bold:
#         text = f'\033[01m{text}\033[0m'
#     return text


def html_color(text, color=None, background=None, bold=False):
    if color and background:
        text = f'<span style="color: {color}; background: {background};">{text}</span>'
    elif color:
        text = f'<span style="color: {color};">{text}</span>'
    elif background:
        text = f'<span style="background: {background};">{text}</span>'
    if bold:
        text = f'<b>{text}</b>'
    return text


# class Render(object):
#     @ classmethod
#     def new_pairid(cls, input_text, output_text):
#         eid = len(_PAIRs)
#         _PAIRs.append((input_text, output_text))
#         return eid

#     @ classmethod
#     def create_button(cls, eid, title='いいね', copy=False):
#         func = 'cp' if copy else 'like'
#         button = f'<button onlick="{func}({eid})">{title}</button>'
#         return button

#     @ classmethod
#     def create_code(cls, eid, text, title='コピー'):
#         button = Render.create_button(eid, title, copy=True)
#         if '\n' in text or '<br>' in text:
#             return f'<pre id="e{eid}">{text}</pre>'+button
#         else:
#             return f'<code id="e{eid}">{text}</code>'+button

#     def __init__(self, div='{}'):
#         self.div = div
#         self.texts = []
#         self.htmls = []
#         self.terms = []

#     def update(self, data):
#         data['_text'] = self.text()
#         data['_html'] = self.html()
#         data['_term'] = self.term()

#     def s(self, text):
#         text = str(text)
#         self.texts.append(text)
#         self.terms.append(text)
#         self.htmls.append(text)

#     def print(self, text='', color=None, background=None, bold=False):
#         text = str(text)
#         self.texts.append(text)
#         self.terms.append(term_color(text, color, background, bold))
#         self.htmls.append(html_color(tohtml(text), color, background, bold))

#     def println(self, text='', color=None, background=None, bold=False):
#         text = str(text)+'\n'
#         self.texts.append(text)
#         self.terms.append(term_color(text, color, background, bold))
#         self.htmls.append(html_color(tohtml(text), color, background, bold))

#     def extend(self, render, div='<div>{}</div>'):
#         if isinstance(render, Render):
#             self.texts.append(render.text())
#             self.htmls.append(div.format(render.html()))
#             self.terms.append(render.term())
#         else:
#             self.texts.append(render['_text'])
#             self.htmls.append(div.format(render['_html']))
#             self.terms.append(render['_term'])

#     def appendHTML(self, content, div='<div>{}</div>'):
#         if hasattr(content, '_repr_html_'):
#             content = content._repr_html_()
#         self.htmls.append(div.format(content))

#     def text(self):
#         return ''.join(self.texts)

#     def term(self):
#         return ''.join(self.terms)

#     def html(self):
#         return self.div.format(''.join(self.htmls))

#     def termtext(self):
#         return ''.join(self.terms)

#     def get_message(self, heading=''):
#         m = {}
#         if heading != '':
#             heading = html_color(heading, bold=True)+'<br>'
#         m['text'] = self.text()
#         m['html'] = heading+self.html()
#         return m
