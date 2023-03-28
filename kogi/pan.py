import sys
import numbers
import string
import os
import pandas as pd
from IPython import get_ipython
from kogi.service import debug_print, model_generate, kogi_set
from .OLDconversation import ConversationAI, set_chatbot
try:
    import pegtree as pg
except ModuleNotFoundError:
    os.system('pip install pegtree')
    import pegtree as pg

kogi_set(
    model_id='NaoS2/multi-kogi',
    debug=True,
)


def extract_tag(text):
    if text.startswith('<'):
        tag, end_tag, text = text.partition('>')
        return tag+end_tag, text
    return '', text


# ユーザの入力→モデルの入力
# 実行時型取得
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
    if getattr(value, '__iter__'):
        return '_イテラブル_'
    return f'_結果_'


possy = {'n': '_整数_', 'N': '_整数_', }  # みんなが使う変数名


def get_variable_type(name):
    shell = get_ipython()
    if name in shell.user_ns:
        value = shell.user_ns[name]
        return get_kogitype(value)
    else:  # 変数が未定義な場合
        return possy.get(name, '_結果_')


def eval_code_type(code):
    shell = get_ipython()
    try:
        value = eval(code, shell.user_ns)
        return get_kogitype(value)
    except:
        return '_結果_'


# pegtree
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


def scan_dataframes():
    column_maps = {}
    dataframe_names = []
    shell = get_ipython()
    user_ns = shell.user_ns
    for name in user_ns:
        if name[0] == "_":  # 仮
            pass
        else:
            value = user_ns[name]
            if isinstance(value, pd.DataFrame):
                dataframe_names.append(name)
                for column in list(value.columns):
                    column_maps.setdefault(column, name)
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

# parser


def parse(text):
    dataframe_names, column_maps = scan_dataframes()
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
# 下線区切り
def get_words(text):
    words = []
    while True:
        if len(text) > 0:
            pos1 = text.find('_')
            pos2 = text.find('_', pos1+1)
            if pos1 == -1 or pos2 == -1:
                break
            else:
                word = text[pos1:pos2+1]
                words.append(word)
                text = text[pos2:]
        else:
            break
    return words


def make_output(text, dic):
    words = get_words(text)
    for word in words:
        if word in dic:
            new_word = dic[word].pop(0)
            text = text.replace(word, new_word, 1)
            dic[word].append(new_word)
    return text


# <tag>省略
def extract_tag(text):
    if text.startswith('<'):
        tag, end_tag, text = text.partition('>')
        return tag+end_tag, text
    return '', text


class PanAI(ConversationAI):

    def response(self, user_input):
        user_input, after_maps = parse(user_input)  # ユーザ入力→モデルの入力
        debug_print("user_input:"+user_input)
        response_text = model_generate(user_input)  # 予測
        if response_text is None:
            return 'ZZ.. zzz.. 眠む眠む..'
        debug_print("response_text:"+response_text)
        response_text = make_output(
            response_text, after_maps)  # モデルの出力→ユーザへの出力

        tag, text = extract_tag(response_text)
        return text


debug = False
set_chatbot(PanAI())
