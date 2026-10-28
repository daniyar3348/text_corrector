"""
Language detection service for Russian and Kazakh text.

Detection strategy (layered):
1. Presence of Kazakh-exclusive Unicode characters → strong Kazakh signal
2. Token overlap with high-frequency word sets → fine-grained scoring
3. Cyrillic coverage → fallback Russian signal
4. Mixed / Unknown when signals conflict or are absent

This module is self-contained; it can be replaced with a trained classifier
by implementing the same `detect_language()` function contract.
"""
import os
import re
from typing import Dict, Set, Union

# ── Kazakh-exclusive characters (absent from standard Russian) ──────────────
# Uppercase + lowercase variants
KAZAKH_EXCLUSIVE: Set[str] = set(
    "ӘәҒғҚқҢңӨөҰұҮүҺһІі"
)

# ── High-frequency Russian vocabulary (function words + common lexemes) ──────
RUSSIAN_SIGNAL_WORDS: Set[str] = {
    # Function words
    "и", "в", "не", "на", "я", "что", "он", "она", "оно", "это",
    "вы", "мы", "они", "то", "как", "за", "из", "по", "от", "же",
    "но", "да", "нет", "или", "если", "так", "уже", "всё", "ещё",
    "при", "для", "до", "про", "под", "над", "без", "через", "после",
    "перед", "между", "против", "вдоль", "около", "среди",
    # Pronouns / determiners
    "этот", "эта", "эти", "тот", "та", "те", "свой", "весь", "каждый",
    "другой", "такой", "какой", "кто", "что", "где", "когда", "почему",
    # Common verbs
    "есть", "был", "была", "было", "были", "будет", "будут",
    "делать", "делает", "сказать", "говорит", "знает", "видит",
    "идёт", "может", "нужно", "надо", "можно",
    # Common nouns / adjectives
    "человек", "люди", "год", "день", "время", "рука", "работа",
    "школа", "книга", "язык", "русский", "новый", "большой",
    "хороший", "первый", "только", "очень", "тоже",
    # Greetings / phrases used in demos
    "привет", "здравствуйте", "пожалуйста", "спасибо", "хорошо",
}

# ── High-frequency Kazakh vocabulary ─────────────────────────────────────────
KAZAKH_SIGNAL_WORDS: Set[str] = {
    # Function words
    "және", "немесе", "бірақ", "егер", "онда", "себебі", "өйткені",
    "да", "де", "та", "те", "ма", "ме", "ба", "бе", "па", "пе",
    # Pronouns
    "мен", "сен", "ол", "біз", "сіз", "олар",
    "маған", "саған", "оған", "бізге", "сізге", "оларға",
    # Common verbs / predicates
    "бар", "жоқ", "болды", "болсын", "болады", "болмайды",
    "айтты", "айтады", "жазды", "жазады", "білді", "біледі",
    "көрді", "көреді", "келді", "келеді", "кетті", "кетеді",
    # Common nouns
    "адам", "жер", "су", "күн", "ай", "жыл", "үй", "қала",
    "ауыл", "мектеп", "кітап", "тіл", "халық", "ел", "бала",
    # Common adjectives
    "жақсы", "жаман", "үлкен", "кіші", "жаңа", "ескі",
    "қызыл", "жасыл", "көк", "қара", "ақ", "сары",
    # Numbers
    "бір", "екі", "үш", "төрт", "бес", "алты", "жеті", "сегіз", "тоғыз", "он",
    # Greetings
    "сәлем", "сәлеметсіз", "рахмет", "кешіріңіз", "өтінемін",
    # Kazakh-specific words commonly used in demos
    "қазақ", "қазақша", "қазақстан",
}

# ── Regex helpers ─────────────────────────────────────────────────────────────
_CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]", re.UNICODE)
_WORD_RE = re.compile(r"[\u0400-\u04FF]+", re.UNICODE)  # any Cyrillic run

# \u2500\u2500 Kazakh lexicon, "russified" (special letters \u2192 Russian look-alikes) \u2500\u2500\u2500\u2500\u2500\u2500\u2500
# A token is a strong Kazakh signal if it matches a real Kazakh word AFTER
# mapping \u04D9\u2192\u0430, \u04E9\u2192\u043E, \u04B1/\u04AF\u2192\u0443, \u049B\u2192\u043A, \u0493\u2192\u0433, \u04A3\u2192\u043D, \u0456\u2192\u0438, \u04BB\u2192\u0445. This recognises Kazakh that
# has NO Kazakh-exclusive letters AND ka2ru-corrupted Kazakh (whose surface
# looks Russian) \u2014 the case that otherwise misroutes to the Russian pipeline.
_KA2RU_MAP = str.maketrans({"\u04D9": "\u0430", "\u04E9": "\u043E", "\u04B1": "\u0443", "\u04AF": "\u0443",
                            "\u049B": "\u043A", "\u0493": "\u0433", "\u04A3": "\u043D", "\u0456": "\u0438", "\u04BB": "\u0445"})
_KAZ_RUSSIFIED: Set[str] = set()
_LEX_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "kk_lexicon.tsv",
)
try:
    with open(_LEX_PATH, encoding="utf-8") as _f:
        for _ln in _f:
            _w, _, _c = _ln.rstrip("\n").partition("\t")
            if _c and len(_w) >= 3 and int(_c) >= 3:
                _KAZ_RUSSIFIED.add(_w.translate(_KA2RU_MAP))
except Exception:  # lexicon is optional \u2014 detection still works without it
    pass


def _tokenize(text: str) -> list[str]:
    """Return lowercase Cyrillic tokens."""
    return [m.lower() for m in _WORD_RE.findall(text)]


