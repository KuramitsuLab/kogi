import sys
import random
import warnings
import collections
from typing import List, Dict
from debug import DEBUG
from randomcode import RandomCode
from hint import Hint
import typo

N_TRY = 8
DUP = {}
Counter_EMSG = collections.Counter()

_TYPO_METHOD = 'char_swap missing_char extra_char nearby_char similar_char repeated_char unichar'.split()


def misspell(s):
    if '__' in s and not s.endswith('__'):
        name, sep, suffix = s.rpartition('__')
        return f'{misspell(name)}{sep}{suffix}'
    if s.startswith('"') and s.endswith('"'):
        return f'"{misspell(s[1:-1])}"'
    if s.startswith("'") and s.endswith("'"):
        return f"'{misspell(s[1:-1])}'"
    gen = typo.StrErrer(s)
    s2 = str(getattr(gen, random.choice(_TYPO_METHOD))().result)
    if s != s2 and (len(s) < 6 or random.random() < 0.8):
        return s2
    gen = typo.StrErrer(s2)
    return str(getattr(gen, random.choice(_TYPO_METHOD))().result)


RANDOMCODE = RandomCode()


def isinstance_all(x, C):
    for a in x:
        if not isinstance(a, C):
            return False
    return True


def make_filter(C=object, fn=lambda x: True):
    def filter(x):
        return isinstance(x, C) and fn(x)
    return filter


def default_filter(x):
    return True


def mycopy(v, always_copy=True):
    if always_copy:
        if hasattr(v, 'copy'):
            return v.copy()
    return v


SUFFIX = '__1 __2 __3 __4 __5 __6 __7 __8 __9 __0 __A __Z'.split()


def remove_suffix(code):
    for suffix in SUFFIX:
        code = code.replace(suffix, '')
    return code


def append_unique(d, key, value, always_copy=True):
    if key not in d:
        d[key] = mycopy(value, always_copy=always_copy)
        return key
    for suffix in SUFFIX:
        new_key = f'{key}{suffix}'
        if new_key not in d:
            d[new_key] = mycopy(value, always_copy=always_copy)
            return new_key
    return None


def eval_filter(code, fn, code_names):
    warnings.simplefilter('error')
    try:
        v = eval(code, None, code_names)
        return fn(v)
    except:
        return False


def is_masked(s: str):
    return s.startswith('_') and s.endswith('_')


