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
    """Extracts all visible texts except ignored elements"""
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
                return ignoreSelectors.some(sel => {
                    try {
                        return el.matches && el.matches(sel);
                    } catch(e) {
                        return false;
                    }
                });
            }
            
            const texts = [];
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
                if (txt.length > 2) {
                    texts.push(txt);
                }
            }
            
            return texts;
        }
    """
    
    try:
        return page.evaluate(js_script, ignore_selectors)
    except Exception as e:
        print(f"Error extracting texts: {e}")
        return []

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove common unwanted characters
    text = re.sub(r'[^\w\s\u3040-\u30FF\u4E00-\u9FFF.,!?;:()\[\]{}"\'-]', '', text)
    
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
