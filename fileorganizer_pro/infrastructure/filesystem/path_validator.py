"""
Path safety and validation utilities.

Ensures all paths are:
- Absolute and normalized
- Cannot escape the root directory (prevents directory traversal)
- Cross-platform compatible
"""

from pathlib import Path as PathlibPath
from typing import Optional
import os

from ...domain.exceptions import InvalidPathError, PathEscapeError, PermissionError


class PathValidator:
    """Validates and normalizes file paths safely."""

    @staticmethod
    def normalize(path: str) -> str:
        """Normalize a path (resolve, remove duplicates, etc.).

        Args:
            path: Path string to normalize

        Returns:
            Normalized absolute path

        Raises:
            InvalidPathError: If path is invalid
        """
        try:
            normalized = PathlibPath(path).resolve()
            return str(normalized)
        except (OSError, ValueError) as e:
            raise InvalidPathError(f"Cannot normalize path: {path}") from e

    @staticmethod
    def validate_root_confinement(path: str, root: str) -> None:
        """Ensure path stays within root directory.

        This prevents directory traversal attacks like '../../etc/passwd'.

        Args:
            path: The path to validate
            root: The root directory (jail)

        Raises:
            PathEscapeError: If path escapes root
            InvalidPathError: If paths cannot be resolved
        """
        try:
            path_resolved = PathlibPath(path).resolve()
            root_resolved = PathlibPath(root).resolve()

            # Ensure path is under root
            path_resolved.relative_to(root_resolved)
        except ValueError:
            raise PathEscapeError(path, root)
        except (OSError, RuntimeError) as e:
            raise InvalidPathError(f"Cannot validate path confinement: {path}") from e

    @staticmethod
    def check_file_exists(path: str) -> bool:
        """Check if file exists.

        Args:
            path: Path to check

        Returns:
            True if file exists, False otherwise
        """
        try:
            return PathlibPath(path).is_file()
        except (OSError, ValueError):
            return False

    @staticmethod
    def check_directory_exists(path: str) -> bool:
        """Check if directory exists.

        Args:
            path: Path to check

        Returns:
            True if directory exists, False otherwise
        """
        try:
            return PathlibPath(path).is_dir()
        except (OSError, ValueError):
            return False

    @staticmethod
    def get_parent(path: str) -> str:
        """Get parent directory of path.

        Args:
            path: File or folder path

        Returns:
            Parent directory path
        """
        return str(PathlibPath(path).parent)

    @staticmethod
    def get_filename(path: str) -> str:
        """Get filename from path.

        Args:
            path: File path

        Returns:
            Filename with extension
        """
        return PathlibPath(path).name

    @staticmethod
    def get_stem(path: str) -> str:
        """Get filename without extension.

        Args:
            path: File path

        Returns:
            Filename without extension
        """
        return PathlibPath(path).stem

    @staticmethod
    def get_extension(path: str) -> str:
        """Get file extension (including dot).

        Args:
            path: File path

        Returns:
            Extension (e.g., '.pdf') or empty string
        """
        return PathlibPath(path).suffix.lower()

    @staticmethod
    def join(base: str, *parts: str) -> str:
        """Safely join path components.

        Args:
            base: Base path
            *parts: Path components to join

        Returns:
            Joined path

        Raises:
            InvalidPathError: If joined path is invalid
        """
        try:
            result = PathlibPath(base)
            for part in parts:
                # Prevent empty parts and relative traversal
                if not part or part in (".", "..", ""):
                    continue
                result = result / part
            return str(result.resolve())
        except (OSError, ValueError) as e:
            raise InvalidPathError(f"Cannot join paths: {base} + {parts}") from e

    @staticmethod
    def check_readable(path: str) -> bool:
        """Check if path is readable.

        Args:
            path: Path to check

        Returns:
            True if readable, False otherwise
        """
        return os.access(path, os.R_OK)

    @staticmethod
    def check_writable(path: str) -> bool:
        """Check if path is writable.

        Args:
            path: Path to check

        Returns:
            True if writable, False otherwise
        """
        # Check write permission on the file if it exists, or parent directory
        path_obj = PathlibPath(path)
        if path_obj.exists():
            return os.access(path, os.W_OK)
        else:
            return os.access(path_obj.parent, os.W_OK)

    @staticmethod
    def ensure_directory(path: str) -> str:
        """Ensure directory exists, create if needed.

        Args:
            path: Directory path

        Returns:
            Normalized path

        Raises:
            PermissionError: If cannot create directory
            InvalidPathError: If path is invalid
        """
        try:
            path_obj = PathlibPath(path)
            path_obj.mkdir(parents=True, exist_ok=True)
            return str(path_obj.resolve())
        except PermissionError as e:
            raise PermissionError(path, "create") from e
        except OSError as e:
            raise InvalidPathError(f"Cannot create directory: {path}") from e
