from IPython.display import display, HTML
#import difflib
import requests
from bs4 import BeautifulSoup
import builtins
from .logger import log
from .liberr import KogiError


_lines = None
_outputs = None


def input(s=''):
    global _lines
    if _lines is not None and len(_lines) > 0:
        return _lines.pop(0)
    else:
        _lines = None
    return builtins.input(s)


def print(*a, **kw):
    if _outputs is not None:
        sep = kw.get('sep', ' ')
        end = kw.get('end', '\n')
        s = sep.join([str(s) for s in a]) + end
        _outputs.append(s)
    else:
        builtins.print(*a, **kw)


def _get_problemid(problem):
    problem, _, _ = problem.partition('&')
    _, _, problem = problem.rpartition('/')
    problem = problem.lower()
    num = 'a'
    if problem[-1] in 'abcdefgh':
        num = problem[-1]
        problem = problem[:-1].replace('_', '').replace('-', '')
    return f'{problem}_{num}'


def _get_url(problem):
    if '/' in problem:
        return problem
    problem = problem.lower()
    num = 'a'
    if problem[-1] in 'abcdefgh':
        num = problem[-1]
        problem = problem[:-1].replace('_', '').replace('-', '')
    return f'https://atcoder.jp/contests/{problem}/tasks/{problem}_{num}'


SAMPLE = {}


def _get_sample(problem):
    pid = None
    try:
        if '/' in problem:
            problem = problem[problem.rfind('/')+1:]
        problem = problem.lower()
        if '_' in problem:
            problem, num = problem.split('_')
        else:
            num = problem[-1].lower()
            problem = problem[:-1].lower()
        pid = f'{problem}_{num}'
        if pid in SAMPLE:
            return SAMPLE[pid], pid
        response_text = requests.get(
            url=f"https://atcoder.jp/contests/{problem}/tasks/{problem}_{num}").text
        html = BeautifulSoup(response_text, "lxml")
        d = {}
        for a in html.find_all("section"):
            # print(a)
            if a.h3 and a.pre:
                key = a.h3.text.replace('\r\n', '\n')
                value = a.pre.text.replace('\r\n', '\n')
                d[key] = value
        SAMPLE[pid] = d
        return d, pid
    except:
        return {}, pid


# def _check_atcoder(option):
#     try:
#         if 'atcoder' in option:
#             d = _get_sample(option)
#             return True
#     except Exception as e:
#         print('問題が読み込めません', e)
#     return False


# _COLOR_HTML_DIC = {
#     'yellow': '<span style="background: pink">',
#     'red': '<span style="background: lightblue">',
#     'end': '</span>'
# }


# def _display_diff(ground_truth, target):
#     _CDIC = _COLOR_HTML_DIC

#     if ground_truth == target:
#         return

#     d = difflib.Differ()
#     diffs = d.compare(ground_truth, target)

#     result = ''
#     for diff in diffs:
#         status, _, character = list(diff)
#         if status == '-':
#             character = _CDIC['red'] + character + _CDIC['end']
#         elif status == '+':
#             character = _CDIC['yellow'] + character + _CDIC['end']
#         else:
#             pass
#         result += character

#     display(
#         HTML(f'<h4>差分</h4><div style="white-space: pre-wrap;">{result}</div>'))


JUDGE_CSS = '''
<style>
.parent {
  background-color: #edebeb;
  width: 100%;
  //height: 150px;
}
textarea {
  width: 100%; 
  box-sizing: border-box;  /* ※これがないと横にはみ出る */
  //height:120px; 
  font-size: large;
  outline: none;           /* ※ブラウザが標準で付加する線を消したいとき */
  resize: none;
}
.box18{  // ひだり
  //padding: 0.2em 0.5em;
  //margin: 2em 0;
  color: #565656;
  background: #ffeaea;
  background-size: 150%;
  background-repeat: no-repeat;
  background-position: top right;
  background-color:rgba(255,255,255,0.8);
  //box-shadow: 0px 0px 0px 10px #ffeaea;
  border: dashed 2px #ffc3c3;
  //border-radius: 8px;
}
.box16{
    background: repeating-linear-gradient(-45deg, #D5FFB0, #D5FFB0 3px,#ffffff 3px, #ffffff 7px);
}
.box17{
    background-image: repeating-linear-gradient(45deg, rgba(255, 0, 0, .3), rgba(255, 0, 0, .3) 10px, #FFEFF7 10px, #FFEFF7 20px);
}
.box24 {
    position: relative;
    padding: 0.5em 0.7em;
    margin: 2em 0; background: #6f4b3e;
    color: white; font-weight: bold;
}
.box23:after {
    position: absolute;
    content: '';
    top: 100%; left: 30px;
    border: 15px solid transparent;
    border-top: 15px solid #6f4b3e;
    width: 0; height: 0;
}
</style>
'''

JUDGE_HTML = '''
<div class="parent" style="clear:both;">
<h4>{title}</h4>
<pre>{input}</pre>
<div style="float: left; width: 48%; text-align: right;">
<label class="box24" for="input">実行結果</label>
<textarea class="box18" style="height:{height}" readonly>{output}</textarea>
</div>
<div style="float: left; width: 48%">
<label class="box24" for="outout">正解例</label>
<textarea class="box18" style="height:{height}" readonly>{sample}</textarea>
</div>
</div>
<p style="clear:both;"></p>
'''

AC_HTML = '''
<div style="clear:both;">
AtCoderでACを取るためには、<b>制約条件</b>を満たす全ての入力にパスするようにプログラムする必要があります。<br/>
もう一度、確認してから<a href="{url}" target="atcoder">提出</a>しましょう。
</div>
'''


def _run_judge(code, problem):
    global _lines, _outputs
    d, problem_id = _get_sample(problem)
    if len(d) == 0:
        raise KogiError(
            translated='問題データが読み込めません。',
            reason='問題の指定方法が間違っています',
            hint='問題ページのURLをコピーしてください',
            solution='%%atcoder 問題ページのURL'
        )
    get_ipython()._run_cell_context = problem_id
    try:
        ac = 0
        display(HTML(JUDGE_CSS))
        for key in ['入力例 1', '入力例 2', '入力例 3']:
            if key not in d:
                continue
            data = {'title': key, 'input': d[key]}
            _lines = [s for s in d[key].split('\n') if len(s) > 0]
            _outputs = []
            res = get_ipython().run_cell(code)
            res.raise_error()
            key = key.replace('入力', '出力')
            data['sample'] = d[key]
            data['output'] = ''.join(_outputs)
            data['box'] = 'box16' if data['sample'] == data['output'] else 'box17'
            ac += 1 if data['sample'] == data['output'] else 0
            lines = max(data['output'].count('\n'),
                        data['sample'].count('\n'))+1
            data['height'] = '240px' if lines > 10 else f'{lines*24}px'
            display(HTML(JUDGE_HTML.format(**data)))
        display(HTML(AC_HTML.format(url=_get_url(problem))))
        get_ipython()._run_cell_context = None
        log(type='atcoder', problem=problem_id, ac=ac, code=code)
    except:
        pass
    finally:
        _lines = None
        _outputs = None
