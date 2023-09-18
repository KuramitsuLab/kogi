import os
import string
import pegtree as pg
from .globals import kogi_get
from .textra import translate

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

'''

_parser = pg.generate(pg.grammar(_PEG))
_IDX = string.ascii_uppercase


def _extract_params(emsg, maybe=True, maxlen=120):
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
    return (f'{etype}: {body}').strip(), params

# ルールベース

_RULES = {}

def _abspath(file):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), file)


def _load_rules(lang):
    rule_file = f'simplemsg_{lang}.tsv'
    if not os.path.exists(rule_file):
        rule_file = _abspath(rule_file)
    if not os.path.exists(rule_file):
        return
    _RULES[lang] = {}
    with open(rule_file) as f:
        for line in f.readlines():
            if line.startswith('#'):
                continue
            sentence = line.strip().split('\t')
            if len(sentence) == 2:
                _RULES[lang][sentence[0].strip()] = sentence[1].strip()


def _find_rule(epat, lang='ja'):
    if lang not in _RULES:
        _load_rules(lang)
    if lang not in _RULES:
        return None
    epat = epat.strip()
    if epat in _RULES[lang]:
        return _RULES[lang][epat]
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


def _apply_rule(rule, eparams):
    t = rule
    for X, val in zip(string.ascii_uppercase, eparams):
        t = t.replace(f'<{X}>', _unquote(val))
    return t

def simplify(emsg):
    lang = kogi_get('lang', 'en')
    epat, eparams = _extract_params(emsg, maxlen=None)
    rule = _find_rule(epat, lang=lang)
    if rule is None and lang != 'en':
        #print(f"<{epat}>", rule)
        rule = translate(epat, lang=f'en_{lang}')
    if rule is not None:    
        return _apply_rule(rule, eparams)
    return None