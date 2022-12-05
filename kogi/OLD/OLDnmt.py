# translate
import builtins
import warnings
import IPython
from IPython.display import display, HTML
import os

from .logger import logging_asjson, send_log, print_nop

TRANSLATE_CSS_HTML = '''
<style>
.parent {
  background-color: #edebeb;
  width: 100%;
  height: 150px;
}
textarea {
  width: 100%;
  box-sizing: border-box;  /* ※これがないと横にはみ出る */
  height:120px;
  font-size: large;
  outline: none;           /* ※ブラウザが標準で付加する線を消したいとき */
  resize: none;
}
.box11{
//    padding: 0.5em 1em;
//    margin: 2em 0;
    color: #5d627b;
    background: white;
    border-top: solid 5px #5d627b;
    box-shadow: 0 3px 5px rgba(0, 0, 0, 0.22);
}
.box18{
  //padding: 0.2em 0.5em;
  //margin: 2em 0;
  color: #565656;
  background: #ffeaea;
  //background-image: url(https://2.bp.blogspot.com/-u7NQvQSgyAY/Ur1HXta5W7I/AAAAAAAAcfE/omW7_szrzao/s800/dog_corgi.png);
  background-size: 150%;
  background-repeat: no-repeat;
  background-position: top right;
  background-color:rgba(255,255,255,0.8);
  background-blend-mode:lighten;
  //box-shadow: 0px 0px 0px 10px #ffeaea;
  border: dashed 2px #ffc3c3;
  //border-radius: 8px;
}
.box16{
    //padding: 0.5em 1em;
    //margin: 2em 0;
    background: -webkit-repeating-linear-gradient(-45deg, #f0f8ff, #f0f8ff 3px,#e9f4ff 3px, #e9f4ff 7px);
    background: repeating-linear-gradient(-45deg, #f0f8ff, #f0f8ff 3px,#e9f4ff 3px, #e9f4ff 7px);
}
.box24 {
    position: relative;
    padding: 0.5em 0.7em;
    margin: 2em 0;
    background: #6f4b3e;
    color: white;
    font-weight: bold;
}
.box24:after {
    position: absolute;
    content: '';
    top: 100%;
    left: 30px;
    border: 15px solid transparent;
    border-top: 15px solid #6f4b3e;
    width: 0;
    height: 0;
}
</style>

<div class="parent">
<div style="float: left; width: 48%; text-align: right;">
<label class="box24" for="input">INPUT</label>
<textarea id="input" class="box16"></textarea>
</div>
<div style="float: left; width: 48%; text-align: right;">
<label class="box24" for="outout">OUTPUT</label>
<textarea id="output" class="box18 python" readonly></textarea>
</div>
</div>
<div id="js-loader" class="loader"></div>
'''

TRANSLATE_SCRIPT = '''
<script>
    var timer = null;
    var logtimer = null;
    var inputPane = document.getElementById('input');
    inputPane.addEventListener('input', (e) => {
        var text = e.srcElement.value;
        if(timer !== null) {
            clearTimeout(timer);
        }
        if(logtimer !== null) {
            clearTimeout(logtimer);
        }
        timer = setTimeout(() => {
            timer = null;
            (async function() {
                const result = await google.colab.kernel.invokeFunction('notebook.Convert', [text], {});
                const data = result.data['application/json'];
                const textarea = document.getElementById('output');
                textarea.textContent = data.result;
            })();
        }, 600);  // 何も打たななかったら600ms秒後に送信
        logtimer = setTimeout(() => {
            // logtimer = null;
            google.colab.kernel.invokeFunction('notebook.Logger', [], {});
        }, 60*1000*5); // 5分に１回まとめて送信
    });
</script>
'''


def check_sentencepiece():
    try:
        import sentencepiece
    except:
        print('Installing sentencepiece')
        os.system('pip install -q sentencepiece')
    try:
        import transformers
    except:
        print('Installing transformers')
        os.system('pip install -q transformers')


