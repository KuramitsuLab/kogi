
TERM = {
    'glay': '\033[07m{}\033[0m',
    'red': '\033[31m{}\033[0m',
    'green': '\033[32m{}\033[0m',
    'yellow': '\033[33m{}\033[0m',
    'blue': '\033[34m{}\033[0m',
    'cyan': '\033[36m{}\033[0m',
}


def term_color(text, color=None, bold=False):
    if color and color in TERM:
        text = TERM[color].format(text)
    if bold:
        text = f'\033[01m{text}\033[0m'
    return text


def html_color(text, color=None, bold=False):
    if color:
        text = f'<font color="{color}">{text}</font>'
    if bold:
        text = f'<b>{text}</b>'
    return text


def tohtml(text):
    return text.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')


class Render(object):
    def __init__(self):
        self.texts = []
        self.htmls = []
        self.terms = []

    def update(self, data):
        data['_text'] = ''.join(self.texts)
        data['_html'] = ''.join(self.htmls)
        data['_term'] = ''.join(self.terms)

    def s(self, text):
        text = str(text)
        self.texts.append(text)
        self.terms.append(text)
        self.htmls.append(text)

    def print(self, text='', color=None, bold=False):
        text = str(text)
        self.texts.append(text)
        self.terms.append(term_color(text, color, bold))
        self.htmls.append(html_color(tohtml(text), color, bold))

    def println(self, text='', color=None, bold=False):
        text = str(text)+'\n'
        self.texts.append(text)
        self.terms.append(term_color(text, color, bold))
        self.htmls.append(html_color(tohtml(text), color, bold))

    def extend(self, render, div='<div>{}</div>'):
        if isinstance(render, Render):
            self.texts.append(render.text())
            self.htmls.append(div.format(render.html()))
            self.terms.append(render.term())
        else:
            self.texts.append(render['_text'])
            self.htmls.append(div.format(render['_html']))
            self.terms.append(render['_term'])

    def appendHTML(self, content):
        if hasattr(content, '_repr_html_'):
            content = content._repr_html_()
        self.htmls.append(content)

    def text(self):
        return ''.join(self.texts)

    def term(self):
        return ''.join(self.terms)

    def html(self):
        return ''.join(self.htmls)

    def termtext(self):
        return ''.join(self.terms)

    def get_message(self):
        m = {}
        m['text'] = ''.join(self.texts)
        m['html'] = ''.join(self.htmls)
        return m
