from .globals import kogi_defined, kogi_get, globals_update
from .s3logging import kogi_print, print_nop, debug_print
from .textra import load_mt, translate
from .slack import load_slack, slack_send
from .huggingface import load_model, model_generate
from .__async__ import is_loading, async_download


def kogi_set(**kwargs):
    globals_update(kwargs)
    if 'model_id' in kwargs:
        load_model(kwargs['model_id'], async_downloading=True)
    if 'mt_key' in kwargs:
        load_mt(kwargs['mt_key'])
    if 'slack_key' in kwargs:
        load_slack(kwargs['slack_key'])
    if 'textra_key' in kwargs:
        load_mt(kwargs['textra_key'])


def isEnglishDemo():
    return kogi_get('english_demo', False)
