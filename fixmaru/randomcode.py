from typing import List, Dict
import random
import collections
import re
from debug import DEBUG

# snippet

_MASK = re.compile(r'(\$[^\$]+\$)')

_FRAGMENTS = {
    '$num$': '$Cint$ $int$ $Cfloat$ $float$'.split(),
    '$cmp$': '== != < <= >= > =='.split(),
    '$op$': '+ - * ** / // % + -'.split(),
    '$and$': 'and or'.split(),
    '$isupper$': 'isupper islower isdigit isascii'.split(),
    '$sign$': ['-', ''],
}


_COMMON = """\
$var$ = @@
$var$ = [@@]
$var$.append(@@)
print(@@)
print('result:', @@)
print('Value is "{}"'.format(@@))
"""

_NUM = """\
$var$ = @@
$var$ = @@ $op$ $num$
if @@ $cmp$ $num$:
while @@ $cmp$ $num$:
    return @@
    return $num$ $op$ @@
if @@+$num$ $cmp$ $num$:
if @@ $cmp$ $num$ and $bool$:
if $bool$ $and$ @@ $cmp$ $num$:
if @@ $cmp$ $num$ $and$ $bool$:
if $bool$ or @@ $cmp$ $num$:
"""

_BOOL = '''\
assert @@
'''


class RandomCode(object):
    templates: Dict[str, List[str]]
    fragments: Dict[str, List[str]]

    def __init__(self, commons=None):
        self.commons = _COMMON.splitlines() if commons is None else commons
        self.templates = {'NoneType': '@@'}
        self.fragments = _FRAGMENTS.copy()

    def add_template(self, ty: str, template: str) -> None:
        if ty not in self.templates:
            self.templates[ty] = []
            self.templates[ty].extend(self.commons)
        self.templates[ty].append(template)

    def add(self, ty: str, text: str | List[str]) -> None:
        if isinstance(text, str):
            text = [s for s in text.splitlines() if '@@' in s]
        for s in text:
            self.add_template(ty, s)

    def add_fragment(self, ty: str, fragment: str) -> None:
        if ty not in self.fragments:
            self.fragments[ty] = collections.deque(maxlen=10)
        self.fragments[ty].append(fragment)

    def get_fragment(self, ty: str, defaults="ABCDEFGHIJKLMNOPQRSTUVWXYZ") -> str:
        while True:
            if ty in self.fragments:
                result = random.choice(self.fragments[ty])
            else:
                ty = ty[1:-1]  # $int$を外す
                if ty in self.fragments:
                    result = random.choice(self.fragments[ty])
                result = random.choice(defaults)
            if not result.startswith('$'):
                break
            ty = result
        return result

    def apply_template(self, template: str) -> str:
        for mask in re.findall(_MASK, template):
            selected = self.get_fragment(mask)
            template = template.replace(mask, selected, 1)
        return template

    def get_template(self, ty: type) -> str:
        template = '@@'
        if ty in self.templates:
            template = random.choice(self.templates[ty])
        return self.apply_template(template)


def main():
    random_code = RandomCode()
    random_code.add('bool', _BOOL)
    print(random_code.get_template('bool'))


if __name__ == '__main__':
    main()
