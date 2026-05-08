"""
Pydantic request schemas for all API endpoints.
"""
from pydantic import BaseModel, field_validator


class TextRequest(BaseModel):
    """Shared request body for both /detect-language and /correct-text."""

    text: str

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("text must not be empty")
        return v
