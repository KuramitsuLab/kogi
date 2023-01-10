import keyword
import typo
import collections
import sys
import random
from expr import Seed
import testcase
from hint import Hint

N_TRY = 8
DUP = {}


def debug(msg):
    if msg not in DUP:
        print('\033[31m[DEBUG]\033[0m', msg)
        DUP[msg] = msg


N_VAR, N_FUNC, N_LEFT, N_RIGHT, FORMATS = 0, 1, 2, 3, 4

VOCAB = {
    "": ['変数', '関数', '', '引数', ('(', ',', ')')],  # tbase is None
    # tbase is <type>
    "object": ['プロパティ', 'メソッド', 'レシーバ', '引数', ('(', ',', ')')],
    "module": ['定数', '関数', 'モジュール', '引数', ('(', ',', ')')],  # tbase is モジュール
    "class": ['定数', '関数', 'クラス', '引数', ('(', ',', ')')],  # tbase is クラス
    "operator": ['', '演算子', '右辺', '左辺', ('(', ',', ')')],
    "indexer": ['', 'インデクサ', '列', '添字', ('[', ',', ']')],
    "slicer": ['', 'スライス', '列', '添字', ('[', ':', ']')],
}


def is_identifer(s: str):
    return len(s) > 0 and s.replace('.', '_').isidentifier()


DISABLE = -1
KEYWORD = -2
INC = -3
DEC = -4


