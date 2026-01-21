"""API routes for FileOrganizer Pro."""

from .auth import router as auth_router
from .health import router as health_router
from .operations import router as operations_router

__all__ = [
    "auth_router",
    "health_router",
    "operations_router",
]
