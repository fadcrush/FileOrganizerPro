"""
Domain Value Objects - Immutable, self-validating value objects.

These represent core business concepts that must be validated and safe to share.
"""

from dataclasses import dataclass, field
from pathlib import Path as PathlibPath
from enum import Enum
from typing import Optional
from datetime import datetime

from ..exceptions import InvalidPathError


class OperationMode(Enum):
    """File operation mode: move or copy."""

    MOVE = "move"  # Remove file from source after operation
    COPY = "copy"  # Keep file in source

    def __str__(self) -> str:
        return self.value


class OrganizationMode(Enum):
    """Organization path structure."""

    CATEGORY_ONLY = "category"  # Documents/, Images/, etc.
    YEAR_ONLY = "year"  # 2025/, 2024/, etc.
    CATEGORY_YEAR = "category_year"  # Documents/2025/, Images/2024/, etc.

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class FilePath:
    """Safe, normalized file path value object.

    Ensures paths are:
    - Absolute and resolved
    - No directory traversal escapes
    - Properly normalized (no double slashes, etc.)
    - Cross-platform compatible
    """

    path: str
    _resolved: Optional[PathlibPath] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        """Validate and normalize path after construction."""
        if not self.path:
            raise InvalidPathError("Path cannot be empty")

        try:
            # Resolve to absolute path
            resolved = PathlibPath(self.path).resolve()
            object.__setattr__(self, "_resolved", resolved)
        except (OSError, ValueError) as e:
            raise InvalidPathError(f"Invalid path: {self.path}", path=self.path)

    @property
    def resolved(self) -> PathlibPath:
        """Get the resolved Path object."""
        if self._resolved is None:
            raise InvalidPathError("Path not resolved", path=self.path)
        return self._resolved

    def validate_root(self, root: str) -> bool:
        """Check if this path is within root directory.

        Args:
            root: The root directory path

        Returns:
            True if path is within root, False otherwise

        Raises:
            InvalidPathError: If path escapes root
        """
        try:
            root_path = PathlibPath(root).resolve()
            # This raises ValueError if path is outside root
            self.resolved.relative_to(root_path)
            return True
        except ValueError:
            raise InvalidPathError(
                f"Path escapes root directory: {self.path} (root: {root})",
                path=self.path,
            )

    def __str__(self) -> str:
        return str(self.resolved)

    def __truediv__(self, other: str) -> "FilePath":
        """Support path joining: file_path / "subfolder" / "file.txt"."""
        new_path = str(self.resolved / other)
        return FilePath(new_path)


@dataclass(frozen=True)
class FileHash:
    """Immutable file hash value object.

    Supports multiple hash algorithms (MD5, SHA256, etc.).
    """

    digest: str  # The hex digest
    algorithm: str = "md5"  # Default algorithm

    def __post_init__(self) -> None:
        """Validate hash format."""
        if not self.digest:
            raise ValueError("Hash digest cannot be empty")
        if not self.digest.isalnum():
            raise ValueError(f"Invalid hash format: {self.digest}")

    def __str__(self) -> str:
        return f"{self.algorithm}:{self.digest}"

    def matches(self, other: "FileHash") -> bool:
        """Check if two hashes match (comparing digest only)."""
        return (
            self.algorithm == other.algorithm
            and self.digest.lower() == other.digest.lower()
        )


@dataclass(frozen=True)
class Category:
    """File category value object.

    Represents a file type grouping (Documents, Images, Code, etc.).
    """

    name: str

    BUILTIN_CATEGORIES = {
        "Documents",
        "Images",
        "Videos",
        "Audio",
        "Code",
        "Archives",
        "Spreadsheets",
        "Presentations",
        "Executables",
        "Fonts",
        "Others",
    }

    def __post_init__(self) -> None:
        """Validate category name."""
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Category name must be a non-empty string")

    @property
    def is_builtin(self) -> bool:
        """Check if this is a built-in category."""
        return self.name in self.BUILTIN_CATEGORIES

    def __str__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.name.lower())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Category):
            return NotImplemented
        return self.name.lower() == other.name.lower()


@dataclass(frozen=True)
class FileSize:
    """File size value object with formatting.

    Represents file size in bytes with convenience methods for display.
    """

    bytes: int

    def __post_init__(self) -> None:
        """Validate size is non-negative."""
        if self.bytes < 0:
            raise ValueError("File size cannot be negative")

    @property
    def kilobytes(self) -> float:
        """Size in kilobytes."""
        return self.bytes / 1024

    @property
    def megabytes(self) -> float:
        """Size in megabytes."""
        return self.bytes / (1024 * 1024)

    @property
    def gigabytes(self) -> float:
        """Size in gigabytes."""
        return self.bytes / (1024 * 1024 * 1024)

    def formatted(self, precision: int = 2) -> str:
        """Get human-readable size string.

        Args:
            precision: Decimal places for output

        Returns:
            Formatted string (e.g., "1.50 MB")
        """
        for unit, divisor in [
            ("GB", 1024 ** 3),
            ("MB", 1024 ** 2),
            ("KB", 1024),
            ("B", 1),
        ]:
            size = self.bytes / divisor
            if size >= 1 or unit == "B":
                return f"{size:.{precision}f} {unit}"
        return f"{self.bytes} B"

    def __str__(self) -> str:
        return self.formatted()


@dataclass(frozen=True)
class Timestamp:
    """Timestamp value object with timezone support."""

    dt: datetime

    @classmethod
    def now(cls) -> "Timestamp":
        """Create timestamp for current time."""
        return cls(datetime.now())

    @classmethod
    def from_string(cls, iso_string: str) -> "Timestamp":
        """Parse ISO format timestamp string."""
        try:
            dt = datetime.fromisoformat(iso_string)
            return cls(dt)
        except ValueError as e:
            raise ValueError(f"Invalid timestamp format: {iso_string}") from e

    def __str__(self) -> str:
        return self.dt.isoformat()

    def formatted(self, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format timestamp as string.

        Args:
            fmt: strftime format string

        Returns:
            Formatted timestamp string
        """
        return self.dt.strftime(fmt)
