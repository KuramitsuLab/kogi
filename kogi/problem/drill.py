import builtins
from ..service import record_log
from .timeout import exec_with_timeout
from .judge import render_result, render_footer


def get_target(code):
    for c in code.splitlines()[::-1]:
        if '_ =' in c:
            return c.replace('_ =', '').strip()
        if '_=' in c:
            return c.replace('_=', '').strip()
    return ''


def safe_exec(code, globals, locals):
    try:
        exec(code, globals, locals)
    except Exception as e:
        locals['_'] = repr(e)


def judge_drill(code: str, data: dict, local_vars: dict):
    exec_with_timeout(code, None, local_vars, 15)
    if 'sample' in data:
        ref_vars = {}
        exec(data['sample'], None, ref_vars)
    else:
        ref_vars = local_vars.copy()

    for i, testcase in enumerate(data['testcases']):
        testcode = testcase.get('testcode')
        title = get_target(testcode)
        safe_exec(testcode, None, ref_vars)
        safe_exec(testcode, None, local_vars)
        sample = ref_vars['_']
        result = local_vars['_']
        render_result(title, '', result, sample)


# judge

_lines = None
_outputs = None


def judge_set(lines: list):
    global _lines, _outputs
    if lines is None:
        _lines = None
        _outputs = None
    else:
        _lines = lines[:]
        _outputs = []


def judge_input(prompt=''):
    global _lines
    if _lines is not None:
        if len(_lines) > 0:
            return _lines.pop(0)
        return ''
    return builtins.input(prompt)


def judge_print(*a, **kw):
    if _outputs is not None:
        sep = kw.get('sep', ' ')
        end = kw.get('end', '\n')
        s = sep.join([str(s) for s in a]) + end
        _outputs.append(s)
    else:
        builtins.print(*a, **kw)


def judge_cpc(ipy, code, data, context):
    context['problem_id'] = data['problem_id']
    global_vars = {
        'print': judge_print,
        'input': judge_input,
    }
    ac = 0
    for i, testcase in enumerate(data['testcases']):
        title = testcase.get('title', f'Case {i+1}')
        inputData = testcase['input']
        outputData = testcase['output']
        lines = [s for s in inputData.split('\n') if len(s) > 0]
        judge_set(lines)
        exec_with_timeout(code, global_vars, None, 10)
        resultData = ''.join(_outputs)
        ac += 1 if outputData == resultData else 0
        render_result(title, inputData, resultData, outputData)
    render_footer(data)
    return ac


def kogi_judge(ipy, code, data, judge_fn, catch_and_start_kogi):
    try:
        context = {}
        ac = judge_fn(ipy, code, data, context)
        record_log(type='atcoder', problem_id=data.get('problem_id'), ac=ac, code=code)
    except SyntaxError as e:
        catch_and_start_kogi(code=code, context=context, exception=e)
    except:
        catch_and_start_kogi(code=code, context=context)
