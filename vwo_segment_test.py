import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import json
import re
import os

PROMPTS = [


    "Returning users who clicked #formSubmit with referrer google",
    "Paid traffic users who clicked #ctaButton and referrer facebook",
    "Tablet users whose landing page contains /products and clicked #addToCart",
    "New visitors whose landing page ends with /pricing and bounced",
    "Referral traffic users on Windows desktops",
    "Social traffic users from USA using Chrome",
    "India, USA, and Canada users who are returning",
    "Users on weekends during 14, 15, 16, and 17th hours",
    "sers whose landing page is https://app.vwo.com/  and Referrer contains ccp",
    "Returning users whose referrer does not contain facebook",
    "Users with screen width less than 1024px or screen height not equal to 768px",
    "Tablet users from Canada whose landing page contains /pricing and scrolled beyond 50%",
    "Returning users from UK on Safari who viewed more than 3 pages"
]

OUTPUT_FILE = "segment_query_results.xlsx"
REPEAT_COUNT = 10  # runs per prompt


def extract_combined_query(text: str):
    """Extract all valid JSON objects from the response string and combine them into one query list."""
    matches = re.findall(r"\{.*?\}", text, re.DOTALL)
    query_parts = []

    for m in matches:
        try:
            parsed = json.loads(m)
            if "queryElementType" in parsed or "id" in parsed:
                query_parts.append(parsed)
        except Exception as e:
            print(f"⚠️ Skipped invalid JSON block: {e}")

    return query_parts


def save_to_excel(row_dict):
    """Append a row to the Excel file safely."""
    df_new = pd.DataFrame([row_dict])
    if os.path.exists(OUTPUT_FILE):
        # Append to existing file
        existing = pd.read_excel(OUTPUT_FILE)
        df_all = pd.concat([existing, df_new], ignore_index=True)
        df_all.to_excel(OUTPUT_FILE, index=False)
    else:
        # Create new file
        df_new.to_excel(OUTPUT_FILE, index=False)


async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=200)
        context = await browser.new_context()
        page = await context.new_page()

        # Step 1: Login
        await page.goto("https://app.vwo.com/#/login")
        await page.fill("input[name='username']", "qa+apiautomation+1725779368742@wingify.com")
        await page.fill("input[name='password']", "Wingify@123")
        await page.click("button[type='submit']")
        await page.wait_for_timeout(6000)

        # Step 2: Go to campaign audience page
        await page.goto("https://app.vwo.com/#/test/ab/517/edit/audience-and-traffic/?accountId=955080")
        await page.wait_for_timeout(6000)

        # Step 3: Ensure Copilot tab is clicked
        try:
            await page.click("div[data-qa='calizitetu'] >> text=Copilot")
            await page.wait_for_timeout(2000)
        except Exception:
            print("⚠️ Copilot tab not found or already active")

        for prompt in PROMPTS:
            print(f"\n🔎 Testing prompt: {prompt}")
            prev_query = None

            for i in range(REPEAT_COUNT):
                input_selector = "input[placeholder='Who do you want to target?']"
                await page.wait_for_selector(input_selector, timeout=10000)
                await page.fill(input_selector, prompt)

                generate_button_selector = "button:has-text('Generate')"

                try:
                    async with page.expect_response(
                        lambda res: "/ai/segments/new" in res.url and res.request.method == "POST",
                        timeout=30000,
                    ) as resp_info:
                        await page.click(generate_button_selector)

                        # Handle "Yes, Proceed" modal if it appears
                        try:
                            confirm_button = page.locator("button[data-qa='alert-modal-ok-button']")
                            await confirm_button.wait_for(state="visible", timeout=5000)
                            await confirm_button.click()
                            print("✅ Clicked 'Yes, Proceed'")
                        except Exception:
                            pass  # Modal didn’t appear

                    response = await resp_info.value
                    body = await response.body()
                    text = body.decode("utf-8", errors="ignore")

                    combined_query = extract_combined_query(text)

                    if combined_query:
                        query_part = json.dumps(combined_query, indent=2)
                        print("\n📥 Combined Query Extracted:")
                        print(query_part)
                    else:
                        query_part = "ERROR: No valid JSON found"
                        print("⚠️ No valid JSON extracted from response")

                except Exception as e:
                    print(f"⚠️ No API response captured, marking as ERROR: {e}")
                    query_part = "ERROR: No API response"

                # Compare with previous runs
                status = "Consistent" if prev_query is None or query_part == prev_query else "Not Consistent"
                prev_query = query_part

                row = {
                    "Prompt": prompt,
                    "Query": query_part,
                    "Status": status,
                    "Run": i + 1,
                }

                # Save immediately after every run
                save_to_excel(row)

                print(f"Run {i+1}: {status}")
                await page.wait_for_timeout(2000)

        print(f"\n✅ Results continuously saved to {OUTPUT_FILE}")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(run())
