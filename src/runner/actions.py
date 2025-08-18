
from typing import List, Set
from pathlib import Path
from playwright.sync_api import Page
from .selectors import first_working_selector
from src.utils.extract import clean_text, should_ignore_text
import re

def login_if_needed(page: Page, cfg: dict):
    auth = cfg.get("auth", {})
    if not auth.get("enabled"):
        return
    page.goto(auth["url"])
    page.fill(auth["usernameSelector"], auth["username"])
    page.fill(auth["passwordSelector"], auth["password"])
    page.click(auth["submitSelector"])
    page.wait_for_load_state("networkidle")

def switch_language(page: Page, cfg: dict, to_japanese=True):
    lang = cfg.get("language", {})
    selector = lang["switchToJapaneseSelector"] if to_japanese else lang["switchToEnglishSelector"]
    sel = first_working_selector(page, selector)
    if sel:
        page.click(sel)
        page.wait_for_timeout(lang.get("postSwitchWaitMs", 500))
        page.wait_for_load_state("networkidle")

def collect_visible_texts(page: Page, cfg: dict, ignored_words: Set[str]) -> List[str]:
    ignoreSelectors = cfg.get("ignoreSelectors", [])
    # JS to collect visible inner texts excluding ignored selectors
    script = f"""
    () => {{
      const ignored = new Set([{",".join([repr(s) for s in ignoreSelectors])}]);
      function isVisible(el) {{
        const style = window.getComputedStyle(el);
        if (style && (style.visibility === 'hidden' || style.display === 'none')) return false;
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
      }}
      const nodes = Array.from(document.body.querySelectorAll('*'));
      const texts = [];
      for (const n of nodes) {{
        let skip = false;
        for (const sel of ignored) {{
          try {{
            if (sel && n.matches && n.matches(sel)) {{ skip = true; break; }}
          }} catch(e){{}}
        }}
        if (skip) continue;
        if (!isVisible(n)) continue;
        if (n.childElementCount === 0) {{
          const t = (n.innerText || n.textContent || '').trim();
          if (t) texts.push(t);
        }}
      }}
      return texts;
    }}
    """
    raw_texts = page.evaluate(script)
    texts = []
    for t in raw_texts:
        t = clean_text(t)
        if t:
            texts.append(t)
    # Filter ignored words and trivial strings here
    final = [t for t in texts if not should_ignore_text(t, ignored_words)]
    return final

def take_screenshot(page: Page, path: str, fullPage: bool = True):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=path, full_page=fullPage)
