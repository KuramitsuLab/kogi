import requests
from requests.exceptions import Timeout
from bs4 import BeautifulSoup

SAMPLE = {}


def download_atcoder_sample(url):
    if '?' in url:
        url, _, _ = url.rpartition('?')
    _, _, problem_id = url.rpartition('/')
    if problem_id in SAMPLE:
        return SAMPLE[problem_id]
    # try:
    response = requests.get(url, timeout=(3.0, 7.5))
    if response.status_code != 200:
        return {'error': f'読み込めません {response.status_code} {url}'}
    response_text = response.text
    html = BeautifulSoup(response_text, "lxml")
    d = {}
    for a in html.find_all("section"):
        # print(a)
        if a.h3 and a.pre:
            key = a.h3.text.replace('\r\n', '\n')
            value = a.pre.text.replace('\r\n', '\n')
            d[key] = value
    data = {'problem_id': problem_id, 'url': url}
    testcases = []
    if '入力例 1' in d:
        testcases.append(dict(input=d['入力例 1'], output=d['出力例 1']))
    if '入力例 2' in d:
        testcases.append(dict(input=d['入力例 2'], output=d['出力例 2']))
    if '入力例 3' in d:
        testcases.append(dict(input=d['入力例 3'], output=d['出力例 3']))
    data['testcases'] = testcases
    SAMPLE[problem_id] = data
    return data


# https://zenn.dev/hellorusk/articles/copy-from-blog-20210211
DROPBOX = 'https://www.dropbox.com/sh/nx3tnilzqz7df8a/AABP2YNyT09nYDTLV7d9bPwka/ABC102/A/in/sample_01.txt'
HOST = 'https://www.dropbox.com/sh/nx3tnilzqz7df8a/AACe0splFqRfbrMiRu41zmLna'


def download_atcoder_problem(directive):
    ss = directive.split()
    try:
        data = download_atcoder_sample(ss[0])
        return data
    except Timeout:
        return dict(error='ネットワーク接続できません')


if __name__ == '__main__':
    download_atcoder_problem(
        'https://atcoder.jp/contests/abc204/tasks/abc204_a random00.txt')
