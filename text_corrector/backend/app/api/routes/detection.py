"""
POST /detect-language
"""
from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.core.logging_config import logger
from app.schemas.requests import TextRequest
from app.schemas.responses import LanguageDetectionResponse
from app.services.language_detection import detect_language
from app.utils.text_utils import sanitise_input

router = APIRouter()


@router.post(
    "/detect-language",
    response_model=LanguageDetectionResponse,
    summary="Detect the language of the input text",
    tags=["Language Detection"],
)
def detect_language_endpoint(body: TextRequest) -> LanguageDetectionResponse:
    """
    Detect whether the input text is **Russian**, **Kazakh**, **Mixed**, or **Unknown**.

    Returns a confidence score in the range `[0, 1]`.
    """
    text, warnings = sanitise_input(body.text, settings.MAX_TEXT_LENGTH)

    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Input text is empty after sanitisation.",
        )

    result = detect_language(text)
    message = "; ".join(warnings) if warnings else None

    logger.info(
        "detect-language | lang=%s | conf=%.2f | input_len=%d",
        result["language"],
        result["confidence"],
        len(text),
    )

    return LanguageDetectionResponse(
        detected_language=result["language"],
        confidence=result["confidence"],
        status="success",
        message=message,
    )
