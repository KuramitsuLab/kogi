import sklearn.linear_model
import re
import warnings
import fractions
from fractions import Fraction
import sys
import math
import random
import typo
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import collections
from expr import Seed
N_TRY = 8
Counter_EMSG = collections.Counter()
DUP = {}


def debug(msg):
    if msg not in DUP:
        print('\033[31m[DEBUG]\033[0m', msg)
        DUP[msg] = msg


def print__9(*a, **kw):
    pass


class C:
    def __init__(self):
        self.A = 0
        self.B = 1


class Person:
    def __init__(self):
        self.A = 0
        self.B = 1
        self.C = 2


# def make_model(d):
#     model = sklearn.linear_model.LinearRegression()
#     df = pd.DataFrame({'A': [0, 1, 2], 'B': [0, 1, 2], 'C': [0, 1, 0]})
#     X = df[['A', 'B']].values
#     y = df['C'].values
#     model.fit(X, y)
#     print(model.predict(X))
#     model2 = sklearn.linear_model.LinearRegression()


# make_model(None)
# exit(0)


def test_vars():
    aList = [0, 1, 2]
    aSList = ['0', '1', '2']
    aName = ['A', 'B', 'C']
    aDict = {'A': 0, 'B': 1, 'C': 2}
    aTuple = (0, 1, 2)
    aSet = {0, 1, 2}
    aFraction = Fraction(1, 2)
    aArray = np.array(aList[:])
    aArray2d = np.array([[0, 1, 2], [1, 1, 1], [2, 1, 0]])
    df = pd.DataFrame({'A': aList[:], 'B': aList[:], 'C': aSList[:]})
    # print(df.iat[0, 0])
    return dict(
        C=C, o=C(), obj=C(), Person=Person, o__1=Person(), obj__1=Person(),
        i=1, j=2, n=2, N=2, x=0, y=0, a=0, b=1,
        v=0, value=0, result=0, ans=0, res=0, index=-1,
        x__1=0.0, y__1=1.0, z__1=1.0,
        v__1=0.0, value__1=1.0, result__1=0.0, ans__1=1.0, res__1=1.0,
        alpha__1=0.5, beta__1=2.0, mu__1=0.0, sigma__1=1.0, kappa__1=1.0,
        s="1", S="0", t="2", u="1", value__2="1",
        name="A", key="A", text="text",
        file="file.txt", path="file.csv", filepath="file.txt", filename="file.txt",
        A__3=aList[:], xs=aList[:], ys=aList[:], lst=aList[:], values=aList[:],
        names=aName, keys=aName,
        pair=aTuple, point=aTuple, xy=aTuple, xyz=aTuple,
        d=aDict, dic=aDict,
        st__4=aSet, v__4=aSet, A__4=aSet, B__4=aSet,  # Set
        x__4=aFraction, y__4=aFraction, a__4=aFraction, b__4=aFraction,  # Fraction
        a__5=aArray, b__5=aArray, x__5=aArray, y__5=aArray,  # np.array
        mat=aArray2d.copy(), mat2=aArray2d.copy(),
        df=df, df2=df, df3=df, ds=df["A"], ds2=df["B"], ds3=df["C"],
        _列名_="A", _列名2_="B", _列名3_="C",
        binary=b'0', buffer=b'0', b__2=b'000',
        X__9=None, s__9=None, df__9=None, a__9=None,
        print__9=print__9,
        np=np, pd=pd,
    )


def make_filter(C=object, fn=lambda x: True):
    def filter(x):
        return isinstance(x, C) and fn(x)
    return filter


def isinstance_all(x, C):
    for a in x:
        if not isinstance(a, C):
            return False
    return True


