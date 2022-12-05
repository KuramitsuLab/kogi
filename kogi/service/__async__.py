import sys
import os

_LOCKFILE = '._Lock9293.txt'


def is_loading():
    try:
        with open(_LOCKFILE) as f:
            return f.read().strip()
    except FileNotFoundError as e:
        return None


_MODELS = set()


def async_download(model_id):
    if model_id in _MODELS:
        return
    script = os.path.abspath(__file__)
    #print(f'python3 {script} {model_id} &')
    os.system(f'python3 {script} {model_id} &')
    _MODELS.add(model_id)


class _Lock(object):
    def __init__(self, msg):
        self.msg = msg

    def __enter__(self):
        if os.path.exists(_LOCKFILE):
            raise FileExistsError(_LOCKFILE)

        with open(_LOCKFILE, 'w') as w:
            print(self.msg, file=w)

    def __exit__(self, etype, evalue, tb):
        os.remove(_LOCKFILE)


def _check_modules():
    try:
        import sentencepiece
    except:
        with _Lock('sentencepiece') as _:
            os.system('pip install -q sentencepiece')
    try:
        import transformers
    except:
        with _Lock('transformers') as _:
            os.system('pip install -q transformers')


def _load_huggingface(model_id):
    _check_modules()

    import warnings
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        with _Lock(f'downloading {model_id}') as _:
            tokenizer = AutoTokenizer.from_pretrained(model_id, is_fast=False)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_id)


if __name__ == '__main__':
    _load_huggingface(sys.argv[1])
