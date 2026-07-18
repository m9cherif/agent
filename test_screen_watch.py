import os, time
os.chdir(r'C:\j.a.r.v.i.s')
from jarvis_app.ai import AIEngine

ai = AIEngine()

done = False
def on_complete(success, response):
    global done
    print('COMPLETE:', success)
    print('RESPONSE:', repr(response[:500]))
    done = True

messages = [
    {'role': 'system', 'content': 'You are JARVIS. Output tool calls as JSON: {"tool":"name","params":{...}}'},
    {'role': 'user', 'content': 'use screen_watch tool to start monitoring my screen. Output JSON: {"tool":"screen_watch","params":{"action":"start","interval":2}}'}
]
ai.send_message(messages, None, on_complete)

start = time.time()
while not done and time.time() - start < 30:
    time.sleep(0.1)
if not done:
    print('TIMEOUT')