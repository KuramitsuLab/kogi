# kogi global settings

import os
import warnings
import json
import requests
from requests_oauthlib import OAuth1

from kogi.logger import logging_asjson, print_nop

GLOBALS = {
    'textra': 'cb25461ac40e7a2dc0b2bc05d381995a',
    'model_key': 'rhOcswxkXzMbhlkKQJfytbfxAPVsblhRHX',
}


def kogi_get(key, value=None):
    return GLOBALS.get(key, value)


def kogi_set(**kwargs):
    global GLOBALS
    GLOBALS.update(kwargs)
    if 'model_id' in kwargs:
        load_mt5(kwargs['model_id'])
    if 'textra_key' in kwargs:
        load_textra(kwargs['textra_key'])
    if 'slack_key' in kwargs:
        load_slack(kwargs['slack_key'])


def isEnglishDemo():
    return kogi_get('english_demo', False)


# LOGGING

def kogi_print(*args, **kwargs):
    if GLOBALS.get('verbose', True):
        print('\033[35m[🐶]', *args, **kwargs)
        print('\033[0m', end='')


def kogi_log(log_type, right_now=True, **kwargs):
    global GLOBALS
    if 'class' not in kwargs:
        if 'class_name' not in GLOBALS:
            return
        kwargs['class'] = GLOBALS['class_name']
    if 'name' in GLOBALS:
        kwargs['user_name'] = GLOBALS['name']
    # kogi_print(kwargs)
    logging_asjson(log_type, right_now=right_now, **kwargs)


# Translate

TEXTRA_NAME = 'kkuramitsu'
TEXTRA_KEY = '6c0bbdfd6c5c53cb0b0699729ed56a5c062ebba7c'
TEXTRA_URL = 'https://mt-auto-minhon-mlt.ucri.jgn-x.jp/api/mt/generalNT'
TEXTRA_CACHE = {}
TexTraOAuth = None


def load_textra(secret):
    global TexTraOAuth
    TexTraOAuth = OAuth1(TEXTRA_KEY, secret)


def _isEnglish(text):
    for c in text:
        if c >= 'あ':
            return False
    return True


def translate(text, lang=None):
    global TexTraOAuth
    if TexTraOAuth is None:
        return None

    if lang is not None:
        URL = f'{TEXTRA_URL}_{lang}/'
    elif _isEnglish(text):
        URL = f'{TEXTRA_URL}_en_ja/'
    else:
        URL = f'{TEXTRA_URL}_ja_en/'

    isMulti = False
    if isinstance(text, list):
        text = '\n'.join(text)
        isMulti = True

    if text in TEXTRA_CACHE:
        return TEXTRA_CACHE[text]

    params = {
        'key': TEXTRA_KEY,
        'name': TEXTRA_NAME,
        'type': 'json',
        'text': text,
    }

    try:
        res = requests.post(URL, data=params, auth=TexTraOAuth)
        res.encoding = 'utf-8'
        data = json.loads(res.text)
        result = data['resultset']['result']['text']
        if isMulti:
            return result.split('\n')
        TEXTRA_CACHE[text] = result
        return result
    except Exception as e:
        #     kogi_print('翻訳エラー:', e)
        return None


def translate_en(text):
    return translate(text, lang='en_ja')


def translate_ja(text):
    return translate(text, lang='ja_en')

# NMT


mt5_model_id = None
mt5_model = None
mt5_tokenizer = None


def check_sentencepiece():
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


def load_mt5(model_id, qint8=True, device='cpu'):
    global mt5_model_id, mt5_model, mt5_tokenizer, mt5_device
    if model_id == mt5_model_id:
        return

    check_sentencepiece()
    import torch
    from transformers import MT5ForConditionalGeneration, MT5Tokenizer

    model_id = model_id
    model = MT5ForConditionalGeneration.from_pretrained(model_id)
    tokenizer = MT5Tokenizer.from_pretrained(model_id, is_fast=True)

    if qint8:
        kogi_print('quantization')
        model = torch.quantization.quantize_dynamic(
            model, {torch.nn.Linear}, dtype=torch.qint8
        )

    if isinstance(device, str):
        device = torch.device(device)
    model.to(device)

    mt5_model_id = model_id
    mt5_model = model
    mt5_tokenizer = tokenizer
    mt5_device = device


def generate_gready(s: str, max_length=128, print=print) -> str:
    global mt5_model, mt5_tokenizer, mt5_device
    input_ids = mt5_tokenizer.encode_plus(
        s,
        add_special_tokens=True,
        max_length=max_length,
        padding="do_not_pad",
        truncation=True,
        return_tensors='pt').input_ids.to(mt5_device)

    greedy_output = mt5_model.generate(input_ids, max_length=max_length)
    t = mt5_tokenizer.decode(greedy_output[0], skip_special_tokens=True)
    #kogi_log(type='nmt', mode_id=mt5_model_id, input=s, output=t)
    return t


def generate_beam(s: str, beam: int, max_length=12, print=print) -> str:
    global mt5_model, mt5_tokenizer, mt5_device
    input_ids = mt5_tokenizer.encode_plus(
        s,
        add_special_tokens=True,
        max_length=max_length,
        padding="do_not_pad",
        truncation=True,
        return_tensors='pt').input_ids.to(mt5_device)

    # beem_search
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', UserWarning)
        outputs = mt5_model.generate(
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
        results = [mt5_tokenizer.decode(out, skip_special_tokens=True)
                   for out in outputs.sequences]
        scores = [float(x) for x in outputs.sequences_scores]
        return results, scores


API_URL = "https://api-inference.huggingface.co/models/kkuramitsu/kogi-mt5-test"
API_CACHE = {}


def generate_api(text, model_key, print=print):
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


def model_generate(text, beam=1, max_length=128, print=print) -> str:
    global GLOBALS, mt5_model
    if mt5_model is not None:
        if beam > 1:
            return generate_beam(text, beam, max_length, print)
        return generate_gready(text, max_length, print)
    if 'model_key' in GLOBALS:
        model_key = GLOBALS['model_key']
        model_key = f'hf_{model_key}'
        return generate_api(text, model_key, print)
    return None

# Slack


SLACK_COM = None


def load_slack(slack_id):
    global SLACK_COM
    try:
        from slackweb import Slack
    except ModuleNotFoundError:
        import os
        os.system('pip install slackweb')
        from slackweb import Slack
    url = f'https://hooks.slack.com/services/{slack_id}'
    try:
        SLACK_COM = Slack(url)
    except Exception as e:
        kogi_print('Slackに接続できませんでした.', e)


def send_slack(text):
    global SLACK_COM
    if SLACK_COM is None:
        return
    try:
        SLACK_COM.notify(text=text)
    except Exception as e:
        kogi_print('Slack Error:', e)
