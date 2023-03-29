_GLOBALS = {
    'height': 360,
    'textra': 'cb25461ac40e7a2dc0b2bc05d381995a',
    # 'model_key': 'rhOcswxkXzMbhlkKQJfytbfxAPVsblhRHX',
}


def kogi_defined(key):
    global _GLOBALS
    return key in _GLOBALS


def kogi_get(key, value=None):
    global _GLOBALS
    return _GLOBALS.get(key, value)


def globals_update(data: dict):
    global _GLOBALS
    _GLOBALS.update(data)


def is_debugging():
    global _GLOBALS
    return _GLOBALS.get('debug', False)
