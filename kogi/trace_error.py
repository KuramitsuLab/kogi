import sys
import re
import linecache
from .service import EJ, record_log
import traceback

# import ast

# def _astnode_stringfy(node, inner=True):
#     if isinstance(node, ast.Name):
#         return str(node.id)
#     if isinstance(node, ast.Attribute):
#         return _astnode_stringfy(node.value) + '.' + str(node.attr)
#     if isinstance(node, ast.Call):
#         return _astnode_stringfy(node.func) + '()'
#     if isinstance(node, ast.Subscript):
#         return _astnode_stringfy(node.value)+'['+_astnode_stringfy(node.slice)+']'
#     if isinstance(node, ast.Slice):
#         if not inner:
#             return '@'
#         base = _astnode_stringfy(node.lower)+':'+_astnode_stringfy(node.upper)
#         if node.step is None:
#             return base
#         return base + ':' + _astnode_stringfy(node.step)
#     if isinstance(node, ast.Index):
#         return _astnode_stringfy(node.value)
#     if inner:
#         if isinstance(node, ast.Constant):
#             return str(node.value)
#         if isinstance(node, ast.Num):
#             return str(node.n)
#         if isinstance(node, ast.Str):
#             return str(node.s)
#         if node is None:
#             return ''
#     return '@'

# def _astnode_traverse(node, ss: set):
#     snipet = _astnode_stringfy(node, inner=False)
#     if '@' not in snipet:
#         ss.add(snipet)
#     for sub_node in ast.iter_child_nodes(node):
#         _astnode_traverse(sub_node, ss)
#     return ss

# def _extract_variables(code):
#     try:
#         node = ast.parse(code)
#         ss = _astnode_traverse(node, set())
#         return [s for s in ss if (not s.endswith('()')) and (s+'()' not in ss)]
#     except SyntaxError:
#         return []


variable_pattern = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b')

def _extract_variables(code):
    return re.findall(variable_pattern, code)

_LINES = []

def _SET_LINES(code: str):
    global _LINES
    _LINES = code.splitlines()

def _getline(filename, lineno):
    global _LINES
    if filename == '<string>' or filename == '<unknown>':
        if 0 <= lineno-1 < len(_LINES):
            return _LINES[lineno-1]
        return ''
    return linecache.getline(filename, lineno).rstrip()

def _format_arrow(doc, lineno, here=False):
    if here:
        arrow = '-' * max(5-len(str(lineno)), 0) + '> '
    else:
        arrow = ' ' * max(5-len(str(lineno)), 0) + '  '
    doc.append(f'<span style="color: red">{arrow}</span>')
    doc.append(f'<span style="color: green">{lineno} </span>')

def _format_linecode(record, offset=None, doc=None):
    if doc is None:
        doc = []
    doc.append('<pre>')
    filename = record['filename']
    lineno = record['lineno']
    if lineno-2 > 0:
        _format_arrow(doc, lineno-2)
        doc.append(_getline(filename, lineno-2))
        doc.append('<br>')
    if lineno-1 > 0:
        _format_arrow(doc, lineno-1)
        doc.append(_getline(filename, lineno-1))
        doc.append('<br>')
    _format_arrow(doc, lineno, here=True)
    doc.append(_getline(filename, lineno))
    doc.append('<br>')
    if offset is not None:
        offset = max(0, offset-1)
        _format_arrow(doc, lineno)
        doc.append(' ' * offset)
        doc.append('<b>^^</b>')
    doc.append('</pre>')
    return ''.join(doc)

def _format_name_value(name, value):
    doc=[]
    dump = repr(value)
    if len(dump) > 40:
        dump = dump[:40] + '...'
    dump = dump.replace('<', '&lt;')
    doc.append(f"<b>{name}</b>={dump} : ")
    doc.append(f'<span style="color:red">{type(value).__name__}</span>')
    if hasattr(value, 'columns'):
        doc.append(f' {name}.columns = {list(value.columns)}')
    elif hasattr(value, 'keys'):
        doc.append(f' {name}.keys = {list(value.keys)}')
    elif hasattr(value, 'shape'):
        doc.append(f' {name}.shape = {repr(value.shape)}')
    elif hasattr(value, '__len__'):
        doc.append(f' len({name})={len(value)}')
    return ''.join(doc)

