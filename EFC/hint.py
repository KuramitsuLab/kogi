import re
DUP = {}


def debug(msg):
    if msg not in DUP:
        print('\033[31m[DEBUG]\033[0m', msg)
        DUP[msg] = msg


def bq(s):
    s = str(s).strip()
    if ' ' in s:
        s = f'`{s}`'
    return s


TE_HINT = [
    ("'function' object is not subscriptable", "Cもしくは B修正_添字コール"),
    ("'type' object is not subscriptable", "Cもしくは B修正_添字コール"),
    ("'set' object is not subscriptable", "Eセット添字"),
    ("not subscriptable", "E添字元"),
    ("unhashable type: 'slice'", '_構文ミス 修正_スライス'),
    ("can only concatenate", 'C両辺同じ'),
    ('must be', 'Cエラー読め'),
    ('should be', 'Cエラー読め'),
    ('cannot be', 'Cエラー読め'),
    ('KeyError', 'Eキー？'),
]

VE_HINT = [
    ('ZeroDivisionError', 'Cゼロ以外'),
    ('cannot be 0', 'Cゼロ以外'),
    ('cannot be zero', 'Cゼロ以外'),
    ('negative', 'Cゼロ以上'),
    ('within 0-1 range', 'C正規範囲'),
    ('empty range', 'C空範囲'),
    ('int() with base 2', 'C書式_2進数'),
    ('int() with base 16', 'C書式_16進数'),
    ('int() with base', 'C書式_整数'),
    ('not convert string to float', 'C書式_浮動小数点数'),
    ('literal for Fraction', 'C書式_有理数'),
    ('malformed string', 'C書式_文字列'),
    ('list index out of range', 'C添字範囲 T=リスト'),
    ('tuple index out of range', 'C添字範囲 T=タプル'),
    ('string index out of range', 'C添字範囲 T=文字列'),
    ('KeyError', 'Eキー'),
    ('KeyError: "None of', 'Aカラム名なし'),
    ('index out of range', 'C添字範囲'),
    ('out of bounds for axis', 'C添字範囲 T=配列'),
    ('too many indices', 'C添字次元 T=配列'),
    ('only integers, slices', 'are valid indices', 'Cエラー読め'),
    ('can only have integer', 'Cエラー読め'),
    ('not in list', 'C要素なし E要素確認'),
    ('not in tuple', 'C要素なし E要素確認'),
    ('substring not found', 'C部分文字なし'),
    ('cannot reshape', 'C修正_シェイプ'),
    ('operands could not be broadcast together with shapes', 'C配列形状'),
    ('contains NaN', 'C非数'),
    ('not supported between instances', 'C両辺同じ'),
    ('both arguments should be', 'C両引数同じ'),
    ('The truth value of', 'C複数ブール値'),
    ('repeated', 'C繰り返し'),
    ('must be', 'Cエラー読め'),
    ('should be', 'Cエラー読め'),
    ('cannot be', 'Cエラー読め'),
]

_NOTE = re.compile(r'(__D[^\x00-\x7F]+)')

# A原因 (パラメータ) B修正法 C補足 D注意 E解説


class Hint(object):
    def __init__(self, *args, **kwargs):
        self.main = []
        self.params = {}
        self.append(*args, **kwargs)

    def append(self, *args, **kwargs):
        for a in args:
            if ' ' in a:
                self.append(*a.split())
                continue
            if a[0] in 'ABCDE':
                self.main.append(a)
            else:
                if a.startswith('注意_'):
                    self.main.append(f'D{a[3:]}')
                elif a.startswith('解説_'):
                    self.main.append(f'E{a[3:]}')
                elif a.startswith('解説_'):
                    self.main.append(f'E{a[3:]}')
                else:
                    self.main.append(f'C{a}')
        for key, value in kwargs.items():
            if value is None:
                if value in self.params:
                    del self.params[key]
            else:
                self.params[key] = value

    def __str__(self):
        ss = []
        for a in self.main:
            if a.startswith('A'):
                ss.append(a)
        for key, value in self.params.items():
            if value is not None and value != '':
                ss.append(f'{key}={bq(value)}')
        for a in self.main:
            if not a.startswith('A'):
                ss.append(a)
        return ' '.join(ss)

    def is_type_error(self, emsg):
        if 'can only have integer indexers' in emsg:
            return True
        if 'IndexError: only integers' in emsg and 'valid indices' in emsg:
            return True
        return 'TypeError' in emsg or emsg.startswith('AttributeError')

    def remove_suffix(self, emsg, code, suffix):
        emsg = emsg.replace(suffix, '')
        code = code.replace(suffix, '')
        for key, value in self.params.items():
            if isinstance(value, str):
                self.params[key] = value.replace(suffix, '')
        return emsg, code

    def update(self, emsg, code, pattern=[]):
        HINT = TE_HINT if emsg.startswith('TypeError') else VE_HINT
        self.check_from_emsg(emsg, pattern+HINT)
        self.check_from_code(emsg, code)
        self.check_from_type(emsg, code)

    def check_from_code(self, emsg: str, code: str):
        for note in re.findall(_NOTE, code):
            print('@@@', note)
            self.append(note[2:])
            emsg, code = self.remove_suffix(emsg, code, note)
        if '__A' in code:
            self.append('D危険な変数名')
            emsg, code = self.remove_suffix(emsg, code, '__A')
        if '__Z' in code:
            self.append('C自作クラス')
            emsg, code = self.remove_suffix(emsg, code, '__Z')
        return emsg, code

    def check_from_emsg(self, emsg: str, patterns: list):
        for pat in patterns:
            if len(pat) == 2 and pat[0] in emsg:
                self.append(pat[-1])
                return
            if len(pat) == 3 and pat[0] in emsg and pat[1] in emsg:
                self.append(pat[-1])
                return
            if pat[0] in emsg and pat[1] in emsg and pat[2] in emsg:
                self.append(pat[-1])
                return
        if emsg.startswith('ValueError'):
            debug(f'_ノーヒント {len(emsg)} {emsg}')
            self.append('Xヒント欲しい？')

    def check_from_type(self, emsg: str, code: str):
        if 'NoneType' in emsg:
            self.append('Eノン型')