class CodeCase(object):
    def __init__(self, seed: Seed, case):
        self.seed = seed
        self.case = case
        if isinstance(case, str):
            case = [v if v != '``' else None for v in case.split()]
        self.case = case
        self.tbase, self.name, *params = case
        self.additional_hint = []
        while len(params) > 0 and params[-1].startswith('#'):
            self.additional_hint.append(params[-1][1:])
            params = params[:-1]
        self.kwarg = ''
        if len(params) > 0 and '=' in params[-1]:
            self.kwarg = params[-1]
            params = params[:-1]  # 最後の一つだけ
        self.tparams = params
        self.is_property = False
        self.is_operator = False
        self.is_indexer = False
        self.is_slicer = False
        self.part = ''
        self.K = 0
        self._check_name()
        for _ in range(N_TRY):
            self.base = seed.select_expr(self.tbase)
            self.params = seed.select_expr(self.tparams)
            self.check_emsg()
            if self.emsg == '':
                break

    def _check_name(self):
        # 前処理
        if self.name.startswith('`'):
            self.name = self.name[1:-1].replace('_', ' ')
            if self.name[0].isalpha():
                self.name = f' {self.name}'
            if self.name[-1].isalpha():
                self.name = f'{self.name} '
        # チェック
        if self.name.endswith('_'):
            self.is_property = True
            self.name = self.name[:-1]
            self.kind = "" if self.tbase is None else "object"
            return
        if self.name.endswith('__get'):
            self.name = self.name[:-5]
            self.is_indexer = True
            self.kind = "indexer"
            return
        if self.name.endswith('__slice'):
            self.name = self.name[:-5]
            self.is_indexer = True
            self.kind = "slicer"
            return
        self.is_operator = not is_identifer(self.name)
        if self.is_operator:
            assert len(self.name) > 0
            self.kind = "operator"
            return
        if self.tbase is None:
            self.kind = ""
        elif self.tbase.startswith('<'):
            self.kind = "object"
        elif f'import_{self.tbase}' in self.seed.ns:
            self.kind = "module"
        else:
            self.kind = "class"

    def is_user_defined(self):
        return self.name.endswith('__Z')

    def get_name(self, kind=None):
        return VOCAB[kind or self.kind][N_VAR if self.is_property else N_FUNC]

    def get_left(self, kind=None):
        return VOCAB[kind or self.kind][N_LEFT]

    def get_right(self, kind=None):
        return VOCAB[kind or self.kind][N_RIGHT]

    def get_punctuation(self, kind=None):
        return VOCAB[kind or self.kind][FORMATS]

    def get_type(self, index):
        if index == 0:
            return self.tbase
        return self.tparams[index-1]

    def expect(self, index):
        return self.seed.expect(self.get_type(index))

    def get(self, index):
        if index == 0:
            return self.base
        return self.params[index-1]

    def set(self, index: int, value: str):
        if index < 0:
            if index == DISABLE:
                self.checkpoint = (index, value)
                self.seed.disable(value)
            elif index == KEYWORD:
                self.checkpoint = (index, self.kwarg)
                self.kwarg = value
            elif index == INC:
                self.checkpoint = (index, value)
                self.params.append(value)
            elif index == DEC:
                self.checkpoint = (index, self.params.pop())
        elif index == 0:
            self.checkpoint = (index, self.base)
            self.base = value
        else:
            self.checkpoint = (index, self.params[index-1])
            self.params[index-1] = value

    def rollback(self):
        if not hasattr(self, 'checkpoint'):
            return
        index, value = self.checkpoint
        if index < 0:
            if index == DISABLE:
                self.seed.enable(value)
            elif index == KEYWORD:
                self.kwarg = value
            elif index == INC:
                self.params.pop()
            elif index == DEC:
                self.params.append(value)
        else:
            self.set(index, value)
        delattr(self, 'checkpoint')

    def disable(self, name: str):
        self.set(DISABLE, name)

    def append_params(self, value):
        self.set(INC, value)

    def pop_params(self):
        self.set(DEC, None)

    def repeat(self, fragment):
        pass

    def too_many_repeated(self, fragment):
        return False

    def gencode(self):
        spc = random.choice([' ', '', ' '])
        if self.is_operator and len(self.params) == 1:
            return f'{self.base}{spc}{self.name}{spc}{self.params[0]}'
        base = '' if self.base is None else self.base
        if len(base) > 0 and base[-1] not in ')]}':
            if not is_identifer(base):
                base = f'({base})'
        dot = '.' if base != '' and self.name != '' else ''
        callee = f'{base}{dot}{self.name}'
        if self.is_property:
            return callee
        open, comma, close = self.get_punctuation()
        params = self.params[:]
        if self.kwarg != '':
            params.append(self.kwarg)
        params = (comma+spc).join(params)
        return f'{callee}{open}{params}{close}'

    def set_K(self, K):
        self.K = K
        self.part = 'キーワード引数'
        if isinstance(K, int):
            self.part = self.get_left() if K == 0 else self.get_right()

    def gen_hint(self, how, detail=True, R='', W=None, E=None, S=None, U=None):
        hint = Hint()
        if how.endswith('_'):
            hint.append(f'{how}{self.part}')
        else:
            hint.append(f'{how}')
        if detail:
            suffix = '' if self.is_property or self.is_indexer or self.is_operator else '()'
            if R is not None:
                R = None if self.is_operator else self.base
            hint.append(T=self.get_name(),
                        N=f'{self.name.strip()}{suffix}', R=R)
        if self.K != 0 and self.K != 1:
            hint.append(K=self.K)
        hint.append(W=W, E=E, S=S, U=U)
        return hint

    def check_emsg(self, code=None):
        self.code = self.gencode() if code is None else code
        self.emsg = ''
        test_vars = self.seed.test_vars()
        try:
            exec(self.code, None, test_vars)
        except Exception as e:
            _, em, _ = sys.exc_info()
            self.emsg = f'{e.__class__.__name__}: {em}'
        self.ret = ''
        if self.emsg == '' and code is None:
            try:
                self.evaled = eval(self.code, None, test_vars)
                self.ret = type(self.evaled).__name__
            except SyntaxError as e:
                self.ret = ''  # 評価できない
            except:
                self.ret = ''  # 評価できない

    def apply_snippet(self, templ, code=None):
        return self.seed.apply_snippet(templ, code or self.code)[0]

    def get_snippet(self):
        self.code, _ = self.seed.apply_snippet(self.ret, self.code)
        self.ret = ''
        return self.code

    def record(self, hint, fix=None):
        if self.emsg == '':
            return False
        hint.update(self.emsg, self.code, self.seed.local_hints)
        code = self.get_snippet()
        d = dict(
            eline=code,
            emsg=self.emsg,
            hint=hint,
        )
        if fix is not None:
            d['fix'] = fix
        self.seed.record(d)
        return True

# FalltInjector


