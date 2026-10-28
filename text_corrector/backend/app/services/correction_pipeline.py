"""
Correction pipeline orchestrator.

This module ties together:
  • language detection
  • model selection (placeholder vs. trained)
  • text correction services
  • timing and logging

All API route handlers should import `run_correction_pipeline` from here.
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional

from app.core.config import settings
from app.core.logging_config import logger
from app.models.model_loader import BaseCorrectModel, PlaceholderModel, load_model
from app.services.language_detection import detect_language
from app.services.text_correction import correct_text

# ── Load models once at startup ───────────────────────────────────────────────
_russian_model: BaseCorrectModel = load_model("Russian", settings.RUSSIAN_MODEL_PATH)
_kazakh_model: BaseCorrectModel = load_model("Kazakh", settings.KAZAKH_MODEL_PATH)

# Warm up any real (non-placeholder) model once, single-threaded, at import —
# forces lazy torch/kernel init before concurrent threadpool requests arrive
# (avoids a cold-burst lazy-init race + the ~200ms first-request latency).
for _m in (_russian_model, _kazakh_model):
    if not isinstance(_m, PlaceholderModel) and _m.is_ready:
        try:
            _m.correct("Сынақ мәтіні.")
            logger.info("warmed up %s", _m.model_name)
        except Exception as _exc:  # pragma: no cover
            logger.warning("model warm-up failed: %s", _exc)


def get_model_status() -> Dict[str, str]:
    """Return a dict summarising loaded model states (used by /health)."""
    return {
        "russian_model": _russian_model.model_name,
        "russian_model_ready": str(_russian_model.is_ready),
        "kazakh_model": _kazakh_model.model_name,
        "kazakh_model_ready": str(_kazakh_model.is_ready),
    }


def run_correction_pipeline(
    text: str,
    language: Optional[str] = None,
    confidence: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Full correction pipeline.

    Steps
    -----
    1. Detect language — unless *language* is supplied, in which case detection
       is skipped and the caller's routing decision is used. Document-level
       callers need this: the router reads a whole text reliably, but judged
       line by line it mistakes short non-Kazakh fragments for Kazakh and sends
       them to the wrong corrector.
    2. Select the appropriate model.
    3. If the model is a real trained model (TransformerModel, is_ready=True),
       delegate directly to `model.correct(text)`.
       Otherwise use the dictionary/edit-distance services.
    4. Collect corrections, timing, and metadata.

    Returns a dict matching `CorrectionResponse` schema.
    """
    start_ns = time.perf_counter_ns()

    # ── Step 1: language detection (skipped when the caller routes) ────────
    if language is None:
        lang_result = detect_language(text)
        language = lang_result["language"]
        confidence = lang_result["confidence"]
    elif confidence is None:
        confidence = 1.0

    # ── Step 2: choose model ───────────────────────────────────────────────
    if language == "Russian":
        model = _russian_model
    elif language == "Kazakh":
        model = _kazakh_model
    else:
        # Mixed / Unknown: default to Russian pipeline
        model = _russian_model

    # ── Step 3: run correction ─────────────────────────────────────────────
    corrections_list = []

    if isinstance(model, PlaceholderModel):
        # Use the dictionary + edit-distance services directly
        corrected_text, corrections_list = correct_text(text, language)
    else:
        # Real trained model is available
        corrected_text = model.correct(text)
        # The corrector substitutes words in place, so list one item per
        # changed word; fall back to a whole-text item if the count changed.
        if corrected_text != text:
            before_words, after_words = text.split(), corrected_text.split()
            if len(before_words) == len(after_words):
                corrections_list = [
                    {"before": b, "after": a, "type": "spelling"}
                    for b, a in zip(before_words, after_words)
                    if b != a
                ]
            else:
                corrections_list = [
                    {
                        "before": text,
                        "after": corrected_text,
                        "type": "model_correction",
                    }
                ]

    elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000

    # ── Step 4: logging ────────────────────────────────────────────────────
    if settings.LOG_REQUESTS:
        logger.info(
            "correction | lang=%s | conf=%.2f | in_len=%d | out_len=%d "
            "| corrections=%d | time=%.1fms",
            language,
            confidence,
            len(text),
            len(corrected_text),
            len(corrections_list),
            elapsed_ms,
        )

    return {
        "original_text": text,
        "corrected_text": corrected_text,
        "detected_language": language,
        "confidence": confidence,
        "corrections": corrections_list,
        "processing_time_ms": round(elapsed_ms, 2),
        "status": "success",
        "message": None,
    }
