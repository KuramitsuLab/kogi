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


def define_task(key, func):
    global _TASK
    for key in key.split():
        if key in _TASK:
            debug_print(f'duplicated task {key}')
        _TASK[key] = func


def run_command(cmd, args, kw):
    global _TASK
    if cmd in _TASK:
        return _TASK[cmd](args, kw)
    else:
        debug_print('undefined task', cmd)
    return None


def run_task(text, kw):
    global _TASK
    cmds = []
    args, kw = model_parse(text, kw, cmds)
    ms = []
    for cmd in cmds:
        if cmd in _TASK:
            ms.append(_TASK[cmd](args, kw))
        else:
            debug_print('undefined task', cmd)
    if len(ms) == 0:
        debug_print('undefined tasks', cmds)
        return 'あわわわ'
    return ms
