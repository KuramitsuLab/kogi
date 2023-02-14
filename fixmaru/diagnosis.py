
from importlib import import_module
import re

# from .common import debug_print, Doc, status_message
# from .runner import model_parse, task, run_prompt
# from kogi.liberr.rulebase import extract_params, expand_eparams
# from kogi.data.diagnosis_ja import kwconv_diagnosis

_CODE = re.compile(r'(`[^`]+`)')
_SPECIAL = re.compile(r'\<([^\>]+)\>')
_SVAR = re.compile(r'\<[A-Z]\>')
_OPTIONAL = re.compile(r'(\[[^\]]+\])')


def _extract_patterns(text, pat):
    return re.findall(pat, text)


def encode(text):
    codec = {}
    for code in _extract_patterns(text, _CODE):
        if re.search(_SVAR, code):
            continue
        key = f'@{id(code)}@'
        text = text.replace(code, key)
        codec[key] = code
    return text, codec


def decode(text, codec):
    for key, code in codec.items():
        text = text.replace(key, code)
    return text


def conv_nop(s):
    return s


def conv_unquote(s):
    if len(s) > 2 and s[0] in '"`\'' and s[-1] in '"`\'':
        return s[1:-1]
    return s


CONV_FUNC = {
    '': conv_nop,
    'unquote': conv_unquote,
}


def _replace_special_token(text, svar, kwargs):
    conv_fn = conv_unquote
    if '_' in svar:
        svar, _, funcname = svar.partition('_')
        if funcname not in CONV_FUNC:
            debug_print(f'{funcname} not in CONV_FUNC: {svar}_{funcname}')
            CONV_FUNC[funcname] = conv_unquote
        conv_fn = CONV_FUNC[funcname]
    if svar in kwargs:
        if svar < "D":
            replaced_text = conv_fn(str(kwargs[svar]))
        else:
            replaced_text = str(kwargs[svar])
    else:
        replaced_text = f'<{svar}>'  # そのまま
    return text.replace(f'<{svar}>', replaced_text)


def replace_special(text, kwargs):
    svars = _extract_patterns(text, _SPECIAL)
    for svar in svars:
        text = _replace_special_token(text, svar, kwargs)
        if f'<{svar}>' in text:
            return None
    return text


def select_option(option, kwargs):
    if '|' in option:
        for local_option in option.split('|'):
            local_option = replace_special(local_option, kwargs)
            if local_option is not None:
                return local_option
        return ''
    option = replace_special(option, kwargs)
    if option is None:
        return ''
    return option


def format_trago(text, kwargs):
    text, codec = encode(text)
    for option in _extract_patterns(text, _OPTIONAL):
        text = text.replace(option, select_option(option[1:-1], kwargs))
    text = decode(text, codec)
    return text


def expand_keywords(text, d={}, bot=None, kwconv_fn=kwconv_diagnosis, UNDEFINED=None):
    keywords, kwargs = model_parse(text, d)
    if '_eparams' in kwargs:
        for X, val in zip('ABC', kwargs['_eparams']):
            kwargs[X] = val
    doc = Doc()
    for keyword in keywords:
        msg = kwconv_fn(keyword)
        if msg is None or msg == '':
            if UNDEFINED is not None:
                UNDEFINED.update([keyword])
            continue
        prompt_doc = None
        if '@' in msg:
            msg, _, cmd = msg.rpartition('@')
            cmd = f'@{cmd.strip()}'
            msg = msg.strip()
            prompt_doc = run_prompt(bot, cmd, kwargs)
        msg_doc = Doc.md(format_trago(msg, kwargs))
        doc.append(msg_doc)
        if prompt_doc:
            doc.append(prompt_doc)
    return doc


def convert_error_diagnosis(d, bot=None, UNDEFINED=None):
    etype, epat, eparams = extract_params(d['emsg'], maxlen=None)
    d['_etype'] = etype
    d['_epat'] = epat
    d['_eparams'] = eparams
    doc = expand_keywords(d['hint'], d, bot=bot, UNDEFINED=UNDEFINED)
    d2 = dict(
        eline=d['eline'],
        emsg=d['emsg'],
        epat=epat,
        eparams=eparams,
        hint=d['hint'],
        desc=str(doc).replace('\n', '')
    )
    return d2
