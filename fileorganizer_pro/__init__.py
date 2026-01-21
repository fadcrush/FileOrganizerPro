"""
FileOrganizer Pro - Modular Architecture
Main package root with version and imports.
"""

__version__ = "4.0.0-alpha"
__author__ = "David - JSMS Academy"
__license__ = "Proprietary"

# Version tuple for comparisons
VERSION_INFO = (4, 0, 0, "alpha")

# Conditional exports - only expose public API
__all__ = [
    "FileOrganizer",
    "OrganizationTask",
    "OperationResult",
]

try:
    from .services import FileOrganizer  # Main facade
    from .domain.entities import OrganizationTask, OperationResult
except ImportError as e:
    raise RuntimeError(
        f"Failed to import FileOrganizer Pro modules: {e}\n"
        "Ensure all dependencies are installed: pip install -r requirements.txt"
    )
