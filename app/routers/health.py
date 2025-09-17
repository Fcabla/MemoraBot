"""Health check endpoints."""

from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    environment: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic health check endpoint."""
    from app import __version__

    return HealthResponse(
        status="healthy",
        version=__version__,
        environment=settings.APP_ENV
    )


@router.get("/ready")
async def readiness_check() -> dict:
    """Readiness check for deployment."""
    # Check critical dependencies
    checks = {
        "database": True,  # Placeholder for future DB check
        "llm_configured": bool(
            settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY
        ),
        "data_directory": Path(settings.DATA_DIR).exists(),
    }

    all_ready = all(checks.values())

    return {
        "ready": all_ready,
        "checks": checks
    }