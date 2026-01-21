"""
Domain Entities - Core business entities with identity and lifecycle.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path as PathlibPath
from datetime import datetime

from ..exceptions import InvalidPathError
from ..value_objects import (
    FilePath,
    FileHash,
    Category,
    FileSize,
    Timestamp,
    OperationMode,
    OrganizationMode,
)


@dataclass
class FileItem:
    """Represents a single file in the system.

    A file item has an identity (path), properties (size, hash), and metadata
    (category, modification time).
    """

    path: FilePath
    size: FileSize
    modified: Timestamp
    category: Optional[Category] = None
    hash: Optional[FileHash] = None

    def __post_init__(self) -> None:
        """Validate entity invariants."""
        if not self.path:
            raise InvalidPathError("FileItem must have a path")

    @classmethod
    def from_path(cls, file_path: str, category: Optional[Category] = None) -> "FileItem":
        """Create FileItem from filesystem path.

        Args:
            file_path: Path to file
            category: Optional category

        Returns:
            FileItem instance
        """
        try:
            path = FilePath(file_path)
            file = PathlibPath(file_path)
            size = FileSize(file.stat().st_size)
            modified = Timestamp(
                datetime.fromtimestamp(file.stat().st_mtime)
            )
            return cls(path=path, size=size, modified=modified, category=category)
        except (OSError, ValueError) as e:
            raise InvalidPathError(f"Cannot create FileItem from {file_path}") from e

    @property
    def name(self) -> str:
        """Get file name with extension."""
        return self.path.resolved.name

    @property
    def stem(self) -> str:
        """Get file name without extension."""
        return self.path.resolved.stem

    @property
    def extension(self) -> str:
        """Get file extension (including dot)."""
        return self.path.resolved.suffix

    def is_duplicate_of(self, other: "FileItem") -> bool:
        """Check if this file is a duplicate of another.

        Files are duplicates if they have the same hash.
        """
        if not self.hash or not other.hash:
            return False
        return self.hash.matches(other.hash)


@dataclass
class FolderItem:
    """Represents a folder/directory in the system."""

    path: FilePath
    name: str
    created: Timestamp
    modified: Timestamp
    file_count: int = 0
    total_size: FileSize = field(default_factory=lambda: FileSize(0))


@dataclass
class ScanResult:
    """Result of directory scanning operation."""

    files: List[FileItem]
    folders: List[FolderItem] = field(default_factory=list)
    total_count: int = 0
    errors: List[str] = field(default_factory=list)
    scanned_at: Timestamp = field(default_factory=Timestamp.now)

    @property
    def total_size(self) -> FileSize:
        """Total size of all files."""
        total_bytes = sum(f.size.bytes for f in self.files)
        return FileSize(total_bytes)

    @property
    def has_errors(self) -> bool:
        """Check if scan encountered errors."""
        return len(self.errors) > 0


@dataclass
class DuplicateGroup:
    """Represents a group of duplicate files (same hash)."""

    hash: FileHash
    files: List[FileItem]
    original: Optional[FileItem] = None  # The "keeper"

    def __post_init__(self) -> None:
        """Validate duplicate group invariants."""
        if len(self.files) < 2:
            raise ValueError("DuplicateGroup must have at least 2 files")
        if not self.original:
            # Assume first file is original if not specified
            object.__setattr__(self, "original", self.files[0])

    @property
    def duplicates(self) -> List[FileItem]:
        """Get the duplicate files (excluding original)."""
        return [f for f in self.files if f != self.original]

    @property
    def total_size(self) -> FileSize:
        """Total size of all duplicates (excluding original)."""
        total_bytes = sum(f.size.bytes for f in self.duplicates)
        return FileSize(total_bytes)


# Import at module level to avoid circular dependency
from datetime import datetime as dt_module


@dataclass
class OrganizationTask:
    """Input parameters for an organization operation.

    Defines what, how, and where to organize files.
    """

    source_path: str
    destination_path: Optional[str] = None
    operation_mode: OperationMode = OperationMode.MOVE
    organization_mode: OrganizationMode = OrganizationMode.CATEGORY_YEAR
    skip_duplicates: bool = True
    create_backup: bool = True
    dry_run: bool = True
    excluded_patterns: List[str] = field(default_factory=list)
    custom_rules: Optional[dict] = None

    def __post_init__(self) -> None:
        """Validate task parameters."""
        if not self.source_path:
            raise InvalidPathError("Source path is required")

        if self.destination_path is None:
            # Default: create "Organized" folder in source
            self.destination_path = str(PathlibPath(self.source_path) / "Organized")

    def validate(self) -> None:
        """Validate all task parameters.

        Raises:
            InvalidPathError: If paths are invalid
            ValueError: If parameters are inconsistent
        """
        FilePath(self.source_path).validate_root(self.source_path)
        FilePath(self.destination_path).validate_root(self.destination_path)


@dataclass
class OperationResult:
    """Result of an organization operation."""

    success: bool
    files_processed: int = 0
    files_organized: int = 0
    duplicates_found: int = 0
    duplicates_grouped: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    completed_at: Timestamp = field(default_factory=Timestamp.now)
    elapsed_seconds: float = 0.0

    @property
    def has_errors(self) -> bool:
        """Check if operation had errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if operation had warnings."""
        return len(self.warnings) > 0
