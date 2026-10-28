"""
Plain-text extraction from uploaded documents.

Supported inputs
----------------
* ``.txt`` / ``.md`` / ``.csv`` / ``.tsv`` / ``.log`` — decoded directly
* ``.docx`` — paragraphs + table cells (``python-docx``)
* ``.pdf``  — per-page text layer (``pypdf``)

Anything else raises :class:`UnsupportedFileType` with a human-readable
message that the API returns verbatim to the client.

Encoding
--------
Kazakh/Russian files produced on Windows are frequently CP1251 rather than
UTF-8, so plain-text payloads are decoded against an ordered candidate list
instead of assuming UTF-8.
"""
from __future__ import annotations

import io
import os
from typing import List, Tuple

# Extensions treated as raw text
_TEXT_EXT = {".txt", ".md", ".csv", ".tsv", ".log", ".text"}

# Tried in order; first clean decode wins
_ENCODINGS = ("utf-8-sig", "utf-8", "cp1251", "koi8-r", "iso-8859-5")

_SUPPORTED: List[str] = sorted(_TEXT_EXT) + [".docx", ".pdf"]


class FileExtractionError(ValueError):
    """Raised when an uploaded file cannot be turned into text."""


class UnsupportedFileType(FileExtractionError):
    """Raised for formats the service does not handle."""


def supported_extensions() -> List[str]:
    """Extensions accepted by :func:`extract_text` (with leading dot)."""
    return list(_SUPPORTED)


# ── Per-format readers ────────────────────────────────────────────────────────

def _decode(data: bytes) -> str:
    """Decode raw bytes, trying the most likely Cyrillic encodings in turn."""
    for enc in _ENCODINGS:
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    # Last resort: never fail the request over a few bad bytes
    return data.decode("utf-8", errors="replace")


def _from_docx(data: bytes) -> str:
    try:
        import docx  # python-docx
    except ImportError as exc:  # pragma: no cover - depends on install
        raise UnsupportedFileType(
            "Чтение .docx недоступно: не установлен пакет python-docx."
        ) from exc

    try:
        document = docx.Document(io.BytesIO(data))
    except Exception as exc:
        raise FileExtractionError(
            "Не удалось открыть .docx — файл повреждён или защищён паролем."
        ) from exc

    blocks = [p.text for p in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            blocks.append("\t".join(cell.text.replace("\n", " ") for cell in row.cells))
    return "\n".join(blocks)


def _from_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - depends on install
        raise UnsupportedFileType(
            "Чтение .pdf недоступно: не установлен пакет pypdf."
        ) from exc

    try:
        reader = PdfReader(io.BytesIO(data))
        pages = [(page.extract_text() or "") for page in reader.pages]
    except Exception as exc:
        raise FileExtractionError(
            "Не удалось прочитать .pdf — файл повреждён или зашифрован."
        ) from exc

    text = "\n\n".join(pages)
    if not text.strip():
        raise FileExtractionError(
            "В .pdf нет текстового слоя (вероятно, это скан). "
            "Распознайте его через OCR или загрузите .docx/.txt."
        )
    return text


# ── Entry point ───────────────────────────────────────────────────────────────

def extract_text(filename: str, data: bytes) -> Tuple[str, str]:
    """
    Extract plain text from *data*.

    Returns ``(text, file_type)`` where *file_type* is the extension without
    the dot (``"txt"``, ``"docx"``, ``"pdf"``, …).
    """
    ext = os.path.splitext(filename or "")[1].lower()

    if ext in _TEXT_EXT:
        return _decode(data), ext.lstrip(".")
    if ext == ".docx":
        return _from_docx(data), "docx"
    if ext == ".pdf":
        return _from_pdf(data), "pdf"
    if ext == ".doc":
        raise UnsupportedFileType(
            "Формат .doc (Word 97-2003) не поддерживается — "
            "пересохраните документ как .docx."
        )
    if not ext:
        # No extension: assume text rather than rejecting outright
        return _decode(data), "txt"

    raise UnsupportedFileType(
        f"Формат {ext} не поддерживается. Доступные форматы: "
        + ", ".join(_SUPPORTED)
    )
