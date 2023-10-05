import builtins
import numpy as np
import json
import os
import sys
import shlex
from base64 import b64encode
from binascii import a2b_base64
import traceback
import IPython
from IPython.display import HTML, JSON, display

from .google_check import google_output

INSTALLED = False


def _install():
    global INSTALLED
    if not INSTALLED and google_output:
        os.system('apt-get -y install imagemagick')
        os.system('apt-get -y install pngquant')
        INSTALLED = True


def _convert(file, width=None, height=None):
    if height is None:
        height = width * 10 if width else None
    if width is None:
        width = height * 10 if height else None
    if width and height:
        file2 = file.replace('.', '_.')
        os.system(f'convert -resize {width}x{height} {file} {file2}')
        os.remove(file)
        return file2
    return file


def toDataURL(file, mimetype):
    with open(file, 'rb') as f:
        bin = f.read()
    return f'data:{mimetype};base64,'+b64encode(bin).decode()


IMAGE_CACHE = {}


def wget_dataurl(url, width=None, height=None):
    _install()
    key = f'{url}{width}x{height}'
    if key in IMAGE_CACHE:
        return IMAGE_CACHE[key]
    qurl = shlex.quote(url)
    data_url = None
    if url.endswith('.png') or url.endswith('.PNG'):
        os.system(f'wget {qurl} -O im.png')
        if not os.path.exists('im.png'):
            return False
        file = _convert('im.png', width, height)
        file2 = file.replace('.png', '-fs8.png')
        os.system(f'pngquant {file}')
        os.remove(file)
        data_url = toDataURL(file2, 'image/png')
        os.remove(file2)
    if url.endswith('.jpg') or url.endswith('.jpeg'):
        os.system(f'wget {qurl} -O im.jpg')
        if not os.path.exists('im.jpg'):
            return False
        file = _convert('im.jpg', width, height)
        data_url = toDataURL(file, 'image/jpeg')
        os.remove(file)
    if data_url is None:
        return False
    IMAGE_CACHE[key] = data_url
    return data_url


class MP4(object):
    def __init__(self, filename, width=400):
        self.filename = filename
        self.width = width

    def _repr_html_(self):
        with open(self.filename, 'rb') as fd:
            bin = fd.read()
            data_url = "data:video/mp4;base64," + b64encode(bin).decode()
            return f'''
            <video width="{self.width}" controls>
            <source src="{data_url}" type="video/mp4">
            </video>
            '''


def new_context(contexts=[]):
    class KParam(object):
        def __init__(self, name, value):
            nonlocal contexts
            self.name = name
            self.value = value
            contexts.append(self)

        def to_json(self):
            return (0, self.name, self.value)

    class KMethod(object):
        def __init__(self, name):
            self.name = name
            self.args = ()
            nonlocal contexts
            contexts.append(self)

        def __call__(self, *args):
            self.args = args

        def to_json(self):
            return (1, self.name, self.args)

    class Context(object):
        def __setattr__(self, name, value):
            KParam(name, value)
            return None

        def __getattr__(self, name):
            return KMethod(name)

    return Context()

# HTML


def html_img(key, data_url):
    return f'<img id="{key}" src="{data_url}">'


ANIME = '''
<div style="display:none;">
IMG
</div>
<canvas id="canvas" width="400" height="300" style="background-color:rgb(0,0,0)">
</canvas>
'''

MOVIE = '''
<progress id="prog_bar" value="0" max="100"></progress>
<div style="display:none;">
IMG
<canvas id="canvas" width="400" height="300" style="background-color:rgb(0,0,0)">
</canvas>
</div>
'''


def make_html(canvas, base=ANIME):
    images = ''
    if len(canvas.images) > 0:
        ss = [html_img(key, data_url)
              for key, data_url in canvas.images.items()]
        images = '\n'.join(ss)
    newid = f'"canvas{id(canvas)}"'
    base = base.replace('"canvas"', newid)
    base = base.replace('400', f'{canvas.width}')
    base = base.replace('300', f'{canvas.height}')
    base = base.replace('IMG', images)
    return base


