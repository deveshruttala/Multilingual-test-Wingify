
from typing import Optional, Tuple
from lingua import Language, LanguageDetectorBuilder

# Build a detector focusing on likely languages to improve accuracy & speed
_DETECTOR = LanguageDetectorBuilder.from_languages(
    Language.JAPANESE, Language.ENGLISH, Language.CHINESE, Language.KOREAN
).build()

def detect_lang_code(text: str) -> Optional[str]:
    if not text or not text.strip():
        return None
    lang = _DETECTOR.detect_language_of(text)
    if not lang:
        return None
    # Return ISO 639-1 (e.g., 'ja')
    code = lang.iso_code_639_1.name.lower() if lang.iso_code_639_1 else None
    return code

# Quick unicode heuristic for Japanese presence (Hiragana, Katakana, Kanji)
import re
_JP_PATTERN = re.compile(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]")
def contains_japanese(text: str) -> bool:
    return bool(_JP_PATTERN.search(text or ""))
