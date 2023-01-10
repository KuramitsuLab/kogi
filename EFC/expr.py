import re
import warnings
import random
import collections

N_TRY = 8
Counter_EMSG = collections.Counter()
DUP = {}


def debug(msg):
    if msg not in DUP:
        print('\033[31m[DEBUG]\033[0m', msg)
        DUP[msg] = msg

# snippet


_COMMON = """\
$var$ = @@
$var$ = [@@]
$var$.append(@@)
print(@@)
print('result:', @@)
print('Value is "{}"'.format(@@))
"""

_NUM = """\
$var$ = @@
$var$ = @@ $op$ $num$
if @@ $cmp$ $num$:
while @@ $cmp$ $num$:
    return @@
    return $num$ $op$ @@
if @@+$num$ $cmp$ $num$:
if @@ $cmp$ $num$ and $bool$:
if $bool$ $and$ @@ $cmp$ $num$:
if @@ $cmp$ $num$ $and$ $bool$:
if $bool$ or @@ $cmp$ $num$:
"""

_BOOL = '''\
assert @@
'''


SNIPPET_TEMPLATE = {
    'bool': _COMMON+_BOOL,
    'float': _COMMON+_NUM,
}


def init_SNIPPET_TEMPLATE():
    for key, value in SNIPPET_TEMPLATE.items():
        SNIPPET_TEMPLATE[key] = [v for v in value.splitlines() if '@@' in v]


init_SNIPPET_TEMPLATE()


_UNMASKED = {
    '$num$': '$Cint$ $int$ $Cfloat$ $float$'.split(),
    '$cmp$': '== != < <= >= > =='.split(),
    '$op$': '+ - * ** / // % + -'.split(),
    '$and$': 'and or'.split(),
    '$isupper$': 'isupper islower isdigit isascii'.split(),
    '$sign$': ['-', ''],
}


def add_random(ty, code):
    if ty not in _UNMASKED:
        _UNMASKED[ty] = collections.deque(maxlen=10)
    _UNMASKED[ty].append(code)


def _get_random(ty):
    if ty in _UNMASKED:
        return random.choice(_UNMASKED[ty])
    ty = ty[1:-1]  # $int$を外す
    if ty in _UNMASKED:
        return random.choice(_UNMASKED[ty])
    return random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


def get_random(ty):
    result = _get_random(ty)
    if result.startswith('$'):
        return get_random(result)
    return result


_MASK = re.compile(r'(\$[^\$]+\$)')


def replace_mask(code, self_expr='@@'):
    for mask in re.findall(_MASK, code):
        selected = get_random(mask)
        code = code.replace(mask, selected, 1)
    code2 = code.replace('@@', self_expr)
    return code2, code  # テンプレートも返す


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


SUFFIX = '__1 __2 __3 __4 __5 __6 __7 __8 __9 __0  __A'.split()


def remove_suffix(code):
    for suffix in SUFFIX:
        code = code.replace(suffix, '')
    return code


def mycopy(v, always_copy=True):
    if always_copy:
        if hasattr(v, 'copy'):
            return v.copy()
    return v


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


def eval_filter(code, fn, test_vars):
    warnings.simplefilter('error')
    try:
        v = eval(code, None, test_vars)
        return fn(v)
    except:
        return False


