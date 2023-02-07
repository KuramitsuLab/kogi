import re
import os
import numbers
import os
import pandas as pd
from IPython import get_ipython
from .service import model_generate, debug_print

# PEGパーサ
try:
    import pegtree as pg
except ModuleNotFoundError:
    os.system('pip install pegtree')
    import pegtree as pg

_PEG = '''

Start = { 
    (Chunk /  { (!Chunk .)* #Chunk } )*
}

Chunk = 
    / SingleQuote
    / DoubleQuote
    / BackQuoteCode
    / Number
    / Variable

SingleQuote = { '\\'' (!'\\'' .)* '\\'' #String } // ' ... '
DoubleQuote = { '"' (!'"' .)* '"' #String }  // " "
BackQuoteCode = '`' {  (!'`' .)*  #Code } '`' // `1+2`

Number = { '-'? [0-9]+ ('.' [0-9]+)? #Number } // 1.2
Variable = { [A-Za-z_0-9]+ #Name }  // a

'''

_parser = pg.generate(pg.grammar(_PEG))

# 型取得
KOGI_TYPEMAP = {
    'bool': '_結果_',
    'int': '_整数_',
    'float': '_数値_',
    'tuple': '_タプル_',
    'list': '_リスト_',
    'str': '_文字列_',
    'function': '_関数_',
    'ndarray': '_配列_',
    'DataFrame': '_データフレーム_',
}


def get_kogitype(value):
    py_type = type(value).__name__
    kg_type = KOGI_TYPEMAP.get(py_type, None)
    if kg_type is not None:
        return kg_type
    if isinstance(value, numbers.Number):
        return '_数値_'
    if hasattr(value, '__iter__'):
        return '_イテラブル_'
    return f'_結果_'


# みんなが使いそうな変数
FREQUENT_NAMES = {'n': '_整数_', 'N': '_整数_',
                  'kogi': 'コギー', 'Kogi': 'コギー', 'KOGI': 'コギー'}


def get_variable_type(name):
    shell = get_ipython()
    if name in shell.user_ns:
        value = shell.user_ns[name]
        return get_kogitype(value)
    else:  # 変数が未定義な場合
        return FREQUENT_NAMES.get(name, '_結果_')


def eval_code_type(code):
    shell = get_ipython()
    try:
        value = eval(code, shell.user_ns)
        return get_kogitype(value)
    except:
        return '_結果_'


def scan_dataframes():
    column_maps = {}
    dataframe_names = []
    shell = get_ipython()
    user_ns = shell.user_ns
    for name in user_ns:
        # 仮
        if name[0] == "_":
            pass
        else:
            value = user_ns[name]
            if isinstance(value, pd.DataFrame):
                dataframe_names.append(name)
                for column in list(value.columns):
                    column_maps[column] = name
                    # column_maps.setdefault(column, name)
    return dataframe_names, column_maps


def detect_string_type(s):
    content = s[1:-1]  # クオートをとる
    if content.endswith('.csv'):
        return '_CSVファイル_'
    if len(content) == 1:
        return '_文字_'
    return '_文字列_'


def append_map(maps, key, value):
    if key not in maps:
        maps[key] = []
    maps[key].append(value)


def parse(text):
    dataframe_names, column_maps = scan_dataframes()
    # debug_print(dataframe_names, column_maps)
    after_maps = {}
    tree = _parser(text)
    ss = []
    for t in tree:
        token = str(t)
        if t == 'Number':
            kgtype = '_数値_' if '.' in token else '_整数_'
            append_map(after_maps, kgtype, token)
            ss.append(kgtype)
        elif t == 'String':
            kgtype = detect_string_type(token)
            append_map(after_maps, kgtype, token)
            ss.append(kgtype)
        elif t == 'Name':
            kgtype = get_variable_type(token)
            append_map(after_maps, kgtype, token)
            ss.append(kgtype)
        elif t == 'Code':
            kgtype = eval_code_type(token)
            append_map(after_maps, kgtype, token)
            ss.append(kgtype)
        elif t == 'Chunk':
            for column, dfname in column_maps.items():
                if column in token:
                    append_map(after_maps, '_列名_', f'"{column}"')
                    append_map(after_maps, '_データフレーム_', dfname)
                    append_map(after_maps, '_データ列_', f'{dfname}["{column}"]')
                    token = token.replace(column, '_列名_')
            ss.append(token)
    return ''.join(ss).replace('_', ''), after_maps


# モデル出力→ユーザへの出力


VARPAT = re.compile(r'(_[^_]+_)')
# 漢字ひらがなカタカナ
KPAT = re.compile(
    r'(_*[\u3041-\u309F\u30A1-\u30FF\u2E80-\u2FDF\u3005-\u3007\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]+_*)')


def get_kvars(text):
    return re.findall(KPAT, text)


def make_output(text, dic, output_fmt='{}'):
    words = get_kvars(text)
    for word in words:
        if word in dic:
            new_word = dic[word].pop(0)
            text = text.replace(word, output_fmt.format(new_word), 1)
            dic[word].append(new_word)
    return text


def model_transform(text, beam=1, transform_before=parse, transform_after=make_output, output_fmt='{}'):
    # debug_print(text)
    user_input, after_maps = transform_before(text)
    # debug_print(user_input, after_maps)
    if beam == 1:
        generated_text = model_generate(user_input, beam=1)
        if generated_text is not None:
            generated_text = transform_after(
                generated_text, after_maps, output_fmt)
        return generated_text
    outputs = model_generate(user_input, beam=beam)
    outputs = [transform_after(t, dict(after_maps), output_fmt)
               for t in outputs]
    return outputs


def rmt_model_transform(text, cache):
    output_fmt = '<b><font color="red">{}</font></b>'
    ss = []
    for line in text.splitlines():
        if line in cache:
            generated = cache[line]
        else:
            generated = model_transform(text, output_fmt=output_fmt)
            if generated.startswith('<') and '>' in generated:
                _, _, generated = generated.partition('>')
                generated = generated.strip()
            cache[line] = generated
        ss.append(generated)
    return '\n'.join(ss)
