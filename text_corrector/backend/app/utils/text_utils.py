"""
Shared text utility helpers.
"""
from __future__ import annotations

import re
import unicodedata
from typing import List, Tuple


def normalise_whitespace(text: str) -> str:
    """Collapse multiple whitespace characters into a single space."""
    return re.sub(r"\s+", " ", text).strip()


def truncate(text: str, max_length: int, ellipsis: str = "…") -> str:
    """Truncate *text* to *max_length* characters, appending *ellipsis*."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(ellipsis)] + ellipsis


def word_diff(original: str, corrected: str) -> List[Tuple[str, str, bool]]:
    """
    Compute a word-level diff between *original* and *corrected*.

    Returns a list of (original_token, corrected_token, changed) tuples.
    Tokens include spaces / punctuation so that the original text can be
    reconstructed exactly.
    """
    _SPLIT = re.compile(r"(\s+|\S+)")
    orig_tokens = _SPLIT.findall(original)
    corr_tokens = _SPLIT.findall(corrected)

    results: List[Tuple[str, str, bool]] = []
    max_len = max(len(orig_tokens), len(corr_tokens))

    for i in range(max_len):
        orig = orig_tokens[i] if i < len(orig_tokens) else ""
        corr = corr_tokens[i] if i < len(corr_tokens) else ""
        results.append((orig, corr, orig != corr))

    return results


def char_diff(original: str, corrected: str) -> List[Tuple[str, str, bool]]:
    """
    Compute a character-level diff between *original* and *corrected*.

    Returns a list of (orig_char, corr_char, changed) tuples.
    Useful for short single-word corrections.
    """
    max_len = max(len(original), len(corrected))
    result: List[Tuple[str, str, bool]] = []
    for i in range(max_len):
        o = original[i] if i < len(original) else ""
        c = corrected[i] if i < len(corrected) else ""
        result.append((o, c, o != c))
    return result


def is_cyrillic(text: str) -> bool:
    """Return True if the majority of alphabetic chars are Cyrillic."""
    alpha = [c for c in text if c.isalpha()]
    if not alpha:
        return False
    cyrillic = [c for c in alpha if "\u0400" <= c <= "\u04FF"]
    return len(cyrillic) / len(alpha) > 0.5


def sanitise_input(text: str, max_length: int = 5000) -> Tuple[str, List[str]]:
    """
    Sanitise raw user input.

    Returns (sanitised_text, list_of_warnings).
    """
    warnings: List[str] = []

    # Remove null bytes
    text = text.replace("\x00", "")

    # Normalise unicode (NFC form)
    text = unicodedata.normalize("NFC", text)

    # Truncate
    if len(text) > max_length:
        text = text[:max_length]
        warnings.append(f"Text was truncated to {max_length} characters.")

    return text, warnings
