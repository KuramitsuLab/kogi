import traceback
import uuid
import json
import signal
from datetime import datetime
import requests


def kogi_print(*args, **kw):
    print('\033[34m[🐶]', *args, **kw)
    print('\033[0m', end='')


def print_nop(*x, **kw):
    pass


# Slack Messaging

slack_conn = None
HOST = 'slack.com'


def _connect_slack():
    global slack
    if slack_conn is not None:
        return slack_conn
    slack_id = kogi_get('slack_id')
    if slack_id is None:
        return None
    try:
        from slackweb import Slack
    except ModuleNotFoundError:
        import os
        os.system('pip install slackweb')
        from slackweb import Slack
    url = f'https://hooks.{HOST}/services/{slack_id}'
    try:
        slack_conn = Slack(url)
        return slack_conn
    except Exception as e:
        kogi_print('Slack Error', e)
    return None


def send_message(text):
    try:
        conn = _connect_slack()
        if conn is None:
            return False
        conn.notify(text=text)
        return True
    except Exception as e:
        kogi_print('Slack Error:', e)
    return False


slack = None


def load_slack(slack_id='QNZDoUPuLo7C3lHyh9PWhZz3', update=True):
    global slack
    if slack_id is None:
        slack = None
        return None
    try:
        from slackweb import Slack
    except ModuleNotFoundError:
        import os
        os.system('pip install slackweb')
        from slackweb import Slack
    HOST = 'slack.com'
    ID = 'T02NYCBFP7B'
    ID2 = 'B02QPM8HNBH'
    if '/' not in slack_id:
        url = f'https://hooks.{HOST}/services/{ID}/{ID2}/{slack_id}'
    else:
        url = f'https://hooks.{HOST}/services/{slack_id}'
    try:
        local_slack = Slack(url)
        if update:
            slack = local_slack
    except Exception as e:
        print('Slack Error', e)
    return local_slack


def send_slack(logs, slack_id='QNZDoUPuLo7C3lHyh9PWhZz3'):
    try:
        local_slack = load_slack(slack_id=slack_id, update=False)
        jsondata = json.dumps(logs, ensure_ascii=False)
        local_slack.notify(text=jsondata)
    except Exception as e:
        print('Slack Error:', e)


SESSION = str(uuid.uuid1())
SEQ = 0
LOGS = []
UID = 'unknown'
POINT = 'ixe8peqfii'
HOST2 = 'amazonaws'
KEY = 'OjwoF3m0l20OFidHsRea3ptuQRfQL10ahbEtLa'
prev_epoch = datetime.now().timestamp()


def send_log(right_now=True, print=kogi_print):
    global prev_epoch, LOGS, POINT
    now = datetime.now().timestamp()
    delta = (now - prev_epoch)
    prev_epoch = now
    if len(LOGS) > 0 and (right_now or delta > 30 or len(LOGS) > 4):
        data = {
            "session": SESSION,
            "uid": UID,
            "logs": LOGS.copy(),
        }
        LOGS.clear()
        url = f'https://{POINT}.execute-api.ap-northeast-1.{HOST2}.com/dev'
        headers = {'x-api-key': f'A{KEY}s'}
        r = requests.post(url, headers=headers, json=data)
        #print('logging', r.status_code, data)
        if r.status_code != 200:
            print(r.status_code)
            print(r)
            #print(f'delta={delta} data={data}')


def log(**kw):
    global SEQ, LOGS, epoch
    now = datetime.now()
    date = now.isoformat(timespec='seconds')
    logdata = dict(seq=SEQ, date=date, **kw)
    LOGS.append(logdata)
    SEQ += 1
    send_log(right_now=False)
    return logdata


def logging_json(**kw):
    global SEQ, LOGS, epoch
    now = datetime.now()
    date = now.isoformat(timespec='seconds')
    logdata = dict(seq=SEQ, date=date, **kw)
    LOGS.append(logdata)
    SEQ += 1
    send_log(right_now=False)
    return logdata


def logging_asjson(log_type, right_now=False, **kwargs):
    global SEQ, LOGS, epoch
    now = datetime.now()
    date = now.isoformat(timespec='seconds')
    logdata = dict(log_type=log_type, seq=SEQ, date=date)
    logdata.update(kwargs)
    LOGS.append(logdata)
    SEQ += 1
    send_log(right_now=right_now)
    return logdata


LAZY_LOGGER = []


def add_lazy_logger(func):
    LAZY_LOGGER.append(func)


def sync_lazy_loggger():
    for logger in LAZY_LOGGER:
        try:
            logger()
        except:
            traceback.print_exc()


def _handler(signum, frame):
    sync_lazy_loggger()
    version = None
    try:
        import google.colab as colab
        version = f'colab {colab.__version__}'
    except ModuleNotFoundError:
        pass
    if version is None:
        version = 'unknown'
    logging_asjson('terminal', right_now=True, version=version)


signal.signal(signal.SIGTERM, _handler)
