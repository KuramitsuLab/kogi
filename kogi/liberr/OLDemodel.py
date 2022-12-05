import os
import string

try:
    import pegtree as pg
except ModuleNotFoundError:
    os.system('pip install pegtree')
    import pegtree as pg


_PEG = '''

Start = { 
    (Param /  { (!Param .)* } )*
}

Param = LQuote / Quote / DoubleQuote / BackQuote 
    / Data / FuncName / MaybeName / CellName/ VarName 
    / ClassName / PathName / UName
    / Float / Int / Hex

LQuote = LQuote1 / LQuote2 / LQuote3
LQuote1 = {'\\'(' (!')\\'' . )+ ')\\'' #Quote}
LQuote2 = {'\\'<' (!'>\\'' . )+ '>\\'' #Quote}
LQuote3 = {'\\'[' ('\\\\' '\\'' / !']\\'' . )+ ']\\'' #Quote}
Quote = { '\\'' (!'\\'' .)* '\\'' #Quote }
BackQuote = { '`' (!'`' .)* '`' #Quote }
DoubleQuote = { '"' (![" ] .)* '"' #Quote }

Data = Set / Tuple
Set = { '{' ( Data / !'}' . )* '}' #Set }
Tuple = { '[' ( Data / !']' . )* ']' #Tuple }

FuncName = { NAME &'()' #FuncName }
CellName = { '%' '%'? NAME  #CellName }
VarName = { NAME ('\\'' NAME)? }  // can't
NAME = [A-Za-z_] [A-Za-z_.0-9]*
ClassName = { '<' [A-Za-z] (!'>' .)* '>' #ClassName }
PathName = { '(/' (!')' .)+ ')' #Path }

MaybeName = 
    / { NAME &(' object' !NAME) #Maybe }
    / { NAME &(' instance' !NAME) #Maybe }
    / { NAME &(' expected' !NAME) #Maybe }
    / { TYPENAME #Maybe }

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


def extract_params_from_error(emsg, maybe=False):
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
        ss.append(idx)
        params.append(s)
    return ''.join(ss), params


def _safe(s):
    ss = list(s)
    for i in range(len(ss)-1):
        if 'A' <= ss[i] <= 'Z':
            c = ss[i+1]
            if 'A' <= c <= 'z' or '0' <= c <= '9' or c == '_':
                pass
            else:
                ss[i] = f'_{ss[i]}_'
    return ''.join(ss)


UNQUOTE_FORMAT = '{}'


def _unquote(s):
    if s[0] == s[-1] and s[0] == "'" or s[0] == '`':
        s2 = s[1:-1]
        for c in s2:
            if ord(c) > 127 or not c.isalnum() and c != '_':
                return s
        return UNQUOTE_FORMAT.format(s2)
    return UNQUOTE_FORMAT.format(s)


def replace_params(t, params):
    t = _safe(t)
    for X, val in zip(string.ascii_uppercase, params):
        t = t.replace(f'_{X}_', _unquote(val))
    return t


def abspath(file):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), file)


class ErrorModel(object):
    def __init__(self, file=None):
        self.eDict = {}
        if file is not None:
            self.load(file)

    def load(self, file='emsg_ja.txt'):
        if not os.path.exists(file):
            file = abspath(file)
        with open(file) as f:
            ekey = None
            lines = []
            for line in f.readlines():
                line = line.strip()
                if line.startswith('#'):
                    continue
                if line == '':
                    self.define_emsg(ekey, lines)
                    ekey = None
                    lines = []
                    continue
                if ekey is None:
                    ekey = line
                else:
                    lines.append(line)
            self.define_emsg(ekey, lines)

    def define_emsg(self, key, lines):
        if key is None or len(lines) == 0:
            return
        if key in self.eDict:
            d = self.eDict[key]
        else:
            d = {}
            self.eDict[key] = d
        for line in lines:
            key, _, value = line.partition(':')
            if key in d:
                d[key] = d[key] + '\n' + value.strip()
            else:
                d[key] = value.strip()

    def find_new(self, series):
        ss = set()
        for emsg in series:  # df['emsg']
            emsg = emsg.strip()
            emsg, params = extract_params_from_error(emsg)
            # print(emsg)
            ss.add(emsg)
            #print('\t', params)
        for s in ss:
            if len(s) < 256:
                if s not in self.eDict:
                    print(s)
        #print(len(series), '=>', len(ss))

    def translate(self, emsg):
        ekey, params = extract_params_from_error(emsg)
        if ekey in self.eDict:
            d = self.eDict[ekey]
            if 'translated' in d:
                return replace_params(d['translated'], params)
        return emsg

    def get_slots(self, emsg):
        ekey, params = extract_params_from_error(emsg)
        slots = {}
        if ekey in self.eDict:
            d = self.eDict[ekey]
            for key, value in d.items():
                slots[key] = replace_params(value, params)
            return slots
        ekey2, params2 = extract_params_from_error(emsg, maybe=True)
        if ekey2 in self.eDict:
            d = self.eDict[ekey2]
            for key, value in d.items():
                slots[key] = replace_params(value, params2)
        else:
            slots['error_key'] = ekey
            slots['error_params'] = params
            #print('@', slots)
        return slots
