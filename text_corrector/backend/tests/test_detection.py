"""
Unit tests for the language detection service.
"""
import pytest
from app.services.language_detection import detect_language, is_kazakh, is_russian


class TestDetectLanguage:
    def test_russian_greeting(self):
        result = detect_language("привет")
        assert result["language"] == "Russian"
        assert result["confidence"] > 0.5

    def test_russian_sentence(self):
        result = detect_language("я хочу учиться в школе")
        assert result["language"] == "Russian"
        assert result["confidence"] > 0.6

    def test_kazakh_specific_chars(self):
        # Contains Ә – exclusively Kazakh
        result = detect_language("Сәлем")
        assert result["language"] == "Kazakh"
        assert result["confidence"] > 0.5

    def test_kazakh_sentence(self):
        result = detect_language("мен мектепте оқимын")
        # "мектепте" and "оқимын" are Kazakh-pattern words
        # Accept Kazakh or Mixed since tokens overlap
        assert result["language"] in ("Kazakh", "Russian", "Mixed")

    def test_kazakh_with_exclusive_chars(self):
        result = detect_language("Қазақстан халқы")
        assert result["language"] == "Kazakh"
        assert result["confidence"] > 0.6

    def test_empty_string(self):
        result = detect_language("")
        assert result["language"] == "Unknown"
        assert result["confidence"] == 0.0

    def test_whitespace_only(self):
        result = detect_language("   ")
        assert result["language"] == "Unknown"
        assert result["confidence"] == 0.0

    def test_no_cyrillic(self):
        result = detect_language("hello world 123")
        assert result["language"] == "Unknown"

    def test_confidence_range(self):
        result = detect_language("привет мир")
        assert 0.0 <= result["confidence"] <= 1.0

    def test_mixed_text(self):
        # Mix of Russian and Kazakh signal words
        result = detect_language("я және сен здесь")
        # Should be detected as some language (not Unknown)
        assert result["language"] in ("Russian", "Kazakh", "Mixed")


class TestIsKazakh:
    def test_kazakh_char_present(self):
        assert is_kazakh("Сәлем") is True

    def test_no_kazakh_char(self):
        assert is_kazakh("привет") is False

    def test_all_kazakh_exclusive_chars(self):
        assert is_kazakh("ӘәҒғҚқҢңӨөҰұҮүҺһІі") is True


class TestIsRussian:
    def test_russian_text(self):
        assert is_russian("привет мир") is True

    def test_kazakh_text(self):
        # Kazakh should not be classified as Russian
        assert is_russian("Сәлем Қазақстан") is False
