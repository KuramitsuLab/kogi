import requests
import os
from .s3logging import debug_print


def getpid():
    try:
        with open('.PID1789') as f:
            return int(f.read())
    except:
        return None


_MODEL_ID = None


def load_model(model_id):
    global _MODEL_ID
    if _MODEL_ID == model_id:
        return
    pid = getpid()
    if pid:
        debug_print(f'kill -15 {pid}')
        os.system(f'kill -15 {pid}')
    script = os.path.abspath(__file__).replace('api', 'serv')
    os.system(f'python3 {script} {model_id} &')


def extract_tag(text):
    if text.startswith('<'):
        tag, end_tag, text = text.partition('>')
        return tag+end_tag, text
    return '', text


def model_generate(text, max_length=128, beam=1, split_tag=False):
    payload = {"inputs": text, "max_length": max_length}
    #headers = {"Authorization": f"Bearer {model_key}"}
    #response = requests.post(URL, headers=headers, json=payload)
    try:
        response = requests.post("http://127.0.0.1:5000/predict",
                                 json=payload, timeout=(3.5, 7.0))
        output = response.json()
        # print(text, type(output), output)
        if isinstance(output, (list, tuple)):
            output = output[0]
        output = output.get('generated_text', '')
        output = output.replace('<tab>', '    ').replace('<nl>', '\n')
        if split_tag:
            return extract_tag(output)
        return output
    except Exception as e:
        if split_tag:
            return '<status>', f'{e}'
        return f'<status>{e}'
