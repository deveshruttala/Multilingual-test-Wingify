
# Multilingual Translation Validation Framework

A comprehensive testing framework for validating multilingual pages in SaaS applications using Playwright, Python, and advanced language detection. This framework automates the process of checking translation coverage, visual regressions, and locale-specific formatting.



# Multilingual SaaS Testing (Playwright + Pytest + Lingua)

A ready-to-run project to validate multilingual pages for a large SaaS app using Playwright 
(Python).
It checks:
- Translation coverage/accuracy using offline language detector (lingua-py).
- UI/UX visual regressions by screenshot comparison.
- Language switching keeps page state.
- Locale formatting for dates, times, numbers (basic rules for ja-JP).

## 🚀 Features

- **🔐 Automated Authentication**: Integrated login flow with configurable credentials
- **🌐 Language Switching**: Automated language switching using precise XPath selectors
- **📊 Translation Coverage Analysis**: Offline language detection using lingua-py
- **📸 Visual Regression Testing**: Screenshot comparison with enhanced diff visualization
- **📈 Comprehensive Reporting**: Multi-format reports (JSON, Excel, CSV) with detailed analytics
- **🎯 Smart Screenshot Capture**: Only captures screenshots for pages below translation threshold
- **⚙️ Configurable Testing**: YAML-based configuration for easy customization
- **🔍 Advanced Text Analysis**: Japanese character detection and content filtering

## 📋 Prerequisites

- Python 3.8+
- Windows 10/11 (tested on Windows 10.0.26100)
- PowerShell

## 🛠️ Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd Multilingual-test-Wingify

# 2. Create virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate  # Windows PowerShell

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright browsers
python -m playwright install
```

## ⚙️ Configuration

### 1. Main Configuration (`config/config.yaml`)

```yaml
# Application settings
baseUrl: "https://app.vwo.com"
urlsFile: "data/urls.csv"
ignoredWordsFile: "data/ignored_words_ja.txt"

# Authentication
auth:
  enabled: true
  url: "https://app.vwo.com"
  username: "qa+apiautomation+1725779368742@wingify.com"
  password: "@123"
  usernameSelector: "input[name='username']"
  passwordSelector: "input[name='password']"
  submitSelector: "button:has-text('Sign in')"
  postLoginUrl: "https://app.vwo.com/#/dashboard"
  postLoginTimeout: 15000

# Language switching
language:
  switchToJapaneseSelector: "xpath=//*[@id='main-page']/main/div[5]/footer/div/div[3]/div/ul/li/div/button[2]"
  switchToEnglishSelector: "xpath=//*[@id='main-page']/main/div[5]/footer/div/div[3]/div/ul/li/div/button[1]"
  postSwitchWaitMs: 1500
  expectedCode: "ja"

# Visual testing
visual:
  enabled: true
  fullPage: true
  viewport:
    width: 1440
    height: 900
  diffThreshold: 0.02

# Translation thresholds
minJapaneseCoveragePercent: 70
```

### 2. URL Configuration (`data/urls.csv`)

```csv
url
https://app.vwo.com/#/settings/profile-details?accountId=955080
```

### 3. Ignored Words (`data/ignored_words_ja.txt`)

Add words that should be ignored during translation analysis:

```
VWO
Wingify
API
```

## 🧪 Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest -q

# Run with verbose output
pytest -v -s

# Run specific test file
pytest tests/test_multilingual_pages.py -v
```

### Visual Regression Testing

```bash
# Update baseline screenshots after intentional UI changes
pytest --update-snapshots -q

# Run visual tests only
pytest -k "visual" -v
```

### Language Switching Test

```bash
# Run focused language switching test
python test_language_switching.py
```

## 📊 Generated Reports

### 1. Translation Report (`reports/translation_report.csv`)
- URL analysis
- Total text nodes found
- Japanese text detection count
- Coverage percentage
- Non-Japanese text examples

### 2. Format Report (`reports/format_report.csv`)
- Date formatting validation
- Number grouping checks
- Currency symbol presence

### 3. Visual Reports
- `reports/screenshots/` - Current run screenshots
- `snapshots/` - Approved baseline screenshots
- `reports/visual_diffs/` - Enhanced diff visualizations

### 4. JSON Report (`reports/translation_validation_report.json`)
Comprehensive report with:
- Translation statistics
- Failed translations
- Coverage analysis
- Timestamp and metadata

## 🔧 Key Components

### Core Modules

- **`src/utils/config.py`** - Configuration loading and validation
- **`src/utils/text_utils.py`** - Text extraction and language detection
- **`src/utils/visual.py`** - Visual regression testing with enhanced diffs
- **`src/utils/report.py`** - Multi-format report generation
- **`src/runner/actions.py`** - Playwright automation actions
- **`src/runner/browser.py`** - Browser session management

### Test Files

- **`tests/test_multilingual_pages.py`** - Main comprehensive test suite
- **`test_language_switching.py`** - Focused language switching validation
- **`demo_translation_validation.py`** - Standalone demonstration script

## 🎯 How It Works

1. **Authentication**: Logs into the application using configured credentials
2. **Language Switch**: Uses precise XPath to switch to Japanese language
3. **Page Navigation**: Navigates to each configured URL
4. **Text Extraction**: Extracts all visible text while filtering ignored content
5. **Language Analysis**: Detects Japanese text using offline language detection
6. **Coverage Calculation**: Calculates translation coverage percentage
7. **Visual Testing**: Captures screenshots for pages below threshold
8. **Report Generation**: Creates comprehensive reports in multiple formats

## 🔍 Advanced Features

### Smart Screenshot Capture
- Only captures screenshots for pages with translation coverage below threshold
- Avoids capturing login pages and already-translated content
- Creates enhanced diff visualizations with before/after/diff panels

### Language Detection
- Uses `lingua-language-detector` for offline language detection
- Japanese character detection using Unicode ranges
- Configurable ignored words and selectors

### Visual Regression Testing
- Enhanced diff visualization with side-by-side comparisons
- Configurable diff thresholds
- Automatic baseline management

## 🐛 Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Ensure `__init__.py` files exist in all directories
2. **Playwright Installation**: Run `python -m playwright install` if browsers are missing
3. **Visual Diff Failures**: Use `pytest --update-snapshots` to update baselines
4. **Language Switch Failures**: Verify XPath selectors in config file

### Debug Mode

```bash
# Run with non-headless browser for debugging
pytest --headed -v -s
```

## 📝 Notes

- Uses **lingua-py** for offline language detection (no API costs)
- Supports Japanese (ja-JP) locale with configurable formatting rules
- Extensible for additional languages and locales
- Enhanced visual diff reporting for better debugging
- Comprehensive error handling and logging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
