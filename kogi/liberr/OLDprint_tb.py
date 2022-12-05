from kogi.liberr.emodel import ErrorModel
import sys
import linecache
from numbers import Number
from .extract_vars import extract_vars


def bold(s):
    return f'\033[01m{s}\033[0m'


def glay(s):
    return f'\033[07m{s}\033[0m'


def red(s):
    return f'\033[31m{s}\033[0m'


def green(s):
    return f'\033[32m{s}\033[0m'


def yellow(s):
    return f'\033[33m{s}\033[0m'


def blue(s):
    return f'\033[34m{s}\033[0m'


def cyan(s):
    return f'\033[36m{s}\033[0m'


dots = green('...')


def _repr_list(value):
    if len(value) > 1:
        return f'[{value[0]}, {dots}]'
    return '[]'


REPR_VALUE = {

}


def kogi_register_repr(value_or_typename, repr_func):
    if not isinstance(value_or_typename, str):
        value_or_typename = type(value_or_typename).__name__
    REPR_VALUE[kogi_register_repr] = repr_func


def repr_value(value):
    typename = type(value).__name__
    if typename in REPR_VALUE:
        return REPR_VALUE[typename](value)
    if isinstance(value, str):
        s = repr(value)
        if len(s) > 32:
            s = s[:32] + dots
        return red(s)
    if isinstance(value, Number) or value is None:
        return repr(value)
    return cyan(f'({typename})')


def repr_vars(vars, start=None, end=None):
    ss = []
    for key, value in list(vars.items())[start:end]:
        if key.startswith('_'):
            continue
        value = repr_value(value)
        if value is not None:
            ss.append(f'{bold(key)}={value}')
    return ' '.join(ss)


def getline(filename, lines, n):
    if filename == '<string>':
        if 0 <= n-1 < len(lines):
            return lines[n-1]
        return ''
    if filename == '<unknown>':
        if 0 <= n-1 < len(lines):
            return lines[n-1]
        return ''
    return linecache.getline(filename, n).rstrip()


def arrow(lineno, here=False):
    s = str(lineno)
    if here:
        arrow = '-' * max(5-len(s), 0) + '> '
    else:
        arrow = ' ' * max(5-len(s), 0) + '  '
    return red(arrow) + green(f'{s}')


def filter_expressions(vars, exprs=None):
    if exprs is not None:
        newvars = {}
        for key, value in vars.items():
            if key in exprs:
                newvars[key] = value
        return newvars
    return vars


def print_func(filename, funcname, local_vars, exprs=None, n_args=0):
    if filename.startswith('<ipython-input-'):
        t = funcname.split('-')
        if len(t) > 2:
            filename = f'[{t[2]}]'
    arguments = repr_vars(local_vars, 0, n_args)
    if len(arguments) > 2:
        arguments = f'({arguments})'
    locals = repr_vars(filter_expressions(local_vars, exprs), n_args)
    if '/ipykernel_' in filename:
        print(f'{bold(funcname)}{arguments}')
    elif filename.endswith('.py'):
        print(f'"{glay(filename)}" {bold(funcname)}{arguments}')
        return
    else:
        print(f'"{glay(filename)}" {bold(funcname)}{arguments}')
    if len(locals) > 2:
        print(locals)


def print_linecode(filename, lines, lineno):
    if lineno-2 > 0:
        print(arrow(lineno-2), getline(filename, lines, lineno-2))
    if lineno-1 > 0:
        print(arrow(lineno-1), getline(filename, lines, lineno-1))
    line = getline(filename, lines, lineno)
    print(arrow(lineno, here=True), getline(filename, lines, lineno))
    print(arrow(lineno+1), getline(filename, lines, lineno+1))
    print(arrow(lineno+2), getline(filename, lines, lineno+2))
    return dict(filename=filename, lineno=lineno, line=line)


def print_header(etype):
    print(red('-'*79))
    etype = str(etype.__name__).ljust(46) + ' Traceback(most recent call last)'
    print(bold(red(etype)))


def print_syntax_error(exception, slots, logging_json=None):
    lines = slots['code'].splitlines()
    filename = exception.filename
    slots['lineno'] = lineno = exception.lineno
    slots['line'] = text = exception.text
    slots['offset'] = offset = exception.offset
    print_func(filename, f'[lineno: {lineno} offset: {offset}]', {})
    if lineno-2 > 0:
        print(arrow(lineno-2), getline(filename, lines, lineno-2))
    if lineno-1 > 0:
        print(arrow(lineno-1), getline(filename, lines, lineno-1))
    print(arrow(lineno, here=True), getline(filename, lines, lineno))
    offset = max(0, offset-1)
    print(arrow(lineno), ' '*offset+bold(red('^^')))
    print(f"{bold(red(exception.__class__.__name__))}: {bold(exception.msg)}")
    if logging_json is not None:
        logging_json(
            type='syntax_error',
            code=slots['code'],
            emsg=slots['emsg'],
            lineno=lineno, line=text, offset=offset
        )
    translate_error(slots, logging_json=logging_json)
    return slots


def print_tb(etype, evalue, tb, slots, logging_json=None):
    print_header(etype)

    code = slots['code']
    lines = code.splitlines()
    if code != '':
        exprs = extract_vars(code)
        slots['exprs_in_code'] = exprs
        exprs = set(exprs)

    prev = None
    repeated = 0
    stacks = []
    while tb:
        filename = tb.tb_frame.f_code.co_filename
        if '-packages/' not in filename:
            funcname = tb.tb_frame.f_code.co_name
            n_args = tb.tb_frame.f_code.co_argcount
            lineno = tb.tb_lineno
            local_vars = tb.tb_frame.f_locals
            cur = (filename, funcname, lineno)
            if cur != prev:
                if repeated > 10:
                    print(f'... repeated {red(str(repeated))} times ...')
                print_func(filename, funcname, local_vars, exprs, n_args)
                stack = print_linecode(filename, lines, lineno)
                stacks.append(stack)
                repeated = 0
            else:
                if repeated < 10:
                    print_func(filename, funcname, local_vars, exprs, n_args)
                repeated += 1
            prev = cur
        tb = tb.tb_next
    slots['traceback'] = list(stacks[::-1])
    print(f"{bold(red(etype.__name__))}: {bold(evalue)}")
    if logging_json is not None:
        logging_json(
            type='runtime_error',
            code=slots['code'],
            emsg=slots['emsg'],
            traceback=list(stacks[::-1])
        )
    translate_error(slots, logging_json=logging_json)
    return slots


defaultErrorModel = ErrorModel('emsg_ja.txt')


def translate_error(slots, logging_json=None):
    slots.update(defaultErrorModel.get_slots(slots['emsg']))
    if logging_json is not None and 'error_key' in slots:
        logging_json(
            type='unknown_error',
            emsg=slots['emsg'],
            error_key=slots['error_key'],
            error_params=slots['error_params']
        )


def kogi_print_exc(code='', exc_info=None, exception=None, logging_json=None):
    if exc_info is None:
        etype, evalue, tb = sys.exc_info()
    else:
        etype, evalue, tb = exc_info
    if etype is None:
        return None
    slots = dict(
        etype=f'{etype.__name__}',
        emsg=(f'{etype.__name__}: {evalue}').strip(),
        code=code,
    )
    if isinstance(exception, SyntaxError):
        return print_syntax_error(exception, slots, logging_json=logging_json)
    if exception is None and issubclass(etype, SyntaxError):
        try:
            raise
        except SyntaxError as e:
            exception = e
        return print_syntax_error(exception, slots, logging_json=logging_json)
    return print_tb(etype, evalue, tb, slots, logging_json=logging_json)