def _format_variables(record, doc):
    filename = record['filename']
    lineno = record['lineno']
    code = '\n'.join([_getline(filename, lineno-2), _getline(filename, lineno-1), _getline(filename, lineno)])
    locals = record['local_vars']
    doc2=[]
    dup=set()
    for name in _extract_variables(code):
        if name in locals and name not in dup:
            doc2.append(_format_name_value(name, locals[name]))
            dup.add(name)
    if len(doc2) > 0:
        v = EJ('Variables', '変数の値')
        open = '' if record.get('_vars', None) else ' open'
        doc.append(f'<details{open}><summary>{v}</summary>')
        doc.append('<br>'.join(doc2))
        doc.append('</details>')
        record['_vars'] = '\n'.join(doc2)
    return ''.join(doc)

def _format_stack(stack, doc=None):
    if doc is None:
        doc = []
    filename = stack.get('filename', '')
    funcname = stack.get('funcname', '')
    if filename.startswith('<ipython-input-'):
        t = funcname.split('-')
        if len(t) > 2:
            filename = f'[{t[2]}]'
    if '/ipykernel_' in filename:
        filename = ''
        if funcname.startswith('<'):
            funcname = ''
    if funcname != '':
        doc.append(f'<b>{funcname}</b>  "{filename}"<br>')
    _format_linecode(stack, doc=doc)
    _format_variables(stack, doc=doc)
    return ''.join(doc)

def trace_runtime_error(context):
    code = context['code']
    _SET_LINES(code)

    record = context['error']
    tb = record['_traceback']

    exprs = None
    if code != '':
        exprs = _extract_variables(code)
        record['variables'] = exprs
        exprs = set(exprs)

    record['_stacks'] = stacks = []
    focused_stack = None
    while tb:
        filename = tb.tb_frame.f_code.co_filename
        funcname = tb.tb_frame.f_code.co_name
        lineno = tb.tb_lineno
        line = _getline(filename, tb.tb_lineno)
        n_args = tb.tb_frame.f_code.co_argcount
        local_vars = tb.tb_frame.f_locals
        stack = dict(
            filename=filename,
            funcname=funcname,
            n_args=n_args,
            local_vars=local_vars,
            lineno=lineno, error_line=line,
            is_line_in_code=line in code,
        )
        stacks.append(stack)
        stack['_doc'] = _format_stack(stack)
        if line in code:
            focused_stack = stack
        tb = tb.tb_next
    if focused_stack:
        record['lineno'] = focused_stack['lineno']
        record['error_line'] = focused_stack['error_line']
        vars = {}
        names = _extract_variables(code)
        for name, value in focused_stack['local_vars'].items():
            if name in names and name not in vars:
                vars[name] = [type(value).__name__, repr(value)]
        record['variables'] = vars

def trace_syntax_error(context):
    code = context['code']
    _SET_LINES(code)
    record = context['error']
    caught_ex = record['_evalue']

    record['filename'] = caught_ex.filename
    record['lineno'] = caught_ex.lineno
    record['offset'] = offset = caught_ex.offset
    record['error_line'] = caught_ex.text
    record['_doc'] = _format_linecode(record, offset=offset)
    return record


def kogi_trace_error(context=None):
    etype, evalue, tb = sys.exc_info()
    if etype is None:
        return {}
    if context is None:
        context = {}
    context['error'] = dict(
#        code=context['code'],
        type=f'{etype.__name__}',
        message=(f'{etype.__name__}: {evalue}').strip(),
        traceback = traceback.format_exc(),
        # exception = traceback.format_exception_only(etype, evalue),
        _traceback = tb,
        _evalue = evalue,
    )
    if isinstance(evalue, SyntaxError):
        trace_syntax_error(context)
    else:
        trace_runtime_error(context)
    code=context['code']
    record_log(log='error', code=code, **(context['error']))
    return context['error']