SYNTAX_ERROR = [
    ('$', '    ', 'B削除_インデント'), ('$', '　　', 'B修正_全角空白'),
    ('$', ' ', 'B削除_インデント'), ('$', '>>> ', 'B削除_ゴミ'),
    ('(', '((', 'B追加_閉じ括弧'), (')', '', 'B追加_閉じ括弧'),
    ('(', '', 'B削除_閉じ括弧'), (')', '))', 'B削除_閉じ括弧'),
    ('[', '[[', 'B追加_閉じ四角括弧'), (']', '', 'B追加_閉じ四角括弧'),
    ('[', '', 'B削除_閉じ四角括弧'), (']', ']]', 'B削除_閉じ四角括弧'),
    ('{', '{{', 'B追加_閉じ中括弧'), ('}', '', 'B追加_閉じ中括弧'),
    ('{', '', 'B削除_閉じ中括弧'), (')', '))', 'B削除_閉じ中括弧'),
    ('(', '[', 'B修正_四角括弧不一致'), (']', ')', 'B修正_括弧不一致'),
    ('()', '', 'B追加_コール'),  (',', '(),', 'B削除_コール'),
    ('[]', '()', 'B修正_コール添字'),  ('()', '[]', 'B削除_添字コール'),
    ('",', '"', 'B追加_カンマ'),  ('),', ')', 'B追加_カンマ'),
    ("',", "'", 'B追加_カンマ'),  ('],', ']', 'B追加_カンマ'),
    ("},", "}", 'B追加_カンマ'),
    ('"', '', 'B追加_ダブルクオート'), ("'", '', 'B追加_クオート'),
    ('"', "'", 'B修正_クオート不一致'), ("'", '"', 'B修正_クオート不一致'),
    ('.', '=', 'B修正_代入'),
    ('.', ',', 'B修正_カンマ'), ('.', ',', 'B修正_カンマ'),
    (',', ':', 'B修正_コロン'), (',', ' ', 'B追加_カンマ'),
    (',', '.', 'B修正_ピリオド'), (',', '.', 'B修正_ピリオド'),
    (':', '', 'B追加_コロン'),
    ('*', ':', 'B修正_コロン'), (' * ', '', 'B修正_積 E数学式'),
    (':', ',', 'B修正_カンマ'),
    (':', ';', 'B修正_セミコロン'),
    ('==', '=', 'B修正_代入 C等号記号'),
    (' = ', ' == ', 'B修正_イコール C等号記号'),
    (' ', '　', 'B修正_全角空白'),
    ('+', '＋', 'B修正_全角文字'),
    ('-', 'ー', 'B修正_全角文字'),
    ('*', '＊', 'B修正_全角文字'), ('*', '×', 'B修正_全角文字'),
    ('/', '／', 'B修正_全角文字'), ('/', '÷', 'B修正_全角文字'),
    ('=', '＝', 'B修正_全角文字'),
    ('<', '＜', 'B修正_全角文字'), ('<=', '≦', 'B修正_全角文字'),
    ('>', '＞', 'B修正_全角文字'), ('>=', '≧', 'B修正_全角文字'),
    ('(', '（', 'B修正_全角文字'), (')', '）', 'B修正_全角文字'),
    ('[', '［', 'B修正_全角文字'), (']', '］', 'B修正_全角文字'),
    ('{', '｛', 'B修正_全角文字'), ('}', '｝', 'B修正_全角文字'),
    (':', '：', 'B修正_全角文字'), ('.', '．', 'B修正_全角文字'),
    ('#', '＃', 'B修正_全角文字'),
    ("'", '’', 'B修正_引用符'),
    ("'", '‘', 'B修正_引用符'), ("'", '’', 'B修正_引用符'),
    ('"', '“', 'B修正_二重引用符'), ('"', '”', 'B修正_二重引用符'),
    ('$', ':', 'B削除_コロン'), ('$', ';', 'B削除_セミコロン'),
    ('$', '　', 'B修正_全角空白'),
    ('?', '$', 'Aタイポ D予約語'),
]

GOMI = ['>>> ', '[] ', '1', '1 ']


def select_error(correct):
    r = 1.0
    for _ in range(N_TRY):
        c, e, h = random.choice(SYNTAX_ERROR)
        if '全角' in h and random.random() < 0.8:  # 全角は多いので減らす
            continue
        if h == 'B削除_ゴミ':
            e = random.choice(GOMI)
        if c == '?':
            ss = []
            for kw in keyword.kwlist:
                if kw in correct:
                    ss.append(kw)
            if len(ss) == 0:
                continue
            c = random.choice(ss)
            if f'{c} ' in correct and random.random() < 0.5:
                if len(c) == 2 and random.random() < 0.7:
                    return r, f'{c} ', '', f'B追加_予約語', ''
                return r, f'{c} ', c, f'B追加_空白', c
            else:
                return r, c, misspell(c), h, ''
        break
    if correct.count(c) > 0:
        r = 0.5
    return r, c, e, h, ''


