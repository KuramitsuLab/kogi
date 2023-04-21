import openai

model_cache = {}


def set_openai(api_key: str):
    openai.api_key = api_key


def model_chat(messages: list):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        used_tokens = response["usage"]["total_tokens"]
        res = response.choices[0]["message"]["content"].strip()
        return res, used_tokens
    except openai.error.AuthenticationError as e:
        return '', 0

def model_prompt(prompt, context='', post_prompt='', **kwargs):
    global model_cache
    input_text = f'{context}{prompt}{post_prompt}'
    if input_text in model_cache:
        return model_cache[input_text], 0

    role = kwargs.get('role', '優秀なPythonの先生')
    if 'disable_example' in kwargs:
        req = '100字以内で簡潔に教えてください。例えや例は不要です。'
    else:
        req = '100字以内で教えてください。'
    premise = f"あなたは{role}です。{req}\n{context}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": premise},
                {"role": "user", f"content": f"{prompt}\n{post_prompt}"},
            ],
        )
        used_tokens = response["usage"]["total_tokens"]
        res = response.choices[0]["message"]["content"].strip()
        model_cache[input_text] = res
        return res, used_tokens
    except openai.error.AuthenticationError as e:
        return '', 0
