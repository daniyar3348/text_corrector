"""
Pydantic response schemas for all API endpoints.
"""
from typing import List, Optional

from pydantic import BaseModel


class LanguageDetectionResponse(BaseModel):
    detected_language: str        # "Russian" | "Kazakh" | "Mixed" | "Unknown"
    confidence: float             # 0.0 – 1.0
    status: str                   # "success" | "error"
    message: Optional[str] = None # optional human-readable note


class CorrectionItem(BaseModel):
    """Describes a single token-level correction."""
    before: str
    after: str
    type: str                     # "spelling" | "typo" | "unknown"
    position: Optional[int] = None


class CorrectionResponse(BaseModel):
    original_text: str
    corrected_text: str
    detected_language: str
    confidence: float
    corrections: List[CorrectionItem]
    processing_time_ms: float
    status: str
    message: Optional[str] = None


class FileCorrectionResponse(BaseModel):
    """Result of correcting a whole uploaded document."""
    filename: str
    file_type: str                # "txt" | "docx" | "pdf" | …
    original_text: str
    corrected_text: str
    detected_language: str
    confidence: float
    corrections: List[CorrectionItem]
    corrections_total: int        # may exceed len(corrections) — list is capped
    total_words: int
    corrected_words: int
    chunks: int                   # model passes used for this document
    processing_time_ms: float
    status: str
    message: Optional[str] = None


class HealthResponse(BaseModel):
    service_status: str           # "ok" | "degraded" | "error"
    model_status: str             # "loaded" | "placeholder" | "error"
    version: str
    details: Optional[dict] = None
