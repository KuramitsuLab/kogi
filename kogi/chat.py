from .webui import start_chat, kogi_print
from .trace_error import kogi_trace_error

from .service import (
    llm_prompt, kogi_get, EJ, record_log, debug_print, simplify
)

def TA(en, ja):
    return {
        'whoami': '@ta', 'content': EJ(en, ja),
    }

def append_code_context(context):
    ss = []
    if 'code' in context:
        code = context['code']
        ss.append("I'm writing the following code:")
        ss.append("")
        for line in code.splitlines():
            line2, _, comment = line.partition('#')
            if '"' in comment or "'" in comment:
                ss.append(line)
            else:
                ss.append(line2)
        ss.append("")
    if 'error' in context:
        ss.append(f"{context['error']['message']}, occured at line {context['error']['lineno']}")
    context['messages'].append(
        {'role': 'user', 'content': '\n'.join(ss)}
    )

def kogi_chat(user_input: str, context: dict):
    if context.get('tokens', 0) > kogi_get('token_limit', 4096):
        return TA(
            'Too many requests! KOGI seems so tired!'
            '質問多すぎね。コギーくんは疲れちゃったみたいよ。',
        )    
    if 'messages' not in context:
        context['messages'] = [
            {'role': 'system', 'content': context['role']}
        ]
        append_code_context(context)
    response = llm_prompt(user_input, context)
    return response

def generate_error_message(context):
    if 'error' not in context:
        return None
    record = context['error']
    doc = []
    doc.append(f"<b>{record['message']}</b><br>")
    simple_msg = simplify(record['message'])
    if simple_msg:
        doc.append(f"{simple_msg}<br>")

    if '_stacks' in record:
        for stack in record['_stacks'][::-1]:  # 逆順に
            if '-packages' in stack['filename']:
                continue
            doc.append(stack['_doc'])
    else:
        doc.append(record['_doc'])

    return {
#        'icon': 'kogi_gaan-fs8.png',
        'content': ''.join(doc),
    }


def start_kogi(context: dict=None, trace_error=False, start_dialog=True):
    if context is None:
        context = {}
    
    for key, value in kogi_get('kogi').items():
        context[key] = value

    if 'prompt' in context:
        dialog = start_chat(context, chat=kogi_chat, placeholder=None)
        prompt = context['prompt']
        if len(prompt) > kogi_get('token_limit', 4096):
            dialog.print(TA('入力が長すぎるよ 💰💰', 'Too long input 💰💰'))
        else:
            response = llm_prompt(prompt, context)
            dialog.print(response)
        return

    if trace_error:
        kogi_trace_error(context)
        context['_start'] = generate_error_message(context)

    dialog = start_chat(context, chat=kogi_chat, placeholder='' if start_dialog else None)
    if '_start' in context:
        dialog.print(context['_start'])
    

