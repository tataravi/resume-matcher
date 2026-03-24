from .analysis import router as analysis_router
from .upload import router as upload_router
from .websocket import router as websocket_router
from .health import router as health_router
from .auth import router as auth_router

__all__ = ["analysis_router", "upload_router", "websocket_router", "health_router", "auth_router"]