DRAW_JS = '''
const canvas = document.getElementById("canvas");
const dpr = window.devicePixelRatio || 1;
const width = canvas.width;
const height = canvas.height;
canvas.width *= dpr;
canvas.height *= dpr;
canvas.style.width = width + 'px';
canvas.style.height = height + 'px';

// Canvasの描画自体を拡大
const ctx = canvas.getContext('2d');
ctx.scale(dpr, dpr);

const draw = (data) => {
    if(data.length===0) {
        return;
    }
    for(const op of data) {
        if(op[0] === 0) {
            ctx[op[1]] = op[2];
        }
        else{
            if(op[1] === 'drawImage' && typeof op[2][0] === 'string') {
                console.log(op[2][0]);
                op[2][0] = document.getElementById(op[2][0]);
            }
            ctx[op[1]](...op[2]);
        }
    }
};

var frame = [[]];
'''

ANIME_JS = '''
var tm = undefined;
const start_anime = (repeat) => {
    if(tm !== undefined) {
        clearInterval(tm);
    }
    var frame_idx = 0;
    tm = setInterval(() => {
        draw(frame[frame_idx]);
        frame_idx += 1;
        if(frame_idx >= frame.length) {
            if(repeat > 0) {
                frame_idx = 0;
                repeat -= 1;
            }
            else {
                clearInterval(tm);
            }
        }
    }, 100);
};
start_anime(10);
'''

CLICK_JS = '''
var mouse = {x: 0, y: 0};
canvas.addEventListener('mousemove', function(e) {
  mouse.x = e.pageX - this.offsetLeft
  mouse.y = e.pageY - this.offsetTop
});

const redraw = (x, y) => {
    (async function() {
        const result = await google.colab.kernel.invokeFunction(
            'notebook.click',
            [x, y],
            {}); // kwargs
        const updated = result.data['application/json'].result;
        if(updated.length > 0) {
            frame = updated;
            start_anime(0);
        }
    })();
};

canvas.onmousedown = () => {
  redraw(mouse.x, mouse.y);
}
'''

MOVIE_JS = '''
var frame_count=0;
const bar = document.getElementById('prog_bar');
const save = () => {
    draw(frame[0]);
    const idx = frame_count++;
    const dataURL = canvas.toDataURL();
    (async function() {
        const result = await google.colab.kernel.invokeFunction(
            'notebook.save',
            [idx, dataURL],
            {}); // kwargs
        const jsondata = result.data['application/json']
        const updated = jsondata.result;
        bar.value = jsondata.value;
        bar.max = jsondata.max;    
        if(updated.length > 0) {
            frame = updated;
            save();
        }
    })();
};
save()
'''


def make_js(canvas, asm, fps=0, onclick=None):
    js = DRAW_JS.replace('[[]]', json.dumps(asm))
    newid = f'"canvas{id(canvas)}"'
    js = js.replace('"canvas"', newid)
    if fps > 0:
        js += ANIME_JS.replace('100', f'{1000//fps}')
    else:
        js += MOVIE_JS
    if onclick is not None:
        js += CLICK_JS
    return f'<script>\n{js}\n</script>'


def safe(f):
    def safe_fn(*args):
        nonlocal f
        try:
            return f(*args)
        except:
            traceback.print_exc()
            return JSON({
                'result': [[]]
            })
    return safe_fn