def load_mt5(model_id, qint8=True, device='cpu', log_class=None, print=print):
    check_sentencepiece()
    import torch
    from transformers import MT5ForConditionalGeneration, MT5Tokenizer
    model = MT5ForConditionalGeneration.from_pretrained(model_id)
    tokenizer = MT5Tokenizer.from_pretrained(model_id, is_fast=True)

    if qint8:
        model = torch.quantization.quantize_dynamic(
            model, {torch.nn.Linear}, dtype=torch.qint8
        )

    if isinstance(device, str):
        device = torch.device(device)
    model.to(device)

    def gready_search(s: str, max_length=128, beam=5) -> str:
        input_ids = tokenizer.encode_plus(
            s,
            add_special_tokens=True,
            max_length=max_length,
            padding="do_not_pad",
            truncation=True,
            return_tensors='pt').input_ids.to(device)
        if beam == 1:  # greedy_search
            greedy_output = model.generate(input_ids, max_length=max_length)
            t = tokenizer.decode(greedy_output[0], skip_special_tokens=True)
            if log_class is not None:
                logging_asjson('nmt', right_now=True,
                               mode_id=model_id,
                               log_class=log_class,
                               input=s,
                               output=t,
                               )
            return t
        # beem_search
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            outputs = model.generate(
                input_ids,
                # max_length=max_length,
                return_dict_in_generate=True, output_scores=True,
                temperature=1.0,          # 生成にランダム性を入れる温度パラメータ
                diversity_penalty=1.0,    # 生成結果の多様性を生み出すためのペナルティ
                num_beams=beam,
                #            no_repeat_ngram_size=2,
                num_beam_groups=beam,
                num_return_sequences=beam,
                repetition_penalty=1.5,   # 同じ文の繰り返し（モード崩壊）へのペナルティ
                early_stopping=True
            )
            results = [tokenizer.decode(out, skip_special_tokens=True)
                       for out in outputs.sequences]
            scores = [float(x) for x in outputs.sequences_scores]
            return results, scores
    return gready_search


_kogi_nmt_fn = None


def kogi_nmt_wakeup(model_id='kkuramitsu/kogi-mt5-test'):
    global _kogi_nmt_fn
    _kogi_nmt_fn = load_mt5(model_id, log_class='wakeup')


def kogi_nmt_talk(s: str, beam=1):
    if _kogi_nmt_fn is not None:
        return _kogi_nmt_fn(s, beam=beam)
    return None


def _transform_nop(text: str):
    return text


def nmt(model_id, load_nmt=load_mt5, log_class=None, kogi_mode=False,
        beam=1, device='cpu', qint8=True,
        transform_before=_transform_nop, transform_after=_transform_nop,
        input='入力', output='予測', print=print):
    global _kogi_nmt_fn
    nmt_fn = load_nmt(model_id, qint8=qint8, device=device,
                      log_class=log_class, print=print)
    _kogi_nmt_fn = nmt_fn

    cached = {'': ''}

    def convert(text):
        try:
            ss = []
            for line in text.splitlines():
                if line not in cached:
                    line = transform_before(line)
                    translated = nmt_fn(line, beam=beam)
                    translated = transform_after(translated)
                    print(len(line), line, '=>', translated)
                    cached[line] = translated
                else:
                    translated = cached[line]
                ss.append(translated)
            text = '\n'.join(ss)
            return IPython.display.JSON({'result': text})
        except Exception as e:
            print(e)

    try:
        display(HTML(TRANSLATE_CSS_HTML.replace(
            'INPUT', input).replace('OUTPUT', output)))
        display(HTML(TRANSLATE_SCRIPT))
        from google.colab import output
        output.register_callback('notebook.Convert', convert)
        output.register_callback('notebook.Logger', send_log)
    except ModuleNotFoundError as e:
        builtins.print('申し訳ありません. 現在、Colab上のみ動作します。')
        print(e)


def kogi_nmt(model_id, load_nmt=load_mt5, class_name='unknown',
             beam=1, device='cpu', qint8=True, print=print_nop):
    nmt(model_id, load_nmt=load_nmt, log_class=class_name, kogi_mode=True,
        beam=beam, device=device, qint8=qint8, input='日本語', output='Python', print=print)
