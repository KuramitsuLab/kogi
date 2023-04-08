import re
import traceback
import warnings
from functools import wraps

# from kogi.logger import sync_lazy_loggger

from .chat import catch_and_start_kogi, call_and_start_kogi, record_log
from IPython.core.interactiveshell import InteractiveShell, ExecutionResult


RUN_CELL = InteractiveShell.run_cell
SHOW_TRACEBACK = InteractiveShell.showtraceback
SHOW_SYNTAXERROR = InteractiveShell.showsyntaxerror


KOGI_PAT = re.compile('#\\s*kogi\\s*(.*)')
HIRA_PAT = re.compile('[あ-を]')


def is_kogi_call(s):
    return re.search(HIRA_PAT, s)


def _find_action(text):
    return re.findall(KOGI_PAT, text)


def _call_kogi(code, actions):
    ss = []
    for action in actions:
        if is_kogi_call(action):
            ss.append(action)
    if len(ss) > 0:
        call_and_start_kogi(ss, code)
        return True
    return False


_DETECTOR = []
_RUNNER = {}


def kogi_register_hook(key, runner, detector):
    if key is not None and runner is not None:
        _RUNNER[key] = runner
    if detector is not None:
        _DETECTOR.append(detector)


def kogi_run_cell(ipy, raw_cell, kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter('error', SyntaxWarning)
        result = None
        actions = _find_action(raw_cell)
        if len(actions) > 0:
            if _call_kogi(raw_cell, actions):
                return RUN_CELL(ipy, 'pass', **kwargs)
            for detector in _DETECTOR:
                key = detector(actions[0], raw_cell)
                if key in _RUNNER:
                    result = _RUNNER[key](
                        ipy, raw_cell, actions[0], catch_and_start_kogi)
                    if not isinstance(result, ExecutionResult):
                        result = RUN_CELL(ipy, 'pass', **kwargs)
                    return result
        if result is None:
            result = RUN_CELL(ipy, raw_cell, kwargs)
            if 'from google.colab.output import _js' not in raw_cell and raw_cell != "":
                record_log(type='run_cell', code=raw_cell)
        return result


def change_run_cell(func):
    @wraps(func)
    def run_cell(*args, **kwargs):
        try:
            # args[1] is raw_cell
            return kogi_run_cell(args[0], args[1], kwargs)
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
            code = ipyshell.user_global_ns['In'][-1]
            catch_and_start_kogi(code=code)
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
