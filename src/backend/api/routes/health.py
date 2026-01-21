"""Health check and status routes."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "FileOrganizer Pro API",
        "version": "1.0.0",
    }


@router.get("/api/v1/status")
def api_status():
    """API status endpoint."""
    return {
        "status": "operational",
        "database": "connected",
        "cache": "connected",
    }
