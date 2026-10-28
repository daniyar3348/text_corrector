"""
Kazakh morphological analyzer package.

Public surface:
    analyze(word, known_stems)      → best Analysis or None
    is_analyzable(word, known_stems) → bool
    segment(word)                   → list of (stem, tags) segmentations

The analyzer turns the agglutinative surface form of a Kazakh word back into
its stem + grammeme chain, validating vowel harmony. It is used by the
correction pipeline to avoid "correcting" perfectly valid inflected forms that
simply do not appear verbatim in the finite vocabulary.
"""
from __future__ import annotations

from .analyzer import Analysis, analyze, is_analyzable, segment

__all__ = ["Analysis", "analyze", "is_analyzable", "segment"]
