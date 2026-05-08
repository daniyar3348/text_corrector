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
