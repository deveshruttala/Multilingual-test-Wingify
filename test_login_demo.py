#!/usr/bin/env python3
"""
Demo script to show the login functionality working
"""

from playwright.sync_api import sync_playwright
from src.utils.config import load_config
from src.runner.actions import login_if_needed, navigate_to_settings_after_login

def test_login_demo():
    """Demo the login flow"""
    cfg = load_config()
    
    with sync_playwright() as p:
        # Launch browser in non-headless mode to see what's happening
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        page = browser.new_page()
        
        print("=== Login Demo ===")
        print(f"Username: {cfg['auth']['username']}")
        print(f"Login URL: {cfg['auth']['url']}")
        
        # Perform login
        login_if_needed(page, cfg)
        
        # Navigate to settings
        settings_url = "https://app.vwo.com/#/settings/profile-details?accountId=955080"
        navigate_to_settings_after_login(page, settings_url)
        
        # Wait a bit to see the page
        page.wait_for_timeout(3000)
        
        # Get page title
        title = page.title()
        print(f"Page title: {title}")
        
        # Check if we're on the right page
        if "Profile" in title or "Settings" in title:
            print("✅ Successfully logged in and navigated to settings page!")
        else:
            print("❌ Page title doesn't match expected content")
        
        # Take a screenshot
        page.screenshot(path="login_demo_screenshot.png")
        print("📸 Screenshot saved as 'login_demo_screenshot.png'")
        
        browser.close()

if __name__ == "__main__":
    test_login_demo()

