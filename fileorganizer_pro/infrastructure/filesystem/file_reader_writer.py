"""
Safe file I/O operations.

Provides type-safe, exception-safe file reading and writing.
"""

import hashlib
from pathlib import Path as PathlibPath
from typing import Optional
import shutil

from ...domain.exceptions import (
    FileNotFoundError,
    PermissionError as DomainPermissionError,
    OperationFailedError,
)
from ...domain.value_objects import FileHash
from .path_validator import PathValidator


class FileReader:
    """Safe file reading operations."""

    HASH_ALGORITHMS = {"md5", "sha256", "sha512"}

    @staticmethod
    def read_bytes(path: str, max_size_bytes: int = 1024 * 1024 * 100) -> bytes:
        """Read file as bytes.

        Args:
            path: File path
            max_size_bytes: Maximum file size to read (safety limit)

        Returns:
            File contents as bytes

        Raises:
            FileNotFoundError: If file doesn't exist
            DomainPermissionError: If cannot read file
            OperationFailedError: If read fails
        """
        try:
            file_path = PathlibPath(path)

            if not file_path.exists():
                raise FileNotFoundError(path)

            # Check size
            if file_path.stat().st_size > max_size_bytes:
                raise OperationFailedError(
                    "read",
                    path,
                    "memory",
                    reason="File exceeds maximum size",
                )

            if not PathValidator.check_readable(path):
                raise DomainPermissionError(path, "read")

            with open(file_path, "rb") as f:
                return f.read()

        except (FileNotFoundError, DomainPermissionError):
            raise
        except OSError as e:
            raise OperationFailedError("read", path, "memory") from e

    @staticmethod
    def read_text(
        path: str,
        encoding: str = "utf-8",
        max_lines: Optional[int] = None,
    ) -> str:
        """Read file as text.

        Args:
            path: File path
            encoding: Text encoding (default: utf-8)
            max_lines: Maximum lines to read (None for unlimited)

        Returns:
            File contents as string
        """
        try:
            file_path = PathlibPath(path)
            if not file_path.exists():
                raise FileNotFoundError(path)

            with open(file_path, "r", encoding=encoding) as f:
                if max_lines:
                    lines = [f.readline() for _ in range(max_lines)]
                    return "".join(lines)
                return f.read()

        except FileNotFoundError:
            raise
        except OSError as e:
            raise OperationFailedError("read", path, "memory") from e

    @staticmethod
    def read_lines(path: str, encoding: str = "utf-8") -> list[str]:
        """Read file as list of lines.

        Args:
            path: File path
            encoding: Text encoding (default: utf-8)

        Returns:
            List of lines (without newlines)
        """
        try:
            file_path = PathlibPath(path)
            if not file_path.exists():
                raise FileNotFoundError(path)

            with open(file_path, "r", encoding=encoding) as f:
                return [line.rstrip("\n\r") for line in f.readlines()]

        except FileNotFoundError:
            raise
        except OSError as e:
            raise OperationFailedError("read", path, "memory") from e

    @staticmethod
    def compute_hash(
        path: str,
        algorithm: str = "md5",
        chunk_size: int = 8192,
    ) -> FileHash:
        """Compute file hash.

        Args:
            path: File path
            algorithm: Hash algorithm (md5, sha256, sha512)
            chunk_size: Bytes to read at a time

        Returns:
            FileHash value object

        Raises:
            FileNotFoundError: If file doesn't exist
            DomainPermissionError: If cannot read file
            OperationFailedError: If hashing fails
        """
        if algorithm not in FileReader.HASH_ALGORITHMS:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")

        try:
            file_path = PathlibPath(path)

            if not file_path.exists():
                raise FileNotFoundError(path)

            if not PathValidator.check_readable(path):
                raise DomainPermissionError(path, "read")

            hasher = hashlib.new(algorithm)

            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    hasher.update(chunk)

            return FileHash(digest=hasher.hexdigest(), algorithm=algorithm)

        except (FileNotFoundError, DomainPermissionError):
            raise
        except OSError as e:
            raise OperationFailedError("hash", path, "memory") from e


class FileWriter:
    """Safe file writing operations."""

    @staticmethod
    def write_bytes(path: str, data: bytes, create_backup: bool = False) -> None:
        """Write bytes to file.

        Args:
            path: File path
            data: Bytes to write
            create_backup: Whether to backup existing file first

        Raises:
            DomainPermissionError: If cannot write
            OperationFailedError: If write fails
        """
        try:
            file_path = PathlibPath(path)

            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            if not PathValidator.check_writable(str(file_path.parent)):
                raise DomainPermissionError(str(file_path.parent), "write")

            # Backup existing file if requested
            if create_backup and file_path.exists():
                backup_path = f"{file_path}.backup"
                shutil.copy2(file_path, backup_path)

            with open(file_path, "wb") as f:
                f.write(data)

        except DomainPermissionError:
            raise
        except OSError as e:
            raise OperationFailedError("write", path, "disk") from e

    @staticmethod
    def write_text(
        path: str,
        text: str,
        encoding: str = "utf-8",
        create_backup: bool = False,
    ) -> None:
        """Write text to file.

        Args:
            path: File path
            text: Text to write
            encoding: Text encoding (default: utf-8)
            create_backup: Whether to backup existing file first
        """
        FileWriter.write_bytes(path, text.encode(encoding), create_backup)


class FileOperations:
    """High-level file operations (move, copy, delete)."""

    @staticmethod
    def move(source: str, destination: str) -> None:
        """Move file from source to destination.

        Args:
            source: Source file path
            destination: Destination file path

        Raises:
            OperationFailedError: If move fails
        """
        try:
            source_path = PathlibPath(source)
            dest_path = PathlibPath(destination)

            if not source_path.exists():
                raise FileNotFoundError(source)

            # Create parent directories
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.move(str(source_path), str(dest_path))

        except FileNotFoundError:
            raise
        except OSError as e:
            raise OperationFailedError("move", source, destination) from e

    @staticmethod
    def copy(source: str, destination: str) -> None:
        """Copy file from source to destination.

        Args:
            source: Source file path
            destination: Destination file path

        Raises:
            OperationFailedError: If copy fails
        """
        try:
            source_path = PathlibPath(source)
            dest_path = PathlibPath(destination)

            if not source_path.exists():
                raise FileNotFoundError(source)

            # Create parent directories
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(str(source_path), str(dest_path))

        except FileNotFoundError:
            raise
        except OSError as e:
            raise OperationFailedError("copy", source, destination) from e

    @staticmethod
    def delete(path: str) -> None:
        """Delete a file.

        Args:
            path: File path to delete

        Raises:
            OperationFailedError: If delete fails
        """
        try:
            file_path = PathlibPath(path)

            if file_path.exists():
                file_path.unlink()

        except OSError as e:
            raise OperationFailedError("delete", path, "null") from e
