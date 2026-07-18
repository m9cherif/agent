import os
import sys
os.chdir(r'C:\j.a.r.v.i.s')
from jarvis_app.tools import create_default_registry
reg = create_default_registry()

def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', 'replace').decode('ascii'))

# Test network tools
print('Testing web_search...')
result = reg.get('web_search').execute({'query': 'python'})
safe_print('OK: ' + str(result['success']) + ' - ' + str(result.get('result', '')[:80]))

print('\nTesting weather...')
result = reg.get('weather').execute({'location': 'London'})
safe_print('OK: ' + str(result['success']) + ' - ' + str(result.get('result', '')[:80]))

print('\nTesting define...')
result = reg.get('define').execute({'word': 'hello'})
safe_print('OK: ' + str(result['success']) + ' - ' + str(result.get('result', '')[:80]))

print('\nTesting joke...')
result = reg.get('joke').execute({})
safe_print('OK: ' + str(result['success']) + ' - ' + str(result.get('result', '')[:80]))

print('\nTesting quote...')
result = reg.get('quote').execute({})
safe_print('OK: ' + str(result['success']) + ' - ' + str(result.get('result', '')[:80]))

print('\nTesting ip_geo...')
result = reg.get('ip_geo').execute({})
safe_print('OK: ' + str(result['success']) + ' - ' + str(result.get('result', '')[:80]))

print('\nTesting news...')
result = reg.get('news').execute({'topic': 'tech'})
safe_print('OK: ' + str(result['success']) + ' - ' + str(result.get('result', '')[:80]))

print('\nTesting translate...')
result = reg.get('translate').execute({'text': 'hello', 'target': 'es'})
safe_print('OK: ' + str(result['success']) + ' - ' + str(result.get('result', '')[:80]))

print('\nTesting shorten...')
result = reg.get('shorten').execute({'url': 'https://example.com'})
safe_print('OK: ' + str(result['success']) + ' - ' + str(result.get('result', '')[:80]))

print('\nTesting file_search...')
result = reg.get('file_search').execute({'pattern': 'test', 'path': r'C:\j.a.r.v.i.s'})
safe_print('OK: ' + str(result['success']) + ' - ' + str(result.get('result', '')[:80]))

print('\nTesting system_info...')
result = reg.get('system_info').execute({})
safe_print('OK: ' + str(result['success']) + ' - ' + str(result.get('result', '')[:80]))

print('\nTesting battery...')
result = reg.get('battery').execute({})
safe_print('OK: ' + str(result['success']) + ' - ' + str(result.get('result', '')[:80]))

print('\nTesting process...')
result = reg.get('process').execute({'action': 'list'})
safe_print('OK: ' + str(result['success']) + ' - ' + str(result.get('result', '')[:80]))

print('\nAll network tests done!')