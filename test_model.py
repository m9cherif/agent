import requests, json, os
os.environ['HTTPS_PROXY'] = ''
os.environ['HTTP_PROXY'] = ''
url = 'https://openrouter.ai/api/v1/chat/completions'
headers = {
    'Authorization': 'Bearer sk-or-v1-placeholder',
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0',
}
for model in ['meta-llama/llama-3.3-70b-instruct:free', 'openai/gpt-oss-20b:free', 'nousresearch/hermes-3-llama-3.1-405b:free']:
    print(f'\n=== Testing {model} ===')
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': 'You are JARVIS. Output tool calls as JSON: {"tool":"name","params":{...}}'},
            {'role': 'user', 'content': 'what time is it'}
        ],
        'max_tokens': 100,
        'stream': False,
    }
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    print(r.status_code)
    print(r.text[:500])