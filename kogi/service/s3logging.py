import inspect
import pytz
import uuid
import json
# import traceback
# import signal
import requests
from datetime import datetime, timezone
from .globals import kogi_get, is_debugging


def kogi_print(*args, **kw):
    print('\033[34m[🐶]', *args, **kw)
    print('\033[0m', end='')


def debug_print(*args, **kw):
    if is_debugging():
        filename = inspect.currentframe().f_back.f_code.co_filename
        lineno = inspect.currentframe().f_back.f_lineno
        if '/kogi/' in filename:
            _, _, filename = filename.rpartition('/kogi/')
        loc = f'[🐝{filename}:{lineno}]'
        print('\033[35m' + loc, *args, **kw)
        print('\033[0m', end='')


def print_nop(*args, **kw):
    pass


SESSION = str(uuid.uuid1())
SEQ = 0
_LOG_BUFFERS = []


def _copylog(logdata):
    if isinstance(logdata, dict):
        copied = {}
        for key, value in logdata.items():
            if key.startswith('_') or key.endswith('_'):
                continue
            copied[key] = _copylog(value)
        return copied
    if isinstance(logdata, list) or isinstance(logdata, tuple):
        return [_copylog(x) for x in logdata]
    return logdata


def record_log(lazy=False, **kargs):
    global SEQ, _LOG_BUFFERS, epoch
    now = datetime.now(pytz.timezone('Asia/Tokyo'))
    date = now.isoformat(timespec='seconds')
    logdata = _copylog(dict(seq=SEQ, date=date, **kargs))
    if 'type' not in logdata:
        logdata['type'] = 'debug'
    if is_debugging():
        logdata['type_orig'] = logdata['type']
        logdata['type'] = 'debug'
    SEQ += 1
    if kogi_get('approved', False):
        _LOG_BUFFERS.append(logdata)
        send_log(not lazy)
    return SEQ-1


UID = 'unknown'
POINT = 'ixe8peqfii'
HOST2 = 'amazonaws'
KEY = 'OjwoF3m0l20OFidHsRea3ptuQRfQL10ahbEtLa'
prev_epoch = datetime.now().timestamp()


def send_log(right_now=True):
    global prev_epoch, _LOG_BUFFERS, POINT
    now = datetime.now().timestamp()
    delta = (now - prev_epoch)
    prev_epoch = now
    if len(_LOG_BUFFERS) > 0 and (right_now or delta > 30 or len(_LOG_BUFFERS) > 4):
        data = {
            "session": SESSION,
            "uname": kogi_get('uname', ''),
            "approved": kogi_get('approved', False),
            "logs": _LOG_BUFFERS,
        }
        url = f'https://{POINT}.execute-api.ap-northeast-1.{HOST2}.com/dev'
        headers = {'x-api-key': f'A{KEY}s'}
        r = requests.post(url, headers=headers, json=data)
        debug_print('logging', data)
        _LOG_BUFFERS.clear()
        if r.status_code != 200:
            debug_print(r.status_code)
            debug_print(r)