def _cyrillic_ratio(text: str) -> float:
    """Fraction of alphabetic characters that are Cyrillic."""
    alpha = [c for c in text if c.isalpha()]
    if not alpha:
        return 0.0
    cyrillic = [c for c in alpha if _CYRILLIC_RE.match(c)]
    return len(cyrillic) / len(alpha)


# ── Public API ────────────────────────────────────────────────────────────────

def detect_language(text: str) -> Dict[str, Union[str, float]]:
    """
    Detect the language of *text*.

    Returns
    -------
    dict with keys:
        language   : "Russian" | "Kazakh" | "Mixed" | "Unknown"
        confidence : float in [0, 1]
    """
    if not text or not text.strip():
        return {"language": "Unknown", "confidence": 0.0}

    tokens = _tokenize(text)
    if not tokens:
        return {"language": "Unknown", "confidence": 0.0}

    total_tokens = len(tokens)

    # ── Signal 1: Kazakh-exclusive character count ───────────────────────────
    kaz_char_count = sum(1 for c in text if c in KAZAKH_EXCLUSIVE)
    alpha_count = sum(1 for c in text if c.isalpha())
    kaz_char_ratio = kaz_char_count / alpha_count if alpha_count else 0.0

    # ── Signal 2: Token-level word matching ──────────────────────────────────
    rus_token_hits = sum(1 for t in tokens if t in RUSSIAN_SIGNAL_WORDS)
    kaz_token_hits = sum(1 for t in tokens if t in KAZAKH_SIGNAL_WORDS)

    rus_token_ratio = rus_token_hits / total_tokens
    kaz_token_ratio = kaz_token_hits / total_tokens

    # ── Signal 2b: Kazakh lexicon coverage (special-letter-insensitive) ──────
    # Fraction of (non-Russian-stopword) tokens matching a real Kazakh word after
    # russify-mapping. Catches Kazakh with no special letters AND ka2ru-corrupted
    # Kazakh. Excluding Russian signal words avoids inflating coverage on Russian.
    kaz_lex_hits = sum(1 for t in tokens
                       if t in _KAZ_RUSSIFIED and t not in RUSSIAN_SIGNAL_WORDS)
    kaz_lex_ratio = kaz_lex_hits / total_tokens
    # Coverage signal scales with length:
    #  - sentences (>=3 tokens): high coverage (Kazakh ~0.8-1.0) vs random Russian
    #    collisions (~0.2-0.3) — nonlinear ramp above 0.5;
    #  - short input (1-2 tokens, e.g. "Салем"->"Сәлем"): accept Kazakh only if
    #    EVERY token is a russified-Kazakh word (kaz_lex_hits already excludes
    #    Russian stopwords), so a lone Kazakh word is caught while "привет мир"
    #    (only 1 of 2 matches) stays Russian.
    if total_tokens >= 3:
        kaz_lex_signal = max(0.0, kaz_lex_ratio - 0.5) / 0.5
    else:
        kaz_lex_signal = 1.0 if (kaz_lex_hits > 0 and kaz_lex_hits == total_tokens) else 0.0

    # ── Signal 3: Cyrillic coverage (Russian fallback) ───────────────────────
    cyrillic_ratio = _cyrillic_ratio(text)

    # ── Aggregate scores ──────────────────────────────────────────────────────
    kaz_score = kaz_char_ratio * 0.6 + kaz_lex_signal * 0.7 + kaz_token_ratio * 0.1
    # Russian fallback unless there's substantial Kazakh-lexicon coverage (else
    # ka2ru-corrupted Kazakh — high coverage, no special chars — leaks to Russian).
    rus_score = rus_token_ratio * 0.60 + (
        cyrillic_ratio * 0.40 if (kaz_char_count == 0 and kaz_lex_signal <= 0.0) else 0.0
    )

    # ── Decision ──────────────────────────────────────────────────────────────
    BOTH_THRESHOLD = 0.15   # both languages have notable presence → Mixed
    KAZ_MIN = 0.10           # minimum Kazakh score to classify as Kazakh
    RUS_MIN = 0.05           # minimum Russian score (Cyrillic-based fallback)

    # Hard rule: ANY Kazakh-exclusive character is a definitive Kazakh signal.
    # Bump kaz_score so it always meets KAZ_MIN when at least one such char exists.
    if kaz_char_count > 0 and kaz_score < KAZ_MIN:
        kaz_score = KAZ_MIN  # floor to ensure classification

    if kaz_score >= BOTH_THRESHOLD and rus_score >= BOTH_THRESHOLD:
        language = "Mixed"
        confidence = round(min(0.95, (kaz_score + rus_score) / 2 + 0.1), 3)
    elif kaz_score >= KAZ_MIN:
        language = "Kazakh"
        confidence = round(min(0.99, 0.45 + kaz_score * 1.2), 3)
    elif rus_score >= RUS_MIN or (cyrillic_ratio > 0.5 and kaz_char_count == 0):
        language = "Russian"
        confidence = round(min(0.99, 0.50 + rus_score * 1.5 + cyrillic_ratio * 0.2), 3)
    else:
        language = "Unknown"
        confidence = 0.0

    return {"language": language, "confidence": confidence}


def is_kazakh(text: str) -> bool:
    """Quick predicate: does the text contain Kazakh-exclusive characters?"""
    return any(c in KAZAKH_EXCLUSIVE for c in text)


def is_russian(text: str) -> bool:
    """Quick predicate: is the text primarily Cyrillic without Kazakh markers?"""
    result = detect_language(text)
    return result["language"] == "Russian"