def rmd(s):
    return s.removeprefix('$').removesuffix('$')


def SE0(cc: CodeCase):  # import の構文エラー
    stmts = [cc.seed.ns[stmt]
             for stmt in cc.seed.ns if stmt.startswith('import')]
    if len(stmts) == 0:
        return False
    correct = random.choice(stmts)
    tokens = correct.split()
    token = random.choice(tokens)
    i = tokens.index(token)
    wrong = misspell(token)
    modified = tokens[:]
    tokens[i] = wrong
    modified = ' '.join(tokens)
    cc.check_emsg(code=modified)
    if 'ModuleNotFoundError' in cc.emsg:
        hint = Hint('Aインストール忘れ Cもしくは Cタイポかも', W=wrong, S=token)
        return cc.record(hint, fix=correct)
    if cc.emsg != '':
        hint = Hint('Aタイポ', W=wrong, S=token)
        return cc.record(hint, fix=correct)
    return False


def SE(cc: CodeCase):  # 構文エラーを発生
    # correct = f'return {cc.get_snippet()} in 1'
    correct = cc.get_snippet()
    code = f'${correct}$'
    for _ in range(N_TRY):
        r, c, e, h, _H = select_error(correct)
        modified = None
        for i in range(len(code)):
            if code.startswith(c, i) and random.random() < r:
                c = rmd(c)
                prefix = rmd(code[:i])
                suffix = rmd(code[i+len(c):])
                modified = (prefix+e+suffix)
                if _H == '':
                    _H = Hint.head(prefix)
                break
        if modified is None:  # もう一度
            continue
        if h.startswith('A'):
            hint = Hint(h, W=e, S=c)
        else:
            hint = Hint(f'A構文ミス {h}', H=_H, W=e, S=c)
        cc.check_emsg(code=modified)
        if cc.emsg != '':
            return cc.record(hint=hint, fix=correct)
    return False


def SE2(cc: CodeCase):  # 構文エラーを発生
    if not hasattr(cc, 'evaled'):
        return False
    if isinstance(cc.evaled, (list, tuple)):
        is_fixlen = isinstance(cc.evaled, tuple)
        n = len(cc.evaled)
        i = random.choice([i for i in range(1, min(n+3, 7)) if i != n])
        vars = ', '.join(['$var$']*i)
        templ = f'{vars} = @@'
        code = cc.apply_snippet(templ)
        print(code, n, i, cc.ret)
        cc.check_emsg(code=code)
        print(cc.emsg)
        if 'too many values to unpack' in cc.emsg:
            hint = Hint('A展開多い', E=i, S=n)
        elif 'not enough values to unpack' in cc.emsg:
            hint = Hint('A展開少ない', E=i, S=n)
        elif 'cannot unpack' in cc.emsg:
            hint = Hint('A展開不可')
    return False


STYPO = 'char_swap missing_char extra_char nearby_char similar_char repeated_char unichar'.split()


def misspell(s):
    if '__' in s and not s.endswith('__'):
        name, sep, suffix = s.rpartition('__')
        return f'{misspell(name)}{sep}{suffix}'
    gen = typo.StrErrer(s)
    s2 = str(getattr(gen, random.choice(STYPO))().result)
    if s != s2 and (len(s) < 3 or random.random() < 0.8):
        return s2
    gen = typo.StrErrer(s2)
    return str(getattr(gen, random.choice(STYPO))().result)


def NE(cc, maxlen=4):
    if len(cc.name) < maxlen or cc.is_user_defined() or cc.is_operator:
        return False
    correct = cc.name
    wrong = misspell(cc.name)
    hint = cc.gen_hint('Aタイポ', W=wrong, S=cc.name)
    cc.name = wrong
    cc.check_emsg()
    if cc.emsg != '':
        cc.name = correct
        return cc.record(hint, fix=cc.gencode())
    return False


def NE2(cc):
    return NE(cc, maxlen=8)


def NM(cc: CodeCase):
    if cc.is_operator or cc.is_indexer:
        return False
    for name in [cc.tbase]+cc.tparams:
        fix = f'import_{name}'
        if fix in cc.seed.ns:
            break
        fix = None
    if fix is None:
        return False
    fix = cc.seed.ns[fix]
    hint = cc.gen_hint('Aインポート忘れ', U=fix)
    cc.seed.disable(name)
    cc.check_emsg()
    cc.seed.enable(name)
    if cc.emsg != '':
        return cc.record(hint, fix=fix)
    return False


