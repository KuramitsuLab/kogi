import traceback
from ._google import google_colab

from IPython.display import display, HTML, JSON
from kogi.service import model_generate, debug_print

RMT_CSS = '''
<style>
.parent {
    background-color: #edebeb;
    width: 100%;
    height: 150px;
}
textarea {
    width: 100%;
    box-sizing: border-box;
    /* ※これがないと横にはみ出る */
    height: 120px;
    font-size: large;
    outline: none;
    /* ※ブラウザが標準で付加する線を消したいとき */
    resize: none;
}
.outbox {
    /*padding: 0.2em 0.5em; margin: 2em 0; */
    color: #565656;
    background: #ffeaea;
    background-size: 150%;
    background-repeat: no-repeat;
    background-position: top right;
    background-color: rgba(255, 255, 255, 0.8);
    background-blend-mode: lighten;
    border: dashed 2px #ffc3c3;
    height: 120px;
    font-size: large;
    text-align: left;
}
.inbox {
    /*
    padding: 0.5em 1em;margin: 2em 0;
    */
    background: -webkit-repeating-linear-gradient(-45deg, #f0f8ff, #f0f8ff 3px, #e9f4ff 3px, #e9f4ff 7px);
    background: repeating-linear-gradient(-45deg, #f0f8ff, #f0f8ff 3px, #e9f4ff 3px, #e9f4ff 7px);
}
.labelbox {
    position: relative;
    padding: 0.5em 0.7em;
    margin: 2em 0;
    background: #6f4b3e;
    color: white;
    font-weight: bold;
}
</style>
'''

RMT_HTML = '''
<div id="{id}" class="parent">
<div style="float: left; width: 48%; text-align: right;">
<label class="labelbox" for="input">{input_caption}</label>
<textarea id="input" class="inbox"></textarea>
</div>
<div style="float: left; width: 48%; text-align: right;">
<label class="labelbox" for="outout">{output_caption}</label>
<div id="output" class="outbox"></div>
</div>
</div>
'''

RMT_JS = '''
<script>
var timer = null;
var inputPane = document.getElementById('input');
inputPane.addEventListener('input', (e) => {
    var text = e.srcElement.value;
    if (timer !== null) {
        clearTimeout(timer);
    }
    timer = setTimeout(() => {
        timer = null;
        (async function () {
            const result = await google.colab.kernel.invokeFunction('notebook.rmt', [text], {});
            const data = result.data['application/json'];
            const textarea = document.getElementById('output');
            textarea.innerHTML = data.result;
        })();
    }, 600);  // 何も打たななかったら600ms秒後に送信
});
</script>
'''


def transform_nop(text):
    return text


def display_rmt(input_caption='入力',
                output_caption='出力',
                delay=600,
                transform_fn=transform_nop):
    data = dict(
        id=1,
        input_caption=input_caption,
        output_caption=output_caption,
        delay=delay,
    )
    _RMT_HTML = RMT_HTML.format(**data)
    _RMT_JS = RMT_JS.replace('600', str(delay))
    display(HTML(RMT_CSS+_RMT_HTML+_RMT_JS))
    _CACHE = {'': ''}

    def rmt(text):
        try:
            if text in _CACHE:
                text2 = _CACHE[text]
            else:
                text2 = transform_fn(text)
                _CACHE[text] = text2
            return JSON({'result': text2})
        except:
            traceback.print_exc()

    if google_colab is not None:
        google_colab.register_callback('notebook.rmt', rmt)


def transform_nop(text, cache):
    return text


def model_fn(text, cache):
    if text in cache:
        return cache[text]
    generated_text = model_generate(text, beam=1)
    cache[text] = generated_text
    return generated_text


def display_rmt(input_caption='入力',
                output_caption='出力',
                delay=600, html=True,
                transform_fn=model_fn):
    data = dict(
        id=1,
        input_caption=input_caption,
        output_caption=output_caption,
        delay=delay,
    )
    _RMT_HTML = RMT_HTML.format(**data)
    display(HTML(RMT_CSS+_RMT_HTML+RMT_JS))
    _CACHE = {'': ''}

    def rmt(text):
        try:
            text2 = transform_fn(text, _CACHE)
            if len(_CACHE) < 3:  # 接続エラーをキャッシュから消す
                for k, v in list(_CACHE.items()):
                    if 'HTTPConnectionPool' in v:
                        del _CACHE[k]
            return JSON({'result': text2})
        except:
            traceback.print_exc()

    if google_colab is not None:
        google_colab.register_callback('notebook.rmt', rmt)
