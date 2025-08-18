
# Multilingual SaaS Testing (Playwright + Pytest + Lingua)

A ready-to-run project to validate multilingual pages for a large SaaS app using Playwright (Python).
It checks:
- Translation coverage/accuracy using offline language detector (lingua-py).
- UI/UX visual regressions by screenshot comparison.
- Language switching keeps page state.
- Locale formatting for dates, times, numbers (basic rules for ja-JP).

## Quick Start

```bash
# 1) Create venv (recommended)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Install Playwright browsers
python -m playwright install

# 4) Configure URLs & credentials
#   - Edit config/config.yaml (baseUrl, login selectors, language switch selectors, etc.)
#   - Add/confirm target URLs in data/urls.csv

# 5) Run tests
pytest -q

# (Optional) Approve/update visual snapshots after intentional UI changes
pytest -q --update-snapshots
```

## What gets reported
- `reports/translation_report.csv` — per page, untranslated or non-Japanese texts and metrics
- `reports/format_report.csv` — locale formatting checks per page
- `reports/screenshots/` — current run screenshots
- `snapshots/` — approved baseline screenshots for visual diffs
- `reports/visual_diffs/` — images highlighting pixel diffs

## Ignoring rules
- Numbers-only strings and input/textarea value texts are ignored.
- Elements marked with `data-i18n-ignore="true"` are ignored.
- "Product words" provided in `data/ignored_words_ja.txt` are ignored (exact match or substring).
- You can add CSS selectors to ignore in `config.yaml` (`ignoreSelectors`).

## Notes
- This project uses **lingua-py** (offline, free) for language detection to keep costs low.
- For RTL coverage, add a locale block in `config.yaml` with `isRTL: true` and extend tests if needed.
