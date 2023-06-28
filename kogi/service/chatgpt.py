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

def model_prompt(prompt, context='', **kwargs):
    global model_cache
    key = f'{context}{prompt}'
    if key in model_cache:
        return model_cache[key], 0
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": context},
                {"role": "user", f"content": f"{prompt}"},
            ],
        )
        used_tokens = response["usage"]["total_tokens"]
        res = response.choices[0]["message"]["content"].strip()
        model_cache[key] = res
        return res, used_tokens
    except openai.error.AuthenticationError as e:
        print("""
import kogi
kogi.set(openai_key="") # 自分のOpenAI キーを設定してください。""")
        return '', 0
    except openai.error.ServiceUnavailableError as e:
        print(e)
        return '', 0
    except Exception as e:
        print(e)
        return '', 0