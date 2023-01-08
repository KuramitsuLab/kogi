import re
from .common import debug_print

_CODE = re.compile(r'(`[^`]+`)')
# _SVAR = re.compile(r'\<[A-Z]\>')


def _extract_patterns(text, pat):
    return re.findall(pat, text)


def encode(text):
    codec = {}
    for code in _extract_patterns(text, _CODE):
        # if re.search(_SVAR, code):
        #     continue
        key = f'@{id(code)}@'
        text = text.replace(code, key)
        codec[key] = code[1:-1]
    return text, codec


def decode(text, codec):
    for key, code in codec.items():
        text = text.replace(key, code)
    return text


def model_parse(text, kw, commands=None):
    kw = dict(kw)
    args = []
    text, codec = encode(text)
    ss = text.replace('　', ' ').split()
    for s in ss:
        if s.startswith('@'):
            if isinstance(commands, list):
                commands.append(s)
            else:
                args = []
        elif '=' in s:
            k, _, v = s.partition('=')
            kw[k] = decode(v, codec)
        else:
            args.append(decode(s, codec))
    return args, kw


_TASK = {

}


def task(names: str):
    def wrapper(func):
        global _TASK
        for name in names.split():
            if name in _TASK:
                debug_print(f'duplicated task {name}')
            _TASK[name] = func
        return func
    return wrapper


def run_prompt(bot, prompt, kwargs):
    global _TASK
    if prompt in _TASK:
        return _TASK[prompt](bot, kwargs)
    else:
        debug_print('undefined task', prompt)
    return None


# def run_task(bot, text, kw):
#     global _TASK
#     cmds = []
#     args, kw = model_parse(text, kw, cmds)
#     ms = []
#     for cmd in cmds:
#         if cmd in _TASK:
#             ms.append(_TASK[cmd](bot, args, kw))
#         else:
#             debug_print('undefined task', cmd)
#     if len(ms) == 0:
#         debug_print('undefined tasks', cmds)
#         return 'あわわわ'
#     return ms
