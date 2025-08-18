
from typing import List, Tuple, Set
import re

def clean_text(s: str) -> str:
    if s is None:
        return ""
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s, flags=re.UNICODE).strip()
    return s

def is_number_like(s: str) -> bool:
    if not s: return False
    s = s.strip()
    # Numbers, phone-like, currency-like -> ignore for translation
    return bool(re.fullmatch(r"[+\-]?([0-9]+([,\.][0-9]+)*)", s))

def should_ignore_text(txt: str, ignored_words: Set[str]) -> bool:
    if not txt: return True
    if len(txt) < 2: return True
    if is_number_like(txt): return True
    low = txt.lower()
    for w in ignored_words:
        w = w.strip()
        if not w: 
            continue
        if w.lower() in low:
            return True
    return False
