import re
import json
import requests
from requests_oauthlib import OAuth1
from .globals import kogi_get, globals_update
from .s3logging import kogi_print

def is_ja():
    return kogi_get('lang', 'en') == 'ja'

def EJ(en, ja=None):
    return ja if is_ja() and ja else en

hira_pattern = re.compile('[あ-をア-ヲ]')

def is_japanese_text(text):
    return re.search(hira_pattern, text) is not None

common_words = [
    "the", "to", "that", "it", "with", "you", "this", "but", "on", 
    "have", "be", "are", "of", "please", "tell", "answer",
    "what", "an", "at", "was", "will", "we", "can", "could",
    "your", "find", "my", "fix", "code", "following",
    "about", "would", "there", "which", "out", "above", 
    "below", "get", "like"
]

word_pattern = re.compile(r'\b(' + '|'.join(common_words) + r')\b')

def is_english_text(text):
    return len(re.findall(word_pattern, text.lower())) > 0

# Translate

TEXTRA_NAME = 'kkuramitsu'
TEXTRA_KEY = '6c0bbdfd6c5c53cb0b0699729ed56a5c062ebba7c'
TEXTRA_URL = 'https://mt-auto-minhon-mlt.ucri.jgn-x.jp/api/mt/generalNT'
TEXTRA_CACHE = {}
TEXTRA_OAUTH = None


def load_mt(secret):
    global TEXTRA_OAUTH
    TEXTRA_OAUTH = OAuth1(TEXTRA_KEY, secret)
    return TEXTRA_OAUTH


def check_oauth():
    global TEXTRA_OAUTH
    if TEXTRA_OAUTH is None:
        secret = kogi_get('textra', None)
        if secret:
            return load_mt(secret)
        return None
    return TEXTRA_OAUTH


def _isEnglish(text):
    for c in text:
        if c >= 'あ':
            return False
    return True


def translate(text, lang=None):
    global TEXTRA_OAUTH
    check_oauth()
    if TEXTRA_OAUTH is None:
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
        res = requests.post(
            URL, data=params, auth=TEXTRA_OAUTH, timeout=(3.5, 7.0))
        res.encoding = 'utf-8'
        data = json.loads(res.text)
        result = data['resultset']['result']['text']
        if isMulti:
            return result.split('\n')
        TEXTRA_CACHE[text] = result
        return result
    except Exception as e:
        kogi_print('翻訳できません', e)
        TEXTRA_OAUTH = None
        globals_update({'textra': None})
        return None


def translate_en(text):
    return translate(text, lang='en_ja')


def translate_ja(text):
    return translate(text, lang='ja_en')
