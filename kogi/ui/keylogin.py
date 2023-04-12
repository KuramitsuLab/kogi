import traceback
from kogi.service import record_log, kogi_set, debug_print
from ._google import google_colab
from .message import kogi_print, Doc
from IPython.display import JSON

LOGIN_HTML = """\
<style>
/* Bordered form */
form {
  border: 3px solid #f1f1f1;
}

/* Full-width inputs */
input[type=text] {
  width: 100%;
  padding: 6px 10px;
  margin: 8px 0;
  display: inline-block;
  border: 1px solid #ccc;
  box-sizing: border-box;
}

/* Set a style for all buttons */
button.login {
  color: white;
  background-color: #f44336;
  margin: 8px 0;
  border: none;
  cursor: pointer;
  width: auto;
  padding: 8px 16px;
  background-color: #f44336;
}

button:disabled {
    background-color: #aaaaaa;
    filter:brightness(0.5);
    cursor:not-allowed;
}

/* Add a hover effect for buttons */
button:hover {
  opacity: 0.8;
}

/* Add padding to containers */
.container {
  padding: 0px;
}

/* The "Forgot password" text */
span.psw {
  float: right;
  padding-top: 8px;
}

</style>
<form id="base">
  <b>こんにちは！ コギーくんは、皆さんの学習状況にあわせてお手伝いします。</b>
  <div class="container">
    <label for="uname">学籍番号(正しくないと機能が制限されます)</label>
    <input type="text" placeholder="学籍番号" id="uname" name="uname" required>
    <label for="psw">タイピング力も見せてね</label>
    <div><code id="code">print("A", "B", "C")</code><div>
    <input type="text" placeholder="上のコードを入力してください。" id="ucode" name="ucode" required>
    <div style="font-size:8pt">コードの意味が同じなら、空白は省略して構いません。</div>
    </div>
  <div class="container" style="background-color:#f1f1f1">
    <button type="button" id="ulogin" class="login">利用規約に同意する</button>
    <span class="psw"> <a href="https://kuramitsulab.github.io/kogi_tos.html" target="_blank">利用規約とは</a></span>
  </div>
</form>
<script>
    const samples = [
        'print("Hello,\\\\nWorld")',
        'print((math.pi * i) / 32)',
        'print("X", 1, "Y", 2, "Z")',
        'print(a[x][y], b[x][y])',
        'print(x if x == y else y)',
        'print(a/gcd(a,b), b/gcd(a,b))',
        'print(file=w, end="")',
        'print(1+2, 2*3, 3//4)',
        'print([1,2,3], (1,2,3))',
        'print({"A": 1, "B": 2})',
    ];
    const index = Math.floor(Math.random() * samples.length);
    document.getElementById('code').innerText=samples[index];
    var buffers = [];
    var before = new Date().getTime();
    var finished = false;
    document.getElementById('ucode').addEventListener('keydown', (e) => {
      var now = new Date().getTime();
      if(e.key === ' ') {
        buffers.push(`${now - before} SPACE`);
      }
      else {
        buffers.push(`${now - before} ${e.key}`);
      }
      if(e.key === ')') {
        finished = true;
      }
      before = now;
      if (finished && buffers.length > samples[index].length) {
        document.getElementById('ulogin').disabled=false;
      }
    });
    document.getElementById('ulogin').disabled=true;
    document.getElementById('ulogin').onclick = () => {
        const uname = document.getElementById('uname').value;
        const ucode = document.getElementById('ucode').value;
        const keys = buffers.join(' ');
        //document.getElementById('code').innerText=keys;
        //google.colab.kernel.invokeFunction('notebook.login', [uname, samples[index], ucode, keys], {});
        (async function() {
            const result = await google.colab.kernel.invokeFunction('notebook.login', [uname, samples[index], ucode, keys], {});
            const data = result.data['application/json'];
            document.getElementById('base').innerText=data.text;
        })();
        document.getElementById('base').innerText='';
    };
</script>
"""


def check_level(ukeys):
    keys = ukeys.split()
    times = [int(t) for t in keys[0::2]]
    keys = keys[1::2]
    average_time = (sum(times)-max(times)) / (len(times)-1)
    if average_time < 300:
        return average_time, 5
    if average_time < 400:
        return average_time, 4
    if average_time < 450:
        return average_time, 3
    if average_time < 500:
        return average_time, 2
    return average_time, 1


ULEVEL = [
    '今日も一緒にがんばりましょう！',
    '今日はとってもプログラミング日和よね！',
    '最近、どんどん上達している感じだね！',
    'なんだか、プログラミングは十分、得意そうだね！',
    'お、上級者来たね！',
]

ZHTBL = str.maketrans('０１２３４５６７８９', '0123456789')
STUDENT_CODE = 'm8YpbzR6ovEjyzJ8oXnpT3BlbkFJYwKQCc1DmrTOj4Adj'
K = 'k'

PID = ('223', '222', '220', '221', '122', '123')


def check_uname(s):
    for p in PID:
        if s.startswith(p):
            return True
    return False


def ulogin(uname, code, ucode, ukeys):
    try:
        kogi_set(approved=True)
        uname = uname.translate(ZHTBL)
        is_student = check_uname(uname)
        average_time, ulevel = check_level(ukeys)
        kogi_set(uname=uname, ulevel=ulevel, approved=True)
        record_log(type='key', uname=uname, code=code,
                   ucode=ucode, average_time=average_time,
                   ulevel=ulevel, ukeys=ukeys)
        if is_student:
            msg = f'コギーくんを呼んだわ！ {ULEVEL[ulevel-1]}'
            kogi_set(openai_key=f's{K}-{STUDENT_CODE}Ag8')
        else:
            msg = f'学籍番号が変ね。AIを使いたいなら再起動してね。'
        return JSON({'text': msg})
    except:
        traceback.print_exc()
        return JSON({'text': 'よろしく！'})


def login(login_func=ulogin):
    if google_colab:
        google_colab.register_callback('notebook.login', login_func)
    doc = Doc.HTML(LOGIN_HTML)
    doc.set_mention('@ta')
    kogi_print(doc, height=280)
