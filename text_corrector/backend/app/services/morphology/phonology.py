"""
Kazakh phonology helpers.

Kazakh is agglutinative and highly regular: suffix shape is determined by
two phonological processes operating on the stem:

1. Vowel harmony (сингармонизм) — the suffix vowel copies the *frontness*
   of the stem's last vowel:
       back  vowels: а о ұ ы   → suffix takes a back  vowel
       front vowels: ә е ө ү і → suffix takes a front vowel

2. Consonant sandhi (ассимиляция) — the suffix's initial consonant is
   chosen from the stem's final sound class (vowel / sonorant / voiced /
   voiceless).

These helpers expose the small set of classifications that every suffix
table in `suffixes.py` relies on.
"""
from __future__ import annotations

# ── Vowel inventory ───────────────────────────────────────────────────────────
BACK_VOWELS = set("аоұы")
FRONT_VOWELS = set("әеөүі")
# 'и' and 'у' are phonetically complex; for harmony we treat them as front/back
# respectively, which matches their behaviour in the vast majority of stems.
FRONT_VOWELS |= {"и", "э"}
BACK_VOWELS |= {"у"}

VOWELS = BACK_VOWELS | FRONT_VOWELS

# ── Consonant classes (for sandhi) ────────────────────────────────────────────
# Sonorants / "үнді"
SONORANTS = set("руйлмнң")
# Voiced obstruents / "ұяң"
VOICED = set("бвгғджз")
# Voiceless / "қатаң"
VOICELESS = set("кқпстфхцчшщһ")


def last_vowel(word: str) -> str | None:
    """Return the last vowel of *word*, or None if it has none."""
    for ch in reversed(word.lower()):
        if ch in VOWELS:
            return ch
    return None


def harmony(word: str) -> str:
    """
    Return 'front' or 'back' — the harmony class of *word*.

    Defaults to 'back' for words without vowels (rare; mostly abbreviations).
    """
    v = last_vowel(word)
    if v is None:
        return "back"
    return "front" if v in FRONT_VOWELS else "back"


def final_char(word: str) -> str:
    """Last character of the (lower-cased) word."""
    return word.lower()[-1] if word else ""


def ends_in_vowel(word: str) -> bool:
    return final_char(word) in VOWELS


def final_class(word: str) -> str:
    """
    Coarse classification of the stem's final sound:
        'V'   — vowel
        'SON' — sonorant   (р у й л м н ң)
        'VCD' — voiced obstruent (б в г ғ д ж з)
        'VLS' — voiceless  (қатаң)
    Unknown characters fall back to 'V' (treated as neutral).
    """
    c = final_char(word)
    if c in VOWELS:
        return "V"
    if c in SONORANTS:
        return "SON"
    if c in VOICED:
        return "VCD"
    if c in VOICELESS:
        return "VLS"
    return "V"
