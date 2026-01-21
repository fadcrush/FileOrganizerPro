"""Async wrappers for Phase 2 services to make them cloud-ready."""

import asyncio
from typing import List, Callable, Optional, Set
from pathlib import Path

from fileorganizer_pro.core.entities import FileItem, Category, ScanResult, DuplicateGroup
from fileorganizer_pro.services.scanning_service import ScanningService as BaseScanningService
from fileorganizer_pro.services.categorization_service import CategorizationService as BaseCategorizationService
from fileorganizer_pro.services.duplicate_service import DuplicateService as BaseDuplicateService


class AsyncScanningService(BaseScanningService):
    """Async wrapper for ScanningService."""
    
    async def scan_async(
        self,
        root_path: str,
        extensions: Optional[Set[str]] = None,
        min_size: int = 0,
        max_size: Optional[int] = None,
        min_date: Optional[float] = None,
        max_date: Optional[float] = None,
        exclude_dirs: Optional[Set[str]] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> ScanResult:
        """Async version of scan() for non-blocking file scanning.
        
        Runs the synchronous scan in a thread pool executor to avoid blocking.
        
        Args:
            root_path: Root directory to scan
            extensions: Extensions to include (e.g., {'.pdf', '.doc'})
            min_size: Minimum file size in bytes
            max_size: Maximum file size in bytes
            min_date: Minimum modification date (Unix timestamp)
            max_date: Maximum modification date (Unix timestamp)
            exclude_dirs: Directories to exclude
            progress_callback: Optional callback for progress updates
            
        Returns:
            ScanResult with files and metadata
        """
        loop = asyncio.get_event_loop()
        
        # Run blocking scan in thread pool
        result = await loop.run_in_executor(
            None,
            self.scan,
            root_path,
            extensions,
            min_size,
            max_size,
            min_date,
            max_date,
            exclude_dirs,
            progress_callback,
        )
        
        return result


class AsyncCategorizationService(BaseCategorizationService):
    """Async wrapper for CategorizationService."""
    
    async def categorize_async(self, file_item: FileItem) -> Category:
        """Async version of categorize().
        
        Args:
            file_item: File to categorize
            
        Returns:
            Category for the file
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.categorize, file_item)
        return result
    
    async def categorize_batch_async(self, files: List[FileItem]) -> dict:
        """Async version of categorize_batch().
        
        Args:
            files: List of files to categorize
            
        Returns:
            Dictionary mapping file paths to categories
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.categorize_batch, files)
        return result


class AsyncDuplicateService(BaseDuplicateService):
    """Async wrapper for DuplicateService."""
    
    async def detect_duplicates_async(
        self,
        files: List[FileItem],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[DuplicateGroup]:
        """Async version of detect_duplicates().
        
        Args:
            files: List of files to check
            progress_callback: Optional progress callback
            
        Returns:
            List of DuplicateGroup objects
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.detect_duplicates,
            files,
            progress_callback,
        )
        return result


# Convenience factory function
def create_async_services():
    """Create instances of all async services.
    
    Returns:
        Tuple of (AsyncScanningService, AsyncCategorizationService, AsyncDuplicateService)
    """
    return (
        AsyncScanningService(),
        AsyncCategorizationService(),
        AsyncDuplicateService(),
    )
