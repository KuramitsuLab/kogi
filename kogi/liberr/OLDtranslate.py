import os
from ._extract_emsg import extract_emsg, replace_eparams

EMSG_DIC = {}


def _define_emsg(key, lines):
    if key is None or len(lines) == 0:
        return
    if key in EMSG_DIC:
        d = EMSG_DIC[key]
    else:
        d = {}
        EMSG_DIC[key] = d
    for line in lines:
        key, _, value = line.partition(':')
        if key in d:
            d[key] = d[key] + '\n' + value.strip()
        else:
            d[key] = value.strip()


def _abspath(file):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), file)


def load_emsg_dic(file='emsg2_ja.txt'):
    if not os.path.exists(file):
        file = _abspath(file)

    with open(file) as f:
        ekey = None
        lines = []
        for line in f.readlines():
            line = line.strip()
            if line.startswith('#'):
                continue
            if line == '':
                _define_emsg(ekey, lines)
                ekey = None
                lines = []
                continue
            if ekey is None:
                ekey = line
            else:
                lines.append(line)
        _define_emsg(ekey, lines)


def _find_dic(emsg):
    ekey, params = extract_emsg(emsg)
    if ekey in EMSG_DIC:
        return ekey, params, EMSG_DIC[ekey]
    ekey2, params2 = extract_emsg(emsg, maybe=True)
    if ekey in EMSG_DIC:
        return ekey2, params2, EMSG_DIC[ekey]
    return ekey, params, None


def translate_emsg(emsg, record=None, translate_en=None):
    ekey, eparams, values = _find_dic(emsg)
    if record is None:
        record = {}

    record['ekey'] = ekey
    record['eparams'] = eparams
    # print(record)
    if values is None:
        if not translate_en:
            return None
        translated = translate_en(ekey)
        if not translated:
            return None
        record['translated'] = replace_eparams(translated, eparams)
        record['translated_by'] = 'TexTra'
    else:
        for key, value in values.items():
            record[key] = replace_eparams(value, eparams)
    return record['translated']


load_emsg_dic('emsg2_ja.txt')