EXPRESSION_PATTERN = {
    '<object>': dict(
        E='オブジェクト',
        fn=make_filter((C, Person, type(None))),
        ns='o obj v value'.split(),
    ),
    '<int>': dict(
        fn=make_filter(int),
        E='整数',
        cs=['-1', '0', '1', '2', '3', '4'],
        e=['int($0)', 'len($0)', '$0+1', '$0-1',
            '$0-$1', '$0[0]', 'values[$0]', '$0[$1]'],
    ),
    '<int0>': dict(
        fn=make_filter(int, lambda x: x == 0),
        E='整数',
        cs=['0'],
    ),
    '<float>': dict(
        E='少数点数',
        fn=make_filter(float),
        cs=['-1.0', '0.0', '1.0', '2.0', 'math.pi/2', 'math.e'],
        e=['float($1)', 'float($0+$1)', '$0+$1',
           '$0-$1', '$0/$1', 'values[$0]'],
    ),
    '<str>': dict(
        E='文字列',
        fn=make_filter(str),
        cs=['""', '"."', "';'", '"\\t"', "','"],
        e=['str($0)', "''.join($0)", '$0+$1', "f'{$0}'",
            '$0.upper()', '$0.lower()', "$0[0]", "$0[$1]"],
    ),
    '<istr>': dict(
        E='文字列/str',  # 整数文字列
        fn=make_filter(str, lambda x: x.isdigit()),
        c=['"0"', '"1"', "'123'"],
        e=['str($1)', '$0+$1', "f'{$0}'", "$0[0]", "$0[$1]"],
    ),
    # '<str>': ['s S', 's t u', 'names[0] keys[i]', 'str(N) str(n)'],
    # '<text>': ['"text" "label" "title"', 'text'],
    # '<filename>': ['file filename filepath path'],
    # '<bytes>': ['binary buffer b__2'],
    # '<name>': ,  # エラー発生
    '<name>': dict(
        fn=make_filter(object, lambda x: str(x) in 'ABCD'),
        E='キー',  # キー文字列
        ns=['name', 'key'],
        cs=['"A"', '"B"', "'C'", "'D'"],
    ),
    '<col>': dict(
        E='列名',  # キー文字列
        fn=make_filter(object, lambda x: str(x) in 'ABCD'),
        ns=['_列名_', '_列名2_', '_列名3_', 'column'],
        e=['df.columns[i]', 'df.columns[$0]'],
        cs=['"A"', '"B"', "'C'"],
    ),
    '<list>': dict(
        E='リスト',  # リスト
        fn=make_filter(list),
        e=['list($0)', '[$0,$1]', "[$1]"],
    ),
    '<ilist>': dict(
        E='数列',  # リスト
        fn=make_filter(list, lambda x: isinstance_all(x, int)),
        e=['list($0)', '[$1]', '[$0,$1]', 'list(range(N))'],
        cs=['[0]', 'list(range(8))'],
    ),
    '<slist>': dict(
        E='文字列のリスト',  # リスト
        fn=make_filter(list, lambda x: isinstance_all(x, str)),
        e=['list(str($0))', '$0.split()', 'list($0)'],
        cs=['[]', '["A"]', '["A","B"]', 's.split()'],
    ),
    '<iterable>': dict(
        E='イテラブル',  # リスト
        fn=make_filter(object, lambda x: hasattr(
            x, '__iter__') and not isinstance(x, str)),
        e=['range(1,$0)', 'range($1)', 'range($1+1)', 'range($1-1)'],
        cs=['range(N)', 'range(len(s))'],
    ),
    # '<seq>': ['s A__3 S'],
    # '<iterator>': ['iter(A__3)'],
    '<tuple>': dict(
        E='タプル',
        fn=make_filter(tuple),
        e=['($0,)', '($0,$1)', 'tuple($0)'],
        cs=['()'],
    ),
    '<dict>': dict(
        E='辞書',
        fn=make_filter(dict),
        e=['dict(A=$0)'],
        cs=['{}', '{"A": $1}'],
    ),
    '<set>': dict(
        E='セット',
        fn=make_filter(set),
        cs=['{1,2}'],
        e=['$0|$1', '$0&$1', '~$0', 'set($0)'],
    ),
    '<Fraction>': dict(
        E='有理数',
        fn=make_filter(Fraction),
        e=['$0+$1', '$0-$1', '$0/$1', '$0*$1', 'Fraction($0,$1)'],
        cs=['Fraction("1/2")'],
    ),
    '<a>': dict(
        E='配列',
        fn=make_filter(np.ndarray),
        e=['$0+$1', '$0-$1'],
        cs=['np.array([1,2,3])'],
    ),
    '<tuple_a>': dict(
        E='配列',
        fn=make_filter(tuple, lambda x: isinstance_all(x, np.ndarray)),
        e=['($0,$1)', '($0,$1,$2)'],
        cs=['(x__5, y__5)', '(a__5, b__5)'],
    ),
    '<df>': dict(
        E='データフレーム',
        fn=make_filter(pd.DataFrame),
        ns=['df', 'df2', 'df3'],
        e=['df[[$0, $1]]'],
        cs=['df[[_列名_]]', 'df[[_列名_, _列名2_]]', 'df.head()'],
    ),
    '<tuple_df>': dict(
        E='データフレームの組',  # リスト
        fn=make_filter(tuple, lambda x: isinstance_all(x, pd.DataFrame)),
        cs=['(df, df2)'],
    ),
    '<ds>': dict(
        E='データ列',
        fn=make_filter(pd.Series),
        e=['df[$1]'],
        cs=['df[_列名_]'],
    ),
    '<xdata>': dict(
        E='X軸のデータ列',
        fn=make_filter((pd.Series, np.ndarray)),
        e=['df[$1]', 'np.arange($1)'],
        cs=['df[_列名_]'],
    ),
    '<ydata>': dict(
        E='y軸のデータ列',
        fn=make_filter((pd.Series, np.ndarray)),
        e=['df[$1]', 'np.sin($1)'],
        cs=['df[_列名2_]'],
    ),
    # '<tuple_df>': ['(df,df2)'],
    # '<col>': ['_列名_'],
    '<func>': dict(
        E='関数',  # リスト
        fn=make_filter(object, lambda x: callable(x)),
        cs=['int', 'str', 'float'],
    ),
    '<class>': dict(
        E='クラス名',  # リスト
        fn=make_filter(type(None)),
        cs=['int', 'str', 'C', 'Person'],
    ),
    '<null>': dict(
        E='None',  # リスト
        fn=make_filter(type(None)),
        cs=['None'],
    ),
}


