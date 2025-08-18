
from playwright.sync_api import Page

def first_working_selector(page: Page, selector_or_list: str) -> str:
    # input can be "a, b, c" separated by commas
    items = [s.strip() for s in selector_or_list.split(",") if s.strip()]
    for sel in items:
        try:
            el = page.query_selector(sel)
            if el:
                return sel
        except Exception:
            continue
    return items[0] if items else None
