#!/usr/bin/env python3
"""
Focused test for language switching functionality
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from playwright.sync_api import sync_playwright
from src.utils.config import load_config
from src.utils.text_utils import extract_visible_texts, clean_text, should_ignore_text, is_japanese
from src.runner.actions import login_if_needed, navigate_to_settings_after_login, switch_language

def read_ignored_words(path: str) -> list:
    """Read ignored words from file"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Warning: Ignored words file not found: {path}")
        return []

def test_language_switching():
    """Test the language switching functionality specifically"""
    
    print("🎯 Language Switching Test")
    print("=" * 50)
    
    # Load configuration
    cfg = load_config()
    ignored_words = read_ignored_words(cfg.get("ignoredWordsFile", ""))
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        page = browser.new_page()
        
        try:
            # 1. Login
            print("\n🔐 Step 1: Login")
            login_if_needed(page, cfg)
            
            # 2. Navigate to settings
            settings_url = "https://app.vwo.com/#/settings/profile-details?accountId=955080"
            print(f"\n📍 Step 2: Navigate to settings")
            navigate_to_settings_after_login(page, settings_url)
            page.wait_for_timeout(3000)
            
            # 3. Check initial language state
            print("\n📝 Step 3: Check initial language state")
            initial_texts = extract_visible_texts(page, cfg.get("ignoreSelectors", []))
            initial_texts = [clean_text(text) for text in initial_texts if not should_ignore_text(text, ignored_words)]
            
            initial_japanese = [text for text in initial_texts if is_japanese(text)]
            initial_english = [text for text in initial_texts if text.isascii() and len(text) > 3]
            
            print(f"   Initial Japanese texts: {len(initial_japanese)}")
            print(f"   Initial English texts: {len(initial_english)}")
            
            # 4. Look for language selector
            print(f"\n🔍 Step 4: Look for language selector")
            selectors_to_try = [
                "xpath=//*[@id='main-page']/main/div[5]/footer/div/div[3]/div/ul/li/div/button[2]",
                "[data-qa='ja-selector']",
                "button[data-qa='ja-selector']",
                "button:has-text('日本語')",
                "text=日本語"
            ]
            
            found_selector = None
            for selector in selectors_to_try:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        print(f"   Found {len(elements)} elements with selector: {selector}")
                        for i, elem in enumerate(elements):
                            try:
                                text = elem.inner_text()
                                is_visible = elem.is_visible()
                                print(f"     Element {i+1}: '{text}' (visible: {is_visible})")
                                if is_visible and ('日本語' in text or 'ja' in text.lower()):
                                    found_selector = selector
                                    print(f"     ✅ Potential language selector found!")
                            except Exception as e:
                                print(f"     Error checking element: {e}")
                except Exception as e:
                    continue
            
            if not found_selector:
                print("   ❌ No suitable language selector found")
                page.screenshot(path="reports/no_language_selector_found.png")
                return
            
            # 5. Try to switch to Japanese
            print(f"\n🔄 Step 5: Try to switch to Japanese")
            try:
                # Use the specific XPath selector that works
                xpath = "//*[@id='main-page']/main/div[5]/footer/div/div[3]/div/ul/li/div/button[2]"
                element = page.locator(f"xpath={xpath}")
                print(f"   Using XPath selector: {xpath}")
                
                # Scroll to element and click
                element.scroll_into_view_if_needed()
                page.wait_for_timeout(1000)
                
                if element.is_visible():
                    print(f"   Clicking selector: {found_selector}")
                    element.click()
                    page.wait_for_timeout(2000)
                    page.wait_for_load_state("networkidle")
                    print("   ✅ Language switch attempted")
                else:
                    print("   ⚠️  Element not visible after scroll")
                    
            except Exception as e:
                print(f"   ❌ Error switching language: {e}")
                return
            
            # 6. Check language state after switch
            print(f"\n📝 Step 6: Check language state after switch")
            page.wait_for_timeout(3000)  # Wait for any dynamic changes
            
            after_texts = extract_visible_texts(page, cfg.get("ignoreSelectors", []))
            after_texts = [clean_text(text) for text in after_texts if not should_ignore_text(text, ignored_words)]
            
            after_japanese = [text for text in after_texts if is_japanese(text)]
            after_english = [text for text in after_texts if text.isascii() and len(text) > 3]
            
            print(f"   After Japanese texts: {len(after_japanese)}")
            print(f"   After English texts: {len(after_english)}")
            
            # 7. Compare before and after
            print(f"\n📊 Step 7: Compare before and after")
            japanese_increase = len(after_japanese) - len(initial_japanese)
            english_decrease = len(initial_english) - len(after_english)
            
            print(f"   Japanese texts change: {japanese_increase:+d}")
            print(f"   English texts change: {english_decrease:+d}")
            
            if japanese_increase > 0:
                print("   ✅ Japanese text increased - language switch successful!")
            elif len(after_japanese) > 0:
                print("   ⚠️  Japanese text present but no increase - may already be in Japanese")
            else:
                print("   ❌ No Japanese text found - language switch may have failed")
            
            # 8. Show sample texts
            if after_japanese:
                print(f"\n✅ Sample Japanese texts after switch:")
                for i, text in enumerate(after_japanese[:5]):
                    print(f"   {i+1}. {text}")
            
            # 9. Take screenshots
            page.screenshot(path="reports/after_language_switch.png")
            print("   📸 Screenshot saved: reports/after_language_switch.png")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            page.screenshot(path="reports/error_screenshot.png")
        finally:
            browser.close()

if __name__ == "__main__":
    test_language_switching()
