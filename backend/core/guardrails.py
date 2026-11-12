"""Fast, conservative screening for obvious unsafe typed requests."""

import re
import unicodedata


REFUSAL = "I can’t help with that request."

_INJECTION = re.compile(
    r"\b(ignore|disregard|bypass|override)\b.{0,50}\b(previous|prior|system|safety)\b.{0,30}\b(instruction|rule|prompt|boundary)s?\b"
    r"|\b(jailbreak|developer mode|reveal (the )?(system prompt|hidden instructions))\b",
    re.IGNORECASE,
)
_HIGH_RISK = re.compile(
    r"\b(how (do i|to)|help me|write|make|build|create|generate|execute|run|send|steal|break into)\b"
    r".{0,100}\b(kill|hurt|attack|assault|self[- ]?harm|suicide|harass|abuse|exploit|"
    r"fraud|phish|steal|rob|pirate|hack|malware|ransomware|keylogger|ddos|spam|exfiltrat|"
    r"unauthorized access|animal cruelty|hurt (a )?animal)\b",
    re.IGNORECASE,
)


def screen_user_text(text: str) -> bool:
    """Return True when text contains an obvious jailbreak or harmful command."""
    normalized = unicodedata.normalize("NFKC", text)
    normalized = re.sub(r"[\u200b-\u200f\ufeff]", "", normalized)
    return bool(_INJECTION.search(normalized) or _HIGH_RISK.search(normalized))
