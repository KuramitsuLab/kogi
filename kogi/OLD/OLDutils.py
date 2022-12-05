def print_nop(*args):
    pass


def listfy(s: str) -> tuple:
    """リストにして返す
    Returns:
        s: タプルにして返す
    """
    if not isinstance(s, (list, tuple)):
        return (s,)
    return s


def remove_suffixes(s, removed_suffixes):
    for suffix in removed_suffixes:
        if s.endswith(suffix):
            return remove_suffixes(s[:-len(suffix)], removed_suffixes)
    return s


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