class Spec(object):
    def __init__(self, sample, E=None,
                 filter_fn=None, types=None,
                 vars={}, consts='', exprs=''):
        self.key = type(sample).__name__
        self.typevar = f'_{self.key}_'
        self.expect = E or self.key
        if filter_fn is None:
            self.filter_fn = make_filter(
                type(sample) if types is None else types)
        else:
            self.filter_fn = filter_fn
        self.vars = vars
        vars[self.typevar] = sample
        self.consts = consts.split() if isinstance(consts, str) else consts
        self.exprs = exprs.split() if isinstance(exprs, str) else exprs
        self.exprs.extend(['@@'] * (1+len(exprs)//2))
        self.all_vars = None
        self.code_names = []
        self.code_consts = []
        self.code_exprs = []
        self.typename = None

    def add_fragment(self, code, is_const=False):
        if self.typename is not None:
            key = f'C{self.typename}' if is_const else self.typename
            RANDOMCODE.add_fragment(key, code)

    def add_var(self, name, value, verbose=True):
        if self.filter_fn(value):
            new_key = append_unique(self.all_vars, name, value)
            if new_key:
                self.code_names.append(new_key)
                if self.typename is None:
                    self.typename = type(value).__name__
                self.add_fragment(new_key)
        elif verbose:
            DEBUG(f'variable type error: {name}={repr(value)}')

    def add_const(self, value, verbose=True):
        if eval_filter(value, self.filter_fn, None):
            self.code_consts.append(value)
            self.add_fragment(value, is_const=True)
        elif verbose:
            DEBUG(f'value type error: {repr(value)}')

    def init(self, all_vars):
        self.all_vars = all_vars
        for key, value in self.vars.items():
            self.add_var(key, value, verbose=True)
        for value in self.consts:
            self.add_const(value, verbose=True)

    def update(self, spec):
        for key, value in spec.vars.items():
            self.add_var(key, value, verbose=True)
        for value in spec.consts:
            self.add_const(value, verbose=True)
        self.exprs.extend(spec.exprs)

    def get_value(self, identifier_only=False):
        if identifier_only:
            return random.choice(self.code_names)
        return random.choice(self.code_names + self.code_consts)

    def get_expr_(self, test_vars=None, identifier_only=False):
        if identifier_only:
            return random.choice(self.code_names)
        if test_vars is not None and len(self.exprs) > 0:
            for _ in range(N_TRY):
                expr_template = random.choice(self.exprs)
                if '?' in expr_template:
                    key = random.choice(list(test_vars))
                    expr_template = expr_template.replace('?', key)
                expr_template = RANDOMCODE.apply_template(expr_template)
                self_code = self.get_value(expr_template != '@@')
                code = expr_template.replace('@@', self_code)
                if eval_filter(code, self.filter_fn, test_vars):
                    self.add_fragment(code)
                    return code
        return self.get_value(identifier_only=identifier_only)

    def get_expr(self, test_vars=None, identifier_only=False, avoid_mask=False):
        v = '_'
        while True:
            v = self.get_expr_(test_vars, identifier_only=identifier_only)
            if not is_masked(v) or not avoid_mask:
                break
        return v


def default_specs():
    return [
        Spec(None, E='None',
             vars=dict(),
             consts=['None'],
             exprs=['@@'],
             ),
        Spec(sys, E='モジュール',
             vars=dict(),
             consts=[],
             exprs=['@@'],
             ),
        Spec(type(object), E='クラス名',
             vars=dict(
                 object=object,
        ),
            consts=[],
            exprs=['@@'],
        ),
        Spec(0, E='整数',
             vars=dict(
                 i=0, j=1, n=2, N=2, x=1, y=1, a=0, b=0,
                 v=0, value=0, result=-1, ans=0, res=-1, index=-1,
             ),
             consts='-1 0 1 2 3 4 5 6 7 8 9',
             exprs=['int(?)', 'len(?)', '@@+1', '@@-1',
                    '@@-$int$', '?[0]', '@@ $op$ $int$'],
             ),
        Spec('', E='文字列',
             vars=dict(
                 s="0", s1="1", s2="2", t="0", t2="2", S="-1", c="a", ch="",
             ),
             consts='"" "," ":" "A"',
             exprs=['str(?)', 'len(str(?))', "''.join(?)",
                    '@@.upper()', '@@.replace($str$, "")',
                    '@@.startswith($str$)', 'f"{?}"', "f'@@={@@}'",
                    '@@ if ? is None else \'\'', '"" if ? is None else @@',
                    ],
             ),
        Spec(0.0, E='少数点数',
             vars=dict(
                 x=0.0, y=0.0, z=1.0, x2=-1.0, y2=-2.0,
             ),
             consts='0.0 0.1 0.01 1.0 0.5 2.0',
             exprs=['float(?)',
                    '$float$ $op$ @@', '$float$ $op$ @@',
                    '?[0]', '($int$)/$int$', '$int$/2'],
             ),
        Spec(False, E='ブール数',
             vars=dict(
                 found=True, sucess=True,
             ),
             consts='True False',
             exprs=['bool(?)',
                    '$int$ $cmp$ $Cint$', '$int$ $cmp$ $int$',
                    '$str$.$isupper$()',
                    '$float$ $cmp$ $Cfloat$', '$len(?) $cmp$ $Cint$',
                    '$float$ $cmp$ $Cfloat$ $and$ $float$ $cmp$ $Cfloat$',
                    '$Cfloat$ < $float$ <= $float$'
                    ],
             ),
        Spec([], E='リスト',
             vars=dict(
                 A=[0, 1, 2], B=[0, 1, 2],
                 xs=[0, 1, 2], ys=[0, 1, 2], lst=[0, 0, 0],
                 values=[0, 0, 0],
        ),
            consts='[]',
            exprs=['[?]', 'list($str$)'],
        ),
        Spec((), E='タプル',
             vars=dict(
                 A=(0, 1, 2), B=(0, 1, 2),
                 pair=(1, 2), pair2=(1, 2), triple=(0, 1, 2),
                 keyvalue=('A', '1'),
        ),
            consts=['()'],
            exprs=['($Cint$,)', 'tuple(?)', '($Cint$, $Cint$)'],
        ),
        Spec({}, E='辞書',
             vars=dict(
                 d={'A': 0, 'B': 1, 'C': 2},
                 d2={'A': 0, 'B': 1, 'C': 2},
                 mapping={'A': 0, 'B': 1, 'C': 2},
                 dic={'A': 0, 'B': 1},
                 dict__A={'A': 0, 'B': 1, 'C': 2},  # あかんやつ
                 map__A={'A': 0, 'B': 1, 'C': 2},  # あかんやつ
        ),
            consts=['{}', 'dict()'],
            exprs=['dict(A=$Cint$)', '@@.copy()'],
        ),
        Spec(set(), E='セット',
             vars=dict(
                 A=set([0, 1, 2]), B=set([0, 1, 2]),
                 s=set([0, 1, 2]), st=set([0, 1, 2]),
                 set__A=set([0, 1, 2]),
        ),
            consts=['set()'],
            exprs=['set($list$)', 'set(?)'],
        ),
        # spec('iterable', E='イテラブル',
        #      filter_fn=make_filter(object, lambda x: hasattr(x, '__iter__')),
        #      vars=dict(
        #          iterable=[0, 1, 2],
        #          ALPHABET='ABCDEFEGH'
        #      ),
        #      consts=['range(3)'],
        #      exprs=['range($int$)', 'range($int$+1)', 'range($int$-1)'],
        #      ),
        Spec(lambda x:x, E='関数',
             filter_fn=make_filter(object, lambda x: callable),
             vars=dict(
                 f=lambda x:x, f2=lambda x, y:x,
                 g=lambda x:x, g2=lambda x, y:y,
                 h=lambda x:x,
             ),
             consts=['int', 'float', 'str'],
             exprs=['lambda x: x $op$ $Cint$'],
             ),
    ]


class FaultSuite(object):
    def __init__(self):
        self.namespace = {}
        self.specs = []
        self.hints = []
        self.cases = []

    def testcase(self, api_doc):
        self.cases = []
        for line in api_doc.splitlines():
            line = line.strip()
            if line == '' or line.startswith('#'):
                continue
            self.cases.append(line)


# def is_modulename(ty):
#     return not ty.startswith('<')


class Seed(object):
    def __init__(self, suite=FaultSuite(), logs=None):
        self.suite = suite
        self.logs = logs
        self.ns = {} if suite.namespace is None else suite.namespace
        self.all_vars = {key: value for key,
                         value in self.ns.items() if not key.startswith('import_')}
        self.types = {}
        self.local_hints = [] if suite.hints is None else suite.hints
        self.past_kw = collections.deque(maxlen=10)
        self.load(default_specs())
        if suite.specs is not None:
            self.load(suite.specs)
        self.reflesh()

    def load(self, specs):
        for spec in specs:
            self.append(spec)

    def append(self, spec: Spec):
        if spec.key not in self.types:
            spec.init(self.all_vars)
            self.types[spec.key] = spec
        else:
            self.types[spec.key].update(spec)

    def reflesh(self):
        none_names = []
        for key, value in self.all_vars.items():
            if isinstance(value, type(sys)):  # module
                module_spec: Spec = self.types['module']
                if key not in module_spec.code_names:
                    module_spec.code_names.append(key)
                self.types[key] = module_spec
            elif isinstance(value, type(object)):
                class_spec: Spec = self.types['type']
                if key not in class_spec.code_names:
                    class_spec.code_names.append(key)
            else:
                if '__' not in key:
                    none_names.append(key)
        none_spec: Spec = self.types['NoneType']
        for name in none_names:
            none_spec.add_var(name, None)

    def test_vars(self):
        return {key: mycopy(value) for key, value in self.all_vars.items()}

    def enable(self, name):
        new_name = f'{name}_'
        if new_name in self.all_vars:
            self.all_vars[name] = self.all_vars[new_name]
            del self.all_vars[new_name]

    def disable(self, name):
        if name in self.all_vars:
            new_name = f'{name}_'
            self.all_vars[new_name] = self.all_vars[name]
            del self.all_vars[name]

    def is_module(self, name):
        if '.' in name:
            return
        if name in self.all_vars:
            return self.all_vars[name].__class__.__name__ == 'module'
        return False

    def print_test(self, a):
        print(f'\033[31m{a}\033[0m')
        print(' guess_type:', self.guess_type(a))
        print(' expect:', self.expect(a))
        print(' get_value:', self.get_value(a))
        print(' wrong_type:', self.wrong_type(a))
        print(' wrong_value:', self.wrong_value(a))

    def guess_type(self, value: str):
        if ':' in value:
            value, _, _ = value.partition(':')
        if '=' in value:
            _, _, value = value.partition('=')
        if value in self.types:
            return value
        try:
            value = eval(value, None, self.test_vars())
            return type(value).__name__
        except Exception as e:
            DEBUG(f'{value}: {e}')
        return 'NoneType'

    def expect(self, value):
        if ':' in value:
            head, _, expect = value.partition(':')
            if '"' not in expect and "'" not in expect:
                if expect.startswith('か'):
                    return self.expect(head)+expect
                return expect
        if '=' in value:
            _, _, value = value.partition('=')
            return value
        if self.is_module(value):
            return value
        if value in self.types:
            return self.types[value].expect
        return f'たとえば{value}'

    def get_value(self, argv, identifier_only=False, avoid_mask=False):
        if ':' in argv:
            argv, _, _ = argv.partition(':')
        if '=' in argv:
            key, _, argv = argv.partition('=')
            return f'{key}={self.get_value(argv, identifier_only, avoid_mask)}'
        if argv in self.types:
            return self.types[argv].get_expr(self.test_vars(), identifier_only, avoid_mask)
        return argv

    def select(self, params, is_operator=False):
        for _ in range(3):
            tokens = [self.get_value(a) for a in params]
            if is_operator or len(tokens[0]) == 0:
                break
            t = tokens[0][-1]
            if t.isalpha() or t == ')':
                break
        return tokens

    def wrong_type(self, argv, identifier_only=False):
        if ':' in argv:
            argv, _, _ = argv.partition(':')
        if '=' in argv:
            key, _, argv = argv.partition('=')
            return f'{key}={self.wrong_type(argv, identifier_only)}'
        if argv not in self.types:
            argv = self.guess_type(argv)
        keys = list(self.types.keys())
        if argv in keys:
            keys.remove(argv)
        argv = random.choice(keys)
        return self.types[argv].get_expr(self.test_vars(), identifier_only, avoid_mask=True)

    def wrong_value(self, argv, identifier_only=False):
        if ':' in argv:
            argv, _, _ = argv.partition(':')
        if '=' in argv:
            key, _, argv = argv.partition('=')
            return f'{key}={self.wrong_value(argv, identifier_only)}'
        if argv.startswith('"') or argv.startswith("'"):
            return misspell(argv)
        if argv not in self.types:
            argv = self.guess_type(argv)
        if argv in self.types:
            return self.types[argv].get_expr(self.test_vars(), identifier_only, avoid_mask=True)
        return argv

    def apply_snippet(self, ret, code):
        return code
        # if '@@' in ret:
        #     return replace_mask(ret, code)
        # if ret not in SNIPPET_TEMPLATE:
        #     return code, '@@'
        # ret = random.choice(SNIPPET_TEMPLATE[ret])
        # return replace_mask(ret, code)

    def record(self, d):
        if self.logs is None:
            return
        d['eline'] = remove_suffix(d['eline'])
        d['emsg'] = remove_suffix(d['emsg'])
        d['hint'] = remove_suffix(str(d['hint']))
        if 'fix' in d:
            d['fix'] = remove_suffix(d['fix'])
        d['fault'] = self.fault
        key = (d['emsg'], d['eline'])
        # print('@@', d)
        if key not in DUP:
            self.logs.append(d)
            DUP[key] = d['hint']
            # Counter_EMSG.update([result['emsg']])

    def dump(self):
        for key, spec in self.types.items():
            print(f'\033[31m{key}\033[0m')
            for _ in range(100):
                print(self.get(f'<{key}>'), end='  ')
            print()


def is_identifer(s: str):
    return len(s) > 0 and s.replace('.', '_').isidentifier()


def _unbackquote(s):
    if s.startswith('`'):
        s = s[1:-1].replace('_', ' ')
        if s == '':
            return ''
        if s[0].isalpha():
            s = f' {s}'
        if s[-1].isalpha():
            s = f'{s} '
    return s


class CodeBase(object):
    DVAR = 0
    DFUNC = 1
    DLEFT = 2
    DRIGHT = 3
    DPUNCS = 4
    D = {
        "": ['変数', '関数', '', '引数', ('', '(', ',', ')')],
        "object": ['プロパティ', 'メソッド', 'レシーバ', '引数', ('.', '(', ',', ')')],
        "module": ['定数', '関数', 'モジュール', '引数', ('.', '(', ',', ')')],
        "class": ['定数', '関数', 'クラス', '引数', ('.', '(', ',', ')')],
        "operator": ['', '演算子', '左辺', '右辺', ('', '(', ',', ')')],
        "indexer": ['', 'インデクサ', '列', '添字', ('.', '[', ',', ']')],
        "slicer": ['', 'スライス', '列', '添字', ('.', '[', ':', ']')],
        "mapper": ['', 'マップ', 'マップ', 'キー', ('', '[', ':', ']')],
    }

    # tokens の位置
    FIX = 0
    NAME = 1
    DOT = 2
    OPEN = 3
    COMMA = 4
    CLOSE = 5
    LEFT = 6
    RIGHT = 7
    BASE = 6
    PARAM_START = 6

    def __init__(self, seed: Seed, testcase: str, n_trys=N_TRY):
        self.seed = seed
        if '#' in testcase:
            testcase, _, hints = testcase.partition('#')
            self.hints = hints.split('#')
        self.tparams = [_unbackquote(n) for n in testcase.split()]
        self.name = self.tparams.pop(1)
        self.kind = 'object'  # seed.check_kind(self.name)
        # チェック
        self.is_callable = True
        self.is_operator = False
        self.is_indexer = False
        if self.name.endswith('_'):
            self.is_callable = False
            self.name = self.name[:-1]
        elif self.name.endswith('__get'):
            self.name = self.name[:-5]
            self.is_indexer = True
            self.kind = "indexer" if self.tparams[1] == 'int' else 'mapper'
        elif self.name.endswith('__slice'):
            self.name = self.name[:-7]
            self.is_indexer = True
            self.kind = "slicer"
        elif not is_identifer(self.name):
            self.is_operator = True
            self.kind = "operator"
        elif self.tparams[0] == '':
            self.kind = ""
        elif self.seed.is_module(self.tparams[0]):
            self.kind = "module"
        self.K = 0
        self.masters = list(CodeBase.D[self.kind][CodeBase.DPUNCS])
        # print(self.kind, self.masters)
        if self.name == '' or self.tparams[0] == '' or self.tparams[0].endswith('.'):
            self.masters[CodeBase.DOT-2] = ''
        if not self.is_callable:
            self.masters[CodeBase.OPEN-2] = ''
            self.masters[CodeBase.CLOSE-2] = ''
        for _ in range(n_trys):
            self.tokens = ['', self.name] + \
                self.masters + seed.select(self.tparams, self.is_operator)
            self.check_emsg()
            if self.emsg == '':
                break
        self.masters = self.tokens[:]
        # print(self.tokens)
        self.masters[CodeBase.FIX] = self.code

    def gencode(self, tokens=None):
        tokens = tokens or self.tokens
        spc = random.choice([' ', '', ' '])
        base = tokens[CodeBase.LEFT]
        name = tokens[CodeBase.NAME]
        if self.is_operator and len(self.tparams) == 1:
            return f'{base}{spc}{name}{spc}{tokens[CodeBase.RIGHT]}'
        base = self.safe_base()
        callee = f'{base}{tokens[CodeBase.DOT]}{name}'
        open = tokens[CodeBase.OPEN]
        comma = tokens[CodeBase.COMMA]
        close = tokens[CodeBase.CLOSE]
        params = tokens[CodeBase.PARAM_START+1:]
        params = (comma+spc).join(params)
        return f'{callee}{open}{params}{close}'

    def safe_base(self, base=None):
        base = base or self.tokens[CodeBase.LEFT]
        if len(base) > 0 and base[-1] not in ')]}':
            if not is_identifer(base):
                base = f'({base})'
        return base

    def update_fix(self, index):
        v = self.tparams[index]
        if v in self.seed.types:
            v = f'_{v}_'
            tokens = self.tokens[:]
            tokens[CodeBase.PARAM_START+index] = v
            self.masters[CodeBase.FIX] = self.gencode(tokens)

    def check_emsg(self, error_type=None, code=None):
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
        if self.emsg != '' and isinstance(error_type, str):
            result = error_type in self.emsg
            if not result:
                print('[DEBUG]', error_type, "!=", self.emsg)
            return result
        return self.emsg != ''

    def disable(self, name: str):
        self.disabled = name
        self.seed.disable(name)

    def _idname(self, kind=None):
        return CodeBase.D[kind or self.kind][CodeBase.DFUNC if self.is_callable else CodeBase.DVAR]

    def _left(self, kind=None):
        return CodeBase.D[kind or self.kind][CodeBase.DLEFT]

    def _right(self, kind=None):
        return CodeBase.D[kind or self.kind][CodeBase.DRIGHT]

    def get_name(self):
        return self.tokens[CodeBase.NAME]

    def set_wrong_name(self, name):
        self.tokens[CodeBase.NAME] = name

    def get_param(self, index):
        return self.tokens[CodeBase.PARAM_START+index]

    def value(self, index):
        v = self.tparams[index]
        if '=' in v:
            _, _, v = v.partition('=')
        if v.startswith('_') and v.endswith('_'):
            return ''
        return v

    def expect(self, index):
        return self.seed.expect(self.tparams[index])

    def set_wrong_param(self, index, wrong):
        self.wrong = wrong
        self.expected = self.expect(index)
        self.tokens[CodeBase.PARAM_START+index] = wrong

    def hint_for_param(self, hint, index=-1, correct=None):
        if index > 0:
            hint.append(K=index)
        if self.wrong:
            hint.append(W=self.wrong)
        if correct:
            hint.append(S=correct)
        elif self.expected:
            hint.append(E=self.expected)

    def apply_snippet(self, templ, code=None):
        return self.seed.apply_snippet(templ, code or self.code)

    def get_snippet(self):
        self.code = self.seed.apply_snippet(self.ret, self.code)
        self.ret = ''
        return self.code

    def record(self, hint: Hint, fix=True, apply_snippet=True):
        assert self.emsg != ''
        hint.update(self.emsg, self.code, self.seed.local_hints)
        code = self.get_snippet()
        d = dict(
            eline=code,
            emsg=self.emsg,
            hint=hint,
        )
        if fix:
            d['fix'] = self.masters[CodeBase.FIX]
        self.seed.record(d)
        self.tokens = self.masters[:]
        return True


def main():
    seed = Seed()
    print(seed.types)
    print(seed.all_vars)
    seed.print_test('1')
    seed.print_test('int:数値')
    seed.print_test('sys')
    seed.print_test('end="a"')
    seed.print_test('end')
    cb = CodeBase(seed, '`` int int base=2')
    print(cb.code)
    # seed.dump()


if __name__ == '__main__':
    main()
