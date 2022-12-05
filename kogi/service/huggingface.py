
import os
import warnings
import requests
from .s3logging import kogi_print, print_nop
from .__async__ import is_loading, async_download

# NMT

_MODEL_ID = None
_MODEL = None
_TOKENIZER = None

_DEVICE = None


def _check_modules():
    try:
        import sentencepiece
    except:
        kogi_print('Installing sentencepiece')
        os.system('pip install -q sentencepiece')
    try:
        import transformers
    except:
        kogi_print('Installing transformers')
        os.system('pip install -q transformers')


_ASYNC_MODEL_ID = None


def load_model(model_id, qint8=True, device=None, async_downloading=False):
    global _MODEL_ID, _ASYNC_MODEL_ID, _MODEL, _TOKENIZER, _DEVICE
    if _MODEL_ID == model_id:
        return
    if async_downloading:
        _ASYNC_MODEL_ID = model_id
        async_download(model_id)
        return

    _ASYNC_MODEL_ID = None
    _check_modules()

    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        tokenizer = AutoTokenizer.from_pretrained(model_id, is_fast=False)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_id)

    if qint8:
        model = torch.quantization.quantize_dynamic(
            model, {torch.nn.Linear},
            dtype=torch.qint8
        )

    if device is None:
        device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    if isinstance(device, str):
        device = torch.device(device)
    model.to(device)

    _MODEL_ID = model_id
    _MODEL = model
    _TOKENIZER = tokenizer
    _DEVICE = device


def generate_gready(s: str, max_length=128, print=print) -> str:
    global _MODEL, _TOKENIZER, _DEVICE
    input_ids = _TOKENIZER.encode_plus(
        s,
        add_special_tokens=True,
        max_length=max_length,
        padding="do_not_pad",
        truncation=True,
        return_tensors='pt').input_ids.to(_DEVICE)

    greedy_output = _MODEL.generate(input_ids, max_length=max_length)
    t = _TOKENIZER.decode(greedy_output[0], skip_special_tokens=True)
    #kogi_log(type='nmt', mode_id=_MODEL_ID, input=s, output=t)
    return t


def generate_beam(s: str, beam: int, max_length=12, print=print_nop) -> str:
    global _MODEL, _TOKENIZER, _DEVICE
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
        return results, scores


API_URL = "https://api-inference.huggingface.co/models/kkuramitsu/kogi-mt5-test"
API_CACHE = {}


def generate_api(text, model_key, print=print_nop):
    global API_CACHE
    if len(text) > 120:
        return 'ぐるるるる\n（入力が長すぎます）'
    if text in API_CACHE:
        return API_CACHE[text]
    payload = {"inputs": text}
    headers = {"Authorization": f"Bearer {model_key}"}
    response = requests.post(API_URL, headers=headers, json=payload)
    output = response.json()
    # print(text, type(output), output)
    if isinstance(output, (list, tuple)):
        output = output[0]
    if 'generated_text' in output:
        result = output['generated_text']
        API_CACHE[text] = result
    return 'ねむねむ。まだ、起きられない！\n（しばらく待ってからもう一度試してください）'


def model_generate(text, beam=1, max_length=128, print=print_nop) -> str:
    global _MODEL, _ASYNC_MODEL_ID
    if _MODEL is None and _ASYNC_MODEL_ID:
        loading = is_loading()
        if loading:
            return f'<loading>{loading}をダウンロード中. しばらくお待ちください'
        load_model(_ASYNC_MODEL_ID)
    if _MODEL is not None:
        if beam > 1:
            return generate_beam(text, beam, max_length, print)
        return generate_gready(text, max_length, print)
    # if kogi_defined('model_key'):
    #     model_key = kogi_get('model_key')
    #     model_key = f'hf_{model_key}'
    #     return generate_api(text, model_key, print)
    return None
