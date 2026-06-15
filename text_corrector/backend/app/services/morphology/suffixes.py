"""
Kazakh noun suffix tables (number, possessive, case).

This module is the single source of truth for both directions:

* GENERATION  — `make_*` functions return the correct surface allomorph for a
  given stem, applying vowel harmony + consonant sandhi.
* ANALYSIS    — `*_INVENTORY` lists enumerate every surface allomorph together
  with its grammatical gloss, so `analyzer.py` can strip suffixes off a word.

Only the nominal paradigm is covered in this first version. The verbal
paradigm (tense / person / voice) is the next layer to add and follows the
same pattern.

School-grammar sandhi rules are used. A handful of possessive-conditioned
case variants (-на/-не, -нда/-нде, -нан/-нен, accusative -н) are included in
the analysis inventory so real word-forms parse, and are marked TODO for the
generator.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from .phonology import harmony, final_class

# Grammeme tag → human label (used in glosses / API output)
TAGS: Dict[str, str] = {
    "PL": "көптік (мн. число)",
    "POSS1SG": "тәуелдік 1-жақ жекеше",
    "POSS2SG": "тәуелдік 2-жақ жекеше",
    "POSS2SGF": "тәуелдік 2-жақ сыпайы",
    "POSS3": "тәуелдік 3-жақ",
    "POSS1PL": "тәуелдік 1-жақ көпше",
    "NOM": "атау септік",
    "GEN": "ілік септік",
    "DAT": "барыс септік",
    "ACC": "табыс септік",
    "LOC": "жатыс септік",
    "ABL": "шығыс септік",
    "INS": "көмектес септік",
}


# ═══════════════════════════════════════════════════════════════════════════════
# GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def _pick(stem: str, back: str, front: str) -> str:
    """Choose between a back- and front-harmony allomorph."""
    return back if harmony(stem) == "back" else front


def make_plural(stem: str) -> str:
    """Көптік жалғау: -лар/-лер · -дар/-дер · -тар/-тер."""
    c = final_class(stem)
    fc = stem.lower()[-1]
    if c == "V" or fc in set("руйл"):
        return _pick(stem, "лар", "лер")
    if fc in set("мнңжз"):
        return _pick(stem, "дар", "дер")
    return _pick(stem, "тар", "тер")          # voiceless + б,в,г,д


def make_genitive(stem: str) -> str:
    """Ілік: -ның/-нің · -дың/-дің · -тың/-тің."""
    c = final_class(stem)
    fc = stem.lower()[-1]
    if c in ("V", "SON"):
        return _pick(stem, "ның", "нің")
    if c == "VCD":
        return _pick(stem, "дың", "дің")
    return _pick(stem, "тың", "тің")


def make_dative(stem: str) -> str:
    """Барыс: -ға/-ге · -қа/-ке (two-way: voiceless vs rest)."""
    if final_class(stem) == "VLS":
        return _pick(stem, "қа", "ке")
    return _pick(stem, "ға", "ге")


def make_accusative(stem: str) -> str:
    """Табыс: -ны/-ні · -ды/-ді · -ты/-ті."""
    c = final_class(stem)
    if c in ("V", "SON"):
        return _pick(stem, "ны", "ні")
    if c == "VCD":
        return _pick(stem, "ды", "ді")
    return _pick(stem, "ты", "ті")


def make_locative(stem: str) -> str:
    """Жатыс: -да/-де · -та/-те."""
    if final_class(stem) == "VLS":
        return _pick(stem, "та", "те")
    return _pick(stem, "да", "де")


def make_ablative(stem: str) -> str:
    """Шығыс: -нан/-нен (after м,н,ң) · -тан/-тен (voiceless) · -дан/-ден."""
    fc = stem.lower()[-1]
    if fc in set("мнң"):
        return _pick(stem, "нан", "нен")
    if final_class(stem) == "VLS":
        return _pick(stem, "тан", "тен")
    return _pick(stem, "дан", "ден")


def make_instrumental(stem: str) -> str:
    """Көмектес: -мен/-бен/-пен (front/back share the same vowel 'е')."""
    c = final_class(stem)
    if c in ("V", "SON"):
        return "мен"
    if c == "VCD":
        return "бен"
    return "пен"


CASE_GENERATORS = {
    "NOM": lambda stem: "",
    "GEN": make_genitive,
    "DAT": make_dative,
    "ACC": make_accusative,
    "LOC": make_locative,
    "ABL": make_ablative,
    "INS": make_instrumental,
}


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS INVENTORIES
# Each entry: (surface_allomorph, grammeme_tag)
# Ordered longest-first within a layer so the analyzer prefers the longest match.
# ═══════════════════════════════════════════════════════════════════════════════

NUMBER_INVENTORY: List[Tuple[str, str]] = [
    ("лар", "PL"), ("лер", "PL"),
    ("дар", "PL"), ("дер", "PL"),
    ("тар", "PL"), ("тер", "PL"),
]

POSSESSIVE_INVENTORY: List[Tuple[str, str]] = [
    ("ыңыз", "POSS2SGF"), ("іңіз", "POSS2SGF"), ("ңыз", "POSS2SGF"), ("ңіз", "POSS2SGF"),
    ("ымыз", "POSS1PL"), ("іміз", "POSS1PL"), ("мыз", "POSS1PL"), ("міз", "POSS1PL"),
    ("ым", "POSS1SG"), ("ім", "POSS1SG"), ("м", "POSS1SG"),
    ("ың", "POSS2SG"), ("ің", "POSS2SG"), ("ң", "POSS2SG"),
    ("сы", "POSS3"), ("сі", "POSS3"), ("ы", "POSS3"), ("і", "POSS3"),
]

CASE_INVENTORY: List[Tuple[str, str]] = [
    # Genitive
    ("ның", "GEN"), ("нің", "GEN"), ("дың", "GEN"), ("дің", "GEN"), ("тың", "GEN"), ("тің", "GEN"),
    # Dative (incl. possessive-conditioned -на/-не, -а/-е)
    ("ға", "DAT"), ("ге", "DAT"), ("қа", "DAT"), ("ке", "DAT"),
    ("на", "DAT"), ("не", "DAT"), ("а", "DAT"), ("е", "DAT"),
    # Accusative (incl. possessive 3p -н)
    ("ны", "ACC"), ("ні", "ACC"), ("ды", "ACC"), ("ді", "ACC"), ("ты", "ACC"), ("ті", "ACC"),
    ("н", "ACC"),
    # Locative (incl. possessive-conditioned -нда/-нде)
    ("нда", "LOC"), ("нде", "LOC"), ("да", "LOC"), ("де", "LOC"), ("та", "LOC"), ("те", "LOC"),
    # Ablative
    ("нан", "ABL"), ("нен", "ABL"), ("дан", "ABL"), ("ден", "ABL"), ("тан", "ABL"), ("тен", "ABL"),
    # Instrumental
    ("мен", "INS"), ("бен", "INS"), ("пен", "INS"),
]
