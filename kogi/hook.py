import re
import traceback
import warnings
from functools import wraps

from IPython.core.interactiveshell import InteractiveShell, ExecutionResult
from kogi.chat import start_kogi
from kogi.service import record_log, is_japanese_text, is_english_text, kogi_set

RUN_CELL = InteractiveShell.run_cell
SHOW_TRACEBACK = InteractiveShell.showtraceback
SHOW_SYNTAXERROR = InteractiveShell.showsyntaxerror

# prompt

def is_prompt(code):
    lines = code.strip().replace('"', '#').replace("'", '#').splitlines()
    head, _, _ = lines[0].partition('#') # コメント以降は無視する
    tail, _, _ = lines[-1].partition('#') # コメント以降は無視する
    # print('@head', head, is_japanese_text(head+tail))
    # print('@tail', tail, is_english_text(head+tail))
    if is_japanese_text(head+tail):
        kogi_set(lang='ja')
        return True
    if is_english_text(head+tail):
        return True
    return False

def run_prompt(ipy, raw_cell, **kwargs):
    context = {'prompt': raw_cell}
    start_kogi(context)


_HOOKED_RUN_CELL_FUNCTIONS = [
    ('prompt', is_prompt, run_prompt)
]

def register_hook(hook_name, is_hooked_fn, run_cell_fn):
    global _HOOKED_RUN_CELL_FUNCTIONS
    _HOOKED_RUN_CELL_FUNCTIONS = [(hook_name, is_hooked_fn, run_cell_fn)] + _HOOKED_RUN_CELL_FUNCTIONS

def find_run_cell_function(raw_cell):
    global _HOOKED_RUN_CELL_FUNCTIONS
    for hook_name, is_hooked_fn, run_cell_fn in _HOOKED_RUN_CELL_FUNCTIONS:
        # print(hook_name, is_hooked_fn(raw_cell))
        if is_hooked_fn(raw_cell):
            # if 'from google.colab.output import _js' not in raw_cell and raw_cell != "":
            #     record_log(type='run_cell', key_name=hook_name, code=raw_cell)
            return run_cell_fn
    return RUN_CELL

def hooked_run_cell(ipy, raw_cell, kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter('error', SyntaxWarning)
        run_cell = find_run_cell_function(raw_cell)
        result = run_cell(ipy, raw_cell, **kwargs)
        if isinstance(result, ExecutionResult):
            if hasattr(result.info, 'result') and raw_cell != "":
                if 'from google.colab.output import _js' not in raw_cell:
                    record_log(log='run_cell', 
                               code=raw_cell, result=f'{result.info.result}')
        else:
            result = RUN_CELL(ipy, 'pass', **kwargs)
        return result

def change_run_cell(func):
    @wraps(func)
    def run_cell(*args, **kwargs):
        try:
            # args[1] is raw_cell
            return hooked_run_cell(args[0], args[1], kwargs)
        except:
            traceback.print_exc()
        value = func(*args, **kwargs)
        return value
    return run_cell


def change_showtraceback(func):
    @wraps(func)
    def showtraceback(*args, **kwargs):        
        try:
            ipyshell = args[0]
            context = {
                'code': ipyshell.user_global_ns['In'][-1],
            }
            start_kogi(context, trace_error=True, start_dialog=True)
        except:
            traceback.print_exc()
    return showtraceback


def enable_kogi_hook():
    InteractiveShell.run_cell = change_run_cell(RUN_CELL)
    InteractiveShell.showtraceback = change_showtraceback(SHOW_TRACEBACK)
    InteractiveShell.showsyntaxerror = change_showtraceback(SHOW_SYNTAXERROR)


def disable_kogi_hook():
    InteractiveShell.run_cell = RUN_CELL
    InteractiveShell.showtraceback = SHOW_TRACEBACK
    InteractiveShell.showsyntaxerror = SHOW_SYNTAXERROR
