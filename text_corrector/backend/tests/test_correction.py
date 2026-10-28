"""
Unit tests for the text correction service and pipeline.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.text_correction import correct_russian, correct_kazakh, correct_text
from app.services.correction_pipeline import run_correction_pipeline

client = TestClient(app)


# ── Unit tests for correction services ───────────────────────────────────────

class TestCorrectRussian:
    def test_russian_is_noop(self):
        """Russian path is intentionally a no-op (no trained RU model; the demo
        dictionary corrupted valid Russian). Text passes through unchanged."""
        corrected, corrections = correct_russian("прмвет")
        assert corrected == "прмвет"
        assert corrections == []

    def test_no_change_for_valid_word(self):
        corrected, corrections = correct_russian("привет")
        assert corrected == "привет"
        assert corrections == []

    def test_preserves_spaces(self):
        corrected, _ = correct_russian("привет мир")
        assert " " in corrected

    def test_preserves_punctuation(self):
        corrected, _ = correct_russian("привет, мир!")
        assert "," in corrected
        assert "!" in corrected

    def test_capitalisation_preserved(self):
        corrected, corrections = correct_russian("Прмвет")
        # Should return capitalised correction
        assert corrected[0].isupper()

    def test_multi_word_noop(self):
        text = "прмвет мр"
        corrected, corrections = correct_russian(text)
        # Russian is a no-op: nothing changed
        assert corrected == text
        assert corrections == []


class TestCorrectKazakh:
    def test_valid_kazakh_word_unchanged(self):
        corrected, corrections = correct_kazakh("сәлем")
        assert corrected == "сәлем"
        assert corrections == []


class TestCorrectTextDispatch:
    def test_routes_to_russian(self):
        # Russian routing still works, but the Russian path is now a no-op.
        corrected, _ = correct_text("прмвет", "Russian")
        assert corrected == "прмвет"

    def test_unknown_language_passthrough(self):
        original = "xyz123"
        corrected, corrections = correct_text(original, "Unknown")
        assert corrected == original
        assert corrections == []


# ── Integration tests via HTTP client ────────────────────────────────────────

class TestCorrectTextEndpoint:
    def test_correct_russian_passthrough(self):
        # Russian is a no-op: text returned unchanged, still detected Russian.
        response = client.post("/correct-text", json={"text": "прмвет"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["corrected_text"] == "прмвет"
        assert data["detected_language"] == "Russian"
        assert isinstance(data["corrections"], list)
        assert isinstance(data["processing_time_ms"], float)

    def test_empty_text_returns_422(self):
        response = client.post("/correct-text", json={"text": ""})
        assert response.status_code == 422

    def test_whitespace_only_returns_422(self):
        response = client.post("/correct-text", json={"text": "   "})
        assert response.status_code == 422

    def test_valid_text_returns_200(self):
        response = client.post("/correct-text", json={"text": "привет мир"})
        assert response.status_code == 200

    def test_response_schema(self):
        response = client.post("/correct-text", json={"text": "прмвет"})
        data = response.json()
        required_keys = {
            "original_text", "corrected_text", "detected_language",
            "confidence", "corrections", "processing_time_ms", "status",
        }
        assert required_keys.issubset(data.keys())

    def test_confidence_in_range(self):
        response = client.post("/correct-text", json={"text": "привет"})
        data = response.json()
        assert 0.0 <= data["confidence"] <= 1.0

    def test_russian_is_reported_as_unchecked(self):
        """No Russian corrector: the response must not imply the text is correct."""
        data = client.post("/correct-text", json={"text": "прмвет мр"}).json()
        assert data["corrected_text"] == "прмвет мр"
        assert "только казахский" in data["message"]

    def test_kazakh_has_no_unchecked_note(self):
        data = client.post("/correct-text", json={"text": "Сәлем Қазақстан"}).json()
        assert data["detected_language"] == "Kazakh"
        assert data["message"] is None

    def test_line_breaks_are_preserved(self):
        """Pasted text is corrected sentence by sentence, keeping its layout."""
        text = "Бірінші жол.\n\n    Екінші жол."
        data = client.post("/correct-text", json={"text": text}).json()
        assert data["corrected_text"].count("\n") == 2
        assert "\n\n    " in data["corrected_text"]

    def test_corrections_are_per_word(self):
        """One item per changed word with its offset — not the whole text."""
        data = client.post("/correct-text", json={"text": "кітп оқиды"}).json()
        assert data["corrected_text"] == "кітап оқиды"
        assert [(c["before"], c["after"], c["position"])
                for c in data["corrections"]] == [("кітп", "кітап", 0)]


class TestDetectLanguageEndpoint:
    def test_russian_text(self):
        response = client.post("/detect-language", json={"text": "привет мир"})
        assert response.status_code == 200
        data = response.json()
        assert data["detected_language"] == "Russian"
        assert data["status"] == "success"

    def test_kazakh_text(self):
        response = client.post("/detect-language", json={"text": "Сәлем Қазақстан"})
        assert response.status_code == 200
        data = response.json()
        assert data["detected_language"] == "Kazakh"

    def test_empty_text(self):
        response = client.post("/detect-language", json={"text": ""})
        assert response.status_code == 422
