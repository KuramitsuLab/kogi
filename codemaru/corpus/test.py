import os
import pandas as pd

_str_ = 'A'  # 文字列
_int_ = 0  # 整数
_list_ = [
    1
]  # リスト
_Data_ = _str_ or _int_  # どちらでも

print('Hello World')
'''
ハローワールドと表示する
「こんにちは世界」と出力する
最初のプログラムを書く
'''

print(_str_)  # -> NoneType
'''
_str_を表示する
'''

print(_str_, end='')  # -> NoneType
'''
{_str_を|改行なしに}表示する
_str_を表示する。そのとき改行しない
'''

end = ''
'''
改行なしに
'''

_int_ % 2
'''
_int_が2で割った余り
'''

_int_ % 2 == 0
'''
_int_が2で割り切れるかどうか
_int_が偶数かどうか
'''

if _int_ % 2 == 0:
    ...
'''
_int_が2で割り切れるとき
_int_が偶数の場合
'''
