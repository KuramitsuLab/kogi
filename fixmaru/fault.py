import collections
import keyword
import random
from hint import Hint
from codebase import CodeBase, is_identifer, misspell


class Fault(object):
    def __repr__(self):
        return self.__class__.__name__

    def precheck(self, cb: CodeBase, index):
        return index < len(cb.tparams)

    def inject(self, cb: CodeBase, index):
        if index == -1:
            return self.inject_name(cb)
        elif index == 0:
            return self.inject_base(cb)
        return self.inject_param(cb, index)

    def inject_name(self, cb: CodeBase):
        return False

    def inject_base(self, cb: CodeBase):
        return self.inject_param(cb, 0)

    def inject_param(self, cb: CodeBase, index):
        return False


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


class SyntaxErrorFault(Fault):

    def rmd(self, s: str):
        return s.removeprefix('$').removesuffix('$')

    def select_error(self, correct):
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

    def inject_name(self, cb: CodeBase):
        # correct = f'return {cb.get_snippet()} in 1'
        correct = cb.get_snippet()
        code = f'${correct}$'
        for _ in range(N_TRY):
            r, c, e, h, _H = self.select_error(correct)
            modified = None
            for i in range(len(code)):
                if code.startswith(c, i) and random.random() < r:
                    c = self.rmd(c)
                    prefix = self.rmd(code[:i])
                    suffix = self.rmd(code[i+len(c):])
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
            cb.check_emsg(code=modified)
            if cb.emsg != '':
                return cb.record(hint=hint, fix=correct)
        return False


class RareErrorFault(Fault):

    def __init__(self):
        self.imports = collections.Counter()

    def inject_name(self, cb: CodeBase):
        if hasattr(cb, 'evaled') and hasattr(cb.evaled, "__iter__"):

        stmts = [cb.seed.ns[stmt]
                 for stmt in cb.seed.ns if stmt.startswith('import')]
        if len(stmts) > 0:
            import_stmt = random.choice(stmts)
            self.imports.update([import_stmt])
            if self.imports[import_stmt] < 2:
                return self.inject_ImportError(cb, import_stmt)
        print('evaled', cb.evaled)
        if random.random() < 0.3 and hasattr(cb, 'evaled'):
            return self.inject_UnpackError(cb)
        return False

    def inject_ImportError(self, cb: CodeBase, import_stmt: str):
        cb.masters[CodeBase.FIX] = import_stmt
        correct = import_stmt
        tokens = correct.split()
        token = random.choice(tokens)
        i = tokens.index(token)
        wrong = misspell(token)
        modified = tokens[:]
        tokens[i] = wrong
        modified = ' '.join(tokens)
        cb.check_emsg(code=modified)
        if 'ModuleNotFoundError' in cb.emsg:
            hint = Hint('Aインストール忘れ Cもしくは Cタイポかも', W=wrong, S=token)
            return cb.record(hint)
        if cb.emsg != '':
            hint = Hint('Aタイポ', W=wrong, S=token)
            return cb.record(hint)
        return False

    def inject_UnpackError(self, cb: CodeBase):
        is_fixlen = isinstance(cb.evaled, tuple)
        n = len(cb.evaled)
        i = random.choice([i for i in range(1, min(n+3, 7)) if i != n])
        vars = ', '.join(['$var$']*i)
        code = f'{vars} = {cb.code}'
        print(code, n, i, cb.ret)
        cb.check_emsg(code=code)
        print(cb.emsg)
        if 'too many values to unpack' in cb.emsg:
            hint = Hint('A展開ミス B展開多い', E=i, S=n)
        elif 'not enough values to unpack' in cb.emsg:
            hint = Hint('A展開ミス B展開少ない', E=i, S=n)
        elif 'cannot unpack' in cb.emsg:
            hint = Hint('A展開ミス B展開不可')
        return False


# def SE2(cb: CodeCase):  # 構文エラーを発生


class NameTypoFault(Fault):
    def inject_name(self, cb: CodeBase):
        if cb.is_operator:
            return False
        correct = cb.get_name()
        name_len = len(correct)
        idn = cb._idname()
        while name_len > 2:
            wrong = misspell(correct)
            cb.set_wrong_name(wrong)
            hint = Hint(f'A{idn}なし Bタイポ', R=cb.safe_base(),
                        W=wrong, S=correct)
            if cb.check_emsg():
                cb.record(hint)
            name_len -= 3
        return False

    def inject_param(self, cb: CodeBase, index):
        correct = cb.get_param(index)
        if not is_identifer(correct) or len(correct) < 4:
            return False
        hint = Hint('A変数なし Bタイポ')
        wrong = misspell(correct)
        cb.set_wrong_param(index, wrong)
        cb.hint_for_param(hint, index=-1, correct=correct)
        if cb.check_emsg('NameError'):
            return cb.record(hint)
        return False


