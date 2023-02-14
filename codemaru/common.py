DUP = {}


def DEBUG(*msg):
    msg = ' '.join(str(s) for s in msg)
    if msg not in DUP:
        print('\033[31m[DEBUG]\033[0m', msg)
        DUP[msg] = msg


def parse_poly(s, poly_dic):
    if '_;' in s:
        key, *values = s.split(';')
    else:
        key, *values = s.split('/')
    ss = []
    for v in values:
        sp = v.find(' ')
        cp = v.find(',')
        if sp == -1 and cp == -1:
            ss.append((v, v))
        elif sp == -1 or 0 < cp < sp:
            ss.append((v[:cp], v[cp+1:]))
        elif cp == -1 or 0 < sp < cp:
            ss.append((v[:sp], v[sp+1:]))
    poly_dic[key] = tuple(ss)


def da_poly(code, doc, poly_dic):
    keyvars = []
    snippets = set()
    for key, vars in poly_dic.items():
        if key in code and key in doc:
            keyvars.append((key, vars))
            for v in vars:
                snippets.add(v[1])
    if len(snippets) > 0 and len(keyvars) > 0:
        # print('@snipets', len(snippets))
        for _ in range(len(snippets)*2):
            code2 = code
            doc2 = doc
            for key, vars in keyvars:
                index = random.randrange(0, len(vars))
                w, cs = vars[index]
                if w in snippets:
                    snippets.remove(w)
                code2 = code2.replace(key, cs)
                doc2 = doc2.replace(key, w)
            yield code2, doc2
            if len(snippets) == 0:
                break
    else:
        yield code, doc


def random_index(length, first=False):
    if first:
        return 0
    return random.randint(0, length-1)


def findsep(s, sep='|'):
    if sep not in s:
        return -1
    level = 0
    for i, c in enumerate(s):
        if c == sep and level == 0:
            return i
        if c == '[':
            level += 1
        if c == ']':
            level -= 1
        if c == '{':
            level += 10
        if c == '}':
            level -= 10
    return -1


def split_bar(s):
    ss = []
    while True:
        pos = findsep(s, '|')
        if pos == -1:
            break
        ss.append(s[:pos].strip())
        s = s[pos+1:]
    ss.append(s.strip())
    return ss


def da_alt(s, first=False, check_only=False):
    start = findsep(s, '[')
    if start == -1:
        return s
    sub = s[start+1:]
    end = findsep(sub, ']')
    if end == -1:
        if check_only:
            print(f'\033[34m (error) Unclosed: ] {s} \033[0m')
        return s  # .replace('[', '').replace('|', '')
    pre = s[:start]
    ss = [da_alt(x, first, check_only) for x in split_bar(sub[:end])]
    post = da_alt(sub[end+1:], first, check_only)
    if check_only:
        order = '[' + '|'.join(ss) + ']'
        return f'{pre}{order}{post}'
    index = random_index(len(ss), first)
    # print(ss, index, ss[index])
    return pre + ss[index]+post


def da_order(s, first=False, check_only=False):
    start = findsep(s, '{')
    if start == -1:
        return s
    sub = s[start+1:]
    end = findsep(sub, '}')
    if end == -1:
        if check_only:
            print(f'\033[34m (error) Unclosed: }} {s} \033[0m')
        return s  # .replace('{', '')
    pre = s[:start]
    ss = [da_order(x, first, check_only) for x in split_bar(sub[:end])]
    post = da_order(sub[end+1:], first, check_only)
    if check_only:
        order = '{' + '|'.join(ss) + '}'
        return f'{pre}{order}{post}'
    if not first:
        random.shuffle(ss)
    return pre+''.join(ss)+post


def da_check(s):
    return da_alt(da_order(s, True, True), True, True)


def da_all(s, first=False):
    return da_alt(da_order(s, first), first)


STOP_VARS = ['__', '2_', '_整数_', '_列名_']


def da_many(s, ss=None, tries=3, max=30):
    if ss is None:
        ss = []
    s2 = da_alt(da_order(s, True), True)
    s2 = s2.replace('_', '')
    ss.append(s2)
    for i in range(max):
        s2 = da_alt(da_order(s, False), False)
        nlz = True
        for sw in STOP_VARS:
            if sw in s2:
                nlz = False
                break
        s2 = s2.replace('_', '')  # 常に_は取り除く
        # if nlz and random.random() > 0.6:
        #     s2 = s2.replace('_', '')
        if s2 in ss:
            tries -= 1
            if tries == 0:
                break
        else:
            ss.append(s2)
    return ss


def da_test(s):
    print(s, da_alt(da_order(s)))


def quote_alt(s):
    if s.startswith('[') and s.startswith(']'):
        return s
    return f'[{s}]'


def parse_dic(s, alt_dic, poly_dic, lineno):
    if s.startswith('@alt(') and s.endswith(')'):
        s = s[5:-1]
        # print(s)
        if '=' in s:
            key, _, s = s.partition('=')
            alt_dic[key] = da_check(quote_alt(s))
        else:
            key, _, _ = s.partition('|')
            alt_dic[key] = da_check(quote_alt(s))
    if s.startswith('@poly(') and s.endswith(')'):
        parse_poly(s[6:-1], poly_dic)


def expand_alt(doc, altdic):
    doc = da_check(doc)
    for old, new in altdic.items():
        if old in doc:
            # print('=>', old, new)
            doc = doc.replace(old, new)
    return doc


