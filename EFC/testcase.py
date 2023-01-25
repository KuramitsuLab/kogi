from expr import spec, FaultSuite

_DEBUG = '''\
`` abs <float:数>
int from_bytes <bytes> byteorder='big'
<float:数> + <float:数>
<str> replace <str> <str>
math sin <float> #D信じるな
<str:列> __get <int>
`` tuple <list>
'''


def DebugFaultSuite():
    import math

    def myfunc(x, y=0, z=0):
        return (y+z)/x
    suite = FaultSuite()
    suite.namespace = dict(
        import_math='import math',
        math=math,
        f=myfunc,
    )
    suite.specs = []
    suite.testcase(_DEBUG)

    # SPECS = [
    #     spec('class', E='クラス名',
    #          types=type(type(0)),
    #          vars=dict(
    #              C=C__Z, D=C__Z,
    #              Person=Person__Z,
    #          ),
    #          consts=['int', 'float', 'str', 'list', 'bool'],
    #          exprs=['type(?)'],
    #          ),
    # ]
    return suite


_BUILTINS = '''\
`` abs <float>
`` all <iterable>
`` any <iterable>
`` ascii <object>
`` bin <int>
`` bool <int>
`` bytearray <str> encoding="utf-8"
`` bytes <str> encoding="utf-8"
`` bool <int>
`` callable <function>
`` chr <int>
`` complex <int> <int>
`` complex <str>
`` delattr <object> <name>
`` dir <object>
`` dict <dict>
`` divmod <int> <int>
`` enumerate <iterable>
`` enumerate <iterable> <int>
`` enumerate <iterable> start=0
`` filter <func> <iterable>
`` float <str>
`` float <int>
`` frozenset <iterable>
`` getattr <object> <name>
`` hasattr <object> <name>
`` hash <object>
`` hex <int>
`` id <object>
`` int <str>
`` int <str> <int>
`` int <str> base=16
`` isinstance <object> <class>
`` issubclass <class> <class>
`` iter <seq>
`` len <seq>
`` list <iterable>
`` map <func> <iterable>
`` max <iterable>
`` max <int> <int>
`` min <iterable>
`` min <int> <int>
`` next <iterator>
`` oct <int>
`` open <filename>
`` ord <str>
`` pow <int> <int>
`` pow <int> <int> <int>
`` print <str>
`` print <str> sep=":"
`` print <str> end=""
`` range <int>
`` range <int> <int>
`` range <int> <int> <int>
`` reversed <seq>
`` round <float>
`` round <float> <int>
`` set <iterable>
`` setattr <object> <name> <object>
`` slice <int>
`` slice <int> <int> <int>
`` sorted <iterable>
`` sorted <iterable> key=None
`` sorted <iterable> reverse=False
`` str <object>
`` str <bytes> encoding="utf-8"
`` sum <iterable>
`` sum <iterable> start=0
`` tuple <iterable>
`` type <object>
`` zip <iterable> <iterable>
'''


def BuiltInsFaultSuite():
    class C__Z:  # 自作
        def __init__(self):
            self.A = 0
            self.B = 1
            self.C = 2

    class Point__Z:
        def __init__(self):
            self.x = 0
            self.y = 1
            self.z = 2

    class Person__Z:
        def __init__(self):
            self.name = 'A'
            self.age = 1

    NS = {}
    SPECS = [
        spec('object', E='オブジェクト',
             types=(C__Z, Person__Z, Point__Z),
             vars=dict(obj=C__Z(), o=C__Z(),
                       p=Point__Z(), p2=Point__Z(), p3=Point__Z(),
                       person=Person__Z(),)
             ),
        spec('bytes', E='バイト列',
             types=bytes,
             vars=dict(
                 b=b'000', b2=b'000', byte=b'0',
                 buf=b'000', buffer=b'0000',
             ),
             consts=['Fraction("1/2")'],
             exprs=['$str$.encode()'],
             ),
        spec('name', E='属性名',
             types=str,
             vars=dict(
                 name='A', attrname='A',
                 propname='A', key='D',
             ),
             consts=['"A" "B"'],
             exprs=[],
             ),
        spec('class', E='クラス名',
             types=type(type(0)),
             vars=dict(
                 C=C__Z, D=C__Z,
                 Person=Person__Z,
             ),
             consts=['int', 'float', 'str', 'list', 'bool'],
             exprs=['type(?)'],
             ),
    ]
    return NS, SPECS, _BUILTINS


