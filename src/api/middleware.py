import time
import logging
from typing import Callable
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_client import Counter, Histogram
import structlog

from src.config import settings


logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request
        logger.info(
            "request_started",
            method=request.method,
            url=str(request.url),
            headers=dict(request.headers),
            client_ip=request.client.host if request.client else None
        )
        
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            "request_completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            duration=duration,
            response_headers={k: v for k, v in response.headers.items()}
        )
        
        # Update Prometheus metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        REQUEST_DURATION.observe(duration)
        
        return response


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


class CORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method == "OPTIONS":
            response = Response()
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            return response
            
        response = await call_next(request)
        
        # Only allow configured origins
        origin = request.headers.get("origin")
        if origin in settings.cors_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response


# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)


def setup_rate_limiting(app):
    """Setup rate limiting for the FastAPI app."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except HTTPException as e:
            logger.warning(
                "http_exception",
                status_code=e.status_code,
                detail=e.detail,
                url=str(request.url),
                method=request.method
            )
            raise
        except Exception as e:
            logger.error(
                "unhandled_exception",
                error=str(e),
                error_type=type(e).__name__,
                url=str(request.url),
                method=request.method,
                exc_info=True
            )
            raise HTTPException(status_code=500, detail="Internal server error")


class RequestSizeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_size = max_size
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            raise HTTPException(status_code=413, detail="Request entity too large")
            
        return await call_next(request)