def extract_names(vars, fn=lambda x: True):
    ss = []
    for key, value in vars.items():
        if fn(value):
            ss.append(key)
    return ss


def set_expr(e, all_names):
    for i in range(0, 3):
        idx = f'${i}'
        if idx in e:
            v = random.choice(all_names)
            e = e.replace(idx, v)
    return e


def test_expr(code, fn):
    warnings.simplefilter('error')
    try:
        v = eval(code, None, test_vars())
        return fn(v)
    except:
        return False


def gen_expression(e, all_names, fn):
    for _ in range(N_TRY*2):
        code = set_expr(e, all_names)
        if test_expr(code, fn):
            return code
    return None


def shuffle_expression():
    vars = test_vars()
    all_names = [n for n in extract_names(vars) if n[0] != '_']
    for _, d in EXPRESSION_PATTERN.items():
        if 'cs' in d:
            all_names.extend(d['cs'])
    for key, d in EXPRESSION_PATTERN.items():
        if 'ns' not in d:
            d['ns'] = extract_names(vars, d['fn'])
        if 'cs' not in d:
            d['cs'] = []
        es = []
        if 'e' in d:
            for e in d['e']:
                code = gen_expression(e, all_names, d['fn'])
                if code is not None:
                    es.append(code)
        ss = []
        for x in d['ns']+d['cs']+es:
            if test_expr(x, d['fn']):
                ss.append(x)
        d['es'] = ss
        # print(key, ss)


shuffle_expression()


def is_modulename(ty):
    return not ty.startswith('<')


def get_expr(ty):
    if is_modulename(ty):
        return ty
    if ty not in EXPRESSION_PATTERN:
        debug(f'NOT IN EXPRESSION_PATTERN: {ty}')
        ty = random.choice(list(EXPRESSION_PATTERN.keys()))
    return random.choice(EXPRESSION_PATTERN[ty]['es'])


def select_expr(ty=None, wrong=False, identifier_only=False):
    if ty is None:
        wrong = True
        ty = random.choice(list(EXPRESSION_PATTERN.keys()))
    if is_modulename(ty):
        identifier_only = True
    while True:
        if wrong:
            ty = random.choice(list(EXPRESSION_PATTERN.keys()))
        v = get_expr(ty)
        if (not identifier_only) or v.isidentifier():
            break
    return v


def select_all(ty, identifier_only=False):
    if ty is None:
        return None
    if isinstance(ty, (list, tuple)):
        return [select_expr(x, identifier_only=identifier_only) for x in ty]
    return select_expr(ty, identifier_only=identifier_only)


