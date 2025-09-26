import re

_DENY = [
    r"(?i)ignore (all|previous) instructions",
    r"(?i)run shell|system\(",
]

_PII = [
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[redacted-email]"),
    (re.compile(r"\b\+?\d[\d -]{7,}\d\b"), "[redacted-phone]")
]

def is_malicious(text: str) -> bool:
    if not text: return False
    for p in _DENY:
        if re.search(p, text):
            return True
    return False

def redact_pii(text: str) -> str:
    if not text: return text
    out = text
    for rgx, repl in _PII:
        out = rgx.sub(repl, out)
    return out
