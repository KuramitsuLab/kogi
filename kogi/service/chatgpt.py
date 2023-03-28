import openai

model_cache = {}


def set_openai(api_key: str):
    openai.api_key = api_key


def model_prompt(prompt, **kwargs):
    global model_cache
    if prompt in model_cache:
        return model_cache[prompt], 0

    role = kwargs.get('role', 'あなたは優秀な教師です。')
    req = '1文で教えてください。'
    reduce_example = '例えなくて良いです。'
    if kwargs.get('encourage', False) == True:
        req = '1文で励ましてください。'
    if kwargs.get('example', False) == True:
        req = '1文で励ましてください。'
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"あなたは{role}です。"},
            {"role": "user", f"content": f"{prompt} {req}{reduce_example}"},
        ],
    )
    used_tokens = response["usage"]["total_tokens"]
    res = response.choices[0]["message"]["content"].strip()
    model_cache[prompt] = res
    return res, used_tokens
