_GLOBALS = {
    'height': 360,
    'textra': 'cb25461ac40e7a2dc0b2bc05d381995a',
    'kogi': {
        'icons' : {
            '@system': ('Bot', 'robot-fs8.png'),
            '@user': ('You', 'girl-fs8.png'),
            '@bot': ('KOGI', 'kogi_doya-fs8.png'),
            '@ta': ('TA', 'ta-fs8.png'),
            '@ai': ('KOGI', 'kogi_gpt-fs8.png'),
        },
        'total_tokens': 0,
        'role': 'You are a high school instructor teaching Python.',
        'prompt_suffix': 'To be concise. Please answer in Japanese within 100 characters.',
    }
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
