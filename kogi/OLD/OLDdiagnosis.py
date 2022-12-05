import ast
from IPython import get_ipython


def stringfy(node, inner=True):
    if isinstance(node, ast.Name):
        return str(node.id)
    if isinstance(node, ast.Attribute):
        return stringfy(node.value) + '.' + str(node.attr)
    if isinstance(node, ast.Call):
        return stringfy(node.func) + '()'
    if isinstance(node, ast.Subscript):
        return stringfy(node.value)+'['+stringfy(node.slice)+']'
    if isinstance(node, ast.Slice):
        if not inner:
            return '@'
        base = stringfy(node.lower)+':'+stringfy(node.upper)
        if node.step is None:
            return base
        return base + ':' + stringfy(node.step)
    if isinstance(node, ast.Index):
        return stringfy(node.value)
    if inner:
        if isinstance(node, ast.Constant):
            return str(node.value)
        if isinstance(node, ast.Num):
            return str(node.n)
        if isinstance(node, ast.Str):
            return str(node.s)
        if node is None:
            return ''
    return '@'


def traverse(node, ss: set):
    #print(ast.dump(node), stringfy(node, inner=False))
    snipet = stringfy(node, inner=False)
    if '@' not in snipet:
        ss.add(snipet)
    for sub_node in ast.iter_child_nodes(node):
        traverse(sub_node, ss)
    return ss


def extract_vars(code):
    try:
        node = ast.parse(code)
        ss = traverse(node, set())
        return [s for s in ss if (not s.endswith('()')) and (s+'()' not in ss)]
    except SyntaxError:
        return []


def eval_ipython(code=None, locals=None):
    ipy = get_ipython()
    globals = ipy.user_global_ns
    code = code or ipy.user_global_ns['In'][-1]
    locals = locals or ipy.user_ns
    vars = extract_vars(code)
    #print('@', code, vars)
    ss = []
    for snipet in vars:
        try:
            # print(snipet)
            v = eval(snipet, globals, locals)
            ss.append(dump_value(snipet, v))
        except BaseException as e:
            pass
            #ss.append((snipet, e))
    return ss

##
# dump


_PYTYPE = {
    'NoneType': 'None',
    'bool': 'ブール値',
    'int': '整数',
    'float': '浮動小数点数',
    'complex': '複素数',
    'str': '文字列',
    'bytes': 'バイト列',
    'list': 'リスト',
    'tuple': 'タプル',
    'dict': '辞書',
    'set': 'セット(集合)',
    'ndarray': '配列',
    'DataFrame': 'データフレーム',
    'module': 'モジュール',
    'builtin_function_or_method': 'ビルトイン関数',
    'function': '関数',
    'method': 'メソッド',
    'type': 'クラス(型)',
}


def _typename(value):
    typename = type(value).__name__
    if typename in _PYTYPE:
        return _PYTYPE[typename] + f'({typename}型)'
    return f'{typename}型'


def dump_value(key, value, html=False):
    ss = []
    ss.append(key)
    ss.append(_typename(value))
    if hasattr(value, 'shape'):
        ss.append(f'{key}.shape={value.shape}')
    elif hasattr(value, '__len__'):
        ss.append(f'len({key})={len(value)}')
    # if hasattr(value, '_repr_html_'):
    #     body = value._repr_html_()
    ss.append(repr(value))
    return ' '.join(ss)


def analyze_code(slots):
    code = slots.get('code', None)
    locals = slots.get('vars', None)
    ss = eval_ipython(code, locals)
    ss.insert(0, '変数の値を全部、出してみるよ（変な値はないか探してごらん)')
    #print('@', ss)
    if len(ss) > 1:
        slots['fault_vars'] = ss


def run_diagnosis(slots):
    if 'code' not in slots:
        try:
            slots['code'] = get_ipython().user_global_ns['In'][-1]
        except:
            pass
    if 'code' in slots and 'traceback' in slots:
        code = slots['code']
        lines = []
        for data in slots['traceback']:
            lineno = data['lineno']
            line = data['line'].strip()
            if line in code:
                line = f'[{lineno}行目] {line} に変なところない？'
                lines.append(line)
        if len(lines) > 0:
            slots['fault_lines'] = lines
    analyze_code(slots)
    # if 'problem_id' in slots:
    #     text = slots['problem_id']
    #     if text in HINT:
    #         text = HINT[text]
    #         slots['hint'] = text