_INT = '''\
<int> bit_length
<int> bit_count #注意_バージョン
<int> to_bytes <int> byteorder='big'
int from_bytes <bytes> byteorder='big'
<int> as_integer_ratio
<int> + <int>
<int> - <int>
<int> * <int>
<int> ** <int>
<int> / <int>
<int> // <int>
<int> % <int>
<int> | <int>
<int> & <int>
<int> ^ <int>
<int> << <int>
<int> >> <int>
<int> += <int>
<int> -= <int>
<int> *= <int>
<int> **= <int>
<int> /= <int>
<int> //= <int>
<int> %= <int>
<int> |= <int>
<int> &= <int>
<int> ^= <int>
<int> <<= <int>
<int> >>= <int>
<int> < <int>
<int> <= <int>
<int> > <int>
<int> >= <int>
<int> `in` <ilist>
<int> `not_in` <ilist>
<float> as_integer_ratio
<float> is_integer
<float> hex
float fromhex <str>
<str> `in` <str>
<str> `not_in` <str>
<str> + <str>
<str> * <int>
<str> < <str>
<str> <= <str>
<str> > <str>
<str> >= <str>
<str> __get <int>
<str> __slice <int> <int>
<str> capitalize
<str> casefold
<str> center <int>
<str> count <str>
<str> count <str> <int>
<str> count <str> <int> <int>
<str> encode encoding="utf-8"
<str> endswith <str>
<str> endswith <str> <int>
<str> endswith <str> <int> <int>
<str> expandtabs <int>
<str> expandtabs tabsize=0
<str> find <str>
<str> find <str> <int>
<str> find <str> <int> <int>
<str> index <str>
<str> index <str> <int>
<str> index <str> <int> <int>
<str> isalnum
<str> isalpha
<str> isascii
<str> isdecimal
<str> isdigit
<str> isidentifier
<str> islower
<str> isnumeric
<str> isprintable
<str> isspace
<str> istitle
<str> isupper
<str> join <slist>
<str> ljust <int>
<str> lower
<str> lstrip
<str> lstrip <str>
<str> partition <str>
<str> removeprefix <str> #注意_バージョン
<str> removesuffix <str> #注意_バージョン
<str> replace <str> <str>
<str> replace <str> <str> <int>
<str> rfind <str>
<str> rfind <str> <int>
<str> rfind <str> <int> <int>
<str> rindex <str>
<str> rindex <str> <int>
<str> rindex <str> <int> <int>
<str> rjust <int>
<str> rpartition <str>
<str> rsplit
<str> rsplit <str>
<str> rsplit maxsplit=2
<str> rstrip
<str> rstrip <str>
<str> split
<str> split <str>
<str> split maxsplit=2
<str> splitlines
<str> splitlines keepends=True
<str> startswith <str>
<str> startswith <str> <int>
<str> startswith <str> <int> <int>
<str> strip
<str> strip <str>
<str> swapcase
<str> title
<str> translate <dict>
<str> upper
<str> zfill <int>
'''

_LIST = '''\
<int>  in  <list>
<int>  not in  <list>
<list> + <list>
<list> * <int>
<list> += <list>
<list> index <int>
<list> index <int> <int>
<list> index <int> <int> <int>
<list> count <int>
<list> append <int> #解説_追加
<list> clear
<list> extend <list>
<list> += <list>
<list> insert <int> <int>
<list> pop <int>
<list> pop
<list> remove <int>
<list> reverse
<list> copy
<int>  in  <tuple>
<int>  not in  <tuple>
<tuple> + <tuple>
<tuple> * <int>
<tuple> index <int>
<tuple> index <int> <int>
<tuple> index <int> <int> <int>
<tuple> count <int>
<int> `in` <set>
<int> `not_in`  <set>
<set> isdisjoint <set>
<set> issubset <set>
<set> issuperset <set>
<set> union <set>
<set> intersection <set>
<set> difference <set>
<set> symmetric_difference <set>
<set> update <set>
<set> intersection_update <set>
<set> difference_update <set>
<set> symmetric_difference_update <set>
<set> add <int>
<set> remove <int>
<set> discard <int>
<name>  in  <dict>
<name>  not in  <dict>
<dict> | <dict> #注意_バージョン
<dict> |= <dict> #注意_バージョン
<dict> get <name>
<dict> get <name> <str>
<dict> setdefault <name> <str>
<dict> update <dict>
<dict> keys
<dict> items
<dict> values
'''

_RANDOM = '''
random seed
random seed <int>
random getstate
random randbytes <int> #注意_バージョン
random randrange <int>
random randrange <int> <int>
random randrange <int> <int> <int>
random randint <int> <int>
random getrandbits <int>
random choice <list>
random choices <list>
random choices <list> k=1
random shuffle <list>
random sample <list> <int>
random random
random uniform <float> <float>
random triangular <float> <float> <float>
random betavariate <float> <float>
random expovariate <float>
random gammavariate <float> <float>
random lognormvariate <float> <float>
random normalvariate <float> <float>
random paretovariate <float>
random weibullvariate <float> <float>
'''

