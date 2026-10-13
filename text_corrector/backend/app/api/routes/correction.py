"""
POST /correct-text  — correct a single snippet pasted by the user
POST /correct-file  — correct an entire uploaded document
"""
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.logging_config import logger
from app.schemas.requests import TextRequest
from app.schemas.responses import (
    CorrectionItem,
    CorrectionResponse,
    FileCorrectionResponse,
)
from app.services.correction_pipeline import run_correction_pipeline
from app.services.document_correction import correct_document
from app.services.file_extraction import (
    FileExtractionError,
    UnsupportedFileType,
    extract_text,
    supported_extensions,
)
from app.utils.text_utils import sanitise_input

router = APIRouter()


@router.post(
    "/correct-text",
    response_model=CorrectionResponse,
    summary="Correct spelling and typos in the input text",
    tags=["Text Correction"],
)
def correct_text_endpoint(body: TextRequest) -> CorrectionResponse:
    """
    Detect the language of the input, then apply the appropriate correction
    pipeline.

    Declared as a SYNC ``def`` on purpose: ``run_correction_pipeline`` is
    CPU-bound (torch inference + corrector). FastAPI runs sync path operations
    in the AnyIO worker threadpool, keeping the event loop free so requests are
    served concurrently instead of serialised. **Do NOT add ``async``.**

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


# ── File upload ───────────────────────────────────────────────────────────────

_READ_CHUNK = 1 << 20  # 1 MiB


async def _read_upload(file: UploadFile, max_bytes: int) -> bytes:
    """Stream the upload, aborting as soon as it exceeds *max_bytes*."""
    buffer = bytearray()
    while True:
        chunk = await file.read(_READ_CHUNK)
        if not chunk:
            break
        buffer.extend(chunk)
        if len(buffer) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=(
                    f"Файл больше {settings.MAX_FILE_SIZE_MB} МБ. "
                    "Разделите его на части."
                ),
            )
    return bytes(buffer)


@router.post(
    "/correct-file",
    response_model=FileCorrectionResponse,
    summary="Correct every word in an uploaded document",
    tags=["Text Correction"],
)
async def correct_file_endpoint(
    file: UploadFile = File(..., description="txt / md / csv / docx / pdf"),
) -> FileCorrectionResponse:
    """
    Read an uploaded file, run the full correction pipeline over **all** of its
    text, and return the corrected document together with every replacement.

    Unlike ``/correct-text`` this splits the document into chunks and preserves
    its layout (see ``services.document_correction``), so newlines, indentation
    and paragraph structure survive the round-trip.

    Declared ``async`` so the upload can be streamed, but the CPU-bound
    correction is handed to the worker threadpool — the event loop must stay
    free while a long document is processed.
    """
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    data = await _read_upload(file, max_bytes)

    if not data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Файл пустой.",
        )

    filename = file.filename or "document"

    try:
        raw_text, file_type = extract_text(filename, data)
    except UnsupportedFileType as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc)
        ) from exc
    except FileExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    text, warnings = sanitise_input(raw_text, settings.MAX_FILE_TEXT_LENGTH)

    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "В файле не найдено текста. Поддерживаемые форматы: "
                + ", ".join(supported_extensions())
            ),
        )

    logger.info(
        "file upload | name=%s | type=%s | bytes=%d | chars=%d",
        filename,
        file_type,
        len(data),
        len(text),
    )

    result = await run_in_threadpool(correct_document, text)

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

    return FileCorrectionResponse(
        filename=filename,
        file_type=file_type,
        original_text=result["original_text"],
        corrected_text=result["corrected_text"],
        detected_language=result["detected_language"],
        confidence=result["confidence"],
        corrections=correction_items,
        corrections_total=result["corrections_total"],
        total_words=result["total_words"],
        corrected_words=result["corrected_words"],
        chunks=result["chunks"],
        processing_time_ms=result["processing_time_ms"],
        status=result["status"],
        message=message,
    )
