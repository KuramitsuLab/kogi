def _ZEN():
    _ZA = ''.join(chr(ord('Ａ')+c) for c in range(26))
    _Za = ''.join(chr(ord('ａ')+c) for c in range(26))
    _Z0 = ''.join(chr(ord('０')+c) for c in range(10))
    _Z = '\u3000「」！＂＃＄％＆＇（）＊＋，－．／：；＜＝＞＠［＼］＾＿｀｛｜｝'
    return _Z + _ZA + _Za + _Z0


def _HAN():
    _HA = ''.join(chr(ord('A')+c) for c in range(26))
    _Ha = ''.join(chr(ord('a')+c) for c in range(26))
    _H0 = ''.join(chr(ord('0')+c) for c in range(10))
    _H = '\u0020\'\'!"#$%&\'()*+, -./:<=>@[\\]^_`{|}'
    return _H + _HA + _Ha + _H0


_ZEN2HAN = str.maketrans(_ZEN(), _HAN())


def zen2han(s: str) -> str:
    return s.translate(_ZEN2HAN)


def remove_suffixes(s, removed_suffixes):
    for suffix in removed_suffixes:
        if s.endswith(suffix):
            return remove_suffixes(s[:-len(suffix)], removed_suffixes)
    return s


REMOVED_SUFFIXES = [
    '.', '。', '?', '？', '！', '!',
    '何', '何ですか', '何でしょうか',
    'です'
]


def normalize(text):
    text = zen2han(text)
    return remove_suffixes(text, REMOVED_SUFFIXES)


def startswith(text, prefixes):
    for prefix in prefixes:
        if text.startswith(prefix):
            return True
    return False


def remove_tai(s):
    if s.endswith('したい'):
        return s[:-3]+'する'
    if s.endswith('きたい'):
        return s[:-3]+'く'
    if s.endswith('ちたい'):
        return s[:-3]+'つ'
    if s.endswith('にたい'):
        return s[:-3]+'ぬ'
    if s.endswith('りたい'):
        return s[:-3]+'る'
    if s.endswith('みたい'):
        return s[:-3]+'む'
    if s.endswith('いたい'):
        return s[:-3]+'う'
    if s.endswith('ぎたい'):
        return s[:-3]+'ぐ'
    if s.endswith('びたい'):
        return s[:-3]+'ぶ'
    return s[:-2]+'る'
