from .globals import kogi_defined, kogi_get, globals_update
from .s3logging import kogi_print, print_nop, debug_print, record_log
from .textra import translate, is_ja, EJ, is_japanese_text, is_english_text
# from .slack import load_slack, slack_send
# from .OLDchatgpt import set_openai, model_prompt
# from .flaskapi import load_model, model_generate, check_awake, start_server
from .codellm import llm_prompt, llm_login
from .simplemsg import simplify

def kogi_set(**kwargs):
    globals_update(kwargs)