class Canvas(object):
    def __init__(self, width=400, height=300, background='white', fps=5, onclick=None):
        self.width = width
        self.height = height
        self.images = {}
        self.buffers = []
        self.background = background
        self.fps = fps
        self.onclick_fn = onclick
        self.filename = 'canvas.mp4'
        self.displayed = False
        if google_output:
            google_output.register_callback(
                'notebook.click', safe(self.click))
            google_output.register_callback(
                'notebook.save', safe(self.save))

    def loadImage(self, image_key, url, width=None, height=None):
        self.images[image_key] = wget_dataurl(url, width=width, height=height)
        return HTML(html_img(image_key, self.images[image_key]))

    def getContext(self, target='2d'):
        if self.displayed:
            self.displayed = False
            self.buffers = []
        cb = []
        self.buffers.append(cb)
        ctx = new_context(cb)
        ctx.clearRect(0, 0, self.width, self.height)
        ctx.fillStyle = self.background
        ctx.fillRect(0, 0, self.width, self.height)
        return ctx

    def asm(self):
        if len(self.buffers) == 0:
            return [[]]
        return [[c.to_json() for c in cb] for cb in self.buffers]

    def _repr_html_(self):
        self.displayed = True
        return make_html(self) + make_js(self, self.asm(), self.fps, self.onclick_fn)

    def click(self, x, y):
        self.buffers = []
        self.onclick_fn(self, x, y)
        return JSON({
            'result': self.asm()
        })

    def save_movie(self, filename=None, fps=None):
        if filename is not None:
            self.filename = filename
        if fps is not None:
            self.fps = int(fps)
        i = 0
        while True:
            fname = f'frame{i:04d}.png'
            if not os.path.exists(fname):
                break
            os.remove(fname)
            i += 1
        first_frame = [[c.to_json() for c in self.buffers[0]]]
        display(HTML(make_html(self, MOVIE) + make_js(self, first_frame)))

    def save(self, idx, dataURI):
        _, _, dataURI = dataURI.partition("base64,")
        binary_data = a2b_base64(dataURI)
        fname = f'frame{idx:04d}.png'
        # print(fname)
        with open(fname, 'wb') as fd:
            fd.write(binary_data)
        update = []
        msg = f'Saved'
        if idx < len(self.buffers):
            cb = self.buffers[idx]
            update = [[c.to_json() for c in cb]]
            value = idx
            msg = f'Saved [{idx}/{len(self.buffers)}] {fname}'
        else:
            self._save_movie()
            value = len(self.buffers)
            msg = f'Saved {self.filename}'
        return JSON({
            'result': update,
            'max': len(self.buffers),
            'value': value,
            'meg': msg,
        })

    def _save_movie(self):
        filename = shlex.quote(self.filename)
        framerate = int(self.fps)
        if os.path.exists(filename):
            os.remove(filename)
        os.system(
            f'ffmpeg -y -framerate {framerate} -i frame%04d.png -vcodec libx264 -pix_fmt yuv420p {filename}')
        if os.path.exists(filename):
            print(f'Saved {filename}')
            display(MP4(filename, self.width))


a = np.array([[2, 1, 3], [3, 2, 1]])


def draw_np1d(ctx, a, x=0, y=0, width=400, height=300, ensure_square=True, margin=1, rgb=(255, 219, 237), min=None, max=None):
    max = max or a.max()
    min = min or a.min()
    w = len(a)
    a = a - min
    dx = width//w
    a = a * height / (max-min)
    ca = np.array(rgb)
    ca = ca / (max-min)
    for i, dy in enumerate(a):
        c = (((ca * dy) % 128) + 128).astype(int)
        ctx.fillStyle = f'rgb({c[0]},{c[1]},{c[2]})'
        ctx.fillRect(x+i*dx, y+height-dy, dx-margin, dy)


def draw_np2d(ctx, a, x=0, y=0, width=400, height=300, ensure_square=True, margin=1, rgb=(0, 128, 0), min=None, max=None):
    h, w = a.shape
    min = min or a.min()
    max = max or a.max()
    a = a - min
    dx = width//w
    dy = height//h
    if ensure_square:
        dx = builtins.min(dx, dy)
        dy = builtins.min(dx, dy)
    ca = np.array(rgb)
    ca = ca / (max-min)
    for wi in range(w):
        for hi in range(h):
            c = (ca*a[hi][wi]).astype(int)
            ctx.fillStyle = f'rgb({c[0]},{c[1]},{c[2]})'
            ctx.fillRect(x+wi*dx, y+hi*dy, dx-margin, dy-margin)


def draw_np(ctx, a, x=0, y=0, width=400, height=300, ensure_square=True, margin=1, rgb=(255, 219, 237), min=None, max=None):
    if not isinstance(a, np.ndarray):
        a = np.array(list(a))
    if len(a.shape) == 2:
        draw_np2d(ctx, a, x, y, width, height,
                  ensure_square, margin, rgb, min, max)
    else:
        draw_np1d(ctx, a, x, y, width, height,
                  ensure_square, margin, rgb, min, max)
