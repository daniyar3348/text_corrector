"""
Application configuration using Pydantic Settings.
All settings can be overridden via environment variables or .env file.
"""
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "Turan Text Corrector API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── Server ───────────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── CORS ─────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # ── Text limits ───────────────────────────────────────────────────────────
    MAX_TEXT_LENGTH: int = 5000
    MIN_TEXT_LENGTH: int = 1

    # ── File upload (/correct-file) ───────────────────────────────────────────
    # Rejected above this size, before the body is read into memory
    MAX_FILE_SIZE_MB: int = 5
    # Extracted text is truncated here (documents, not single sentences)
    MAX_FILE_TEXT_LENGTH: int = 200_000
    # Backstop only: chunks are cut per sentence, this caps run-on text that
    # never punctuates (the detector truncates at 512 subtokens)
    FILE_CHUNK_WORDS: int = 180
    # Cap on the itemised correction list in the response (text is never capped)
    MAX_FILE_CORRECTIONS: int = 1000

    # ── Correction thresholds ─────────────────────────────────────────────────
    # Minimum similarity (0–1) to accept a correction candidate
    CORRECTION_SIMILARITY_THRESHOLD: float = 0.55
    # Maximum edit distance for candidate lookup
    MAX_EDIT_DISTANCE: int = 3

    # ── Model paths (set these to activate real trained models) ───────────────
    # Leave empty to use the built-in rule/dictionary-based fallback.
    RUSSIAN_MODEL_PATH: Optional[str] = None
    KAZAKH_MODEL_PATH: Optional[str] = None

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_REQUESTS: bool = True

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()