class NameErrorFault(Fault):
    def inject_name(self, cb: CodeBase):
        if cb.kind == 'module':
            maybe = 'Cモジュールかも'
            expected = cb.get_param(0)
            U = cb.seed.ns.get(f'import_{expected}', '')
            fix = True
        elif cb.kind == 'object':
            maybe = 'Cメソッドかも'
            expected = cb.expect(0)
            U = ''
            fix = False
        else:
            return False
        hint = f'A関数なし {maybe}' if cb.is_callable else f'A変数なし {maybe}'
        hint = Hint(hint, E=expected, U=U)
        cb.set_wrong_param(0, '')
        cb.tokens[CodeBase.DOT] = ''
        if cb.check_emsg('NameError'):
            print(hint)
            return cb.record(hint, fix=fix)
        return False

    def inject_param(self, cb: CodeBase, index):
        correct = cb.get_param(index)
        if not is_identifer(correct):
            return False
        if cb.seed.is_module(correct):
            U = cb.seed.ns.get(f'import_{correct}', '')
            hint = Hint('Aインポートなし B追加_インポート', U=U)
        elif correct.startswith('_') and correct.endswith('_'):
            hint = Hint('Aサンプル B修正_変数', E=cb.expect(index))
        else:
            hint = Hint('A変数なし B追加_変数', E=cb.expect(index))
        cb.disable(correct)
        if cb.check_emsg('NameError'):
            return cb.record(hint=hint)
        return False


N_TRY = 8


class TypeErrorFault(Fault):
    def inject_base(self, cb: CodeBase):
        if cb.kind == '':
            return False
        part = cb._left()
        N = cb.get_name() if not cb.is_indexer else ''
        for _ in range(N_TRY):
            expected = cb.expect(0)
            wrong = cb.seed.wrong_type(cb.tparams[0], identifier_only=True)
            cb.set_wrong_param(0, wrong)
            hint = Hint(f'A型ミス B型修正_{part}', N=N, W=wrong, E=expected)
            if cb.check_emsg() and hint.is_type_error(cb.emsg):
                cb.update_fix(0)
                return cb.record(hint)
        return False

    def inject_param(self, cb: CodeBase, index):
        part = cb._right()
        N = cb.get_name() if not cb.is_indexer else ''
        R = cb.safe_base() if cb.is_indexer else ''
        K = index
        for _ in range(N_TRY):
            expected = cb.expect(index)
            wrong = cb.seed.wrong_type(cb.tparams[index])
            cb.set_wrong_param(index, wrong)
            if '=' in wrong:
                K, _, wrong = wrong.partition('=')
                part = 'キーワード引数'
            hint = Hint(f'A型ミス B型修正_{part}', N=N, R=R,
                        K=K, W=wrong, E=expected)
            if cb.check_emsg() and hint.is_type_error(cb.emsg):
                cb.update_fix(index)
                return cb.record(hint)
        return False


# class ArgumentErrorFault(Fault):
#     def inject_base(self, cb: CodeBase):
#         if cb.is_operator or cb.is_indexer:
#             return False
#         if len(cb.tparams) > 1:
#             expected = cb.expect(1)
#             part = cb._right()
#             hint = Hint(f'A型ミス B追加_{part}', E=expected)
#             cb.tokens = cb.tokens[:-1]
#             if cb.check_emsg():
#                 return cb.record(hint)
#         else:
#             pass
#         return False

#     def inject_name(self, cb: CodeBase):
#         if len(cb.params) == 0 or cb.is_operator or cb.is_indexer:
#             return False
#         expected = cb.expect(1)
#         part = cb._right()
#         hint = Hint(f'A型ミス B追加_{part}', E=expected)
#         cb.tokens = cb.tokens[:-1]
#         if cb.check_emsg():
#             return cb.record(hint)
#         return False

#     def inject_param(self, cb: CodeBase, index):
#                 if cb.is_operator or cb.is_indexer:
#             return False

#         if len(cb.tparams) > 1:
#             expected = cb.expect(1)
#             part = cb._right()
#             hint = Hint(f'A型ミス B追加_{part}', E=expected)
#             cb.tokens = cb.tokens[:-1]
#             if cb.check_emsg():
#                 return cb.record(hint)
#         else:
#             pass

#         part = cb._right()
#         N = cb.get_name() if not cb.is_indexer else ''
#         R = cb.safe_base() if cb.is_indexer else ''
#         K = index
#         expected = cb.value(index)
#         if expected == '':
#             expected = cb.expect(index)
#         for _ in range(N_TRY):
#             wrong = cb.seed.wrong_value(cb.tparams[index])
#             cb.set_wrong_param(index, wrong)
#             if '=' in wrong:
#                 K, _, wrong = wrong.partition('=')
#                 part = 'キーワード引数'
#             hint = Hint(f'A値ミス B値修正_{part}', N=N, R=R,
#                         K=K, W=wrong, E=expected)
#             if cb.check_emsg():
#                 hint.update_expected(cb.emsg)
#                 return cb.record(hint)
#         return False


class ValueErrorFault(Fault):
    def inject_base(self, cb: CodeBase):
        return False

    def inject_param(self, cb: CodeBase, index):
        part = cb._right()
        N = cb.get_name() if not cb.is_indexer else ''
        R = cb.safe_base() if cb.is_indexer else ''
        K = index
        expected = cb.value(index)
        if expected == '':
            expected = cb.expect(index)
        for _ in range(N_TRY):
            wrong = cb.seed.wrong_value(cb.tparams[index])
            cb.set_wrong_param(index, wrong)
            if '=' in wrong:
                K, _, wrong = wrong.partition('=')
                part = 'キーワード引数'
            hint = Hint(f'A値ミス B値修正_{part}', N=N, R=R,
                        K=K, W=wrong, E=expected)
            if cb.check_emsg():
                hint.update_expected(cb.emsg)
                return cb.record(hint)
        return False


DebugFaults = [RareErrorFault()]
AllFaults = [SyntaxErrorFault(), NameTypoFault(), NameErrorFault(),
             TypeErrorFault(), ValueErrorFault()]
