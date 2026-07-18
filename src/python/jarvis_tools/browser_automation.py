"""
JARVIS Browser Automation via Playwright.
Controls web browsers for navigation, scraping, and form filling.
"""

import sys
import json
import os

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class BrowserAutomation:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None

    def start(self, headless: bool = True):
        if not PLAYWRIGHT_AVAILABLE:
            return {"error": "playwright not installed. pip install playwright && playwright install chromium"}

        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=headless)
            self.context = self.browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) JARVIS/1.0"
            )
            self.page = self.context.new_page()
            return {"success": True, "browser": "chromium"}
        except Exception as e:
            return {"error": str(e)}

    def navigate(self, url: str) -> dict:
        if not self.page:
            return {"error": "Browser not started"}
        try:
            self.page.goto(url, timeout=30000)
            return {
                "success": True,
                "url": self.page.url,
                "title": self.page.title(),
                "status": self.page.evaluate("document.readyState")
            }
        except Exception as e:
            return {"error": str(e)}

    def get_text(self, selector: str = "body") -> dict:
        if not self.page:
            return {"error": "Browser not started"}
        try:
            text = self.page.inner_text(selector) if selector else self.page.inner_text("body")
            return {"success": True, "text": text[:5000]}
        except Exception as e:
            return {"error": str(e)}

    def get_html(self, selector: str = "body") -> dict:
        if not self.page:
            return {"error": "Browser not started"}
        try:
            html = self.page.inner_html(selector)
            return {"success": True, "html": html[:5000]}
        except Exception as e:
            return {"error": str(e)}

    def click(self, selector: str) -> dict:
        if not self.page:
            return {"error": "Browser not started"}
        try:
            self.page.click(selector)
            return {"success": True, "selector": selector}
        except Exception as e:
            return {"error": str(e)}

    def fill(self, selector: str, value: str) -> dict:
        if not self.page:
            return {"error": "Browser not started"}
        try:
            self.page.fill(selector, value)
            return {"success": True, "selector": selector}
        except Exception as e:
            return {"error": str(e)}

    def screenshot(self) -> str:
        if not self.page:
            return json.dumps({"error": "Browser not started"})
        try:
            path = os.path.join(os.environ.get("TEMP", "."), "jarvis_browser.png")
            self.page.screenshot(path=path, full_page=True)
            return json.dumps({"path": path})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def close(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def __del__(self):
        self.close()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    ba = BrowserAutomation()

    if cmd == "navigate":
        result = ba.start()
        if result.get("success"):
            result = ba.navigate(sys.argv[2] if len(sys.argv) > 2 else "https://google.com")
        print(json.dumps(result), flush=True)
    elif cmd == "search":
        ba.start()
        ba.navigate("https://www.google.com")
        ba.fill("textarea[name=q]", sys.argv[2] if len(sys.argv) > 2 else "")
        ba.press("Enter")
        import time
        time.sleep(2)
        result = ba.get_text("body")
        print(json.dumps(result), flush=True)
    elif cmd == "screenshot":
        ba.start()
        ba.navigate(sys.argv[2] if len(sys.argv) > 2 else "https://google.com")
        print(ba.screenshot(), flush=True)
    elif cmd == "close":
        ba.close()
        print(json.dumps({"success": True}), flush=True)
    else:
        print(json.dumps({
            "available_commands": [
                "navigate <url>",
                "search <query>",
                "screenshot <url>",
                "close"
            ]
        }), flush=True)
