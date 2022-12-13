from kogi.service import kogi_print
from .drill import kogi_judge, judge_cpc
from .atcoder import download_atcoder_problem
from kogi.hook import kogi_register_hook


def atcoder_detector(directive, raw_cell):
    if 'https://atcoder.jp/contests/' in directive:
        return 'atcoder'
    return None


def atcoder_judge(ipy, raw_cell, directive, catch_and_start_kogi):
    data = download_atcoder_problem(directive)
    if 'error' in data:
        kogi_print(data['error'])
    elif 'problem_id' in data:
        kogi_print('コギーがAtCoderの問題を発見し、テストケースを実行しようとしています')
        kogi_judge(ipy, raw_cell, data, judge_cpc, catch_and_start_kogi)
    else:
        kogi_print('問題が見つかりません。')
    return None


kogi_register_hook('atcoder', atcoder_judge, atcoder_detector)
