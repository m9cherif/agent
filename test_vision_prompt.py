import os, time
os.chdir(r'C:\j.a.r.v.i.s')
from jarvis_app.ai import AIEngine

ai = AIEngine()

done = False
def on_complete(success, response):
    global done
    print('COMPLETE:', success, repr(response[:500]))
    done = True

messages = [
    {'role': 'system', 'content': 'You are JARVIS. Call user boss. Be concise.\n\nTools: vision(action="analyze",prompt,image?). vision auto-captures screen if image omitted.\n\nOutput tool calls as JSON: {"tool":"name","params":{...}}'},
    {'role': 'user', 'content': 'what is on my screen'}
]
ai.send_message(messages, None, on_complete)

start = time.time()
while not done and time.time() - start < 30:
    time.sleep(0.1)
if not done:
    print('TIMEOUT')