import re
from typing import List, Dict, Any
from lingua import Language, LanguageDetectorBuilder

# Build a detector focusing on likely languages to improve accuracy & speed
_DETECTOR = LanguageDetectorBuilder.from_languages(
    Language.JAPANESE, Language.ENGLISH, Language.CHINESE, Language.KOREAN
).build()

def is_japanese(text: str) -> bool:
    """Check if text contains mostly Japanese characters"""
    if not text or not text.strip():
        return False
    
    # Unicode ranges for Japanese characters
    jp_chars = re.findall(r"[\u3040-\u30FF\u4E00-\u9FFF]", text)
    return len(jp_chars) / max(len(text), 1) > 0.3  # 30% threshold

def detect_language(text: str) -> str:
    """Detect language using lingua detector"""
    if not text or not text.strip():
        return "unknown"
    
    try:
        lang = _DETECTOR.detect_language_of(text)
        if lang:
            return lang.iso_code_639_1.name.lower() if lang.iso_code_639_1 else "unknown"
    except Exception:
        pass
    
    return "unknown"

def extract_visible_texts(page, ignore_selectors=None) -> List[str]:
    """Extracts all visible texts except ignored elements, avoiding login/auth pages"""
    ignore_selectors = ignore_selectors or []
    
    js_script = """
        (ignoreSelectors) => {
            function isVisible(el) {
                if (!el) return false;
                const style = window.getComputedStyle(el);
                if (style && (style.visibility === 'hidden' || style.display === 'none')) return false;
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            }
            
            function shouldIgnore(el) {
                // Skip login/auth related elements
                const authSelectors = [
                    'input[name="username"]', 'input[name="password"]', 
                    'button', '.login-form', '.auth-form', '[data-testid*="login"]',
                    '.signin', '.signup', '.authentication'
                ];
                
                // Check auth selectors first
                for (const authSel of authSelectors) {
                    try {
                        if (el.matches && el.matches(authSel)) return true;
                        if (el.closest && el.closest(authSel)) return true;
                    } catch(e) {}
                }
                
                // Check custom ignore selectors
                return ignoreSelectors.some(sel => {
                    try {
                        return el.matches && el.matches(sel);
                    } catch(e) {
                        return false;
                    }
                });
            }
            
            // Skip if we're on a login page (but be less aggressive)
            const hasLoginForm = document.querySelector('input[name="username"]') && 
                                document.querySelector('input[name="password"]') &&
                                document.querySelector('button');
            
            if (hasLoginForm && window.location.pathname.includes('/login')) {
                return [];
            }
            
            const texts = [];
            
            // Method 1: Get text from specific UI elements first (most reliable)
            const uiElements = document.querySelectorAll('nav, .nav-item, .menu-item, .btn, button, a, label, h1, h2, h3, h4, h5, h6, p, span, div');
            for (const el of uiElements) {
                if (!isVisible(el) || shouldIgnore(el)) continue;
                
                const txt = el.innerText.trim();
                if (txt.length > 2 && txt.length < 100) {
                    // Remove duplicate texts and empty strings
                    if (txt && !texts.includes(txt)) {
                        texts.push(txt);
                    }
                }
            }
            
            // Method 2: Fallback to TreeWalker if not enough texts
            if (texts.length < 10) {
                const walker = document.createTreeWalker(
                    document.body, 
                    NodeFilter.SHOW_TEXT, 
                    null, 
                    false
                );
                
                while (walker.nextNode()) {
                    const node = walker.currentNode;
                    const parent = node.parentElement;
                    
                    if (!parent || !isVisible(parent) || shouldIgnore(parent)) continue;
                    
                    const txt = node.nodeValue.trim();
                    if (txt.length > 2 && txt.length < 100 && !texts.includes(txt)) {
                        texts.push(txt);
                    }
                }
            }
            
            // Remove any remaining duplicates and empty strings
            return texts.filter((txt, index) => txt && texts.indexOf(txt) === index);
        }
    """
    
    try:
        return page.evaluate(js_script, ignore_selectors)
    except Exception as e:
        print(f"Error extracting texts: {e}")
        return []

def clean_text(text: str) -> str:
    """Clean and normalize text with proper UTF-8 handling"""
    if not text:
        return ""
    
    # Ensure proper UTF-8 encoding
    if isinstance(text, bytes):
        try:
            text = text.decode('utf-8')
        except UnicodeDecodeError:
            try:
                text = text.decode('latin-1')
            except UnicodeDecodeError:
                return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove common unwanted characters but preserve Japanese characters
    # Allow: alphanumeric, spaces, Japanese characters, basic punctuation
    text = re.sub(r'[^\w\s\u3040-\u30FF\u4E00-\u9FFF\u3400-\u4DBF.,!?;:()\[\]{}"\'-]', '', text)
    
    # Remove very short or very long texts
    if len(text) < 2 or len(text) > 100:
        return ""
    
    return text

def should_ignore_text(text: str, ignored_words: List[str]) -> bool:
    """Check if text should be ignored based on rules"""
    if not text or len(text) < 2:
        return True
    
    # Check if it's only numbers/symbols
    if re.match(r'^[\d\s\W]+$', text):
        return True
    
    # Check if it's in ignored words list
    text_lower = text.lower()
    for ignored in ignored_words:
        if ignored.lower() in text_lower or text_lower in ignored.lower():
            return True
    
    return False