def select_wrong(value=None, identifier_only=False):
    if isinstance(value, str):
        if value.startswith('"') or value.startswith("'"):
            return select_all('<int>')
        if value.startswith('True') or value.startswith("False"):
            return repr(value)
        return repr(value)
    return select_expr(wrong=True, identifier_only=identifier_only)


def expect(ty_or_value):
    if ty_or_value.startswith('<'):
        if ty_or_value in EXPRESSION_PATTERN:
            return EXPRESSION_PATTERN[ty_or_value]['E']
        return 'お手本通り'
    if ty_or_value.startswith('"') or ty_or_value.startswith("'"):
        return '文字列'
    if ty_or_value.startswith('['):
        return 'リスト'
    if ty_or_value.startswith('('):
        return 'タプル'
    if ty_or_value == 'True' or ty_or_value == "False":
        return '論理値'
    if ty_or_value.startswith('-'):
        ty_or_value = ty_or_value[1:]
    if ty_or_value.isdigit():
        return '整数'
    return ty_or_value  # よくわからない

# snippet


_COMMON = """\
$var$ = $$
$var$ = [$$]
$var$.append($$)
print($$)
print('result:', $$)
print('Value is "{}"'.format($$))
"""

_NUM = """\
$var$ = $$
$var$ = $$ $op$ $num$
if $$ $cmp$ $num$:
while $$ $cmp$ $num$:
    return $$
    return $num$ $op$ $$
if $$+$num$ $cmp$ $num$:
if $$ $cmp$ $num$ and $bool$:
if $bool$ and $$ $cmp$ $num$:
if $$ $cmp$ $num$ or $bool$:
if $bool$ or $$ $cmp$ $num$:
"""

_BOOL = '''\
assert $$
'''


SNIPET = {
    'bool': _COMMON+_BOOL,
    'float': _COMMON+_NUM,
}


def init_snipet():
    for key, value in SNIPET.items():
        SNIPET[key] = [v for v in value.splitlines() if '$$' in v]


init_snipet()

_MASKED_PATTERN = {
    '$cmp$': '== != < <= >= > =='.split(),
    '$op$': '+ - * ** / // % + -'.split(),
    '$sign$': ['-', ''],
}


def random_token(mask):
    if mask in _MASKED_PATTERN:
        return random.choice(_MASKED_PATTERN[mask])
    return random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


_MASK = re.compile(r'(\$[^\$]+\$)')


def replace_token(code):
    for mask in re.findall(_MASK, code):
        selected = random_token(mask)
        code = code.replace(mask, selected, 1)
    return code


def apply_snippet(ty, code):
    code = code.replace('  ', ' ')
    format = '$$'
    if ty in SNIPET:
        format = random.choice(SNIPET[ty])
    return replace_token(format.replace('$$', code))


def update_hint(params, hint):
    ss = [hint]
    for p in params:
        if isinstance(p, str) and p.startswith('#'):
            ss.append(p[1:])
    return ' '.join(ss)


def select(values, recursive=True):
    random.shuffle(values)
    value = values[0]
    if recursive and ' ' in value:
        values = value.split()
        random.shuffle(values)
        value = values[0]
    return value


def apply_snippet(ty, code):
    return code


def random_quote(text):
    if random.random() < 0.5:
        if '"' in text:
            return text.replace('"', "'")
        else:
            return text.replace("'", '"')
    return text


SUFFIX = '__1 __2 __3 __4 __5 __6 __7 __8 __9 __0'.split()


def remove_suffix(code):
    for suffix in SUFFIX:
        code = code.replace(suffix, '')
    code = code.replace(':pass', ':')
    return code


def extra_hint(emsg, hint):
    emsg = remove_suffix(emsg)
    hint = remove_suffix(hint)
    if 'NoneType' in emsg:
        hint = f'{hint} 解説_ノン型'
    return emsg, hint


VE_LOGS = []


