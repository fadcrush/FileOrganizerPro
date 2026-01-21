"""Domain layer - Core business entities, rules, and logic.

This package contains:
- Entities: FileItem, FolderItem, ScanResult, DuplicateGroup, OrganizationTask, OperationResult
- Value Objects: FilePath, FileHash, Category, FileSize, Timestamp, OperationMode
- Exceptions: DomainException and subclasses
- Events: Domain events (future event sourcing)

Domain layer should be completely independent of infrastructure, UI, and external frameworks.
"""

from .entities import (
    FileItem,
    FolderItem,
    ScanResult,
    DuplicateGroup,
    OrganizationTask,
    OperationResult,
)
from .value_objects import (
    FilePath,
    FileHash,
    Category,
    FileSize,
    Timestamp,
    OperationMode,
    OrganizationMode,
)
from .exceptions import (
    DomainException,
    InvalidPathError,
    PathEscapeError,
    FileNotFoundError,
    PermissionError,
    CategoryNotFoundError,
    OperationFailedError,
    DuplicateDetectionError,
    ConfigurationError,
    ValidationError,
)

__all__ = [
    # Entities
    "FileItem",
    "FolderItem",
    "ScanResult",
    "DuplicateGroup",
    "OrganizationTask",
    "OperationResult",
    # Value Objects
    "FilePath",
    "FileHash",
    "Category",
    "FileSize",
    "Timestamp",
    "OperationMode",
    "OrganizationMode",
    # Exceptions
    "DomainException",
    "InvalidPathError",
    "PathEscapeError",
    "FileNotFoundError",
    "PermissionError",
    "CategoryNotFoundError",
    "OperationFailedError",
    "DuplicateDetectionError",
    "ConfigurationError",
    "ValidationError",
]
