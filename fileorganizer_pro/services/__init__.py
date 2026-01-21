"""Services layer - Business logic and orchestration.

Services coordinate domain entities, infrastructure adapters, and enforce business rules.
Services are independent of UI and can be used by any presentation layer (GUI, API, CLI).
"""

from typing import Optional, Dict, Callable
from datetime import datetime

from ..domain import (
    OrganizationTask,
    OperationResult,
    FileItem,
    ScanResult,
    DomainException,
)
from ..infrastructure.filesystem import PathValidator, FileReader, FileOperations
from ..infrastructure.logging import get_logger
from .scanning_service import ScanningService
from .categorization_service import CategorizationService
from .duplicate_service import DuplicateService


logger = get_logger(__name__)


class FileOrganizer:
    """Main orchestrator for file organization operations.

    This is the primary service for the application - it coordinates:
    - File scanning and indexing (ScanningService)
    - Categorization (CategorizationService)
    - Duplicate detection (DuplicateService)
    - File movement/copying (FileOperations)
    - Report generation
    
    Workflow:
    1. Scan root directory with ScanningService
    2. Categorize all files with CategorizationService
    3. Detect duplicates with DuplicateService
    4. Execute move/copy/organize with FileOperations
    5. Generate report with statistics
    """

    def __init__(
        self,
        scanning_service: Optional[ScanningService] = None,
        categorization_service: Optional[CategorizationService] = None,
        duplicate_service: Optional[DuplicateService] = None,
        path_validator: Optional[PathValidator] = None,
    ):
        """Initialize the FileOrganizer service.
        
        Args:
            scanning_service: ScanningService instance (created if not provided)
            categorization_service: CategorizationService instance (created if not provided)
            duplicate_service: DuplicateService instance (created if not provided)
            path_validator: PathValidator instance (created if not provided)
        """
        self.scanning_service = scanning_service or ScanningService()
        self.categorization_service = categorization_service or CategorizationService()
        self.duplicate_service = duplicate_service or DuplicateService()
        self.path_validator = path_validator or PathValidator()
        self.file_operations = FileOperations()

    def organize(
        self,
        task: OrganizationTask,
        progress_callback: Optional[Callable[[str, int, str], None]] = None,
    ) -> OperationResult:
        """Execute file organization operation.

        Workflow:
        1. Validate input parameters
        2. Scan directory tree
        3. Categorize all files
        4. Detect duplicates (if enabled)
        5. Execute move/copy operations
        6. Generate report

        Args:
            task: OrganizationTask with parameters
            progress_callback: Called with (stage, current, total) during execution

        Returns:
            OperationResult with statistics and status

        Raises:
            DomainException: If operation fails
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting organization task: {task.root_path}")
            
            # Stage 1: Scan directory
            if progress_callback:
                progress_callback("Scanning", 0, 0)
            
            scan_result = self.scanning_service.scan(
                root_path=task.root_path,
                extensions=task.extensions,
                exclude_dirs=task.exclude_dirs,
                progress_callback=lambda count, path: (
                    progress_callback("Scanning", count, 0) if progress_callback else None
                ),
            )
            
            logger.info(f"Scan complete: {scan_result.total_count} files")
            
            # Stage 2: Categorize files
            if progress_callback:
                progress_callback("Categorizing", 0, scan_result.total_count)
            
            categorization_map = self.categorization_service.categorize_batch(
                scan_result.files
            )
            
            logger.info("Categorization complete")
            
            # Stage 3: Detect duplicates (if enabled)
            duplicate_groups = []
            if task.detect_duplicates:
                if progress_callback:
                    progress_callback("Detecting Duplicates", 0, scan_result.total_count)
                
                duplicate_groups = self.duplicate_service.detect_duplicates(
                    scan_result.files,
                    progress_callback=lambda curr, total: (
                        progress_callback("Detecting Duplicates", curr, total)
                        if progress_callback else None
                    ),
                )
                
                logger.info(f"Found {len(duplicate_groups)} duplicate groups")
            
            # Stage 4: Execute operations (dry run or actual)
            moved_count = 0
            copied_count = 0
            skipped_count = 0
            failed_files = []
            
            if not task.dry_run:
                if progress_callback:
                    progress_callback("Organizing", 0, scan_result.total_count)
                
                # TODO: Execute actual move/copy operations
                # This will be implemented in Phase 3 with proper file operations
                logger.info("File operations execution (Phase 3)")
            
            # Calculate operation time
            operation_time = datetime.now() - start_time
            
            result = OperationResult(
                success=True,
                root_path=scan_result.root_path,
                total_files_processed=scan_result.total_count,
                files_moved=moved_count,
                files_copied=copied_count,
                files_skipped=skipped_count,
                duplicate_groups=duplicate_groups,
                errors=scan_result.errors + failed_files,
                execution_time=operation_time.total_seconds(),
                timestamp=start_time,
            )
            
            logger.info(f"Organization complete in {operation_time.total_seconds():.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Organization failed: {e}", exc_info=True)
            raise DomainException(
                code="ORG_FAILED",
                message=f"File organization failed: {str(e)}",
            )

    def cancel_scan(self) -> None:
        """Cancel ongoing scan operation."""
        self.scanning_service.cancel()
        logger.info("Scan cancellation requested")
        start_time = datetime.now()
        result = OperationResult(success=False)

        try:
            # Validate task
            task.validate()

            # TODO: Implement workflow:
            # 1. Create backup (if enabled)
            # 2. Scan source directory
            # 3. Categorize files
            # 4. Detect duplicates
            # 5. Move/copy files
            # 6. Generate reports
            # 7. Fire completion event

            result.success = True

        except DomainException as e:
            result.errors.append(str(e))
            result.success = False
        except Exception as e:
            result.errors.append(f"Unexpected error: {e}")
            result.success = False
        finally:
            result.elapsed_seconds = (datetime.now() - start_time).total_seconds()

        return result


__all__ = [
    "FileOrganizer",
]