class CodeCase(object):
    def __init__(self, case):
        self.case = case
        self.ret, self.tbase, self.name, *params = case
        self.tparams, self.kwarg = trim_params(params)
        self.is_operator = '.' not in self.name and not self.name.isidentifier()
        self.part = ''
        self.K = 0
        self.is_property = False
        if self.name.endswith('_'):
            self.is_property = True
            self.name = self.name[:-1]
        self.is_indexing = False
        if self.name.endswith('__get'):
            self.name = self.name[:-5]
            self.is_indexing = True
        self.is_slicing = False
        if self.name.endswith('__slice'):
            self.name = self.name[:-7]
            self.is_indexing = True
            self.is_slicing = True
        for _ in range(N_TRY):
            self.base = select_all(self.tbase)
            self.params = select_all(self.tparams)
            self.gen_emsg2()
            if self.emsg == '':
                break

    def set_K(self, K):
        self.K = K
        self.part = 'キーワード引数'
        if isinstance(K, int):
            if self.is_operator:
                self.part = '右辺' if K == 1 else '左辺'
            else:
                if K == 0:
                    self.part = 'レシーバ'
                else:
                    self.part = '添字' if self.is_indexing else '引数'

    def gen_hint(self, how, W=None, E=None, S=None, remove_R=False):
        hint = Hint()
        not_typo = True
        if how == 'タイポ':
            not_typo = False
        elif '型' in how:
            hint.append('_型ミス')
        if how.endswith('_'):
            hint.append(f'{how}{self.part}')
        else:
            hint.append(f'{how}')
        if not_typo:
            if self.is_operator:
                hint.append(T='演算子', O=self.name)
            elif self.is_property:
                if self.base is None:
                    hint.append(T='変数', V=self.name)
                else:
                    if not remove_R:
                        hint.append(R=self.base)
                    hint.append(T='プロパティ', P=self.name)
            elif self.is_indexing:
                hint.append(R=self.base)
            elif self.base is None:
                hint.append(T='関数', F=self.name)
            else:
                if not remove_R:
                    hint.append(R=self.base)
                hint.append(T='メソッド', M=self.name)
            if self.K != 0 and self.K != 1:
                hint.append(K=self.K)
        hint.append(W=W)
        hint.append(E=E)
        hint.append(S=S)
        return hint

    def gencode(self):
        if self.is_operator:
            if len(self.params) == 1:
                spc = random_spc()
                return f'{self.base}{spc}{self.name}{spc}{self.params[0]}'
            else:
                return f'{self.name}{self.base}'
        if self.is_property:
            if self.base is None:
                return apply_snippet(self.ret, self.name)
            return f'{self.base}.{self.name}'
        open, close, comma, dot = '(', ')', random_comma(), '.'
        if self.base is None:
            base = ''
            dot = ''
        elif self.base.isidentifier() or self.base[-1] in ')]}':
            base = f'{self.base}'
        else:
            base = f'({self.base})'
        if self.is_indexing:
            open, close = '[', ']'
            if self.name == '':
                dot = ''
        if self.is_slicing:
            comma = ':'
        func = f'{base}{dot}{self.name}'
        params = self.params[:]
        if self.kwarg != '':
            params.append(self.kwarg)
        params = comma.join(params)
        return f'{func}{open}{params}{close}'

    def gen_emsg2(self, code=None):
        self.code = self.gencode() if code is None else code
        self.ret, self.emsg = typecheck(self.code)

    def update(self, hint):
        self.hint = hint
        hint.update(self.emsg)
        return True

    def jsonfy(self, hint=None):
        code = remove_suffix(self.code)
        emsg = remove_suffix(self.emsg)
        hint = remove_suffix(str(hint if hint else self.hint))
        d = dict(
            eline=code,
            emsg=emsg,
            hint=hint,
            code=code,
        )
        return d

    def record(self, log=VE_LOGS, hint=None):
        if self.emsg != '':
            if hint is not None:
                self.update(hint)
            result = self.jsonfy(hint=hint)
            key = (result['emsg'], result['eline'])
            if key not in DUP:
                log.append(result)
                DUP[key] = result['hint']
                Counter_EMSG.update([result['emsg']])


# Injector


