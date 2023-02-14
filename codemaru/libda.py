import sys
import random
import json


def _find_close(s, close=']', verbose=False):
    ss = []
    start = 0
    level = 0
    out_backquote = True
    for i, c in enumerate(s):
        if c == '`':
            out_backquote = not out_backquote
            continue
        if out_backquote:
            if level == 0:
                if c == close:
                    ss.append(s[start:i])
                    return ss, s[i+1:]
                if c == '|' or c == '/':
                    ss.append(s[start:i])
                    start = i+1
                    continue
            if c == '[':
                level += 1
            elif c == ']':
                level -= 1
            elif c == '{':
                level += 10
            elif c == '}':
                level -= 10
    if verbose:
        print(f'\033[34m (error) Unclosed: `{close}` {s} \033[0m')
    ss.append(s[start:])
    return ss, ''


def choice_fn(ss: list):
    return random.choice(ss)


def suffle_fn(ss: list):
    random.shuffle(ss)
    return ss


def da_random(s, choice=choice_fn, shuffle=suffle_fn, verbose=True):
    ss = []
    while len(s) > 0:
        square = s.find('[')
        brace = s.find('{')
        if square == -1 and brace == -1:
            ss.append(s)
            break
        if square != -1 and (brace == -1 or square < brace):
            ss.append(s[:square])
            subs, s = _find_close(s[square+1:], ']')
            ss.append(da_random(choice(subs), choice=choice,
                      shuffle=shuffle, verbose=verbose))
        if brace != -1 and (square == -1 or brace < square):
            ss.append(s[:brace])
            subs, s = _find_close(s[brace+1:], '}')
            for sub in shuffle(subs):
                ss.append(da_random(sub, choice=choice,
                                    shuffle=shuffle, verbose=verbose))
    return ''.join(ss)


def choice_nop(ss: list):
    return ss[0]


def shuffle_nop(ss: list):
    return ss


def da_first(s):
    return da_random(s, choice=choice_nop, shuffle=shuffle_nop)


def test_da(s):
    print(s, da_random(s))


def main():
    test_da('ハロー[ワールド|世界|]と表示する')
    test_da('{文字列[を|から]/数値に}変換する')


if __name__ == '__main__':
    main()
