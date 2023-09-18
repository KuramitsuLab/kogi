import os
import openai
from .textra import EJ

OPENAI_AUTH_ERROR = EJ("""
Please set your own API_KEY.
                       
```python
import os
os.environ["OPENAI_API_KEY"] = PLEASE SET YOUR OWN API KEY.
```
                       
""", """
ご自分のAPIキーを設定してください。

```
import os
os.environ["OPENAI_API_KEY"] = 自分のAPIキーを設定してください.
````

""")

OPENAI_COMM_ERROR = EJ("""
Communication failed. Perhaps, that server has a problem.

""", """
通信エラーが発生しました。たぶん、あのサーバーに問題があります。

""")


model_cache = {}

def get_messages(prompt, context):
    messages = context.get('messages', [])
    messages.append({
        'role': 'user', 'content': prompt
    })
    context['messages'] = messages
    return messages[:]

def llm_prompt(prompt, context: dict):
    global model_cache
    if openai.api_key is None:
        openai.api_key
    messages = get_messages(prompt, context)
    key = '|'.join(d['content'] for d in messages)
    if key in model_cache:
        return model_cache[key]
    if 'prompt_suffix' in context:
        messages.append({'role': 'user', 'content': context['prompt_suffix']})
    if '_prompt_suffix' in context:
        messages.append({'role': 'user', 'content': context['_prompt_suffix']})
    try:
        openai.api_key = os.environ.get('OPENAI_API_KEY', None)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        openai.api_key = None
        model_name = response["model"]
        used_tokens = response["usage"]["total_tokens"]
        response = response.choices[0]["message"]["content"].strip()
        context['messages'].append({'role': 'assistant', 'content': response})
        context['tokens'] = context.get('tokens', 0) + used_tokens
        model_cache[key] = response
        
        return {
            'content': response,
            'tokens': used_tokens
        }
    except openai.error.AuthenticationError as e:
        return {
            'whoami': '@system',
            'content': OPENAI_AUTH_ERROR,
        }
    except BaseException as e: #openai.error.ServiceUnavailableError as e:
        return {
            'whoami': '@system',
            'content': OPENAI_COMM_ERROR,
        }

def llm_login(apikey):
    try:
        openai.api_key = apikey
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {'role': 'user', 'content': 'Are you ready?'}
            ],
        )
        openai.api_key = None
        used_tokens = response["usage"]["total_tokens"]
        response = response.choices[0]["message"]["content"].strip()
        os.environ['OPENAI_API_KEY']=apikey
        return True
    except openai.error.AuthenticationError as e:
        return False
    except BaseException as e: 
        return False
