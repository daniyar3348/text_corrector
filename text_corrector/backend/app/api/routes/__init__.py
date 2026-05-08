from .correction import router as correction_router
from .detection import router as detection_router
from .health import router as health_router

__all__ = ["correction_router", "detection_router", "health_router"]
