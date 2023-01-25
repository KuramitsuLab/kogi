import socket
import time
import signal
import sys
import os
import warnings
import traceback

_PREV_TIME = time.time()

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

    # https://github.com/huggingface/transformers/issues/2542
    model = torch.quantization.quantize_dynamic(
        model, {torch.nn.Bilinear},
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


def generate_gready(s: str, max_length=128) -> str:
    global _MODEL, _TOKENIZER, _DEVICE, _CACHE
    if _MODEL is None:
        return '<status>Now Loading'
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


def generate_beam(s: str, max_length=128, beam: int = 1) -> str:
    global _MODEL, _TOKENIZER, _DEVICE, _CACHE
    if _MODEL is None:
        return ['<status>Now Loading'], [0]

    key = f'{beam}:{s}'
    if key in _CACHE:
        return _CACHE[key]
    input_ids = _TOKENIZER.encode_plus(
        s,
        add_special_tokens=True,
        max_length=max_length,
        padding="do_not_pad",
        truncation=True,
        return_tensors='pt').input_ids.to(_DEVICE)

    # beem_search
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', UserWarning)
        outputs = _MODEL.generate(
            input_ids,
            # max_length=max_length,
            return_dict_in_generate=True, output_scores=True,
            temperature=1.0,          # 生成にランダム性を入れる温度パラメータ
            diversity_penalty=1.0,    # 生成結果の多様性を生み出すためのペナルティ
            num_beams=beam,
            #            no_repeat_ngram_size=2,
            num_beam_groups=beam,
            num_return_sequences=beam,
            repetition_penalty=1.5,   # 同じ文の繰り返し（モード崩壊）へのペナルティ
            early_stopping=True
        )
        results = [_TOKENIZER.decode(out, skip_special_tokens=True)
                   for out in outputs.sequences]
        scores = [float(x) for x in outputs.sequences_scores]
        _CACHE[key] = (results, scores)
        return results, scores


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    global _PREV_TIME
    _PREV_TIME = time.time()
    content = request.get_json()
    # print(content)
    text = content.get('inputs', '')
    max_length = int(content.get('max_length', 128))
    beam = int(content.get('beam', 1))
    try:
        if beam <= 1:
            output = generate_gready(text, max_length=max_length)
            return jsonify({'model_id': _MODEL_ID, 'generated_text': output})
        outputs, scores = generate_beam(text, max_length=max_length, beam=beam)
        return jsonify({
            'model_id': _MODEL_ID,
            'generated_text': output[0],
            'outputs': outputs, 'scores': scores,
        })
    except Exception as e:
        tb = traceback.format_exc()
        return jsonify({
            'model_id': _MODEL_ID, 'generated_text': f'<error>{tb}',
        })


def get_pid():
    try:
        with open('.PID1789') as f:
            return int(f.read().strip())
    except:
        return None


def check_port(port):
    host = "127.0.0.1"
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0


def save_pid():
    pid = get_pid()
    if pid and check_port(5000):
        print('ALREADY LOADED', pid)
        return False
    with open('.PID1789', 'w') as w:
        print(f'{os.getpid()}', file=w)
    return True


def shutdown_server(signum, frame):
    print('Shutdown server...')
    try:
        func = request.environ.get('werkzeug.server.shutdown')
        if func:
            func()
    finally:
        pid = get_pid()
        if pid and pid == os.getpid():
            os.remove('.PID1789')


@app.route('/shutdown', methods=['GET'])
def shutdown():
    shutdown_server(None, None)
    return 'Server shutting down...'


signal.signal(signal.SIGTERM, shutdown_server)


def check_access(signum, frame):
    current_time = time.time()
    if current_time - _PREV_TIME > 600*6:
        shutdown_server()


signal.signal(signal.SIGALRM, check_access)
signal.setitimer(signal.ITIMER_REAL, 600, 600)  # 10分

if __name__ == '__main__':
    print('PID', get_pid(), os.getpid())
    if save_pid():
        load_model(sys.argv[1])
        app.run(debug=False, host='localhost')
