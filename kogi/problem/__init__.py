import re
from .drill import kogi_judge, judge_cpc
from .atcoder import download_atcoder_problem

from kogi.chat import start_kogi, kogi_print
from kogi.hook import register_hook

KOGI_PAT = re.compile('#\\s*kogi\\s*(.*)')

def _is_atcoder(code):
    for url in re.findall(KOGI_PAT, code):
        if 'https://atcoder.jp/contests/' in url:
            return True
    return False

def _run_atcoder(ipy, raw_cell, **kwargs):
    for url in re.findall(KOGI_PAT, raw_cell):
        if 'https://atcoder.jp/contests/' in url:
            break
    data = download_atcoder_problem(url)
    if 'problem_id' in data:
        kogi_print('コギーがAtCoderの問題を発見し、テストケースを実行しようとしています')
        kogi_judge(ipy, raw_cell, data, judge_cpc, start_kogi)
    else:
        kogi_print('問題が見つかりません。')
    return None

register_hook('atcoder', _is_atcoder, _run_atcoder)