_MATH = '''\
math ceil <float>
math fabs <float>
math floor <float>
math trunc <float>
math ulp <float> #注意_バージョン
math cbrt <float> #注意_バージョン
math exp <float>
math exp2 <float> #注意_バージョン
math expm1 <float>
math log <float>
math log1p <float>
math log2 <float>
math log10 <float>
math sqrt <float>
math sin <float>
math cos <float>
math tan <float>
math asin <float>
math acos <float>
math atan <float>
math sinh <float>
math cosh <float>
math tanh <float>
math asinh <float>
math acosh <float>
math atanh <float>
math degrees <float>
math radians <float>
math erf <float>
math erfc <float>
math gamma <float>
math lgamma <float>
math frexp <float>
math modf <float>
math isfinite <float>
math isinf <float>
math isnan <float>
math isqrt <int> #注意_バージョン
math isfinite <float>
math isfinite <float>
math copysign <float> <float>
math fmod <float> <float>
math ldexp <float> <int>
math nextafter <float> <float> #注意_バージョン
math remainder <float> <float>
math log <float> <float>
math pow <float> <float>
math atan2 <float> <float>
math isclose <float> <float>
math comb <int> <int>
math factorial <int>
math gcd <int> <int> <int>
math gcd <int> <int>
math lcm <int> <int> <int> #注意_バージョン
math lcm <int> <int> #注意_バージョン
math perm <int> <int> #注意_バージョン
math perm <int> #注意_バージョン
math prod <iterable> #注意_バージョン
math prod <iterable> start=1 #注意_バージョン
math pi_
math e_
math tau_
math inf_
math nan_
'''


def MathFaultSuite():
    import math
    NS = dict(
        import_math='import math',
        math=math,
    )
    SPECS = [
    ]
    return NS, SPECS, _MATH


_FRACTION = '''\
fractions Fraction <str:分数書式>
fractions Fraction <int> <int>
fractions Fraction <int> denominator=2
fractions Fraction <float>
`` Fraction <str:分数書式>
`` Fraction <int> <int>
`` Fraction <float>
<Fraction> numerator_
<Fraction> denominator_
Fraction from_float <float>
<Fraction> limit_denominator <int>
<Fraction> limit_denominator max_denominator=1000000
<Fraction> + <Fraction>
<Fraction> - <Fraction>
<Fraction> * <Fraction>
<Fraction> / <Fraction>
<Fraction> == <Fraction>
<Fraction> != <Fraction>
<Fraction> < <Fraction>
<Fraction> <= <Fraction>
<Fraction> > <Fraction>
<Fraction> >= <Fraction>
'''


def FractionFaultSuite():
    import fractions
    from fractions import Fraction
    NS = dict(
        import_fractions='import fractions',
        import_Fraction='from fractions import Fraction',
        Fraction=Fraction,
        fractions=fractions,
    )
    SPECS = [
        spec('Fraction', E='分数',
             types=Fraction,
             vars=dict(
                 a=Fraction(0, 1), b=Fraction(0, 1),
                 x=Fraction(1, 2), y=Fraction(1, 3),
                 fraction=Fraction(0, 1), fraction2=Fraction(0, 1),
                 frac=Fraction(0, 1), frac2=Fraction(0, 1),
             ),
             consts=['Fraction("1/2")'],
             exprs=['Fraction($int$, $int$)', 'Fraction($Cint$, $Cint$)',
                    'Fraction($float$)', 'Fraction($Cfloat$)'],
             ),
    ]
    return NS, SPECS, _FRACTION


_SYS = '''\
sys abiflags_
sys argv_
sys base_exec_prefix_
sys base_prefix_
sys exec_prefix_
sys executable_
sys flags_
sys float_info_
sys float_info.epsilon_
sys float_info.dig_
sys float_repr_style_
sys int_info_
sys int_info.sizeof_digit_
sys maxsize_
sys maxunicode_
sys byteorder_
sys builtin_module_names_
sys path_
sys copyright_
sys platform_
sys hexversion_
sys stdin_
sys stdout_
sys stderr_
sys version_
sys version_info_
sys exc_info
sys getdefaultencoding
sys getrefcount <object>
sys getrecursionlimit
sys getsizeof <object>
sys intern <str>
'''