def misspell(tok):
    r = random.random()
    if r < 0.2:
        gen = typo.StrErrer(tok)
        tok = str(gen.char_swap())
        r = random.random()
        if int(17 * r) % 2 == 0:
            return tok
    if r > 0.9:
        gen = typo.StrErrer(tok)
        tok2 = str(gen.unichar())
        if tok != tok2:
            return tok2
    if len(tok) > 3:
        s = tok[0]
        e = tok[-1]
        gen = typo.StrErrer(tok[1:-1])
        if r < 0.5:
            return f'{s}{str(gen.missing_char().result)}{e}'
        return f'{s}{str(gen.nearby_char().result)}{e}'
    else:
        gen = typo.StrErrer(tok)
        if r < 0.5:
            return str(gen.extra_char().result)
        return str(gen.similar_char().result)


def wrong_value(value):
    if value.startswith('"') or value.startswith("'"):
        return repr(misspell(value[1:-1]))
    if value.isdigit():
        return '-1000'
    return None


SYNTAX_ERROR = [
    ('', '    ', '削除_インデント'), ('', '　　', '修正_全角空白'),
    ('(', '((', '追加_閉じ括弧'), (')', '', '追加_閉じ括弧'),
    ('(', '', '削除_閉じ括弧'), (')', '))', '削除_閉じ括弧'),
    ('[', '[[', '追加_閉じ四角括弧'), (']', '', '追加_閉じ四角括弧'),
    ('[', '', '削除_閉じ四角括弧'), (']', ']]', '削除_閉じ四角括弧'),
    ('{', '{{', '追加_閉じ中括弧'), ('}', '', '追加_閉じ中括弧'),
    ('{', '', '削除_閉じ中括弧'), (')', '))', '削除_閉じ中括弧'),
    ('(', '[', '修正_括弧不一致'), (']', ')', '削除_閉じ括弧'),
    ('()', '', '追加_コール'),  (',', '(),', '削除_コール'),
    ('",', '"', '追加_カンマ'),  ('),', ')', '追加_カンマ'),
    ("',", "'", '追加_カンマ'),  ('],', ']', '追加_カンマ'),
    ("},", "}", '追加_カンマ'),
    ('"', '', '追加_ダブルクオート'), ("'", '', '追加_シングルクオート'),
    ('"', "'", '修正_クオート不一致'), ("'", '"', '修正_クオート不一致'),
    ('.', '=', '修正_代入'),
    ('.', ',', '修正_カンマ'), ('.', ',', '修正_カンマ'),
    (',', ':', '修正_コロン'), (',', ' ', '追加_カンマ'),
    (',', '.', '修正_ピリオド'), (',', '.', '修正_ピリオド'),
    (':', '', '追加_コロン'),
    ('*', ':', '修正_コロン'), (' * ', '', '修正_積 解説_数学式'),
    (':', ',', '修正_カンマ'),
    (':', ';', '修正_セミコロン'),
    ('+', '＋', '修正_全角文字'),
    ('-', 'ー', '修正_全角文字'),
    ('*', '＊', '修正_全角文字'), ('*', '×', '修正_全角文字'),
    ('/', '／', '修正_全角文字'), ('/', '÷', '修正_全角文字'),
    ('=', '＝', '修正_全角文字'),
    ('<', '＜', '修正_全角文字'), ('<=', '≦', '修正_全角文字'),
    ('>', '＞', '修正_全角文字'), ('>=', '≧', '修正_全角文字'),
    ('(', '（', '修正_全角文字'), (')', '）', '修正_全角文字'),
    ('[', '［', '修正_全角文字'), (']', '］', '修正_全角文字'),
    ('{', '｛', '修正_全角文字'), ('}', '｝', '修正_全角文字'),
    (':', '：', '修正_全角文字'), ('.', '．', '修正_全角文字'),
    ('#', '＃', '修正_全角文字'),
    ("'", '’', '修正_引用符'),
    ("'", '‘', '修正_引用符'), ("'", '’', '修正_引用符'),
    ('"', '“', '修正_二重引用符'), ('"', '”', '修正_二重引用符'),
    ('$', ':', '削除_コロン'), ('$', ';', '削除_セミコロン'),
    ('$', '　', '修正_全角空白'),
]


