import re

# Regex for control characters that are not whitespace
NON_PRINTABLE_REGEX = re.compile(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]+")

def strip_nonprintable(text:str)-> str:
    """Removes the invisible control characters"""
    return NON_PRINTABLE_REGEX.sub("",text)

def strip_whitespaces(text:str) -> str:
    """Replace any run of whitespaces by a single space"""
    return re.sub(r"\s+"," ",text).strip()

def clean_text(raw:str, * ,lower:bool=False) -> str:
    """
      Applying the three cleaning steps:
        1. Strip non‑printable characters.
        2. Collapse all whitespace to a single space.
        3. lower‑case the result.
    """
    cleaned=strip_nonprintable(raw)
    cleaned=strip_whitespaces(cleaned)
    if lower:
        cleaned=cleaned.lower()
    return cleaned
