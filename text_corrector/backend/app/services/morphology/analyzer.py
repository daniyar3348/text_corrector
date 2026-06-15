"""
Kazakh morphological analyzer (segmentation / parsing).

Kazakh nominal word-forms are built by concatenating suffixes onto a stem in a
fixed order:

        STEM  (+ NUMBER)  (+ POSSESSIVE)  (+ CASE)

This module reverses that process. Given a surface form it strips suffixes from
the right — case, then possessive, then number — using the allomorph
inventories declared in `suffixes.py`, and reports every segmentation whose
remaining stem is a known word.

Why this matters for correction
-------------------------------
The finite vocabulary in `text_correction.py` cannot list every inflected form
(Kazakh stems take thousands of combinations). Without morphology the edit-
distance corrector "fixes" valid forms like ``мектептердің`` into whatever
dictionary word happens to be closest. The analyzer recognises such a form as
``мектеп`` + PL + GEN and tells the corrector to leave it alone.

Each candidate is scored by vowel-harmony consistency, so that accidental
"suffix-looking" endings on a foreign/misspelled stem are penalised.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Set, Tuple

from .phonology import BACK_VOWELS, FRONT_VOWELS, VOWELS, harmony
from .suffixes import (
    CASE_INVENTORY,
    NUMBER_INVENTORY,
    POSSESSIVE_INVENTORY,
    TAGS,
)


@dataclass(frozen=True)
class Analysis:
    """A single segmentation of a surface form."""

    stem: str
    tags: Tuple[str, ...]          # e.g. ("PL", "GEN")
    surface: str                   # the original word (lower-cased)
    stem_known: bool               # stem found in the supplied lexicon
    harmony_ok: bool               # suffix vowels agree with stem harmony

    @property
    def glosses(self) -> List[str]:
        """Human-readable grammeme labels (Kazakh school-grammar terms)."""
        return [TAGS.get(t, t) for t in self.tags]

    def __str__(self) -> str:
        if not self.tags:
            return self.stem
        return f"{self.stem}-" + "-".join(self.tags)


# ── Suffix stripping ──────────────────────────────────────────────────────────

def _strip_layer(
    word: str, inventory: Iterable[Tuple[str, str]]
) -> List[Tuple[str, str]]:
    """
    Return every ``(remainder, tag)`` produced by removing one suffix of
    *inventory* from the end of *word*.

    A suffix is only stripped if at least two characters of stem remain, which
    avoids pathological single-letter "stems".
    """
    out: List[Tuple[str, str]] = []
    for suffix, tag in inventory:
        if not suffix:
            continue
        if word.endswith(suffix) and len(word) - len(suffix) >= 2:
            out.append((word[: -len(suffix)], tag))
    return out


def _harmony_consistent(stem: str, suffix_str: str) -> bool:
    """
    True if every vowel in *suffix_str* belongs to the stem's harmony class.

    Stems whose harmony is ambiguous (no vowels) pass trivially. Suffixes
    without vowels (rare consonant-only allomorphs) also pass.
    """
    cls = harmony(stem)
    allowed = BACK_VOWELS if cls == "back" else FRONT_VOWELS
    for ch in suffix_str:
        if ch in VOWELS and ch not in allowed:
            return False
    return True


def segment(word: str) -> List[Analysis]:
    """
    Return all NUMBER→POSSESSIVE→CASE segmentations of *word*.

    The bare word (zero suffixes) is always included. ``stem_known`` is left
    False here; :func:`analyze` fills it in against a real lexicon.
    """
    word = word.lower()
    seen: Set[Tuple[str, Tuple[str, ...]]] = set()
    results: List[Analysis] = []

    # Stripping order mirrors the surface order in reverse: CASE, POSS, NUMBER.
    case_opts: List[Tuple[str, Optional[str]]] = [(word, None)]
    case_opts += [(rem, tag) for rem, tag in _strip_layer(word, CASE_INVENTORY)]

    for after_case, case_tag in case_opts:
        poss_opts: List[Tuple[str, Optional[str]]] = [(after_case, None)]
        poss_opts += [
            (rem, tag) for rem, tag in _strip_layer(after_case, POSSESSIVE_INVENTORY)
        ]

        for after_poss, poss_tag in poss_opts:
            num_opts: List[Tuple[str, Optional[str]]] = [(after_poss, None)]
            num_opts += [
                (rem, tag) for rem, tag in _strip_layer(after_poss, NUMBER_INVENTORY)
            ]

            for stem, num_tag in num_opts:
                tags = tuple(t for t in (num_tag, poss_tag, case_tag) if t)
                key = (stem, tags)
                if key in seen:
                    continue
                seen.add(key)
                suffix_str = word[len(stem):]
                results.append(
                    Analysis(
                        stem=stem,
                        tags=tags,
                        surface=word,
                        stem_known=False,
                        harmony_ok=_harmony_consistent(stem, suffix_str),
                    )
                )
    return results


# Stem-final consonant alternation (morphophonemic voicing).
# When a vowel-initial suffix attaches, a final voiceless consonant of the stem
# voices: қ→ғ, к→г, п→б. To recover the dictionary stem we reverse it.
_DEVOICE = {"ғ": "қ", "г": "к", "б": "п"}


def _stem_variants(stem: str) -> List[str]:
    """Return *stem* plus its de-voiced spelling variant (longest-relevant first)."""
    variants = [stem]
    if stem and stem[-1] in _DEVOICE:
        variants.append(stem[:-1] + _DEVOICE[stem[-1]])
    return variants


def _rank_key(a: Analysis) -> Tuple[int, int, int, int]:
    """
    Sort key for picking the best analysis (higher is better, so we negate).

    Preference order:
      1. stem is a known word
      2. vowel harmony is consistent
      3. longer stem (most conservative segmentation)
      4. fewer stripped suffixes
    """
    return (
        1 if a.stem_known else 0,
        1 if a.harmony_ok else 0,
        len(a.stem),
        -len(a.tags),
    )


def analyze(word: str, known_stems: Set[str]) -> Optional[Analysis]:
    """
    Return the best segmentation of *word* whose stem is in *known_stems*,
    or ``None`` if no segmentation lands on a known stem.

    Comparison against *known_stems* is case-insensitive.
    """
    if not word:
        return None

    lexicon = known_stems if all(s.islower() for s in known_stems) else {
        s.lower() for s in known_stems
    }

    scored: List[Analysis] = []
    for a in segment(word):
        # Accept the segmentation if the surface stem — or its de-voiced
        # variant (қ↔ғ, к↔г, п↔б) — is a known word.
        for variant in _stem_variants(a.stem):
            if variant in lexicon:
                scored.append(
                    Analysis(
                        stem=variant,
                        tags=a.tags,
                        surface=a.surface,
                        stem_known=True,
                        harmony_ok=a.harmony_ok,
                    )
                )
                break

    if not scored:
        return None
    return max(scored, key=_rank_key)


def is_analyzable(word: str, known_stems: Set[str]) -> bool:
    """
    True if *word* is a valid inflected form of a known stem.

    A harmony-consistent analysis is required so that misspelled stems with a
    coincidental suffix-shaped ending are not mistaken for valid forms.
    """
    a = analyze(word, known_stems)
    return a is not None and a.harmony_ok
