import os
import requests
import socket
import time
from .s3logging import debug_print


def check_port(port):
    host = "127.0.0.1"
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0


def getpid():
    try:
        with open('.PID1789') as f:
            return int(f.read())
    except:
        return None


_MODEL_ID = None
_START_TIME = time.time()


def start_server(restart=False):
    if check_port(5000):
        debug_print('Model server is still running')
        pid = getpid()
        if restart and pid:
            debug_print(f'shutdown server {pid}')
            os.system(f'kill -15 {pid}')
        if not restart:
            return
    script = os.path.abspath(__file__).replace('api', 'serv')
    res = os.system(f'python3 {script} {_MODEL_ID} > /dev/null 2>&1 &')
    debug_print(f'Model sever is starting. {_MODEL_ID} res={res}')
    _START_TIME = time.time()


def load_model(model_id):
    global _MODEL_ID
    if _MODEL_ID == model_id:
        return
    restart = (_MODEL_ID is not None)
    _MODEL_ID = model_id
    start_server(restart=restart)


def check_awake():
    try:
        payload = {"inputs": "おはよう", "max_length": 128, "beam": 1}
        requests.post("http://127.0.0.1:5000/predict",
                      json=payload, timeout=(3.5, 7.0))
        return True
    except requests.Timeout as e:
        debug_print(e)
        if not check_port(5000) and time.time() - _START_TIME > 60*10:
            debug_print('Server is down. Trying to restart.')
            start_server(restart=True)
        return False
    except requests.ConnectionError as e:
        debug_print(e)
        if not check_port(5000) and time.time() - _START_TIME > 60*10:
            debug_print('Server is down. Trying to restart.')
            start_server(restart=True)
        return False
    except Exception as e:
        debug_print(e)
        return False


def tabnl(s):
    return s.replace('<tab>', '    ').replace('<nl>', '\n')


def model_generate(text, max_length=128, beam=1):
    try:
        payload = {"inputs": text, "max_length": max_length, "beam": beam}
        response = requests.post("http://127.0.0.1:5000/predict",
                                 json=payload, timeout=(3.5, 7.0))
        output = response.json()
        # print(text, type(output), output)
        if isinstance(output, (list, tuple)):
            output = output[0]
        if 'outputs' in output and beam > 1:
            return [tabnl(s) for s in output['outputs']]
        return tabnl(output.get('generated_text', ''))
    except Exception as e:
        debug_print(e)
        if not check_port(5000) and time.time() - _START_TIME > 60*10:
            debug_print('Server is down. Trying to restart.')
            start_server(restart=True)
        return f'<status>{e}'
