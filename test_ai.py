import os, time
os.chdir(r'C:\j.a.r.v.i.s')
from jarvis_app.ai import AIEngine

ai = AIEngine()

done = False
def on_complete(success, response):
    global done
    print('COMPLETE:', success, response[:200] if response else 'None')
    done = True

SYSTEM = """You are JARVIS. Call user "boss". Be concise.

Tools: input_control(action,x,y,duration,button,clicks,keys,text,relative).

Output tool calls as JSON: {"tool":"name","params":{...}}"""

messages = [
    {'role': 'system', 'content': SYSTEM},
    {'role': 'user', 'content': 'click at 500,500'}
]
ai.send_message(messages, None, on_complete)

while not done:
    time.sleep(0.5)
    if time.time() % 2 < 0.5:
        pass
if not done:
    print('TIMEOUT')