import sys
import ast
import random
from libda import da_first, da_random


def _quote_alt(s):
    if s.startswith('[') and s.startswith(']'):
        return s
    return f'[{s}]'


class CodeMaru(object):
    def __init__(self):
        self.imports = {}
        self.janames = {}
        self.varnames = {}
        self.pairs = []
        self.altdic = {}
        self.vocab = {}

    def prepare(self):
        newpairs = []
        for code, ty, doc in self.pairs:
            ss = []
            for line in doc.splitlines():
                if line == '' or line.startswith('#'):
                    continue
                elif line.startswith('@'):
                    self.parse_dic(line)
                else:
                    line = self.replace_alt(line)
                    ss.append(line)
            doc = '\n'.join(ss)
            newpairs.append((code, ty, doc))
        self.pairs = newpairs

    def parse_dic(self, s):
        # @alt(文字|文字列) を読む
        if s.startswith('@alt(') and s.endswith(')'):
            s = s[5:-1]
            if '=' in s:
                key, _, s = s.partition('=')
                self.altdic[key] = _quote_alt(s)
            else:
                key, _, _ = s.partition('|')
                self.altdic[key] = _quote_alt(s)
        # @import(file_vocab.py)  # 外部ファイルを読む
        if s.startswith('@import(') and s.endswith(')'):
            s = s[8:-1]
            with open(s) as f:
                env = {}
                exec(f.read(), None, env)
                print(env)
                if 'ALTDIC' in env:
                    self.altdic.update(env['ALTDIC'])
                if 'VOCAB' in env:
                    self.vocab.update(env['VOCAB'])

    def replace_alt(self, s):
        for old, new in self.altdic.items():
            if old in s:
                # print('=>', old, new)
                s = s.replace(old, new)
        return s

    def replace_vocab(self, code, line):
        for v, vs in self.vocab.items():
            oldv, olds = vs[0]
            if oldv in code and olds in line:
                newv, news = random.choice(vs)
                code = code.replace(oldv, newv)
                line = line.replace(olds, news)
        return code, line

    def generate(self, n_times=1):
        ss = []
        for code, ty, doc in self.pairs:
            dup = set()
            for line in doc.splitlines():
                code2, line2 = self.replace_vocab(code, line)
                line2 = da_first(line2)
                dup.add((code2, ty, line2))
                for _ in range(n_times):
                    code2, line2 = self.replace_vocab(code, line)
                    line2 = da_random(line2)
                    dup.add((code2, ty, line2))
            ss.extend(list(dup))
        return ss


def tostr(tree):
    if isinstance(tree, ast.Name):
        return tree.id
    if isinstance(tree, ast.Constant):
        return tree.value
    return repr(tree)


class CodeMaruAst(CodeMaru):

    def __init__(self):
        super().__init__()
        self.imports = {}
        self.janames = {}
        self.multinames = {}
        self.pairs = []
        self.lines = []
        self.linerange = None
        self.varenv = {}

    def getline(self, lineno, end_lineno=None):
        end_lineno = end_lineno or lineno
        lines = self.lines[lineno-1:end_lineno]
        return '\n'.join(lines)

    def load(self, filename: str):
        with open(filename) as f:
            self.lines = f.read().splitlines()
        tree = ast.parse('\n'.join(self.lines), mode='exec')
        for body in tree.body:
            cname = type(body).__name__
            method = f'tr_{cname}'
            if hasattr(self, method):
                getattr(self, method)(body)
            else:
                # DEBUG(f'Undefined AST {cname}')
                self.append_code(body)
        # print(self.imports)
        # print(self.pairs)

    def tr_Import(self, tree: ast.Import):
        # print(ast.dump(tree, indent=4))
        for alias in tree.names:
            if isinstance(alias, ast.alias):
                if alias.asname:
                    self.imports[f'{alias.asname}.'] = f'import {alias.name} as {alias.asname}'
                else:
                    self.imports[f'{alias.name}.'] = f'import {alias.name}'
        self.extract_varenv(self.getline(tree.lineno, tree.end_lineno))
        # print(self.imports)

    def tr_Assign(self, tree: ast.Assign):
        # print(ast.dump(tree, indent=4))
        for name in tree.targets:
            name = tostr(name)
            self.extract_varenv(self.getline(tree.lineno, tree.end_lineno))
            if name.startswith('_') and name.endswith('_'):
                janame = ''
                comment = self.getline(tree.end_lineno)  # コメント最終行
                if '#' in comment:
                    _, _, janame = comment.rpartition('#')
                    janame = janame.strip()
                self.defvar(name, tree.value, janame)
                return
        self.append_code(tree)

    def extract_varenv(self, code):
        try:
            exec(code, None, self.varenv)
            # print(self.varenv)
        except Exception as e:
            print(code, e)

    def defvar(self, name, tree: ast.Expr, janame: str):
        if isinstance(tree, ast.BoolOp) and isinstance(tree.op, ast.Or):
            names = [tostr(name) for name in tree.values]
            if name in names:
                names.remove(name)
            self.multinames[name] = names
            self.linerange = None
        self.janames[name] = janame

    def tr_Expr(self, tree: ast.Expr):
        # print(ast.dump(tree, indent=4))
        if isinstance(tree.value, ast.Constant):
            doc = tostr(tree.value).strip()
            self.define_doc(doc)
            return
        self.append_code(tree)

    def append_code(self, tree: str):
        if self.linerange is None:
            self.linerange = (tree.lineno, tree.end_lineno)
        else:
            self.linerange = (self.linerange[0], tree.end_lineno)

    def define_doc(self, doc: str):
        if self.linerange is None:
            return
        code = self.getline(*self.linerange)
        ty = ''
        if '# ->' in code:
            code, _, ty = code.rpartition('# ->')
            code = code.strip()
            ty = ty.strip()
        else:
            try:
                v = eval(code, None, self.varenv)
                ty = type(v).__name__
            except SyntaxError as e:
                pass
        self.pairs.append((code, ty, doc))
        self.linerange = None


if __name__ == '__main__':
    for f in sys.argv[1:]:
        cp = CodeMaruAst()
        cp.load(f)
        cp.prepare()
        print(cp.generate())
        # print(ast.dump(tree, indent=4))
