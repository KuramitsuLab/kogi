import traceback
from kogi.service import record_log, kogi_set, kogi_get, llm_login, EJ, debug_print
from ..webui import google_output, kogi_print
from IPython.display import JSON

K = 'k'

_HTML = """\
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
  <b>コギーくんが、皆さんの学習状況にあわせてお手伝いします。</b>
  <div class="container">
    <label for="uname">ニックネーム (Your nick name) </label>
    <input type="text" placeholder="コギーに呼ばれたい名前を入れてね" id="uname" name="uname" required>
    <label for="psw">コンピュータの習熟度を知るため、タイピングしてみてね (Please type in) </label>
    <div><code id="code">print("A", "B", "C")</code><div>
    <input type="text" placeholder="上のコードを入力してください。" id="ucode" name="ucode" required>
    </div>
    <div><code id="code">クラスコード (Classroom code)</code><div>
    <input type="text" placeholder="先生に教えてもらったクラスコード" id="class_code" name="class_code" required>
    </div>
  <div class="container" style="background-color:#f1f1f1">
    <button type="button" id="ulogin" class="login">利用規約に同意する</button>
    <span class="psw"> <a href="https://kuramitsulab.github.io/kogi_tos.html" target="_blank">利用規約とは</a></span>
  </div>
</form>
"""

_JS="""
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
        const class_code = document.getElementById('class_code').value;
        const keys = buffers.join(' ');
        //document.getElementById('code').innerText=keys;
        //google.colab.kernel.invokeFunction('notebook.login', [uname, samples[index], ucode, keys], {});
        (async function() {
            const result = await google.colab.kernel.invokeFunction('notebook.login', [uname, samples[index], ucode, keys, class_code], {});
            const data = result.data['application/json'];
            if(data.text==='') {
              document.getElementById('class_code').value='';
              document.getElementById('class_code').placeholder = "クラスルームコードが違います/Wrong classroom code";
            }
            else {
              document.getElementById('base').innerText=data.text;
            }
        })();
        //document.getElementById('base').innerText='';
    };
</script>
"""

def _maybe_japanese(uname):
    for c in uname:
        if ord(c) > 256:
            return True
    return False

def _check_level(ukeys):
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
    return 60000 / average_time, 1

def get_greeding_message(ulevel, kpm):
  return EJ(
      f"You've got {kpm:.2f} Keystroke Per Minite. ",
      f'タイピングは、1分あたり{kpm:.2f}打数。') + '\n'+ ([
      EJ("Let's work together today!", 
        "今日も一緒にがんばりましょう！"),
      EJ("Today is a perfect day for programming, isn't it?",
        '今日はとってもプログラミング日和よね！'),
      EJ("You seem to be improving rapidly lately!",
        '最近、どんどん上達している感じだね！'),
      EJ('You seem quite skilled at programming!',
        'なんだか、プログラミングはとっても得意そうね！'),   
      EJ('You can make it without KOGI.', '上級者キター！！って、負けないわよ'),
  ][ulevel-1])

STUDENT_CODE = 'iwLErbx4G8pRHT3BlbkFJqjxnJEkXjdce3jDpBTtF'

def ulogin(uname, code, ucode, ukeys, class_code):
    try:
      acode = class_code[-3:]
      apikey = f's{K}-6NFG{acode}{STUDENT_CODE}'
      if not llm_login(apikey):
        return JSON({'text': ''})
      if kogi_get('lang', None) is None and _maybe_japanese(uname):
          kogi_set(lang='ja')
      class_code = class_code[:-3]
      kpm, ulevel = _check_level(ukeys)
      kogi_set(uname=uname, ulevel=ulevel, approved=True)
      kogi_context = kogi_get('kogi')
      kogi_context['nickname'] = uname
      kogi_context['icons']['@user'] = (uname, kogi_context['icons']['@user'][1])
      kogi_context['token_limit']=1024
      kogi_context['ulevel']=ulevel
      kogi_context['kpm']=kpm
      kogi_context['classroom']=class_code
      record_log(log='keytype', uname=uname, code=code,
                  ucode=ucode, ulevel=ulevel, ukeys=ukeys)
      msg = get_greeding_message(ulevel, kpm)
    except:
        traceback.print_exc()
    return JSON({'text': msg})


def classroom_login():
    if not google_output:
        kogi_print(EJ(
            'classroom_login() is available only on Google Colab',
            'classroom_login()は、Google Colab上のみ利用できます。'))
        return
    doc = {
        'whoami': '@ta',
        'content': _HTML,
        'script': _JS,
    }
    kogi_print(doc)
    google_output.register_callback('notebook.login', ulogin)
