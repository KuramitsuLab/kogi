import uuid
# import traceback
# import json
# import signal
from datetime import datetime
import requests
from .globals import kogi_get


def kogi_print(*args, **kw):
    print('\033[34m[🐶]', *args, **kw)
    print('\033[0m', end='')


def debug_print(*args, **kw):
    if kogi_get('debug', False):
        print('\033[33m[🐝]', *args, **kw)
        print('\033[0m', end='')


def print_nop(*args, **kw):
    pass


SESSION = str(uuid.uuid1())
SEQ = 0
_LOG_BUFFERS = []


def _copylog(logdata):
    if isinstance(logdata, dict):
        copied = {}
        for key, value in logdata:
            if key.startswith('_') or key.endswith('_'):
                continue
            copied[key] = _copylog(value)
        return copied
    if isinstance(logdata, list) or isinstance(logdata, tuple):
        return [_copylog(x) for x in logdata]
    return logdata


def record_log(right_now=False, **kargs):
    global SEQ, _LOG_BUFFERS, epoch
    now = datetime.now()
    date = now.isoformat(timespec='seconds')
    logdata = dict(seq=SEQ, date=date, **kargs)
    SEQ += 1
    _LOG_BUFFERS.append(_copylog(logdata))
    send_log(right_now=right_now)
    return logdata


UID = 'unknown'
POINT = 'ixe8peqfii'
HOST2 = 'amazonaws'
KEY = 'OjwoF3m0l20OFidHsRea3ptuQRfQL10ahbEtLa'
prev_epoch = datetime.now().timestamp()


def send_log(right_now=True, print=kogi_print):
    global prev_epoch, _LOG_BUFFERS, POINT
    now = datetime.now().timestamp()
    delta = (now - prev_epoch)
    prev_epoch = now
    if len(_LOG_BUFFERS) > 0 and (right_now or delta > 30 or len(_LOG_BUFFERS) > 4):
        data = {
            "session": SESSION,
            "uid": UID,
            "logs": _LOG_BUFFERS,
        }
        _LOG_BUFFERS.clear()
        url = f'https://{POINT}.execute-api.ap-northeast-1.{HOST2}.com/dev'
        headers = {'x-api-key': f'A{KEY}s'}
        r = requests.post(url, headers=headers, json=data)
        if r.status_code != 200:
            print(r.status_code)
            print(r)


# def logging_json(**kw):
#     global SEQ, _LOG_BUFFERS, epoch
#     now = datetime.now()
#     date = now.isoformat(timespec='seconds')
#     logdata = dict(seq=SEQ, date=date, **kw)
#     _LOG_BUFFERS.append(logdata)
#     SEQ += 1
#     send_log(right_now=False)
#     return logdata


# def logging_asjson(log_type, right_now=False, **kwargs):
#     global SEQ, _LOG_BUFFERS, epoch
#     now = datetime.now()
#     date = now.isoformat(timespec='seconds')
#     logdata = dict(log_type=log_type, seq=SEQ, date=date)
#     logdata.update(kwargs)
#     _LOG_BUFFERS.append(logdata)
#     SEQ += 1
#     send_log(right_now=right_now)
#     return logdata


# LAZY_LOGGER = []


# def add_lazy_logger(func):
#     LAZY_LOGGER.append(func)


# def sync_lazy_loggger():
#     for logger in LAZY_LOGGER:
#         try:
#             logger()
#         except:
#             traceback.print_exc()


# def _handler(signum, frame):
#     sync_lazy_loggger()
#     version = None
#     try:
#         import google.colab as colab
#         version = f'colab {colab.__version__}'
#     except ModuleNotFoundError:
#         pass
#     if version is None:
#         version = 'unknown'
#     logging_asjson('terminal', right_now=True, version=version)


# signal.signal(signal.SIGTERM, _handler)