def SE(cc):  # 構文エラーを発生
    for _ in range(N_TRY):
        c, e, h = random.choice(SYNTAX_ERROR)
        code = apply_snippet(cc.ret, cc.code)
        cc.ret = ''
        modified = None
        _H = ''
        if c == '':
            if random.random() < 0.5:
                modified = e+code
                break
        elif c == '$':
            if random.random() < 0.5:
                modified = code+e
                c = ''
                break
        else:
            for i in range(len(code)):
                if code.startswith(c, i) and random.random() < 0.5:
                    prefix = code[:i]
                    suffix = code[i+len(c):]
                    modified = (prefix+e+suffix)
                    _H = prefix[-4:]
                    break
        if modified is None:
            continue
        hint = Hint(h, H=_H, W=e, S=c, DEBUG=cc.code)
        cc.gen_emsg2(code=modified)
        if cc.emsg != '':
            return cc.update(hint)
    return False


def VE(cc):  # 値エラーを強制的に発生
    for _ in range(N_TRY):
        hint = cc.gen_hint('X修正_')
        cc.gen_emsg2()
        if cc.emsg != '':
            return cc.update(hint)
    return False


def NE(cc):
    if len(cc.name) < 4 or not cc.name.isidentifier():
        return False
    wrong = misspell(cc.name)
    hint = cc.gen_hint('タイポ', W=wrong, S=cc.name)
    cc.name = wrong
    cc.gen_emsg2()
    if cc.emsg != '':
        return cc.update(hint)
    return False


def TER(cc):
    if cc.base is None:
        return False
    for _ in range(N_TRY):
        expected = expect(cc.tbase)
        wrong = select_wrong(identifier_only=True)
        cc.set_K(0)
        cc.base = wrong
        hint = cc.gen_hint('修正型_', W=wrong, E=expected)
        cc.gen_emsg2()
        if is_type_error(cc.emsg):
            return cc.update(hint)
        if cc.is_operator:
            hint = cc.gen_hint('修正_', W=wrong, E=expected)
            cc.record(hint=hint)
        if cc.is_indexing:
            hint = cc.gen_hint('修正_', W=wrong, E='リストや文字列など')
            cc.record(hint=hint)
    return False


def NER(cc):
    if cc.tbase is None or cc.is_operator or cc.is_indexing:
        return False
    expected = expect(cc.tbase)
    hint = f'_変数なし' if cc.is_property else '_関数なし'
    if cc.tbase.startswith('<'):
        hint = f'{hint} 追加_レシーバかも'
    else:
        hint = f'{hint} 追加_モジュール'
    hint = cc.gen_hint(hint, remove_R=True, E=expected)
    cc.base = None
    if cc.emsg.startswith('NameError'):
        return cc.update(hint)
    return False


def TE1(cc, index=1):
    if len(cc.params) < index:
        return False
    for _ in range(N_TRY):
        expected = expect(cc.tparams[index-1])
        wrong = select_wrong()
        cc.set_K(index)
        hint = cc.gen_hint('修正型_', W=wrong, E=expected)
        cc.params[index-1] = wrong
        cc.gen_emsg2()
        if is_type_error(cc.emsg):
            return cc.update(hint)
        hint = cc.gen_hint('修正_', W=wrong, E=expected)
        cc.record(hint=hint)
        cc.emsg = ''
    return False


def TE2(cc):
    return TE1(cc, index=2)


def TE3(cc):
    return TE1(cc, index=3)


def TE4(cc):
    return TE1(cc, index=4)


def TEI(cc):
    if cc.is_operator or cc.is_property or cc.kwarg != '':
        return False
    wrong = select_wrong()
    cc.set_K(len(cc.tparams)+1)
    hint = cc.gen_hint('削除_', W=wrong)
    cc.params.append(wrong)
    cc.gen_emsg2()
    if cc.emsg != '' and not is_type_error(cc.emsg):
        return cc.update(hint)
    return False


def TED(cc):
    if len(cc.params) == 0 or cc.is_operator or cc.is_indexing:
        return False
    cc.set_K(len(cc.tparams)+1)
    hint = cc.gen_hint('追加_', E=expect(cc.tparams[-1]))
    cc.params = cc.params[:-1]
    cc.gen_emsg2()
    if cc.emsg != '':
        return cc.update(hint)
    return False


KW = ['length=128', 'encoding="utf-8"', 'start=0', 'end=""']


def KN(cc):  # キーワードのタイポ
    if cc.kwarg == '':
        return False
    if cc.kwarg not in KW:
        KW.append(cc.kwarg)
    key, _, value = cc.kwarg.partition('=')
    key_ = misspell(key)
    hint = cc.gen_hint('タイポ', W=key_, S=key)
    cc.kwarg = f'{key_}={value}'
    cc.gen_emsg2()
    if cc.emsg != '':
        return cc.update(hint)
    return False


