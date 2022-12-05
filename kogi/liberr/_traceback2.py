import sys
import re
import linecache
from kogi.render import Render

from .extract_vars import extract_vars
from .rulebase import rewrite_emsg


def DEBUG(*args, **kw):
    print('DEBUG', *args, **kw)


def getline(filename, lines, lineno):
    if filename == '<string>' or filename == '<unknown>':
        if 0 <= lineno-1 < len(lines):
            return lines[lineno-1]
        return ''
    return linecache.getline(filename, lineno).rstrip()

# def repr_value(value):
#     typename = type(value).__name__
#     if typename in REPR_VALUE:
#         return REPR_VALUE[typename](value)
#     if isinstance(value, str):
#         s = repr(value)
#         if len(s) > 32:
#             s = s[:32] + dots
#         return red(s)
#     if isinstance(value, Number) or value is None:
#         return repr(value)
#     return cyan(f'({typename})')


# def repr_vars(vars, start=None, end=None):
#     ss = []
#     for key, value in list(vars.items())[start:end]:
#         if key.startswith('_'):
#             continue
#         value = repr_value(value)
#         if value is not None:
#             ss.append(f'{bold(key)}={value}')
#     return ' '.join(ss)

def format_stack(r, filename, funcname, local_vars, exprs=None, n_args=0):
    if filename.startswith('<ipython-input-'):
        t = funcname.split('-')
        if len(t) > 2:
            filename = f'[{t[2]}]'
    if '/ipykernel_' in filename:
        filename = ''
        if funcname.startswith('<'):
            funcname = ''
    if funcname != '':
        r.print(funcname, color='blue', bold=True)
        r.println(f' "{filename}"', color='glay')
    # arguments = repr_vars(local_vars, 0, n_args)
    # if len(arguments) > 2:
    #     arguments = f'({arguments})'
    # locals = repr_vars(filter_expressions(local_vars, exprs), n_args)
    # if '/ipykernel_' in filename:
    #     print(f'{bold(funcname)}{arguments}')
    # elif filename.endswith('.py'):
    #     print(f'"{glay(filename)}" {bold(funcname)}{arguments}')
    #     return
    # else:
    #     print(f'"{glay(filename)}" {bold(funcname)}{arguments}')
    # if len(locals) > 2:
    #     print(locals)


def format_arrow(r, lineno, here=False):
    s = str(lineno)
    if here:
        arrow = '-' * max(5-len(s), 0) + '> '
    else:
        arrow = ' ' * max(5-len(s), 0) + '  '
    r.print(arrow, color='red')
    r.print(f'{s} ', color='green')


def format_linecode(r, filename, lines, lineno):
    if lineno-2 > 0:
        format_arrow(r, lineno-2)
        r.println(getline(filename, lines, lineno-2))
    if lineno-1 > 0:
        format_arrow(r, lineno-1)
        r.println(getline(filename, lines, lineno-1))
    format_arrow(r, lineno, here=True)
    r.println(getline(filename, lines, lineno))
    # render_arrow(r, lineno+1)
    # r.println(getline(filename, lines, lineno+1))
    # render_arrow(r, lineno+2)
    # r.println(getline(filename, lines, lineno-2))


def format_offset(r, lineno, offset):
    offset = max(0, offset-1)
    format_arrow(r, lineno)
    r.print(' ' * offset)
    r.println('▲', color='red', bold=True)


def syntax_exc(code, caught_ex, record):
    filename = caught_ex.filename
    lines = code.splitlines()
    record['lineno'] = lineno = caught_ex.lineno
    record['eline'] = text = caught_ex.text
    record['offset'] = offset = caught_ex.offset
    r = Render()
    format_linecode(r, filename, lines, lineno)
    format_offset(r, lineno, offset)
    # print(dir(caught_ex))
    r.update(record)
    return record


def filter_expressions(vars, exprs=None):
    if exprs is not None:
        newvars = {}
        for key, value in vars.items():
            if key in exprs:
                newvars[key] = value
        return newvars
    return vars


_VARPAT = re.compile(r'([A-Za-z_][A-Za-z_]*)')


def find_var(parent, eline, locals={}):
    r = Render()
    dup = set()
    found = re.findall(_VARPAT, eline)
    if found:
        for name in found:
            if name in locals and name not in dup:
                dup.add(name)
                format_value(r, locals[name], name)
    if len(dup) > 0:
        parent.extend(r, div='<details><summary>変数を確認</summary>{}</details>')


def format_value(r, value, name=None):
    if name:
        r.print(f'   {name}', bold=True)
        r.print(f' = ')
    r.print(f'{type(value).__name__}型 ', color='green')
    if hasattr(value, 'shape'):
        r.print(f'shape:{repr(value.shape)} ', color='green')
    elif hasattr(value, '__len__'):
        r.print(f'len:{len(value)} ', color='green')
    dump = repr(value)
    if len(dump) > 20:
        dump = dump + '...'
    r.println(dump)


def runtime_exc(code, tb, record):
    record['traceback_'] = tb
    exprs = None
    if code != '':
        exprs = extract_vars(code)
        record['exprs_in_code'] = exprs
        exprs = set(exprs)
    lines = code.splitlines()

    stacks = []
    eline = None

    while tb:
        filename = tb.tb_frame.f_code.co_filename
        funcname = tb.tb_frame.f_code.co_name
        lineno = tb.tb_lineno
        line = getline(filename, lines, tb.tb_lineno)
        n_args = tb.tb_frame.f_code.co_argcount
        local_vars = tb.tb_frame.f_locals
        stack = dict(
            filename=filename,
            funcname=funcname,
            n_args=n_args,
            local_vars=local_vars,
            lineno=lineno, line=line,
            line_in_code=line in code,
        )
        r = Render()
        format_stack(r, filename, funcname, local_vars, exprs, n_args)
        format_linecode(r, filename, lines, lineno)
        find_var(r, line, local_vars)
        r.update(stack)
        stacks.append(stack)
        if line in code:
            eline = line
        tb = tb.tb_next
    record['_stacks'] = stacks
    if eline:
        record['eline'] = eline


def kogi_exc(code='', exc_info=None, caught_ex=None, translate=None):
    if exc_info is None:
        etype, evalue, tb = sys.exc_info()
    else:
        etype, evalue, tb = exc_info
    if etype is None:
        return None
    record = dict(
        etype=f'{etype.__name__}',
        emsg=(f'{etype.__name__}: {evalue}').strip(),
        code=code,
    )
    if caught_ex is None and issubclass(etype, SyntaxError):
        try:
            raise
        except SyntaxError as e:
            caught_ex = e
    if isinstance(caught_ex, SyntaxError):
        syntax_exc(code, caught_ex, record)
    else:
        runtime_exc(code, tb, record)
    rewrite_emsg(record, translate=translate)
    return record


def print_record(record):
    r = Render()
    if 'emsg_rewritten' in record:
        r.println(record['emsg_rewritten'], bold=True)
        r.println(record['emsg'])
    else:
        r.println(record['emsg'])
    print(r.termtext())
    if '_stacks' in record:
        for stack in record['_stacks']:
            print_record(stack)
    elif '_term' in record:
        print(record['_term'])
    else:
        print(record['_text'])
    print(r.termtext())


def print_exc(code='', exc_info=None, caught_ex=None, translate=None):
    record = kogi_exc(code, exc_info, caught_ex, translate)
    print_record(record)