ALTDIC = {
    '\n': '<nl>',
    # 助詞
    'で ': '[で|として|を[用いて|使って]]',
    'が ': '[が|は]',
    '、': '',  # '[、|]',
    'を使って': '[を[用い|使っ]て|によって|で]',
    # 副詞・形容詞
    '新たに': '[新しく|新たに|]',
    'まとめて': '[まとめて|一度に|]',
    '全ての': '[全ての|すべての|全|]',
    '指定した': '[指定した|指定された|ある]',
    'された': '[された|された|した]',
    'の名前': '[名|の名前]',
    'かどうか': '[か判定したい|か知りたい|か調べたい]',
    '先頭': '[最初|[前|先頭]|左[側|端|]]',
    '末尾': '[最後|[後ろ|末尾]|右[側|端|]]',
    '順番に': '[順[番|]に|[一つ|ひとつ]ずつ]',
    # 動詞
    'が欲しい': '[が欲しい|が知りたい|を使いたい]',
    'が知りたい': '[が[知り|しり|み]たい|を知りたい|を求めたい]',
    '知りたい': '[求めたい|知りたい|確認したい|調べたい]',
    '使いたい': '[使いたい|用いたい|使用したい]',
    '求めたい': '[求めたい|計算したい|算出したい|知りたい]',
    'に変換したい': '[に[変換|変換|]したい|化したい]',
    '変換したい': '[変換したい|したい]',
    'を行いたい': '[[を|が|]したい|を行いたい]',
    '繰り返したい': '[繰り返したい|ループしたい]',
    #
    'を与えて': '[を[指定して|与えて|使って|用いて]]',

    # 'の中の': '[[|の][中|内]の|の]', 'の中に': '[[|の][中|内]に|に]', '中で': '[[の|][中|内]で|で]',
    '一つ': '[ひとつ|一つ]', '二つ': '[ふたつ|二つ]',
    '１': '[一|１|1]', '２': '[二|２|2]', '３': '[三|３|3]',
    '求める': '[求める|計算する|算出する]',
    '見る': '[見る|確認する|調べる]',
    '使う': '[使う|用いる|使用する]',
    '得る': '[使う|見る|求める]',
    '作る': '[[作る|作成する]|[|新規]生成する|[用意|準備]する]',
    '作って': '[[作って|作成して]|[|新規]生成して|[用意|準備]して]',
    'プリントしたい': '[表示したい|出力したい|プリントしたい]',
    'コピーしたい': '[コピーしたい|複製したい]',
    '列挙したい': '[列挙したい|リスト[化|に|に変換]したい]',
}

for key, alt in ALTDIC.items():
    da_check(f'{key}: {alt}')


def parse_option(option_dic, code, doc):
    if doc.startswith('<option>'):
        doc = doc[8:].strip()
        key, _, _ = code.partition('=')
        key = f', {key.strip()}=_'
        if key not in option_dic:
            option_dic[key] = []
        option_dic[key].append((code, doc))
        # print(option_dic)


def remove_option(option_dic, code, doc):
    for key in option_dic:
        if key in code:
            code = code.replace(key, '')
    return code, doc


def replace_option(option_dic, code, doc):
    for key, items in option_dic.items():
        if key in code:
            index = random.randrange(0, len(items))
            kcode, kdoc = items[index]
            code = code.replace(key, f', {kcode}')
            doc = doc + '。' + kdoc
    return code, doc


def read_source(filename, corpus={}):
    with open(filename) as f:
        lines = [l.rstrip() for l in f.readlines()]
    altdic = ALTDIC.copy()
    poly_dic = {}
    option_dic = {}
    code = None
    docs = []
    for i, line in enumerate(lines):
        if line == '' or line.startswith('#'):
            if code is None:
                docs = []
        elif line.startswith('@'):
            if code is not None:
                parse_dic(line, altdic, poly_dic, i+1)
            else:
                docs.append(line)
        elif line == "'''":
            if code is None:
                code = '\n'.join(docs)
                docs = []
            else:
                docs = [expand_alt(t, altdic) for t in docs if t != '']
                for doc in docs:
                    for code2, doc2 in da_poly(code, doc, poly_dic):
                        parse_option(option_dic, code2, doc2)
                        code3, doc3 = remove_option(option_dic, code2, doc2)
                        if code3 not in corpus:
                            corpus[code3] = []
                        corpus[code3].append(doc3)
                        code2, doc2 = replace_option(option_dic, code2, doc2)
                        if code2 not in corpus:
                            corpus[code2] = []
                        corpus[code2].append(doc2)
                code = None
                docs = []
        else:
            docs.append(line)
    return corpus


def show(corpus):
    for code, docs in corpus.items():
        print(code)
        ss = []
        for doc in docs:
            da_many(doc, ss, tries=2, max=10)
        for s in set(ss):
            print('\t', s)
            print('\t', keyword(s))


def add_prefix(s):
    print(s)
    if s.startswith('"@'):
        return f'<コマンド>{s[1:-1]}'
    return f'<コード翻訳>{s}'


def show(corpus):
    with open('kogi_extra_train.jsonl', 'w') as w:
        for code, docs in corpus.items():
            print(code)
            ss = []
            for doc in docs:
                da_many(doc, ss, tries=2, max=10)
            for s in set(ss):
                d = {'in': s, 'out': add_prefix(code)}
                print(json.dumps(d, ensure_ascii=False), file=w)
                print('\t', s)
                print('\t', keyword(s))
    print('wrote kogi_extra_train.jsonl')


def main():
    corpus = {}
    for file in sys.argv[1:]:
        show(read_source(file, corpus))


if __name__ == '__main__':
    main()
