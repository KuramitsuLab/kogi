from .common import debug_print


def model_parse(text, kw):
    commands = []
    kw = dict(kw)
    args = []
    ss = text.split()
    for s in ss:
        if s.startswith('@'):
            commands.append(s)
        elif '=' in s:
            kv = s.split('=')
            if len(kv) == 2:
                kw[kv[0]] = kv[1]
        elif '_' in s:
            kv = s.split('_')
            if len(kv) == 2:
                kw[kv[0]] = kv[1]
        else:
            args.append(s)
    return args, kw, commands


_TASK = {

}


def define_task(key, func):
    global _TASK
    for key in key.split():
        if key in _TASK:
            debug_print(f'duplicated task {key}')
        _TASK[key] = func


def run_task(text, kw):
    global _TASK
    args, kw, cmds = model_parse(text, kw)
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
