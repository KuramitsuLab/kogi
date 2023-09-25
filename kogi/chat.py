from .webui import start_chat, kogi_print
from .trace_error import kogi_trace_error

from .service import (
    llm_prompt, kogi_get, kogi_set, EJ, is_japanese_text, record_log, debug_print, simplify
)

def TA(en, ja):
    return {
        'whoami': '@ta', 'content': EJ(en, ja),
    }

def extract_string_content(message):
    if isinstance(message, str):
        return message
    if isinstance(message, dict) and message.get('whoami', '') != '@system':
        return message.get('content', '') 
    return None

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
    if is_japanese_text(user_input):
        kogi_set(lang='ja')
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
    record_log(log='chat', prompt=user_input, response=extract_string_content(response), messages=context['messages'])
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
    
    # KOGI Prompt の調整
    nickname = f"My name is {context['nickname']}. " if 'nickname' in context else ''
    ulevel = context.get('ulevel', 3)
    if kogi_get('lang', 'en') == 'ja':
        if ulevel < 3:
            context['role'] = f'{nickname}You are an encouraging friend helping Python programming.'
            context['prompt_suffix'] = 'Use a conversational voice and an empathetic tone. Answer it in Japanese within 100 characters. Be concise.'
        else:
            context['role'] = f'You are an experienced professional Python programmer.'
            context['prompt_suffix'] = 'Be concise. Please answer in Japanese.'
    else:
        if ulevel < 3:
            context['role'] = f'{nickname}You are a high school instructor helping computer and Python.'
            context['prompt_suffix'] = 'Use a conversational voice and tone in English. Be very concise and empathetic.'
        else:
            context['role'] = f'You are an experienced professional Python programmer.'
            context['prompt_suffix'] = 'Be concise. Please answer in English.'

    if 'prompt' in context: # プロンプトの直接呼び出し
        dialog = start_chat(context, chat=kogi_chat, placeholder=None)
        prompt = context['prompt']
        if len(prompt) > kogi_get('token_limit', 2048):
            dialog.print(TA('Too long input 💰💰', '入力が長すぎるよ 💰💰'))
        else:
            context['prompt_suffix'] = 'Be simple and concise. Please answer in ' + EJ('English.', 'Japanese.')
            response = llm_prompt(prompt, context)
            output = extract_string_content(response)
            if output:
                context['output'] = output
                record_log(log='prompt', prompt=prompt, response=output) 
            dialog.print(response)
        return

    if trace_error:
        kogi_trace_error(context)
        context['_start'] = generate_error_message(context)

    dialog = start_chat(context, chat=kogi_chat, placeholder='' if start_dialog else None)
    if '_start' in context:
        dialog.print(context['_start'])
    

