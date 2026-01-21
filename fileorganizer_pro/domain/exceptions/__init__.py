"""
Domain Exceptions - Custom exception hierarchy for domain errors.

These exceptions are raised by services and should be handled gracefully
by presentation layers (UI, API, CLI).
"""

from typing import Optional


class DomainException(Exception):
    """Base exception for all domain-level errors."""

    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        """Initialize domain exception.

        Args:
            message: Human-readable error message
            code: Machine-readable error code (e.g., "INVALID_PATH")
        """
        super().__init__(message)
        self.message = message
        self.code = code

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


class InvalidPathError(DomainException):
    """Raised when a path is invalid or unsafe."""

    def __init__(self, message: str, path: Optional[str] = None):
        """Initialize path error.

        Args:
            message: Error description
            path: The problematic path (optional)
        """
        super().__init__(message, code="INVALID_PATH")
        self.path = path


class PathEscapeError(InvalidPathError):
    """Raised when a path attempts to escape the root directory."""

    def __init__(self, path: str, root: str):
        """Initialize path escape error.

        Args:
            path: The path attempting to escape
            root: The root directory that was escaped
        """
        message = f"Path '{path}' attempts to escape root directory '{root}'"
        super().__init__(message, path=path)
        self.root = root
        self.code = "PATH_ESCAPE_DETECTED"


class FileNotFoundError(DomainException):
    """Raised when a required file is not found."""

    def __init__(self, path: str):
        """Initialize file not found error.

        Args:
            path: The missing file path
        """
        super().__init__(f"File not found: {path}", code="FILE_NOT_FOUND")
        self.path = path


class PermissionError(DomainException):
    """Raised when access to a file/folder is denied."""

    def __init__(self, path: str, operation: str = "access"):
        """Initialize permission error.

        Args:
            path: The protected file/folder
            operation: The operation that was denied (read, write, execute)
        """
        message = f"Permission denied to {operation} '{path}'"
        super().__init__(message, code="PERMISSION_DENIED")
        self.path = path
        self.operation = operation


class CategoryNotFoundError(DomainException):
    """Raised when a category cannot be determined."""

    def __init__(self, file_path: str, reason: str = "unknown"):
        """Initialize category not found error.

        Args:
            file_path: The file that couldn't be categorized
            reason: Why categorization failed
        """
        message = f"Cannot categorize '{file_path}': {reason}"
        super().__init__(message, code="CATEGORY_NOT_FOUND")
        self.file_path = file_path
        self.reason = reason


class OperationFailedError(DomainException):
    """Raised when a file operation (move/copy) fails."""

    def __init__(
        self,
        operation: str,
        source: str,
        destination: str,
        reason: Optional[str] = None,
    ):
        """Initialize operation failed error.

        Args:
            operation: 'move' or 'copy'
            source: Source file path
            destination: Destination file path
            reason: Why the operation failed (optional)
        """
        message = f"Failed to {operation} '{source}' → '{destination}'"
        if reason:
            message += f": {reason}"
        super().__init__(message, code="OPERATION_FAILED")
        self.operation = operation
        self.source = source
        self.destination = destination
        self.reason = reason


class DuplicateDetectionError(DomainException):
    """Raised when duplicate detection fails."""

    def __init__(self, file_path: str, reason: str = "hash calculation failed"):
        """Initialize duplicate detection error.

        Args:
            file_path: The file causing the error
            reason: Why detection failed
        """
        message = f"Could not detect duplicates for '{file_path}': {reason}"
        super().__init__(message, code="DUPLICATE_DETECTION_ERROR")
        self.file_path = file_path
        self.reason = reason


class ConfigurationError(DomainException):
    """Raised when configuration is invalid."""

    def __init__(self, message: str, key: Optional[str] = None):
        """Initialize configuration error.

        Args:
            message: Error description
            key: The configuration key that caused the error (optional)
        """
        super().__init__(message, code="CONFIG_ERROR")
        self.key = key


class ValidationError(DomainException):
    """Raised when input validation fails."""

    def __init__(
        self, message: str, field: Optional[str] = None, value: Optional[str] = None
    ):
        """Initialize validation error.

        Args:
            message: Error description
            field: The field that failed validation (optional)
            value: The invalid value (optional)
        """
        super().__init__(message, code="VALIDATION_ERROR")
        self.field = field
        self.value = value
