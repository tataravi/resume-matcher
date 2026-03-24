from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime
import sys
import psutil
import asyncio

from src.config import settings


router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    environment: str
    services: dict
    system: dict


class ServiceStatus(BaseModel):
    status: str
    response_time_ms: float
    last_check: datetime


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint."""
    
    # Check system metrics
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    system_info = {
        "cpu_usage_percent": cpu_percent,
        "memory_usage_percent": memory.percent,
        "memory_available_gb": round(memory.available / (1024**3), 2),
        "disk_usage_percent": disk.percent,
        "disk_free_gb": round(disk.free / (1024**3), 2),
        "python_version": sys.version,
        "uptime": "N/A"  # Would be calculated from app start time
    }
    
    # Mock service checks (in real implementation, check actual services)
    services = {
        "database": {"status": "healthy", "response_time_ms": 5.2},
        "redis": {"status": "healthy", "response_time_ms": 1.8},
        "deepseek_api": {"status": "healthy", "response_time_ms": 150.0},
        "aws_s3": {"status": "healthy", "response_time_ms": 45.0},
        "aws_dynamodb": {"status": "healthy", "response_time_ms": 25.0}
    }
    
    # Determine overall status
    overall_status = "healthy"
    for service_status in services.values():
        if service_status["status"] != "healthy":
            overall_status = "degraded"
            break
            
    if cpu_percent > 90 or memory.percent > 90:
        overall_status = "warning"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        environment="development" if settings.debug else "production",
        services=services,
        system=system_info
    )


@router.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe endpoint."""
    # Check if all critical services are available
    try:
        # In real implementation, check database connection, etc.
        await asyncio.sleep(0.1)  # Simulate quick checks
        return {"status": "ready", "timestamp": datetime.utcnow()}
    except Exception as e:
        return {"status": "not_ready", "error": str(e), "timestamp": datetime.utcnow()}


@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe endpoint."""
    return {"status": "alive", "timestamp": datetime.utcnow()}