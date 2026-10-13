"""
Unit tests for document extraction and whole-file correction.

The layout tests are the important ones: /correct-file must return a document
that is byte-identical to the input except for the words that changed.
"""
import io

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.document_correction import _sentence_chunks, correct_document
from app.services.file_extraction import (
    UnsupportedFileType,
    extract_text,
    supported_extensions,
)

client = TestClient(app)


# ── Text extraction ───────────────────────────────────────────────────────────

class TestExtractText:
    def test_utf8_txt(self):
        text, kind = extract_text("a.txt", "Қазақ тілі".encode("utf-8"))
        assert text == "Қазақ тілі"
        assert kind == "txt"

    def test_cp1251_is_decoded(self):
        """Windows-authored Russian files are CP1251, not UTF-8."""
        text, _ = extract_text("a.txt", "Привет мир".encode("cp1251"))
        assert text == "Привет мир"

    def test_bom_is_stripped(self):
        text, _ = extract_text("a.txt", "﻿текст".encode("utf-8"))
        assert text == "текст"

    def test_no_extension_is_treated_as_text(self):
        text, kind = extract_text("README", b"plain")
        assert (text, kind) == ("plain", "txt")

    def test_legacy_doc_is_rejected_with_guidance(self):
        with pytest.raises(UnsupportedFileType, match="docx"):
            extract_text("a.doc", b"\xd0\xcf\x11\xe0")

    def test_unknown_extension_is_rejected(self):
        with pytest.raises(UnsupportedFileType):
            extract_text("a.exe", b"MZ")

    def test_supported_list_covers_the_documented_formats(self):
        for ext in (".txt", ".md", ".csv", ".docx", ".pdf"):
            assert ext in supported_extensions()


class TestExtractDocx:
    def test_paragraphs_and_tables(self):
        docx = pytest.importorskip("docx")
        document = docx.Document()
        document.add_paragraph("Бірінші абзац")
        table = document.add_table(rows=1, cols=2)
        table.cell(0, 0).text = "Тіл"
        table.cell(0, 1).text = "Қате"
        buffer = io.BytesIO()
        document.save(buffer)

        text, kind = extract_text("a.docx", buffer.getvalue())
        assert kind == "docx"
        assert "Бірінші абзац" in text
        assert "Тіл\tҚате" in text


# ── Chunking ──────────────────────────────────────────────────────────────────

class TestSentenceChunks:
    @staticmethod
    def _chunks(text):
        import re

        parts = re.compile(r"(\s+)").split(text)
        slots = [i for i in range(0, len(parts), 2) if parts[i]]
        return [
            [parts[i] for i in chunk]
            for chunk in _sentence_chunks(slots, parts, 180)
        ]

    def test_one_chunk_per_sentence(self):
        """The detector is trained on single sentences and flags nothing on a
        long concatenation, so each sentence must get its own pass."""
        assert self._chunks("Бір сөйлем. Екінші сөйлем.") == [
            ["Бір", "сөйлем."],
            ["Екінші", "сөйлем."],
        ]

    def test_line_break_closes_a_chunk(self):
        """Headings and list items carry no final period."""
        assert self._chunks("Тақырып\nМәтін") == [["Тақырып"], ["Мәтін"]]

    def test_word_cap_splits_run_on_text(self):
        parts = __import__("re").compile(r"(\s+)").split(" ".join(["сөз"] * 10))
        slots = [i for i in range(0, len(parts), 2) if parts[i]]
        assert len(_sentence_chunks(slots, parts, 4)) == 3  # 4 + 4 + 2

    def test_trailing_quote_still_ends_a_sentence(self):
        assert self._chunks('Ол «сөз.» Келесі.') == [["Ол", "«сөз.»"], ["Келесі."]]


# ── Whole-document correction ─────────────────────────────────────────────────

class TestCorrectDocument:
    def test_layout_is_preserved_exactly(self):
        """Indentation, tabs, blank lines and the trailing newline all survive."""
        text = "ТАҚЫРЫП\n\n    Бірінші жол.\n\tЕкінші жол.\n\nСоңы.\n"
        result = correct_document(text)
        corrected = result["corrected_text"]

        assert corrected.count("\n") == text.count("\n")
        assert corrected.endswith("\n")
        assert "\n    " in corrected and "\n\t" in corrected
        assert len(corrected.split()) == len(text.split())

    def test_whitespace_runs_are_identical(self):
        import re

        text = "сөз   сөз\n\n\nсөз\tсөз"
        corrected = correct_document(text)["corrected_text"]
        gaps = lambda s: re.compile(r"(\s+)").split(s)[1::2]
        assert gaps(corrected) == gaps(text)

    def test_reports_word_and_chunk_counts(self):
        result = correct_document("Бірінші сөйлем. Екінші сөйлем.")
        assert result["total_words"] == 4
        assert result["chunks"] == 2
        assert result["status"] == "success"

    def test_empty_and_whitespace_only_input(self):
        for text in ("", "   \n\n  "):
            result = correct_document(text)
            assert result["corrected_text"] == text
            assert result["corrected_words"] == 0

    def test_corrections_carry_original_offsets(self):
        """Positions index the ORIGINAL text so a client can highlight in place."""
        result = correct_document("Бірінші жол.\nЕкінші жол.")
        for correction in result["corrections"]:
            start = correction["position"]
            assert result["original_text"][start:].startswith(correction["before"])


# ── API ───────────────────────────────────────────────────────────────────────

class TestCorrectFileEndpoint:
    def test_txt_upload(self):
        response = client.post(
            "/correct-file",
            files={"file": ("a.txt", "Бірінші жол.\nЕкінші жол.\n", "text/plain")},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["filename"] == "a.txt"
        assert body["file_type"] == "txt"
        assert body["status"] == "success"
        assert body["corrected_text"].count("\n") == 2

    def test_empty_file_is_rejected(self):
        response = client.post(
            "/correct-file", files={"file": ("a.txt", b"", "text/plain")}
        )
        assert response.status_code == 422

    def test_unsupported_type_is_rejected(self):
        response = client.post(
            "/correct-file", files={"file": ("a.exe", b"MZ", "application/x-msdownload")}
        )
        assert response.status_code == 415
        assert "не поддерживается" in response.json()["detail"]

    def test_oversized_file_is_rejected(self):
        from app.core.config import settings

        payload = b"a" * (settings.MAX_FILE_SIZE_MB * 1024 * 1024 + 1024)
        response = client.post(
            "/correct-file", files={"file": ("big.txt", payload, "text/plain")}
        )
        assert response.status_code == 413

    def test_missing_file_field(self):
        assert client.post("/correct-file").status_code == 422
