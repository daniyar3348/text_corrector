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
    Skeleton integration for a HuggingFace-compatible seq2seq model.

    How to complete this integration
    ---------------------------------
    1. Train or download a model (e.g. T5, mBART, BERT-based spell-checker).
    2. Set the path in .env:
           RUSSIAN_MODEL_PATH=/models/russian_spellcheck
           KAZAKH_MODEL_PATH=/models/kazakh_spellcheck
    3. Implement the `_run_inference()` method below using the Transformers
       library (or ONNX Runtime for faster CPU inference).
    4. Optionally add batching, caching, or beam-search parameters.

    The pipeline and API will automatically use this model when the path
    is configured, with no changes required elsewhere.
    """

    def __init__(self, model_path: str, language: str) -> None:
        self._language = language
        self._model_path = model_path
        self._model = None
        self._tokenizer = None
        self._ready = False

        self._load(model_path)

    # ── Loading ───────────────────────────────────────────────────────────────

    def _load(self, model_path: str) -> None:
        """Load model artefacts from *model_path*."""
        if not os.path.exists(model_path):
            logger.warning(
                "TransformerModel: path %s does not exist. "
                "Falling back to placeholder.",
                model_path,
            )
            return

        try:
            # ── INSERT YOUR LOADING CODE HERE ────────────────────────────────
            # Example using HuggingFace Transformers:
            #
            # from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            # self._tokenizer = AutoTokenizer.from_pretrained(model_path)
            # self._model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
            # self._model.eval()
            #
            # Example using ONNX Runtime:
            #
            # import onnxruntime as ort
            # self._session = ort.InferenceSession(
            #     os.path.join(model_path, "model.onnx"),
            #     providers=["CPUExecutionProvider"],
            # )
            # ─────────────────────────────────────────────────────────────────
            self._ready = True
            logger.info(
                "TransformerModel loaded for language=%s from %s",
                self._language,
                model_path,
            )
        except Exception as exc:
            logger.error(
                "Failed to load TransformerModel from %s: %s",
                model_path,
                exc,
            )

    # ── Inference ─────────────────────────────────────────────────────────────

    def _run_inference(self, text: str) -> str:
        """
        Run model inference on a single text string.

        Replace the NotImplementedError body with your actual inference code.
        """
        # ── INSERT YOUR INFERENCE CODE HERE ─────────────────────────────────
        # Example using HuggingFace Transformers:
        #
        # inputs = self._tokenizer(
        #     text, return_tensors="pt", max_length=512, truncation=True
        # )
        # outputs = self._model.generate(**inputs, max_new_tokens=512)
        # return self._tokenizer.decode(outputs[0], skip_special_tokens=True)
        # ────────────────────────────────────────────────────────────────────
        raise NotImplementedError("TransformerModel._run_inference() not implemented.")

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
    if model_path:
        model = TransformerModel(model_path=model_path, language=language)
        if model.is_ready:
            return model
        logger.warning(
            "TransformerModel not ready for %s; using PlaceholderModel instead.",
            language,
        )

    return PlaceholderModel(language=language)