class spec(object):
    def __init__(self, key, E='オブジェクト',
                 filter_fn=default_filter, extra_fn=None,
                 types=None, vars={}, consts='', exprs=''):
        self.key = key
        self.expect = E
        self.filter_fn = filter_fn
        if types is not None:
            self.filter_fn = make_filter(types)
        self.vars = vars
        self.extra_fn = extra_fn
        self.consts = consts.split() if isinstance(consts, str) else consts
        self.exprs = exprs.split() if isinstance(exprs, str) else exprs
        self.exprs.extend(['@@'] * (1+len(exprs)//2))

    def update(self, vars):
        self.test_vars = []
        for key, value in self.vars.items():
            if not self.filter_fn(value):
                debug(
                    f'variable type error: {self.expect}, {key}={repr(value)}')
                continue
            new_key = append_unique(vars, key, value)
            if new_key:
                self.test_vars.append(new_key)
        if self.extra_fn:
            extra_vars = {}
            self.extra_fn(extra_vars)
            for key, value in extra_vars.items():
                if self.filter_fn(value):
                    new_key = append_unique(vars, key, value)
                    if new_key:
                        self.test_vars.append(new_key)
        if not hasattr(self, 'test_consts'):
            self.test_consts = []
            for key in self.consts:
                if eval_filter(key, self.filter_fn, None):
                    self.test_consts.append(key)
                else:
                    debug(f'const error: {repr(key)}')
        self.test_values = self.test_vars + self.test_consts
        for v in self.test_vars:
            add_random(self.key, v)
        for v in self.test_consts:
            add_random(f'C{self.key}', v)

    def get_value(self, identifier_only=False):
        if identifier_only:
            return random.choice(self.test_vars)
        return random.choice(self.test_values)

    def get_expr(self, test_vars=None, identifier_only=False):
        if identifier_only:
            return random.choice(self.test_vars)
        if test_vars and len(self.exprs) > 0:
            for _ in range(N_TRY):
                expr = random.choice(self.exprs)
                if '?' in expr:
                    key = random.choice(list(test_vars))
                    expr = expr.replace('?', key)
                self_code = self.get_value(expr != '@@')
                code = replace_mask(expr, self_code)
                if eval_filter(code, self.filter_fn, test_vars):
                    add_random(self.key, code)
                    return code
        return random.choice(self.test_values)


def default_specs():
    return [
        spec('int', E='整数',
             types=int,
             vars=dict(
                 i=0, j=1, n=2, N=2, x=1, y=1, a=0, b=0,
                 v=0, value=0, result=-1, ans=0, res=-1, index=-1,
             ),
             consts='-1 0 1 2 3 4 5 6 7 8 9',
             exprs=['int(?)', 'len(?)', '@@+1', '@@-1',
                    '@@-$int$', '?[0]', '@@ $op$ $int$'],
             ),
        spec('str', E='文字列',
             types=str,
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
        spec('float', E='少数点数',
             types=float,
             vars=dict(
                 x=0.0, y=0.0, z=1.0, x2=-1.0, y2=-2.0,
             ),
             consts='0.0 0.1 0.01 1.0 0.5 2.0',
             exprs=['float(?)',
                    '$float$ $op$ @@', '$float$ $op$ @@',
                    '?[0]', '($int$)/$int$', '$int$/2'],
             ),
        spec('bool', E='ブール数',
             types=bool,
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
        spec('list', E='リスト',
             types=list,
             vars=dict(
                 A=[0, 1, 2], B=[0, 1, 2],
                 xs=[0, 1, 2], ys=[0, 1, 2], lst=[0, 0, 0],
                 values=[0, 0, 0],
             ),
             consts='[]',
             exprs=['[?]', 'list($str$)'],
             ),
        spec('tuple', E='タプル',
             types=tuple,
             vars=dict(
                 A=(0, 1, 2), B=(0, 1, 2),
                 pair=(1, 2), pair2=(1, 2), triple=(0, 1, 2),
                 keyvalue=('A', '1'),
             ),
             consts=['()'],
             exprs=['($Cint$,)', 'tuple(?)', '($Cint$, $Cint$)'],
             ),
        spec('dict', E='辞書',
             types=dict,
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
        spec('set', E='セット',
             types=set,
             vars=dict(
                 A=set([0, 1, 2]), B=set([0, 1, 2]),
                 s=set([0, 1, 2]), st=set([0, 1, 2]),
                 set__A=set([0, 1, 2]),
             ),
             consts=['set()'],
             exprs=['set($list$)', 'set(?)'],
             ),
        spec('iterable', E='イテラブル',
             filter_fn=make_filter(object, lambda x: hasattr(x, '__iter__')),
             vars=dict(
                 iterable=[0, 1, 2],
                 ALPHABET='ABCDEFEGH'
             ),
             consts=['range(3)'],
             exprs=['range($int$)', 'range($int$+1)', 'range($int$-1)'],
             ),
        spec('function', E='関数',
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


# EXPRESSION_PATTERN = {
#     '<int0>': dict(
#         fn=make_filter(int, lambda x: x == 0),
#         E='整数',
#         cs=['0'],
#     ),
#     '<istr>': dict(
#         E='文字列/str',  # 整数文字列
#         fn=make_filter(str, lambda x: x.isdigit()),
#         c=['"0"', '"1"', "'123'"],
#         e=['str($1)', '$0+$1', "f'{$0}'", "$0[0]", "$0[$1]"],
#     ),
#     # '<str>': ['s S', 's t u', 'names[0] keys[i]', 'str(N) str(n)'],
#     # '<text>': ['"text" "label" "title"', 'text'],
#     # '<filename>': ['file filename filepath path'],
#     # '<bytes>': ['binary buffer b__2'],
#     # '<name>': ,  # エラー発生
#     '<name>': dict(
#         fn=make_filter(object, lambda x: str(x) in 'ABCD'),
#         E='キー',  # キー文字列
#         ns=['name', 'key'],
#         cs=['"A"', '"B"', "'C'", "'D'"],
#     ),
#     '<col>': dict(
#         E='列名',  # キー文字列
#         fn=make_filter(object, lambda x: str(x) in 'ABCD'),
#         ns=['_列名_', '_列名2_', '_列名3_', 'column'],
#         e=['df.columns[i]', 'df.columns[$0]'],
#         cs=['"A"', '"B"', "'C'"],
#     ),
#     '<ilist>': dict(
#         E='数列',  # リスト
#         fn=make_filter(list, lambda x: isinstance_all(x, int)),
#         e=['list($0)', '[$1]', '[$0,$1]', 'list(range(N))'],
#         cs=['[0]', 'list(range(8))'],
#     ),
#     '<slist>': dict(
#         E='文字列のリスト',  # リスト
#         fn=make_filter(list, lambda x: isinstance_all(x, str)),
#         e=['list(str($0))', '$0.split()', 'list($0)'],
#         cs=['[]', '["A"]', '["A","B"]', 's.split()'],
#     ),
#     '<iterable>': dict(
#         E='イテラブル',  # リスト
#         fn=make_filter(object, lambda x: hasattr(
#             x, '__iter__') and not isinstance(x, str)),
#         e=['range(1,$0)', 'range($1)', 'range($1+1)', 'range($1-1)'],
#         cs=['range(N)', 'range(len(s))'],
#     ),
#     # '<seq>': ['s A__3 S'],
#     # '<iterator>': ['iter(A__3)'],
#     '<a>': dict(
#         E='配列',
#         fn=make_filter(np.ndarray),
#         e=['$0+$1', '$0-$1'],
#         cs=['np.array([1,2,3])'],
#     ),
#     '<tuple_a>': dict(
#         E='配列',
#         fn=make_filter(tuple, lambda x: isinstance_all(x, np.ndarray)),
#         e=['($0,$1)', '($0,$1,$2)'],
#         cs=['(x__5, y__5)', '(a__5, b__5)'],
#     ),
#     '<df>': dict(
#         E='データフレーム',
#         fn=make_filter(pd.DataFrame),
#         ns=['df', 'df2', 'df3'],
#         e=['df[[$0, $1]]'],
#         cs=['df[[_列名_]]', 'df[[_列名_, _列名2_]]', 'df.head()'],
#     ),
#     '<tuple_df>': dict(
#         E='データフレームの組',  # リスト
#         fn=make_filter(tuple, lambda x: isinstance_all(x, pd.DataFrame)),
#         cs=['(df, df2)'],
#     ),
#     '<ds>': dict(
#         E='データ列',
#         fn=make_filter(pd.Series),
#         e=['df[$1]'],
#         cs=['df[_列名_]'],
#     ),
#     '<xdata>': dict(
#         E='X軸のデータ列',
#         fn=make_filter((pd.Series, np.ndarray)),
#         e=['df[$1]', 'np.arange($1)'],
#         cs=['df[_列名_]'],
#     ),
#     '<ydata>': dict(
#         E='y軸のデータ列',
#         fn=make_filter((pd.Series, np.ndarray)),
#         e=['df[$1]', 'np.sin($1)'],
#         cs=['df[_列名2_]'],
#     ),
#     # '<tuple_df>': ['(df,df2)'],
#     # '<col>': ['_列名_'],
#     '<func>': dict(
#         E='関数',  # リスト
#         fn=make_filter(object, lambda x: callable(x)),
#         cs=['int', 'str', 'float'],
#     ),
#     '<class>': dict(
#         E='クラス名',  # リスト
#         fn=make_filter(type(None)),
#         cs=['int', 'str', 'C', 'Person'],
#     ),
#     '<null>': dict(
#         E='None',  # リスト
#         fn=make_filter(type(None)),
#         cs=['None'],
#     ),
# }


def is_modulename(ty):
    return not ty.startswith('<')


def is_typename(specid):
    return specid is not None and specid[0] == '<'


class Seed(object):
    def __init__(self, ns=None, specs=None, local_hints=None, logs=None):
        self.ns = {} if ns is None else ns
        self.all_vars = {key: value for key,
                         value in self.ns.items() if not key.startswith('import_')}
        self.types = {}
        self.load(default_specs() if specs is None else specs)
        self.local_hints = [] if local_hints is None else local_hints
        self.logs = logs
        self.past_kw = collections.deque(maxlen=10)

    def load(self, specs):
        for spec in specs:
            self.append(spec)

    def append(self, spec: spec):
        if spec.key is None:
            self.ns.update(spec.vars)
            self.all_vars.update(spec.vars)
            return
        if spec.key not in self.types:
            spec.update(self.all_vars)
            self.types[spec.key] = spec

    def shuffle(self):
        self.all_vars = dict(self.ns)
        for _, spec in self.types.items():
            # spec.shuffle()
            spec.update(self.all_vars)

    def test_vars(self):
        return {key: mycopy(value) for key, value in self.all_vars.items()}

    def is_module(self, name):
        if name in self.all_vars:
            return self.all_vars[name].__class__.__name__ == 'module'
        return False

    def disable(self, name):
        if name in self.all_vars:
            new_name = f'{name}_'
            self.all_vars[new_name] = self.all_vars[name]
            del self.all_vars[name]

    def enable(self, name):
        new_name = f'{name}_'
        if new_name in self.all_vars:
            self.all_vars[name] = self.all_vars[new_name]
            del self.all_vars[new_name]

    def get_random(self, identifier_only=False):
        ty = random.choice(list(self.types.keys()))
        return self.types[ty].get_expr(self.test_vars(), identifier_only=identifier_only)

    def _unpack_typename(self, ty):
        assert ty[0] == '<'
        if ':' in ty:
            return ty[1:-1].partition(':')[0]
        return ty[1:-1]

    def get_expr(self, ty=None, wrong=False, identifier_only=False):
        if wrong:
            return self.get_random(identifier_only=identifier_only)
        if ty is None:
            return None
        if is_modulename(ty):
            return ty
        ty = self._unpack_typename(ty)
        if ty not in self.types:
            debug(f'NOT IN SEED: {ty}')
            return self.get_random(identifier_only=identifier_only)
        return self.types[ty].get_expr(self.test_vars(), identifier_only=identifier_only)

    def select_expr(self, ty=None, identifier_only=False):
        if ty is None:
            return None
        if isinstance(ty, (list, tuple)):
            return [self.get_expr(x, identifier_only=identifier_only) for x in ty]
        return self.get_expr(ty, identifier_only=identifier_only)

    def select_wrong(self, value=None, identifier_only=False):
        if isinstance(value, str):
            if value.startswith('"') or value.startswith("'"):
                return self.get_expr('<int>')
            if value.startswith('True') or value.startswith("False"):
                return repr(value)
            return repr(value)
        return self.get_expr(wrong=True, identifier_only=identifier_only)

    def _unpack_expect(self, ty):
        if ty is None:
            return ty, None
        if ty[0] == '<':
            if ':' in ty:
                ty, _, expect = ty[1:-1].partition(':')
                return ty, expect
            return ty[1:-1], None
        return ty, None

    def safe_eval(self, code):
        warnings.simplefilter('error')
        try:
            v = eval(code, None, self.test_vars())
            return v
        except Exception as e:
            return e

    def typecheck(self, code):
        v = self.safe_eval(code)
        if isinstance(v, Exception):
            return ''
        return type(v).__name__

    def expect(self, tyv):
        if is_typename(tyv):
            ty, expect = self._unpack_expect(tyv)
            if expect is not None:
                return expect
            if ty in self.types:
                return self.types[ty].expect
            return 'お手本通り'
        ty = self.typecheck(tyv)
        if ty in self.types:
            return self.types[ty].expect
        return tyv

    def apply_snippet(self, ret, code):
        if '@@' in ret:
            return replace_mask(ret, code)
        if ret not in SNIPPET_TEMPLATE:
            return code, '@@'
        ret = random.choice(SNIPPET_TEMPLATE[ret])
        return replace_mask(ret, code)

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
        if key not in DUP:
            self.logs.append(d)
            DUP[key] = d['hint']
            # Counter_EMSG.update([result['emsg']])

    def dump(self):
        for key, spec in self.types.items():
            print(f'\033[31m{key}\033[0m')
            for _ in range(100):
                print(self.get_expr(f'<{key}>'), end='  ')
            print()

    @classmethod
    def parse_testcase(cls, api_doc):
        ss = []
        for line in api_doc.splitlines():
            line = line.strip()
            if line == '' or line.startswith('#'):
                continue
            ss.append(line)
        return ss


if __name__ == '__main__':
    seed = Seed()
    for _ in range(100):
        print(seed.get_expr('<bool>'), end='  ')
