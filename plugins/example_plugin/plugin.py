"""
Example JARVIS Plugin/Skill.
Implements a hello world tool and demonstrates the plugin interface.
"""

import sys
import json


class JarvisPlugin:
    def __init__(self):
        self.name = "example_skill"
        self.version = "1.0.0"

    def hello_world(self, params: dict) -> dict:
        name = params.get("name", "World")
        return {
            "success": True,
            "result": f"Hello, {name}! This is JARVIS plugin speaking."
        }

    def get_current_time(self, params: dict) -> dict:
        from datetime import datetime
        return {
            "success": True,
            "result": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def execute(self, tool: str, params: dict) -> str:
        tools = {
            "hello_world": self.hello_world,
            "get_current_time": self.get_current_time,
        }

        func = tools.get(tool)
        if not func:
            return json.dumps({"error": f"Unknown tool: {tool}"})

        try:
            result = func(params)
            return json.dumps(result)
        except Exception as e:
            return json.dumps({"error": str(e)})


if __name__ == "__main__":
    plugin = JarvisPlugin()

    if len(sys.argv) > 1:
        tool = sys.argv[1]
        params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
        print(plugin.execute(tool, params), flush=True)
    else:
        print(json.dumps({
            "name": plugin.name,
            "version": plugin.version,
            "tools": ["hello_world", "get_current_time"]
        }), flush=True)
