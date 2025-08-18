
from playwright.sync_api import sync_playwright
from typing import Iterator, Optional, Dict

class BrowserSession:
    def __init__(self, headless: bool = True, viewport=None):
        self._p = None
        self.browser = None
        self.page = None
        self.viewport = viewport or {"width": 1440, "height": 900}
        self._context = None

    def __enter__(self):
        self._p = sync_playwright().start()
        self.browser = self._p.chromium.launch(headless=True)
        self._context = self.browser.new_context(viewport=self.viewport)
        self.page = self._context.new_page()
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if self._context:
                self._context.close()
            if self.browser:
                self.browser.close()
        finally:
            if self._p:
                self._p.stop()
