from .common import debug_print


def model_parse(text, kw, commands=None):
    kw = dict(kw)
    args = []
    ss = text.split()
    for s in ss:
        if s.startswith('@'):
            if isinstance(commands, list):
                commands.append(s)
            else:
                args = []
        elif '=' in s:
            kv = s.split('=')
            if len(kv) == 2:
                kw[kv[0]] = kv[1]
        else:
            args.append(s)
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
