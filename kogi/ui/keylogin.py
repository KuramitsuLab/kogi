import traceback
from kogi.service import record_log, kogi_set, debug_print
from ._google import google_colab
from .message import kogi_print
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
button {
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
  こんにちは！ まず、あなたのことを教えてね
  <div class="container">
    <label for="uname">お名前</label>
    <input type="text" placeholder="ニックネームでどうぞ" id="uname" name="uname" required>
    <label for="psw"><code id="code">print("A", "B", "C")</code></label>
    <input type="text" placeholder="上の1文をそのまま入力してみてください" id="ucode" name="ucode" required>
  </div>
  <div class="container" style="background-color:#f1f1f1">
    <button type="button" id="ulogin">利用規約に同意する</button>
    <span class="psw"> <a href="#">利用規約とは</a></span>
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
        'print((1,2,3), [1,2,3])',
        'print({"A": 1, "B": 2})',
    ];
    const index = Math.floor(Math.random() * samples.length);
    document.getElementById('code').innerText=samples[index];
    var buffers = [];
    var before = new Date().getTime();
    document.getElementById('ucode').addEventListener('keydown', (e) => {
      var now = new Date().getTime();
      if(e.key === ' ') {
        buffers.push(`${now - before} SPACE`);
      }
      else {
        buffers.push(`${now - before} ${e.key}`);
      }
      before = now;
      if (buffers.length > 16) {
        document.getElementById('ulogin').disabled=false;
      }
    });
    document.getElementById('ulogin').disabled=true;
    document.getElementById('ulogin').onclick = () => {
        const uname = document.getElementById('uname').innerText;
        const ucode = document.getElementById('ucode').innerText;
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
    times = [int(t) for t in keys[1::2]]
    keys = keys[0::2]
    average_time = (sum(times)-max(times)) / (len(times)-1)
    if average_time < 200:
        return average_time, 5
    if average_time < 300:
        return average_time, 4
    if average_time < 400:
        return average_time, 3
    if average_time < 500:
        return average_time, 2
    return average_time, 1


ULEVEL = [
    '今日は一緒にがんばりましょう！',
    'どんどん上達しているね！',
    '今日はよいプログラミング日和だね！',
    'プログラミングは得意そうですね！',
    '上級者キター！！',
]


def ulogin(uname, code, ucode, ukeys):
    try:
        debug_print(uname, code, ucode, ukeys)
        if len(uname) > 0:
            kogi_set(uname=uname)
        average_time, ulevel = check_level(ukeys)
        kogi_set(ulevel=ulevel)
        record_log(type='key', uname=uname, code=code,
                   ucode=ucode, average_time=average_time, ulevel=ulevel, ukeys=ukeys)
        return JSON({'text': ULEVEL[ulevel-1]})
    except:
        traceback.print_exc()
        return JSON({'text': 'よろしく！'})


def login(login_func=ulogin):
    if google_colab:
        google_colab.register_callback('notebook.login', login_func)
    kogi_print(LOGIN_HTML, html=True, height=280)
