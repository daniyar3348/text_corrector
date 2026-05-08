"""
POST /correct-text
"""
from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.schemas.requests import TextRequest
from app.schemas.responses import CorrectionItem, CorrectionResponse
from app.services.correction_pipeline import run_correction_pipeline
from app.utils.text_utils import sanitise_input

router = APIRouter()


@router.post(
    "/correct-text",
    response_model=CorrectionResponse,
    summary="Correct spelling and typos in the input text",
    tags=["Text Correction"],
)
async def correct_text_endpoint(body: TextRequest) -> CorrectionResponse:
    """
    Detect the language of the input, then apply the appropriate correction
    pipeline.

    Returns the **original** text, the **corrected** text, a list of
    per-token corrections, the detected language, and timing metadata.
    """
    text, warnings = sanitise_input(body.text, settings.MAX_TEXT_LENGTH)

    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Input text is empty after sanitisation.",
        )

    result = run_correction_pipeline(text)

    # Map raw correction dicts → Pydantic models
    correction_items = [
        CorrectionItem(
            before=c["before"],
            after=c["after"],
            type=c.get("type", "spelling"),
            position=c.get("position"),
        )
        for c in result["corrections"]
    ]

    message = result.get("message")
    if warnings:
        extra = "; ".join(warnings)
        message = f"{message}; {extra}" if message else extra

    return CorrectionResponse(
        original_text=result["original_text"],
        corrected_text=result["corrected_text"],
        detected_language=result["detected_language"],
        confidence=result["confidence"],
        corrections=correction_items,
        processing_time_ms=result["processing_time_ms"],
        status=result["status"],
        message=message,
    )
