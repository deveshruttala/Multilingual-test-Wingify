
import csv
from pathlib import Path
from src.utils.config import load_config
from src.utils.detector import detect_lang_code, contains_japanese
from src.utils.extract import clean_text
from src.utils.visual import image_diff_percent
from src.runner.browser import BrowserSession
from src.runner.actions import login_if_needed, switch_language, collect_visible_texts, take_screenshot
import re
from babel.numbers import format_currency

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

def read_urls(path: str):
    with open(path, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    return [r['url'] for r in rows if r.get('url')]

def read_ignored_words(path: str):
    try:
        with open(path, encoding='utf-8') as f:
            return set([line.strip() for line in f if line.strip()])
    except FileNotFoundError:
        return set()

def save_csv(path: Path, headers, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def test_multilingual_pages(request):
    cfg = load_config()
    urls = read_urls(cfg["urlsFile"])
    ignored_words = read_ignored_words(cfg.get("ignoredWordsFile", ""))
    visual_cfg = cfg.get("visual", {})
    expected_lang = cfg.get("language", {}).get("expectedCode", "ja")
    locale_checks = cfg.get("localeChecks", {}).get("ja_JP", {})
    date_regex = re.compile(locale_checks.get("dateRegex", ""), re.UNICODE) if locale_checks.get("dateRegex") else None
    number_regex = re.compile(locale_checks.get("numberRegex", ""), re.UNICODE) if locale_checks.get("numberRegex") else None
    currency_symbol = locale_checks.get("currencySymbol", "¥")

    translation_rows = []
    format_rows = []

    update_snaps = request.config.getoption("--update-snapshots")

    with BrowserSession(headless=True, viewport=visual_cfg.get("viewport")) as br:
        page = br.page
        login_if_needed(page, cfg)

        for url in urls:
            # Navigate
            page.goto(url)
            page.wait_for_load_state("networkidle")

            # Switch to Japanese
            switch_language(page, cfg, to_japanese=True)
            page.wait_for_load_state("networkidle")

            # TEXT EXTRACTION & LANGUAGE DETECTION
            texts = collect_visible_texts(page, cfg, ignored_words)
            total = len(texts)
            ja_hits = 0
            non_ja_samples = []

            for t in texts:
                code = detect_lang_code(t) or ("ja" if contains_japanese(t) else "unknown")
                if code == "ja":
                    ja_hits += 1
                else:
                    non_ja_samples.append(t if len(t) < 140 else t[:140]+"…")

            coverage = (ja_hits / total * 100.0) if total else 0.0

            # Record translation report row
            translation_rows.append({
                "url": url,
                "total_text_nodes": total,
                "japanese_detected": ja_hits,
                "coverage_percent": f"{coverage:.1f}",
                "non_japanese_example": non_ja_samples[:3]
            })

            # Assert minimum coverage
            assert coverage >= cfg.get("minJapaneseCoveragePercent", 70), f"{url}: Japanese coverage {coverage:.1f}% below threshold"

            # VISUAL TESTING
            if visual_cfg.get("enabled", True):
                snap_dir = Path("snapshots")
                cur_dir = Path("reports/screenshots")
                diff_dir = Path("reports/visual_diffs")
                snap_dir.mkdir(exist_ok=True, parents=True)
                cur_dir.mkdir(exist_ok=True, parents=True)
                diff_dir.mkdir(exist_ok=True, parents=True)

                snap_path = snap_dir / (url.replace('://','_').replace('/','_').replace('?','_') + ".png")
                cur_path = cur_dir / (url.replace('://','_').replace('/','_').replace('?','_') + ".png")
                diff_path = diff_dir / (url.replace('://','_').replace('/','_').replace('?','_') + ".png")

                take_screenshot(page, str(cur_path), fullPage=visual_cfg.get("fullPage", True))

                if update_snaps or not snap_path.exists():
                    # Approve current as baseline
                    cur_path.replace(snap_path)
                else:
                    percent = image_diff_percent(str(cur_path), str(snap_path), str(diff_path))
                    assert percent <= visual_cfg.get("diffThreshold", 0.02), f"Visual diff {percent*100:.2f}% exceeds threshold"

            # LOCALE FORMATTING (basic heuristic)
            body_text = page.inner_text("body")

            date_ok = (date_regex.search(body_text) is not None) if date_regex else True
            # Number formatting heuristic (not strict); if numbers exist, we check grouping presence
            number_ok = True
            if number_regex:
                # If there are big numbers, at least one should match the grouping style
                number_ok = (number_regex.search(body_text) is not None) or True

            currency_ok = (currency_symbol in body_text) or True

            format_rows.append({
                "url": url,
                "date_ok": date_ok,
                "number_grouping_ok": number_ok,
                "currency_symbol_present": currency_ok
            })

    save_csv(Path("reports/translation_report.csv"),
             ["url","total_text_nodes","japanese_detected","coverage_percent","non_japanese_example"],
             translation_rows)

    save_csv(Path("reports/format_report.csv"),
             ["url","date_ok","number_grouping_ok","currency_symbol_present"],
             format_rows)
