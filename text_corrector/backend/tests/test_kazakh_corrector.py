"""
Unit tests for KazakhCorrector (needs data/kk_lexicon.tsv, which is not in git).
"""
import os

import pytest

from app.services.kazakh_corrector import DEFAULT_LEXICON, KazakhCorrector

pytestmark = pytest.mark.skipif(
    not os.path.exists(DEFAULT_LEXICON), reason="kk_lexicon.tsv not available"
)


@pytest.fixture(scope="module")
def corrector():
    return KazakhCorrector()


class TestShadowFix:
    """Unflagged ka2ru noise that the corpus put into the lexicon."""

    @pytest.mark.parametrize("word, fixed", [
        ("казакстан", "қазақстан"),
        ("Казакстан", "Қазақстан"),
        ("салем", "сәлем"),
    ])
    def test_rare_ka2ru_form_is_fixed_without_a_flag(self, corrector, word, fixed):
        assert corrector.correct(word, only_positions=set()) == fixed

    def test_frequent_word_is_left_alone(self, corrector):
        assert corrector.correct("мектепке барамыз", only_positions=set()) == "мектепке барамыз"

    def test_reverse_direction_is_not_applied(self, corrector):
        # «жылың» (your year) is valid; ң→н would turn it into «жылын»
        assert corrector.correct("жылың", only_positions=set()) == "жылың"

    def test_can_be_disabled(self):
        c = KazakhCorrector(use_shadow=False)
        assert c.correct("казакстан", only_positions=set()) == "казакстан"


class TestCorrectWord:
    def test_all_caps_stays_all_caps(self, corrector):
        assert corrector.correct_word("ЖҰЙЕЛЕУ", force=True) == "ЖҮЙЕЛЕУ"

    def test_suffix_letter_past_six_alternation_positions(self, corrector):
        # 8 alternation positions; the genitive ң is the last one
        assert corrector.correct_word("республикасынын", force=True) == "республикасының"
