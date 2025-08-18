#!/usr/bin/env python3
"""
Demo script for complete translation validation workflow
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from playwright.sync_api import sync_playwright
from src.utils.config import load_config
from src.utils.text_utils import extract_visible_texts, clean_text, should_ignore_text, is_japanese
from src.utils.report import generate_comprehensive_report
from src.runner.actions import login_if_needed, navigate_to_settings_after_login

def read_ignored_words(path: str) -> list:
    """Read ignored words from file"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Warning: Ignored words file not found: {path}")
        return []

def demo_translation_validation():
    """Demo the complete translation validation workflow"""
    
    print("🎯 Translation Validation Demo")
    print("=" * 50)
    
    # Load configuration
    cfg = load_config()
    ignored_words = read_ignored_words(cfg.get("ignoredWordsFile", ""))
    
    print(f"📋 Configuration loaded:")
    print(f"   - Ignored words: {len(ignored_words)}")
    print(f"   - Auth enabled: {cfg['auth']['enabled']}")
    print(f"   - Min coverage: {cfg.get('minJapaneseCoveragePercent', 70)}%")
    
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
            page.wait_for_timeout(2000)
            
            # 3. Extract current texts
            print("\n📝 Step 3: Extract current page texts")
            current_texts = extract_visible_texts(page, cfg.get("ignoreSelectors", []))
            current_texts = [clean_text(text) for text in current_texts if not should_ignore_text(text, ignored_words)]
            
            print(f"   Found {len(current_texts)} text elements")
            
            # 4. Analyze language distribution
            print("\n🔍 Step 4: Analyze language distribution")
            japanese_texts = []
            english_texts = []
            other_texts = []
            
            for text in current_texts:
                if is_japanese(text):
                    japanese_texts.append(text)
                elif text.isascii():
                    english_texts.append(text)
                else:
                    other_texts.append(text)
            
            print(f"   Japanese texts: {len(japanese_texts)}")
            print(f"   English texts: {len(english_texts)}")
            print(f"   Other texts: {len(other_texts)}")
            
            # 5. Show sample texts
            if japanese_texts:
                print(f"\n✅ Sample Japanese texts:")
                for i, text in enumerate(japanese_texts[:5]):
                    print(f"   {i+1}. {text}")
            
            if english_texts:
                print(f"\n🇺🇸 Sample English texts:")
                for i, text in enumerate(english_texts[:5]):
                    print(f"   {i+1}. {text}")
            
            # 6. Calculate coverage
            total_analyzed = len(japanese_texts) + len(english_texts)
            coverage = (len(japanese_texts) / max(total_analyzed, 1)) * 100
            
            print(f"\n📊 Coverage Analysis:")
            print(f"   Total analyzed: {total_analyzed}")
            print(f"   Japanese coverage: {coverage:.1f}%")
            print(f"   Required coverage: {cfg.get('minJapaneseCoveragePercent', 70)}%")
            
            # 7. Try to find language selector
            print(f"\n🔍 Step 5: Look for language selector")
            selectors_to_try = [
                "text=日本語",
                "[data-lang='ja']",
                "button:has-text('日本語')",
                ".language-selector",
                "[class*='language']",
                "[class*='locale']"
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
                print("   📸 Taking screenshot for analysis...")
                page.screenshot(path="reports/page_analysis.png")
                print("   📸 Screenshot saved: reports/page_analysis.png")
            
            # 8. Generate report
            print(f"\n📊 Step 6: Generate comprehensive report")
            
            # Create mock data for demonstration
            english_sample = english_texts[:10] if english_texts else ["Sample English Text"]
            japanese_sample = japanese_texts[:10] if japanese_texts else ["サンプル日本語テキスト"]
            
            report = generate_comprehensive_report(
                english_sample,
                japanese_sample,
                ignored_words,
                settings_url
            )
            
            print(f"   ✅ Report generated successfully!")
            print(f"   📄 JSON: reports/translation_report.json")
            print(f"   📊 Excel: reports/translation_report.xlsx")
            print(f"   📋 CSV: reports/translation_report.csv")
            
            # 9. Summary
            print(f"\n🎯 Summary:")
            print(f"   ✅ Login: Successful")
            print(f"   ✅ Navigation: Successful")
            print(f"   ✅ Text extraction: {len(current_texts)} elements")
            print(f"   ✅ Language analysis: {coverage:.1f}% Japanese coverage")
            print(f"   ✅ Reports: Generated in multiple formats")
            
            if coverage >= cfg.get('minJapaneseCoveragePercent', 70):
                print(f"   🎉 Coverage requirement met!")
            else:
                print(f"   ⚠️  Coverage below requirement")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            page.screenshot(path="reports/error_screenshot.png")
        finally:
            browser.close()

if __name__ == "__main__":
    demo_translation_validation()
