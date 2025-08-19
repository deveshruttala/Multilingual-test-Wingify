
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
    
    print("Starting login process...")
    
    # Navigate to login page
    page.goto(auth["url"])
    
    # Wait for login form to be ready
    page.wait_for_selector(auth["usernameSelector"], timeout=10000)
    
    # Fill credentials
    page.fill(auth["usernameSelector"], auth["username"])
    page.fill(auth["passwordSelector"], auth["password"])
    
    # Click Sign in
    page.click(auth["submitSelector"])
    
    # Wait for successful login (dashboard or specified URL pattern)
    post_login_url = auth.get("postLoginUrl", "**/dashboard")
    post_login_timeout = auth.get("postLoginTimeout", 15000)
    
    try:
        page.wait_for_url(post_login_url, timeout=post_login_timeout)
        print("Login successful - dashboard loaded")
    except Exception as e:
        print(f"Warning: Could not detect dashboard load: {e}")
        # Fallback: wait for network idle
        page.wait_for_load_state("networkidle")
        print("Login completed (fallback)")

def switch_language(page: Page, cfg: dict, to_japanese=True):
    lang = cfg.get("language", {})
    selector = lang["switchToJapaneseSelector"] if to_japanese else lang["switchToEnglishSelector"]
    sel = first_working_selector(page, selector)
    if sel:
        try:
            # Use first match to avoid strict mode violations when multiple elements match
            element = page.locator(sel).first

            # Scroll footer into view if needed
            try:
                element.scroll_into_view_if_needed(timeout=2000)
            except Exception:
                # Fallback: scroll to bottom
                try:
                    page.keyboard.press("End")
                    page.wait_for_timeout(300)
                except Exception:
                    pass

            # Wait for element to be visible, then click
            try:
                element.wait_for(state="visible", timeout=4000)
            except Exception:
                print(f"Language selector '{sel}' not visible; attempting click anyway")

            element.click()

            # Post-click waits
            page.wait_for_timeout(lang.get("postSwitchWaitMs", 800))
            page.wait_for_load_state("networkidle")

            # Verify selection state by class on footer buttons if available
            target_button = page.locator("[data-qa='ja-selector']" if to_japanese else "[data-qa='en-selector']").first
            try:
                if target_button.count() > 0:
                    handle = target_button.first.element_handle()
                    if handle:
                        # Wait until selected class appears (best-effort)
                        page.wait_for_function(
                            "btn => btn && btn.classList.contains('btn-footer--selected')",
                            handle,
                            timeout=3000,
                        )
            except Exception:
                # Non-fatal if class check fails; rely on network idle + timeout above
                pass
        except Exception as e:
            print(f"Failed to switch language using selector '{sel}': {e}")
            # Continue without failing the test

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

def navigate_to_settings_after_login(page: Page, settings_url: str):
    """Navigate to settings page after successful login with complete page loading"""
    print(f"Navigating to settings page: {settings_url}")
    
    # Navigate to the page with more lenient timeout
    try:
        page.goto(settings_url, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print(f"Warning: Navigation timeout, trying without wait: {e}")
        page.goto(settings_url, timeout=60000)
    
    # Wait for the page to be fully loaded
    try:
        page.wait_for_load_state("domcontentloaded", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=30000)
    except Exception as e:
        print(f"Warning: Load state timeout: {e}")
    
    # Additional wait for dynamic content
    page.wait_for_timeout(3000)
    
    # Wait for settings page to load (look for common settings page indicators)
    try:
        # Try multiple selectors for settings page content
        selectors_to_try = [
            "text=Profile details",
            "text=Settings",
            "[data-testid*='settings']",
            "[data-testid*='profile']",
            ".settings-content",
            ".profile-content"
        ]
        
        for selector in selectors_to_try:
            try:
                page.wait_for_selector(selector, timeout=5000)
                print(f"Settings page loaded successfully (found: {selector})")
                break
            except Exception:
                continue
        else:
            print("Settings page navigation completed (fallback)")
            
    except Exception as e:
        print(f"Warning: Could not detect settings page load: {e}")
        # Fallback: wait for network idle
        page.wait_for_load_state("networkidle")
        print("Settings page navigation completed (fallback)")
    
    # Ensure we're not on a login page
    try:
        login_elements = page.query_selector_all('input[name="username"], input[name="password"], button:has-text("Sign in")')
        if login_elements:
            print("Warning: Still on login page, waiting for redirect...")
            page.wait_for_timeout(5000)
    except Exception:
        pass
