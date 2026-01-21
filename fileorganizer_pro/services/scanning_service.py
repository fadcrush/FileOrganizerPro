"""Scanning Service - Recursive directory traversal and file collection.

This service handles:
- Recursive directory scanning
- File filtering (by extension, size, date)
- Progress tracking and cancellation
- Safe path handling with validation
- Error handling and recovery
"""

import os
from pathlib import Path
from typing import Callable, List, Optional, Set
from datetime import datetime

from ..domain.entities import FileItem, FolderItem, ScanResult
from ..domain.value_objects import FilePath, FileSize, Timestamp
from ..domain.exceptions import InvalidPathError, OperationFailedError
from ..infrastructure.filesystem import PathValidator, FileReader
from ..infrastructure.logging import get_logger


logger = get_logger(__name__)


class ScanningService:
    """Scans directories recursively and creates FileItem entities.
    
    Features:
    - Recursive directory traversal with symlink safety
    - File filtering by extension, size, date
    - Progress tracking via callback
    - Cancellation support
    - Error tracking (skipped files, access denied, etc.)
    - Memory-efficient (yields results incrementally)
    """

    def __init__(
        self,
        path_validator: Optional[PathValidator] = None,
        file_reader: Optional[FileReader] = None,
    ):
        """Initialize ScanningService.
        
        Args:
            path_validator: Path validation service (created if not provided)
            file_reader: File reading service (created if not provided)
        """
        self.path_validator = path_validator or PathValidator()
        self.file_reader = file_reader or FileReader()
        self._cancelled = False

    def scan(
        self,
        root_path: str,
        extensions: Optional[Set[str]] = None,
        min_size: int = 0,
        max_size: Optional[int] = None,
        min_date: Optional[datetime] = None,
        max_date: Optional[datetime] = None,
        exclude_dirs: Optional[Set[str]] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> ScanResult:
        """Scan directory tree and collect files.
        
        Args:
            root_path: Root directory to scan
            extensions: File extensions to include (e.g., {'.pdf', '.txt'}).
                       If None, includes all files.
            min_size: Minimum file size in bytes (default 0)
            max_size: Maximum file size in bytes (None = no limit)
            min_date: Minimum modification date
            max_date: Maximum modification date
            exclude_dirs: Directory names to skip (e.g., {'.git', '__pycache__'})
            progress_callback: Called with (count, path) during scanning
            
        Returns:
            ScanResult with collected files, folders, and error tracking
            
        Raises:
            InvalidPathError: If root_path is invalid or escapes confinement
            OperationFailedError: If scan fails unexpectedly
        """
        self._cancelled = False
        
        try:
            # Validate root path
            root = FilePath(root_path)
            self.path_validator.validate_root_confinement(root.path, root.path)
            
            files: List[FileItem] = []
            folders: List[FolderItem] = []
            errors: List[str] = []
            skipped_count = 0
            
            exclude_dirs = exclude_dirs or {'.git', '__pycache__', '.venv', 'node_modules'}
            
            logger.info(f"Starting scan of: {root.path}")
            
            # Walk directory tree
            for dir_path, dir_names, file_names in os.walk(root.path):
                if self._cancelled:
                    logger.info("Scan cancelled by user")
                    break
                
                try:
                    # Filter out excluded directories
                    dir_names[:] = [d for d in dir_names if d not in exclude_dirs]
                    
                    # Create FolderItem for current directory
                    folder_path = FilePath(dir_path)
                    folder_stat = Path(dir_path).stat()
                    folder_item = FolderItem(
                        path=folder_path,
                        name=Path(dir_path).name,
                        created=Timestamp(datetime.fromtimestamp(folder_stat.st_ctime)),
                        modified=Timestamp(datetime.fromtimestamp(folder_stat.st_mtime)),
                        file_count=len(file_names),
                    )
                    folders.append(folder_item)
                    
                    # Process files in current directory
                    for file_name in file_names:
                        if self._cancelled:
                            break
                        
                        file_path = FilePath(os.path.join(dir_path, file_name))
                        
                        # Check if file meets filters
                        if not self._should_include_file(
                            file_path, extensions, min_size, max_size, min_date, max_date
                        ):
                            skipped_count += 1
                            continue
                        
                        try:
                            # Create FileItem
                            stat_info = Path(file_path.path).stat()
                            file_item = FileItem(
                                path=file_path,
                                size=FileSize(stat_info.st_size),
                                modified=Timestamp(
                                    datetime.fromtimestamp(stat_info.st_mtime)
                                ),
                            )
                            files.append(file_item)
                            
                            # Progress callback
                            if progress_callback:
                                progress_callback(len(files), file_path.path)
                                
                        except (PermissionError, OSError) as e:
                            error_msg = f"Cannot read: {file_path.path} ({e})"
                            errors.append(error_msg)
                            logger.warning(error_msg)
                            
                except (PermissionError, OSError) as e:
                    error_msg = f"Cannot access directory: {dir_path} ({e})"
                    errors.append(error_msg)
                    logger.warning(error_msg)
                    continue
            
            result = ScanResult(
                files=files,
                folders=folders,
                total_count=len(files),
                errors=errors,
            )
            
            logger.info(
                f"Scan complete: {result.total_count} files, "
                f"{skipped_count} skipped, {len(errors)} errors"
            )
            
            return result
            
        except InvalidPathError as e:
            logger.error(f"Invalid path: {e}")
            raise
        except Exception as e:
            logger.error(f"Scan failed: {e}", exc_info=True)
            raise OperationFailedError(
                source=root_path,
                destination=root_path,
            )

    def cancel(self) -> None:
        """Cancel ongoing scan."""
        self._cancelled = True
        logger.info("Scan cancellation requested")

    def _should_include_file(
        self,
        file_path: FilePath,
        extensions: Optional[Set[str]],
        min_size: int,
        max_size: Optional[int],
        min_date: Optional[datetime],
        max_date: Optional[datetime],
    ) -> bool:
        """Check if file matches filter criteria.
        
        Args:
            file_path: File path to check
            extensions: Set of extensions to include (None = include all)
            min_size: Minimum size in bytes
            max_size: Maximum size in bytes
            min_date: Minimum modification date
            max_date: Maximum modification date
            
        Returns:
            True if file should be included, False otherwise
        """
        try:
            # Extension filter
            if extensions:
                file_ext = Path(file_path.path).suffix.lower()
                if file_ext not in extensions:
                    return False
            
            # Size filter
            stat_info = Path(file_path.path).stat()
            size = stat_info.st_size
            
            if size < min_size:
                return False
            if max_size and size > max_size:
                return False
            
            # Date filter
            if min_date or max_date:
                mtime = datetime.fromtimestamp(stat_info.st_mtime)
                if min_date and mtime < min_date:
                    return False
                if max_date and mtime > max_date:
                    return False
            
            return True
            
        except (OSError, PermissionError):
            return False
