import signal
import requests
import sys
import os
import warnings

try:
    from flask import Flask, request, jsonify
except ModuleNotFoundError:
    os.system('pip install -q flask')
    from flask import Flask, request, jsonify

app = Flask(__name__)


def _check_modules():
    try:
        import sentencepiece
    except:
        os.system('pip install -q sentencepiece')
    try:
        import transformers
    except:
        os.system('pip install -q transformers')

# NMT


_MODEL_ID = None
_MODEL = None
_TOKENIZER = None
_DEVICE = None
_CACHE = {}


def load_model(model_id):
    global _MODEL_ID, _MODEL, _TOKENIZER, _DEVICE, _CACHE
    if _MODEL_ID == model_id:
        return

    _check_modules()

    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        tokenizer = AutoTokenizer.from_pretrained(model_id, is_fast=False)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_id)

    model = torch.quantization.quantize_dynamic(
        model, {torch.nn.Linear},
        dtype=torch.qint8
    )

    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    if isinstance(device, str):
        device = torch.device(device)
    model.to(device)

    _MODEL_ID = model_id
    _MODEL = model
    _TOKENIZER = tokenizer
    _DEVICE = device
    _CACHE = {}


def generate_gready(s: str, max_length=128, print=print) -> str:
    try:
        global _MODEL, _TOKENIZER, _DEVICE, _CACHE
        if s in _CACHE:
            return _CACHE[s]
        input_ids = _TOKENIZER.encode_plus(
            s,
            add_special_tokens=True,
            max_length=max_length,
            padding="do_not_pad",
            truncation=True,
            return_tensors='pt').input_ids.to(_DEVICE)

        greedy_output = _MODEL.generate(input_ids, max_length=max_length)
        t = _TOKENIZER.decode(greedy_output[0], skip_special_tokens=True)
        _CACHE[s] = t
        return t
    except Exception as e:
        return f'<status>{e}'


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    content = request.get_json()
    # print(content)
    text = content.get('inputs', '')
    max_length = int(content.get('max_length', 128))
    output = generate_gready(text, max_length=max_length)
    return jsonify({'model_id': _MODEL_ID, 'generated_text': output})


# @app.route('/load', methods=['GET', 'POST'])
# def predict():
#     content = request.get_json()
#     print(content)
#     text = content.get('model_id', 'NaoS2/multi-kogi')
#     load_model(model_id)
#     return jsonify({'model_id': _MODEL_ID, 'generated_text': output})


def generate_api(text, max_length=128):
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
        output.get('generated_text')
    except Exception as e:
        return f'<status>{e}'
    return ''


def save_pid():
    with open('.PID1789', 'w') as w:
        print(f'{os.getpid()}', file=w)


def remove_pid(signum, frame):
    os.remove('.PID1789')


signal.signal(signal.SIGTERM, remove_pid)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
    save_pid()
    load_model(sys.argv[1])
