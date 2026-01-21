"""Infrastructure layer - Adapters to external systems.

This layer provides:
- Filesystem operations (path validation, safe I/O)
- Persistence (repository pattern, database)
- Configuration management
- Structured logging
- OS integration (platform-specific features)

These implementations are swappable and testable.
"""

from . import filesystem
from . import logging

__all__ = [
    "filesystem",
    "logging",
]
