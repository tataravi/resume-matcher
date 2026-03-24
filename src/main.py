import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
import structlog

from src.config import settings
from src.api import (
    analysis_router,
    upload_router, 
    websocket_router,
    health_router,
    auth_router,
    LoggingMiddleware,
    SecurityMiddleware,
    ErrorHandlingMiddleware,
    RequestSizeMiddleware,
    setup_rate_limiting
)


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI agent-based resume analyzer with FastAPI",
        debug=settings.debug,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )
    
    # Add middleware
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(RequestSizeMiddleware, max_size=10 * 1024 * 1024)  # 10MB
    app.add_middleware(SecurityMiddleware)
    app.add_middleware(LoggingMiddleware)
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Setup rate limiting
    setup_rate_limiting(app)
    
    # Add root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "message": "Resume Analyzer API",
            "version": settings.app_version,
            "status": "running",
            "docs": "/docs",
            "health": "/health/",
            "auth": "/auth/",
            "api": {
                "analysis": "/api/v1/analysis/",
                "upload": "/api/v1/upload/",
                "websocket": "/api/v1/ws"
            }
        }
    
    # Include routers
    app.include_router(health_router, prefix="/health")
    app.include_router(auth_router, prefix="/auth")
    app.include_router(analysis_router, prefix="/api/v1/analysis")
    app.include_router(upload_router, prefix="/api/v1/upload")
    app.include_router(websocket_router, prefix="/api/v1")
    
    # Add Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    
    @app.on_event("startup")
    async def startup_event():
        """Application startup event."""
        logger = structlog.get_logger()
        logger.info(
            "application_starting",
            app_name=settings.app_name,
            version=settings.app_version,
            debug=settings.debug,
            host=settings.api_host,
            port=settings.api_port
        )
        
        # Initialize services here
        # await initialize_database()
        # await initialize_redis()
        # await start_agents()
        
    @app.on_event("shutdown")
    async def shutdown_event():
        """Application shutdown event."""
        logger = structlog.get_logger()
        logger.info("application_shutting_down")
        
        # Cleanup services here
        # await stop_agents()
        # await close_database_connections()
        # await close_redis_connections()
    
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers if not settings.debug else 1,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True
    )