def NER2(cc: CodeCase):
    if cc.tbase is None or cc.is_operator or cc.is_indexer:
        return False
    expected = cc.seed.expect(cc.tbase)
    hint = f'A変数なし' if cc.is_property else 'A関数なし'
    orig = None
    if cc.tbase.startswith('<'):
        hint = f'{hint} Cメソッドかも'
    else:
        hint = f'{hint} Cモジュールかも'
        orig = cc.base
    hint = cc.gen_hint(hint, E=expected)
    cc.base = None
    cc.check_emsg()
    if cc.emsg.startswith('NameError'):
        if orig:
            cc.base = orig
            return cc.record(hint, fix=cc.gencode())
        return cc.record(hint)
    return False


def NameErrorParam(cc: CodeCase, index=0):
    correct = cc.get(index)
    if correct is None or not correct.isidentifier() or cc.too_many_repeated(correct):
        return False
    if index == 0 and cc.kind in ('module', 'class'):
        return False
    expected = cc.expect(index)
    cc.set_K(index)
    if len(correct) > 4 and random.random() < 0.5:
        wrong = misspell(correct)
        cc.set(index, wrong)
        cc.check_emsg()
        cc.rollback()
        hint = Hint('A変数なし Bタイポ', W=wrong, S=correct)
    else:
        cc.disable(correct)
        cc.check_emsg()
        cc.rollback()
        hint = Hint('A変数なし B追加_変数', E=expected)
        cc.repeat(correct)
    if 'NameError' in cc.emsg:
        return cc.record(hint=hint)
    return False


def NE0(cc: CodeCase):
    return NameErrorParam(cc, index=0)


def NE1(cc: CodeCase):
    return NameErrorParam(cc, index=1)


def NE2(cc: CodeCase):
    return NameErrorParam(cc, index=2)


def NE3(cc: CodeCase):
    return NameErrorParam(cc, index=3)


def TER(cc):
    if cc.base is None:
        return False
    for _ in range(N_TRY):
        expected = cc.seed.expect(cc.tbase)
        wrong = cc.seed.select_wrong(identifier_only=True)
        cc.set_K(0)
        cc.base = wrong
        hint = cc.gen_hint('A型ミス B修正型_', W=wrong, E=expected)
        cc.check_emsg()
        if hint.is_type_error(cc.emsg):
            cc.base = f'_{expected}_'
            return cc.record(hint, fix=cc.gencode())
        if cc.is_operator:  # or cc.is_indexer:
            hint = cc.gen_hint('A値ミス B修正_', W=wrong, E=expected)
            cc.record(hint=hint)
    return False


def TE1(cc: CodeCase, index=1):
    if len(cc.params) < index:
        return False
    if '=' in cc.tparams[index-1]:  # キーワード引数は変更しない
        return False
    for _ in range(N_TRY):
        expected = cc.seed.expect(cc.tparams[index-1])
        wrong = cc.seed.select_wrong()
        cc.set_K(index)
        hint: Hint = cc.gen_hint('A型ミス B修正型_', W=wrong, E=expected)
        cc.params[index-1] = wrong
        cc.check_emsg()
        if hint.is_type_error(cc.emsg):
            return cc.record(hint)
        hint = cc.gen_hint('A値ミス B修正_', W=wrong, E=expected)
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
    fix = cc.code
    wrong = cc.seed.select_wrong()
    cc.set_K(len(cc.tparams)+1)
    hint = cc.gen_hint('A型ミス B削除_', W=wrong)
    cc.params.append(wrong)
    cc.check_emsg()
    if 'arg' in cc.emsg:  # and not hint.is_type_error(cc.emsg):
        return cc.record(hint, fix=fix)
    return False


def TED(cc: CodeCase):
    if len(cc.params) == 0 or cc.is_operator or cc.is_indexer:
        return False
    cc.set_K(len(cc.tparams)+1)
    hint = cc.gen_hint('A型ミス B追加_', E=cc.seed.expect(cc.tparams[-1]))
    cc.params = cc.params[:-1]
    cc.check_emsg()
    if cc.emsg != '':
        hint.append('Cサンプル読め')
        return cc.record(hint)
    return False


