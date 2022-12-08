import os
import string

from ._extract_emsg import extract_emsg, replace_eparams

try:
    import pegtree as pg
except ModuleNotFoundError:
    os.system('pip install pegtree')
    import pegtree as pg


_PEG = '''

Start = { 
    (Param /  { (!Param .)* } )*
}

Param = 
    / LongQuote / Quote 
    / Data / FuncName / CamelName / MaybeName / CellName/ VarName 
    / ClassName / PathName / UName
    / Float / Int / Hex

LongQuote =
    / {'\\'(' (!')\\'' . )+ ')\\'' #Quote}  // '(...)'
    / {'\\'<' (!'>\\'' . )+ '>\\'' #Quote}  // '<...>'
    / {'\\'[' ('\\\\' '\\'' / !']\\'' . )+ ']\\'' #Quote}   // '[  ]'

Quote =
    / SingleQuote
    / BackQuote
    / DoubleQuote

SingleQuote = { '\\'' (!'\\'' .)* '\\'' #Quote }
BackQuote = { '`' (!'`' .)* '`' #Quote }
DoubleQuote = { '"' (!'"' .)* '"' #Quote }

Data = Set / Tuple
Set = { '{' ( Data / !'}' . )* '}' #Set }
Tuple = { '[' ( Data / !']' . )* ']' #Tuple }

NAME = [A-Za-z_] [A-Za-z_.0-9]*
CAMEL = [A-Z]+ [a-z_0-9]+ [A-Z] NAME

FuncName = { NAME &('(x)' / '()') #FuncName }
CellName = { '%' '%'? NAME  #CellName }
CamelName = { CAMEL #CamelName }
VarName = { NAME ('\\'' NAME)? }  // can't
ClassName = { '<' [A-Za-z] (!'>' .)* '>' #ClassName }
PathName = 
    / { '(/' (!')' .)+ ')' #Path }
    / { '/usr' (![ ,] .)+ #Path}
MaybeName = 
    / { NAME &(' object' !NAME) #Maybe }
    / { NAME &(' instance' !NAME) #Maybe }
    / { NAME &(' expected' !NAME) #Maybe }

TYPENAME =
    / 'list' !NAME
    / 'tuple' !NAME
    / 'int' !NAME
    / 'float' !NAME
    / 'str' !NAME
    / 'deque' !NAME

Float = { '-'? [0-9]* '.' [0-9]+ #Number }
Int = { '-'? [0-9]+ ('.py')? ![A-Za-z] #Int }
Hex = { '0x' [0-9A-Fa-f]+ #Hex }

UName = { U (!END .)* #UName }
END = [ (),]

U = [ぁ-んァ-ヶ㐀-䶵一-龠々〇〻ー]

// python3 extract_emsg.py runtime_error-2022-*.jsonl syntax_error-2022-0*.jsonl kogi_chat-2022-08.jsonl kogi_chat-2022-09.jsonl kogi_chat-2022-10.jsonl exception_hook-2022-0*.jsonl undefined_error-2022-04.jsonl undefined_error-2022-05.jsonl unknown_error-2022-07.jsonl unknown_error-2022-08.jsonl unknown_emsg-2022-06.jsonl unknown_emsg-2022-07.jsonl unknown_emsg-2022-08.jsonl > ../emsg_debug.jsonl
'''

_parser = pg.generate(pg.grammar(_PEG))
_IDX = string.ascii_uppercase


def extract_params(emsg, maybe=True, maxlen=120):
    if '\n' in emsg:
        emsg = emsg.split('\n')[0]
    etype, _, emsg = emsg.partition(': ')
    tree = _parser(emsg)
    ss = []
    params = []
    for t in tree:
        s = str(t)
        if t == '':
            ss.append(s)
            continue
        if t == 'Maybe' and not maybe:
            ss.append(s)
            continue
        idx = _IDX[len(params) % 26]
        ss.append(f'<{idx}>')
        params.append(s)
    if maxlen:
        body = ''.join(ss)[:maxlen]
    else:
        body = ''.join(ss)
    return etype, body, params

# ルールベース


_EMSG_RULES = {}


def _abspath(file):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), file)


def load_local_rule(file='emsg_rules.tsv'):
    if not os.path.exists(file):
        file = _abspath(file)

    with open(file) as f:
        for line in f.readlines():
            if line.startswith('#'):
                continue
            sentence = line.strip().split('\t')
            if len(sentence) == 2:
                _EMSG_RULES[sentence[0]] = sentence[1]


load_local_rule('emsg_rules.tsv')


def last_var(epat):
    for v in ('<D>', '<C>', '<B>', '<A>'):
        if v in epat:
            return v
    return None


def find_rule(epat):
    if epat in _EMSG_RULES:
        return _EMSG_RULES[epat]
    var = last_var(epat)
    if var is not None:
        epat, _, _ = epat.rpartition(var)
        #print('@', epat)
        for key, item in _EMSG_RULES.items():
            if key.startswith(epat):
                return item
    return None


UNQUOTE_FORMAT = '{}'


def _unquote(s):
    if s[0] == s[-1] and s[0] == "'" or s[0] == '`':
        s2 = s[1:-1]
        for c in s2:
            if ord(c) > 127 or not c.isalnum() and c != '_':
                return s
        return UNQUOTE_FORMAT.format(s2)
    return UNQUOTE_FORMAT.format(s)


def replace_eparams(msg, eparams):
    t = msg
    for X, val in zip(string.ascii_uppercase, eparams):
        t = t.replace(f'<{X}>', _unquote(val))
    return t


def _dequote(s):
    if len(s) > 2 and s[0] in '"`\'' and s[-1] in '"`\'':
        return s[1:-1]
    return s


def expand_eparams(record):
    if '_eparams' not in record:
        return
    for X, val in zip(string.ascii_uppercase, record['_eparams']):
        record[f'{X}_'] = _dequote(val)
        record[f'{X}'] = val


def rewrite_emsg(record, translate=None):
    emsg = record['emsg']
    etype, epat, eparams = extract_params(emsg, maxlen=None)
    record['_epat'] = epat
    record['_eparams'] = eparams
    translated = find_rule(f'{etype}: {epat}')
    if translated is None:
        if not translate:
            return None
        translated = translate(epat, lang='en_ja')
    if translated:
        translated = replace_eparams(translated, eparams)
        record['emsg_rewritten'] = translated
        return translated
    return None
