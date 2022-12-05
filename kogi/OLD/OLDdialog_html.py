BOT_ICON = 'https://iconbu.com/wp-content/uploads/2021/02/コーギーのイラスト.jpg'
BOT_ICON2 = "https://iconbu.com/wp-content/uploads/2021/09/驚きチワワちゃん.jpg"
BOT_ICON3 = "https://iconbu.com/wp-content/uploads/2020/06/パソコンをするわんこ.jpg"

#BOT_ICON = 'https://kohacu.com/wp-content/uploads/2021/05/kohacu.com_samune_003370-768x768.png'
YOUR_ICON = 'https://2.bp.blogspot.com/-VVtgu8RyEJo/VZ-QWqgI_wI/AAAAAAAAvKY/N-xnZvqeGYY/s800/girl_question.png'

CHAT_CSS = '''
<style>
.sb-box { position: relative; overflow: hidden; }
/* アイコン画像 */
.icon-img {
    position: absolute; overflow: hidden; top: 0; width: 64px; height: 64px;
}
/* アイコン画像（左） */
.icon-img-left { left: 0; }
/* アイコン画像（右） */
.icon-img-right { right: 0; }
/* アイコン画像 */
.icon-img img { border-radius: 50%; border: 2px solid #eee; }
/* アイコンネーム */
.icon-name {
    position: absolute; width: 64px; text-align: center;
    top: 68px; color: #fff; font-size: 10px;
}
/* アイコンネーム（左） */
.icon-name-left { left: 0; }
/* アイコンネーム（右） */
.icon-name-right { right: 0; }
/* 吹き出し */
.sb-side { position: relative; float: left; margin: 0 85px 20px 85px; }
.sb-side-right { float: right; }
/* 吹き出し内のテキスト */
.sb-txt {
    position: relative; border: 2px solid #eee; border-radius: 6px;
    background: #eee; color: #333;
    font-size: 15px; line-height: 1.7; padding: 18px;
}
.sb-txt>p:last-of-type { padding-bottom: 0; margin-bottom: 0; }
/* 吹き出しの三角 */
.sb-txt:before { content: ""; position: absolute; border-style: solid; top: 16px; z-index: 3; }
.sb-txt:after { content: ""; position: absolute; border-style: solid; top: 15px; z-index: 2; }
/* 吹き出しの三角（左） */
.sb-txt-left:before {
    left: -7px; border-width: 7px 10px 7px 0;
    border-color: transparent #eee transparent transparent;
}
.sb-txt-left:after {
    left: -10px; border-width: 8px 10px 8px 0;
    border-color: transparent #eee transparent transparent;
}
/* 吹き出しの三角（右） */
.sb-txt-right:before {
    right: -7px; border-width: 7px 0 7px 10px;
    border-color: transparent transparent transparent #eee;
}
.sb-txt-right:after {
    right: -10px; border-width: 8px 0 8px 10px;
    border-color: transparent transparent transparent #eee;
}
.box{ background: powderblue; }
.scrolly{ overflow-y: scroll; }
textarea {
  width: 100%; 
  box-sizing: border-box;  /* ※これがないと横にはみ出る */
  height:30px; 
  font-size: large;
  outline: none; /* ※ブラウザが標準で付加する線を消したいとき */
  resize: none;
}
</style>
'''

CHAT_HTML = '''
<div id='main'>
<script>
var timer = null;
var inputPane = document.getElementById('input');
inputPane.addEventListener('keydown', (e) => {
  if(e.keyCode == 13) {
    var text = inputPane.value;
    google.colab.kernel.invokeFunction('notebook.ask', [text], {});
    inputPane.value='';
    if(timer !== null) {
        clearTimeout(timer);
    }
    timer = setTimeout(()=>{
        google.colab.kernel.invokeFunction('notebook.log', [], {});
    }, 1000*60*5);
  }
});
var target = document.getElementById('output');
target.scrollIntoView(false);
</script>
<div id='output' class='box scrolly'>
</div>
<div style='text-align: right'>
<textarea id='input' placeholder='質問はここに'></textarea>
</div>
</div>
'''

BOT_HTML = '''
<div class="sb-box">
    <div class="icon-img icon-img-left">
        <img src="{}" width="60px">
    </div>
    <div class="icon-name icon-name-left">{}</div>
    <div class="sb-side sb-side-left">
        <div class="sb-txt sb-txt-left">
          {}
        </div>
    </div>
</div>
'''

CLEAR_HTML = '''
<script>
setTimeout(()=>{
    const element = document.getElementById('main'); 
    element.remove();
}, 2000);
</script>
'''


USER_HTML = '''
<div class="sb-box">
  <div class="icon-img icon-img-right">
      <img src="{}" width="60px">
  </div>
  <div class="icon-name icon-name-right">{}</div>
  <div class="sb-side sb-side-right">
      <div class="sb-txt sb-txt-right">
        {}
      </div>
  </div>
</div>
'''