def KN(cc):  # キーワードのタイポ
    if cc.kwarg == '':
        return False
    cc.seed.past_kw.append(cc.kwarg)
    key, _, value = cc.kwarg.partition('=')
    key_ = misspell(key)
    hint = cc.gen_hint('Aタイポ', W=key_, S=key)
    cc.kwarg = f'{key_}={value}'
    cc.check_emsg()
    if cc.emsg != '':
        cc.kwarg = f'{key}={value}'
        return cc.record(hint, fix=cc.gencode())
    return False


def KT(cc):  # キーワードの型エラー
    if cc.kwarg == '':
        return False
    for _ in range(N_TRY//2):
        key, _, value = cc.kwarg.partition('=')
        cc.set_K(key)
        expected = cc.seed.expect(value)
        wrong = cc.seed.select_wrong(value)
        hint = cc.gen_hint('A型ミス B修正型_', W=wrong, E=expected)
        cc.kwarg = f'{key}={wrong}'
        cc.check_emsg()
        if hint.is_type_error(cc.emsg):
            cc.kwarg = f'{key}={value}'
            return cc.record(hint, fix=cc.gencode())
    return False


def wrong_keyword_value(v):
    if v[0] in '"\'' and v[-1] in '"\'':
        q = v[0]
        s = v[1:-1]
        if s == '':
            return '0'
        return f'{q}{misspell(s)}{q}'
    return repr(v)


def KV(cc):  # キーワード値エラー
    if cc.kwarg == '':
        return False
    for _ in range(N_TRY):
        key, _, value = cc.kwarg.partition('=')
        wrong = wrong_keyword_value(value)
        cc.set_K(key)
        hint = cc.gen_hint('A値ミス B修正_', W=wrong)
        cc.kwarg = f'{key}={wrong}'
        cc.check_emsg()
        if cc.emsg != '':
            hint.append(f'C値タイポかも CW={wrong} CS={value}')
            return cc.record(hint)
    return False


def KA(cc):  # キーワード追加
    if cc.is_operator or cc.is_property or cc.is_indexer:
        return False
    if cc.kwarg == '' and len(cc.seed.past_kw) == 0:
        return False
    cc.params.append(cc.kwarg)
    kwarg = random.choice(cc.seed.past_kw)
    key, _, _ = kwarg.partition('=')
    cc.set_K(key)
    hint = cc.gen_hint('A型ミス B削除_')
    cc.check_emsg()
    if 'arg' in cc.emsg:
        cc.kwarg = cc.params.pop()
        return cc.record(hint, fix=cc.gencode())
    return False


def VE(cc):  # 値エラーを強制的に発生
    for _ in range(N_TRY):
        hint = cc.gen_hint('A値ミス 修正_引数X')
        cc.check_emsg()
        if cc.emsg != '':
            return cc.record(hint)
    return False


FAULT_SET = [
    SE0, SE, NE, NE2, NM,
    TER, TE1, TE2, TE3, TE4, TEI, TED,
    KN, KT, KV, KA, VE]


class Generator(object):
    def __init__(self, faults=FAULT_SET):
        self.generated = []
        self.faults = faults

    def generate(self, ns, specs, api_doc, n_times=1):
        seed = Seed(ns=ns, logs=self.generated)
        seed.load(specs)
        testcase = Seed.parse_testcase(api_doc)
        if n_times == 0:
            seed.dump()
        for test in testcase * n_times:
            for fault in self.faults:
                seed.fault = fault.__name__
                cc = CodeCase(seed, test)
                if cc.emsg != '':
                    print('\033[32m[ERROR]\033[0m', test,
                          f'\n\t{cc.code}\n\t{cc.emsg}')
                    break
                fault(cc)
        return self.generated

    def dump(self):
        import kogi
        from kogi.task.diagnosis import convert_error_diagnosis
        UNDEFINED = collections.Counter()
        ss = []
        for d in self.generated:
            d2 = convert_error_diagnosis(d, UNDEFINED=UNDEFINED)
            ss.append(d2)
            print(d['fault'], d2['eline'])
            print('\033[31m', d2['emsg'], '\033[0m')
            print('   \033[32m' + d2['hint'], '\033[0m')
            print('   \033[33m' + d2['desc'], '\033[0m')
            if 'fix' in d:
                print('   \033[36m' + d['fix'], '\033[0m')
        print(len(ss))
        print(UNDEFINED.most_common())


if __name__ == '__main__':
    gen = Generator(faults=[NameErrorParam])
    # gen = Generator()
    gen.generate(*testcase.DebugFaultSuite(), n_times=1)
    gen.dump()
