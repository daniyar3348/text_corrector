"""
Whole-document correction.

Why this module exists
----------------------
``run_correction_pipeline`` is built for one sentence at a time and cannot be
pointed at a file as-is:

1. The detector tokenises with ``truncation=True, max_length=512``, so every
   word past that budget is silently never inspected.
2. ``KazakhCorrector.correct`` rebuilds its output as ``" ".join(text.split())``,
   which flattens newlines, indentation and repeated spaces — i.e. it destroys
   the layout of any real document.
3. The detector was trained on **single sentences** and degrades sharply on
   longer input: measured on one ka2ru test sentence it flags 6 errors on its
   own, and 0 when the same sentence is repeated eight times in one pass. So
   staying under the 512-subtoken budget is necessary but not sufficient — the
   unit of work has to be a sentence, which is why chunks are cut on sentence
   and line boundaries rather than on a word count.

So a document is corrected here in three steps:

* **Split** the text into a whitespace *skeleton*: alternating word tokens and
  the exact whitespace runs between them.
* **Correct** one sentence per model pass (``FILE_CHUNK_WORDS`` only acts as a
  safety cap for run-on text that carries no punctuation at all).
* **Reassemble** by writing the corrected words back into their original slots.
  Because the corrector substitutes words in place and never adds or removes
  them, this mapping is 1:1 and the document comes back byte-identical except
  for the words that actually changed.

If a chunk ever violates that 1:1 assumption the chunk is left untouched and a
warning is logged, so a surprising corrector change can never scramble a file.
"""
from __future__ import annotations

import re
import time
from typing import Any, Dict, List

from app.core.config import settings
from app.core.logging_config import logger
from app.services.correction_pipeline import run_correction_pipeline
from app.services.language_detection import detect_language

# Splits into [word, ws, word, ws, ..., word] — words sit at even indices
_WS_SPLIT = re.compile(r"(\s+)")

# Terminates a sentence, allowing for trailing quotes/brackets: «сөз.» )
_SENT_END = re.compile(r"[.!?…][\"»\')\]]*$")

_NEWLINE = "\n"


def _sentence_chunks(
    word_slots: List[int],
    parts: List[str],
    max_words: int,
) -> List[List[int]]:
    """
    Group word-slot indices into one chunk per sentence.

    A chunk is closed by sentence-ending punctuation or by a line break, so
    headings, list items and table rows are each processed on their own — this
    matches the single-sentence distribution the detector was trained on.
    *max_words* is only a backstop for text that never punctuates.
    """
    chunks: List[List[int]] = []
    current: List[int] = []

    for slot in word_slots:
        current.append(slot)
        gap = parts[slot + 1] if slot + 1 < len(parts) else ""

        if (
            _SENT_END.search(parts[slot])
            or _NEWLINE in gap
            or len(current) >= max_words
        ):
            chunks.append(current)
            current = []

    if current:
        chunks.append(current)
    return chunks


def correct_document(text: str) -> Dict[str, Any]:
    """
    Correct an entire document, preserving its layout.

    Returns a dict matching the ``FileCorrectionResponse`` schema (minus the
    filename fields, which the route fills in).
    """
    start_ns = time.perf_counter_ns()

    parts = _WS_SPLIT.split(text)
    # Even indices hold words; empty strings appear when text starts/ends with
    # whitespace and must be skipped.
    word_slots = [i for i in range(0, len(parts), 2) if parts[i]]

    # Character offset of every word in the ORIGINAL text, computed before any
    # substitution changes the lengths.
    offsets: Dict[int, int] = {}
    cursor = 0
    for i, part in enumerate(parts):
        if i % 2 == 0 and part:
            offsets[i] = cursor
        cursor += len(part)

    chunks = _sentence_chunks(word_slots, parts, settings.FILE_CHUNK_WORDS)

    # Route once for the whole document. Detecting per chunk looks tempting but
    # corrupts real files: a short Russian heading in isolation reads as Kazakh
    # and its words get "corrected" by the Kazakh corrector (observed on a real
    # PDF, where "ЭВМ" became "Эм").
    doc_language = detect_language(text)
    language: str = doc_language["language"]
    confidence: float = doc_language["confidence"]

    corrections: List[Dict[str, Any]] = []
    corrected_words = 0
    skipped_chunks = 0

    for slots in chunks:
        originals = [parts[i] for i in slots]
        chunk_text = " ".join(originals)

        # Nothing to correct in a chunk with no letters (numbers, separators…)
        if not any(ch.isalpha() for ch in chunk_text):
            continue

        result = run_correction_pipeline(chunk_text, language, confidence)
        produced = result["corrected_text"].split()
        if len(produced) != len(originals):
            # Corrector changed the word count — refuse to guess the alignment
            skipped_chunks += 1
            logger.warning(
                "document chunk skipped: word count %d → %d",
                len(originals),
                len(produced),
            )
            continue

        for slot, before, after in zip(slots, originals, produced):
            if before == after:
                continue
            parts[slot] = after
            corrected_words += 1
            corrections.append(
                {
                    "before": before,
                    "after": after,
                    "type": "spelling",
                    "position": offsets[slot],
                }
            )

    corrected_text = "".join(parts)
    elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000

    # The corrected text is always returned in full; only the itemised list is
    # capped, so huge files stay within a sane response size.
    total_corrections = len(corrections)
    listed = corrections[: settings.MAX_FILE_CORRECTIONS]

    notes: List[str] = []
    if total_corrections > len(listed):
        notes.append(
            f"Показаны первые {len(listed)} правок из {total_corrections}; "
            "исправленный текст содержит все правки."
        )
    if skipped_chunks:
        notes.append(f"Пропущено фрагментов из-за рассинхронизации: {skipped_chunks}.")

    if settings.LOG_REQUESTS:
        logger.info(
            "document | lang=%s | chars=%d | words=%d | chunks=%d "
            "| fixed=%d | time=%.1fms",
            language,
            len(text),
            len(word_slots),
            len(chunks),
            corrected_words,
            elapsed_ms,
        )

    return {
        "original_text": text,
        "corrected_text": corrected_text,
        "detected_language": language,
        "confidence": confidence,
        "corrections": listed,
        "corrections_total": total_corrections,
        "total_words": len(word_slots),
        "corrected_words": corrected_words,
        "chunks": len(chunks),
        "processing_time_ms": round(elapsed_ms, 2),
        "status": "success",
        "message": "; ".join(notes) if notes else None,
    }
