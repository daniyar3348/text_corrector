"""
Model integration layer.

This module defines the abstract interface that any correction model must
implement. Two concrete implementations are provided:

1. PlaceholderModel   — rule/dictionary-based, works out of the box,
                        no GPU or large downloads required.
2. TransformerModel   — skeleton for a real seq2seq / masked-LM model
                        loaded from a local path or HuggingFace Hub.

To plug in a real trained model:
  • Set RUSSIAN_MODEL_PATH or KAZAKH_MODEL_PATH in .env (or env vars).
  • Implement `TransformerModel.correct()` using your inference code.
  • The rest of the pipeline (API, pipeline orchestrator) stays unchanged.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Optional

from app.core.logging_config import logger


# ── Abstract base ─────────────────────────────────────────────────────────────

class BaseCorrectModel(ABC):
    """All correction models must implement this interface."""

    @abstractmethod
    def correct(self, text: str) -> str:
        """Return the corrected version of *text*."""
        ...

    @property
    @abstractmethod
    def is_ready(self) -> bool:
        """True if the model is loaded and ready for inference."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Human-readable model identifier for health checks."""
        ...


# ── Placeholder (default) implementation ─────────────────────────────────────

class PlaceholderModel(BaseCorrectModel):
    """
    Delegates to the dictionary/edit-distance correction services.
    This is the default when no trained model path is configured.
    """

    def __init__(self, language: str) -> None:
        self._language = language
        self._ready = True
        logger.info(
            "PlaceholderModel initialised for language=%s "
            "(dictionary + edit-distance backend)",
            language,
        )

    def correct(self, text: str) -> str:
        # Actual logic lives in text_correction.py; this method is called
        # by correction_pipeline.py, which imports the service functions
        # directly.  PlaceholderModel.correct() acts as a pass-through marker.
        return text   # overridden by pipeline; see correction_pipeline.py

    @property
    def is_ready(self) -> bool:
        return self._ready

    @property
    def model_name(self) -> str:
        return f"PlaceholderModel[{self._language}]"


# ── Transformer model skeleton ────────────────────────────────────────────────

class TransformerModel(BaseCorrectModel):
    """
    KazRoBERTa error-DETECTOR (token classification) + rule/lexicon CORRECTOR.

    Unified Kazakh correction mechanism:
      • the fine-tuned detector tags each token KEEP / ERROR;
      • `KazakhCorrector` fixes the flagged words (inverse ru↔kk rules +
        lexicon + OSA edit-distance).

    Activates when *model_path* holds a HuggingFace token-classification model
    (see scripts/train_detector.py / colab_train_detector.ipynb) AND
    torch+transformers are installed; otherwise falls back to PlaceholderModel.
    Set the path via KAZAKH_MODEL_PATH in .env.
    """

    def __init__(self, model_path: str, language: str) -> None:
        self._language = language
        self._model_path = model_path
        self._model = None
        self._tokenizer = None
        self._corrector = None
        self._ready = False

        self._load(model_path)

    # ── Loading ───────────────────────────────────────────────────────────────

    def _load(self, model_path: str) -> None:
        """Load the token-classification detector + Kazakh corrector."""
        if not os.path.exists(model_path):
            logger.warning(
                "TransformerModel: path %s does not exist. "
                "Falling back to placeholder.",
                model_path,
            )
            return

        try:
            import torch  # noqa: F401  (lazy: not installed in the API venv)
            # Throughput here comes from serving requests concurrently across the
            # FastAPI threadpool, not per-call multithreaded BLAS. Pin intra-op
            # threads to 1 so concurrent inferences don't oversubscribe the CPU.
            try:
                torch.set_num_threads(1)
            except Exception:
                pass
            from transformers import (
                AutoModelForTokenClassification,
                AutoTokenizer,
            )

            from app.services.kazakh_corrector import KazakhCorrector

            self._tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True)
            self._model = AutoModelForTokenClassification.from_pretrained(model_path)
            self._model.eval()
            self._corrector = KazakhCorrector()
            self._ready = True
            logger.info(
                "TransformerModel (detector+corrector) loaded for language=%s "
                "from %s",
                self._language,
                model_path,
            )
        except ImportError as exc:
            logger.warning(
                "torch/transformers unavailable (%s); using placeholder.", exc
            )
        except Exception as exc:
            logger.error("Failed to load detector from %s: %s", model_path, exc)

    # ── Inference ─────────────────────────────────────────────────────────────

    def _run_inference(self, text: str) -> str:
        """Detector tags tokens → corrector fixes the flagged words."""
        import torch

        words = text.split()
        if not words:
            return text

        enc = self._tokenizer(
            words, is_split_into_words=True, truncation=True,
            max_length=512, return_tensors="pt",
        )
        with torch.no_grad():
            logits = self._model(**enc).logits[0]
        preds = logits.argmax(-1).tolist()

        # первая под-токен метка каждого слова; label==1 → ERROR
        error_pos: set[int] = set()
        prev = None
        for tok_idx, wid in enumerate(enc.word_ids(0)):
            if wid is None or wid == prev:
                prev = wid
                continue
            prev = wid
            if preds[tok_idx] == 1:
                error_pos.add(wid)

        # The corrector runs even with no flags: it still fixes unflagged ka2ru
        # noise (see KazakhCorrector use_shadow). It re-joins words with single
        # spaces, so return the input untouched when no word changed.
        fixed = self._corrector.correct(text, only_positions=error_pos)
        return text if fixed.split() == words else fixed

    def correct(self, text: str) -> str:
        if not self._ready:
            return text
        try:
            return self._run_inference(text)
        except Exception as exc:
            logger.error("TransformerModel.correct() failed: %s", exc)
            return text

    @property
    def is_ready(self) -> bool:
        return self._ready

    @property
    def model_name(self) -> str:
        return f"TransformerModel[{self._language}]@{self._model_path}"


# ── Factory ───────────────────────────────────────────────────────────────────

def load_model(language: str, model_path: Optional[str] = None) -> BaseCorrectModel:
    """
    Factory function called at startup.

    If *model_path* is set and the path exists, a TransformerModel is
    returned; otherwise a PlaceholderModel is used.
    """
    # Treat empty/whitespace as unset (e.g. a blank `KAZAKH_MODEL_PATH=` in .env)
    # so it falls back to the placeholder instead of trying to load the path "".
    if model_path and model_path.strip():
        model = TransformerModel(model_path=model_path, language=language)
        if model.is_ready:
            return model
        logger.warning(
            "TransformerModel not ready for %s; using PlaceholderModel instead.",
            language,
        )

    return PlaceholderModel(language=language)
