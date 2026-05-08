"""
GET /health
"""
from fastapi import APIRouter

from app.core.config import settings
from app.schemas.responses import HealthResponse
from app.services.correction_pipeline import get_model_status

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["System"],
)
async def health_check() -> HealthResponse:
    """
    Returns the current health status of the service and loaded models.
    """
    model_status = get_model_status()

    all_ready = all(
        v == "True" for k, v in model_status.items() if k.endswith("_ready")
    )

    return HealthResponse(
        service_status="ok",
        model_status="loaded" if all_ready else "placeholder",
        version=settings.VERSION,
        details=model_status,
    )
