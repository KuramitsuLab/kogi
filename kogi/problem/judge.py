import builtins
from IPython.display import display, HTML
from IPython import get_ipython
from .timeout import exec_with_timeout


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


def render_header():
    display(HTML(JUDGE_CSS))


JUDGE_HTML = '''
<div class="parent" style="clear:both;">
<h4>{title}</h4>
<pre>{input}</pre>
<div style="float: left; width: 48%; text-align: right;">
<label class="box24" for="input">実行結果</label>
<textarea class="box18" style="height:{height}" readonly>{output}</textarea>
</div>
<div style="float: left; width: 48%; text-align: right;">
<label class="box24" for="outout">正解例</label>
<textarea class="box18" style="height:{height}" readonly>{sample}</textarea>
</div>
</div>
<p style="clear:both;"></p>
'''


def render_result(title, input, result, output):
    n_lines = max(output.count('\n'), result.count('\n'))+1
    data = dict(
        title=title,
        input=input,
        output=result,
        sample=output,
        box='box16' if result == output else 'box17',
        height='240px' if n_lines > 10 else f'{n_lines*24}px'
    )
    display(HTML(JUDGE_CSS))
    display(HTML(JUDGE_HTML.format(**data)))


AC_HTML = '''
<div style="clear:both;">
AtCoderでACを取るためには、<b>制約条件</b>を満たす全ての入力にパスするようにプログラムする必要があります。<br/>
もう一度、確認してから<a href="{url}" target="atcoder">提出</a>しましょう。
</div>
'''


def render_footer(data):
    display(HTML(AC_HTML.format(url=data['url'])))