def KT(cc):  # キーワードの型エラー
    if cc.kwarg == '':
        return False
    for _ in range(N_TRY//2):
        key, _, value = cc.kwarg.partition('=')
        cc.set_K(key)
        expected = expect(value)
        wrong = select_wrong(value)
        hint = cc.gen_hint('修正型_', W=wrong, E=expected)
        cc.kwarg = f'{key}={wrong}'
        cc.gen_emsg2()
        if is_type_error(cc.emsg):
            return cc.update(hint)
    return False


def KV(cc):  # キーワード値エラー
    if cc.kwarg == '':
        return False
    for _ in range(N_TRY):
        key, _, value = cc.kwarg.partition('=')
        wrong = wrong_value(value)
        if wrong is None:
            return False
        cc.set_K(key)
        wrong = select_wrong(value)
        hint = cc.gen_hint('修正_', W=wrong)
        cc.kwarg = f'{key}={wrong}'
        cc.gen_emsg2()
        if cc.emsg != '':
            return cc.update(hint)
    return False


def KA(cc):  # キーワード追加
    if cc.is_operator or cc.is_property or cc.is_indexing:
        return False
    if cc.kwarg != '' and random.random() > 0.9:
        return False
    for _ in range(N_TRY):
        random.shuffle(KW)
        cc.kwarg = KW[0]
        key, _, _ = cc.kwarg.partition('=')
        cc.set_K(key)
        hint = cc.gen_hint('削除_')
        cc.gen_emsg2()
        if cc.emsg.startswith('ValueError'):
            hint = cc.gen_hint('修正_')
            cc.record(hint=hint)
            cc.emsg = ''
        if cc.emsg != '':
            return cc.update(hint)
    return False


CASE = [SE, TER, NE, TE1, TE2, TE3, TE4, TEI, TED, KN, KT, KV, KA, NER, VE]

TEST = [
    ('<float', 'math', 'pi_'),
    # ('<list>', '<df>', 'columns_'),
    # ('<ds>', '<df>', '__get', '<col>'),
    # ('<slist>', '<df>', 'iat__get', '<int>', '<int>'),
    # ('<str>', '<str>', '__get', '<int0>'),
    # ('<str>', '<str>', '__slice', '<int0>', '<int0>'),
    # ('<int>', '<a>', '__get', '<int0>'),
    # ('<int>', '<a>', '__slice', '<int0>', '<int0>'),
    # ('<bool>', '<int>', '<', '<int>'),
    # ('<bool>', '<str>', '<', '<str>'),
    # ('<bool>', '<tuple>', '<', '<tuple>'),
    # ('<int>', '<int>', '+', '<int>'),
    # ('<str>', '<str>', '+', '<str>'),
    # ('<tuple>', '<tuple>', '+', '<tuple>'),
    ('<none>', '<model>', 'fit', '<target>', '<label>'),
]


def test_all(testcase=TEST):
    ss = []
    for test in testcase*3:
        # print(test, flush=True)
        VE_LOGS.clear()
        for fault_injector in CASE:
            cc = CodeCase(test)
            if cc.emsg != '':
                print('\033[32m[ERROR]\033[0m', test,
                      f'\n\t{cc.code}\n\t{cc.emsg}')
                break
            if fault_injector(cc):
                cc.record(log=ss)
        ss.extend(VE_LOGS[:3])
    return ss

# '\033[31m[DEBUG]\033[0m'


def dump(ss0):
    import kogi
    from kogi.task.diagnosis import convert_error_diagnosis
    UNDEFINED = collections.Counter()
    ss = []
    for d in ss0:
        d2 = convert_error_diagnosis(d, UNDEFINED=UNDEFINED)
        ss.append(d2)
        print('', d2['eline'])
        print('\033[31m', d2['emsg'], '\033[0m')
        print('   \033[32m' + d2['hint'], '\033[0m')
        print('   \033[33m' + d2['desc'], '\033[0m')
    print(len(ss))
    print(UNDEFINED.most_common())


if __name__ == '__main__':
    warnings.simplefilter('ignore')
    ss = test_all()
    dump(ss)