_NP = '''\
np array <list>
np zeros <int>
np ones <int>
np empty <int>
np arange <int>
np arange <int> <int>
np arange <int> <int> <int>
np linspace <float> <float> <int>
np linspace <float> <float> num=5
np array <list> dtype=np.int64
np zeros <int> dtype=np.int64
np ones <int> dtype=np.int64
np empty <int> dtype=np.int64
np arange <int> dtype=np.int64
np arange <int> <int> dtype=np.int64
np arange <int> <int> <int> dtype=np.int64
np linspace <float> <float> <int> dtype=np.int64
np linspace <float> <float> num=5 dtype=np.int64
<a> sort
<a> sort axis=-1
<a> sort kind="quicksort"
np sort <a>
np sort <a> axis=-1
np sort <a> kind="quicksort"
np flip <a>
np flip <a> axis=0
np argsort <a>
np argsort <a> axis=-1
np argsort <a> kind="quicksort"
np concatenate <tuple_a>
np concatenate <tuple_a> axis=0
np vstack <tuple_a>
np hstack <tuple_a>
<a> ndim_
<a> shape_
<a> size_
<a> reshape <int> <int>
<a> T_
<a> transpose
np expand_dims <a> axis=0
<a> view
<a> copy
<a> + <a>
<a> - <a>
<a> * <a>
<a> / <a>
<a> dot <a>
<a> sum
<a> sum axis=0
<a> min
<a> min axis=0
<a> max
<a> max axis=0
<df> head
<df> head <int>
<df> tail
<df> tail <int>
<df> sample
<df> sample <int>
<df> sample <int> random_state=0
<df> sample <int> replace=True
<df> drop <col> axis=1
<df> drop columns="A"
<df> sort_values <col>
<df> sort_values <col> ascending=False
<df> sort_values <col> na_position="first"
<df> sort_values <col> inplace=True
<df> sort_index
<df> sort_index ascending=False
<df> sort_index inplace=True
<df> reset_index
<df> reset_index drop=True
<df> reset_index inplace=True
<df> set_index <col>
<df> set_index <col> inplace=True
<df> isnull
<df> isna
<df> dropna how="all"
<df> dropna subset=["A"]
<df> fillna <float>
<df> fillna <float> inplace=True
pd concat <tuple_df>
pd concat <tuple_df> axis=1
<df> info
<df> shape_
<df> columns_
<df> size_
<df> iloc_
<df> iloc_
<df> describe
<ds> describe
<df> max
<ds> max
<df> min
<ds> min
<df> mean
<ds> mean
<df> median
<ds> median
<df> mode
<ds> mode
<df> quantile
<ds> quantile
<df> quantile <float>
<ds> quantile <float>
<df> std
<ds> std
<df> std ddof=0
<ds> std ddof=0
<df> var
<ds> var
<df> var ddof=0
<ds> var ddof=0
<df> head
<df> head <int>
<df> tail
<df> tail <int>
<df> sample
<df> sample <int>
<df> sample <int> random_state=0
<df> sample <int> replace=True
<df> drop <col> axis=1
<df> drop columns="A"
<df> sort_values <col>
<df> sort_values <col> ascending=False
<df> sort_values <col> na_position="first"
<df> sort_values <col> inplace=True
<df> sort_index
<df> sort_index ascending=False
<df> sort_index inplace=True
<df> reset_index
<df> reset_index drop=True
<df> reset_index inplace=True
<df> set_index <col>
<df> set_index <col> inplace=True
<df> isnull
<df> isna
<df> dropna how="all"
<df> dropna subset=["A"]
<df> fillna <float>
<df> fillna <float> inplace=True
pd concat <tuple_df>
pd concat <tuple_df> axis=1
<df> info
<df> shape_
<df> columns_
<df> size_
<df> iloc_
<df> iloc_
<df> describe
<ds> describe
<df> max
<ds> max
<df> min
<ds> min
<df> mean
<ds> mean
<df> median
<ds> median
<df> mode
<ds> mode
<df> quantile
<ds> quantile
<df> quantile <float>
<ds> quantile <float>
<df> std
<ds> std
<df> std ddof=0
<ds> std ddof=0
<df> var
<ds> var
<df> var ddof=0
<ds> var ddof=0
plt title <text>
plt xlabel <text>
plt ylabel <text>
plt xlim <float> <float>
plt ylim <float> <float>
plt legend
plt show
plt savefig "output.png"
plt plot <xdata>
plt plot <xdata> label="ラベル"
plt plot <xdata> marker="o"
plt plot <xdata> linestyle="dashed"
plt plot <xdata> color="blue"
plt plot <xdata> <ydata>
plt plot <xdata> <ydata> label="ラベル"
plt plot <xdata> <ydata> marker="o"
plt plot <xdata> <ydata> linestyle="dashed"
plt plot <xdata> <ydata> color="blue"
'''
