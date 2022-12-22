import IPython
from IPython.display import HTML, JSON
from google.colab import output

c = 0

def waiting_fn():
  global c
  c+=1
  return c > 5


def wait_for_ready_html(waiting=waiting_fn, wait='コギーを起こしています。まだ、眠っています。', ready='コギーが起きた！おはよ'):

    def waiting_callback():
        if waiting_fn():
            return JSON({'result': False, 'message': ready})
        return JSON({'result': True, 'message': wait})

    output.register_callback('notebook.Waiting', waiting_callback)

    return '''\
<style>
.lds-facebook {
  display: inline-block; position: relative; 
  width: 60px; height: 30px;
}
.lds-facebook div {
  display: inline-block; position: absolute;
  left: 8px; width: 16px; background: #ebb67f;
  animation: lds-facebook 1.2s cubic-bezier(0, 0.5, 0.5, 1) infinite;
}
.lds-facebook div:nth-child(1) {　
    left: 8px; animation-delay: -0.24s;　
}
.lds-facebook div:nth-child(2) {　
    left: 32px; animation-delay: -0.12s;　
}
.lds-facebook div:nth-child(3) {　
    left: 56px; animation-delay: 0; 
}
@keyframes lds-facebook {
  0% { top: 8px; height: 32px; }
  50%, 100% { top: 24px; height: 16px; }
}
</style>
<div id='loading'>
<span id='loading_msg'></span>
<div class="lds-facebook"><div></div><div></div><div></div></div>
</div>
<script>
const check = () => {
    (async function() {
    const result = await google.colab.kernel.invokeFunction('notebook.Waiting', [], {})
    const data = result.data['application/json'];
    if(!data.result) {
        const loading = document.getElementById('loading');
        loading.innerText=data.message;
    }
    else {
        const loading = document.getElementById('loading_msg');
        loading.innerText=data.message;
        setTimeout(check, 1000)
    }
    })();
}
check()
</script>
'''

#HTML(wait_for_ready_html())

