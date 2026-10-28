"""
Tests for the Kazakh morphological analyzer and its integration into the
Kazakh correction pipeline (stage 4: unified ML/morphology mechanism).
"""
import pytest

from app.services.morphology import analyze, is_analyzable, segment
from app.services.text_correction import correct_kazakh, _KZ_STEMS


# ── Analyzer: segmentation of valid inflected forms ───────────────────────────

@pytest.mark.parametrize(
    "word, stem, tags",
    [
        ("мектептердің", "мектеп", ("PL", "GEN")),
        ("баланың", "бала", ("GEN",)),
        ("мұғаліммен", "мұғалім", ("INS",)),
        ("сабағы", "сабақ", ("POSS3",)),   # қ→ғ consonant alternation
        ("кітабы", "кітап", ("POSS3",)),   # п→б consonant alternation
    ],
)
def test_analyze_known_forms(word, stem, tags):
    a = analyze(word, _KZ_STEMS)
    assert a is not None, f"{word} should be analyzable"
    assert a.stem == stem
    assert a.tags == tags
    assert a.harmony_ok


def test_unknown_stem_is_not_analyzable():
    # Latin gibberish / foreign stem must not parse to a known stem
    assert analyze("блаблабла", _KZ_STEMS) is None
    assert not is_analyzable("блаблабла", _KZ_STEMS)


def test_bare_known_word_segments_to_itself():
    analyses = segment("бала")
    assert any(a.stem == "бала" and a.tags == () for a in analyses)


# ── Pipeline: valid forms protected, real typos fixed ─────────────────────────

def test_valid_inflected_forms_are_not_corrected():
    text = "мектептердің сабағы"
    corrected, corrections = correct_kazakh(text)
    assert corrected == text
    assert corrections == []


def test_genuine_typos_are_corrected():
    corrected, corrections = correct_kazakh("мугалим келді")
    assert "мұғалім" in corrected
    assert any(c["after"] == "мұғалім" for c in corrections)


def test_punctuation_and_spacing_preserved():
    text = "Сәлем, мектептердің сабағы!"
    corrected, _ = correct_kazakh(text)
    assert corrected.startswith("Сәлем,")
    assert corrected.endswith("!")
