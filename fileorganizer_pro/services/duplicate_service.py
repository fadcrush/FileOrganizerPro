"""Duplicate Detection Service - Identify duplicate files using hashing.

This service handles:
- MD5/SHA256 hashing of files
- Duplicate identification and grouping
- Duplicate statistics and reporting
"""

from typing import Dict, List, Optional
from collections import defaultdict

from ..domain.entities import FileItem, DuplicateGroup
from ..domain.value_objects import FileHash
from ..domain.exceptions import DuplicateDetectionError
from ..infrastructure.filesystem import FileReader
from ..infrastructure.logging import get_logger


logger = get_logger(__name__)


class DuplicateService:
    """Detects duplicate files using cryptographic hashing.
    
    Features:
    - MD5 and SHA256 hash support
    - Efficient duplicate grouping
    - Statistics and reporting
    - Configurable hash algorithm
    """

    def __init__(
        self,
        file_reader: Optional[FileReader] = None,
        hash_algorithm: str = "md5",
    ):
        """Initialize DuplicateService.
        
        Args:
            file_reader: File reading service (created if not provided)
            hash_algorithm: 'md5' or 'sha256' (md5 is faster, sha256 is more secure)
        """
        self.file_reader = file_reader or FileReader()
        if hash_algorithm not in ("md5", "sha256"):
            raise ValueError(f"Unsupported hash algorithm: {hash_algorithm}")
        self.hash_algorithm = hash_algorithm

    def detect_duplicates(
        self,
        files: List[FileItem],
        progress_callback: Optional[callable] = None,
    ) -> List[DuplicateGroup]:
        """Detect duplicates in file list using hashing.
        
        Algorithm:
        1. Hash all files (MD5/SHA256)
        2. Group files by hash value
        3. Return groups with 2+ files (duplicates)
        
        Args:
            files: List of FileItem objects to check
            progress_callback: Called with (current, total) during hashing
            
        Returns:
            List of DuplicateGroup objects (only groups with 2+ files)
            
        Raises:
            DuplicateDetectionError: If detection fails
        """
        try:
            hash_map: Dict[str, List[FileItem]] = defaultdict(list)
            errors = []
            
            logger.info(f"Detecting duplicates in {len(files)} files using {self.hash_algorithm}")
            
            # Hash all files
            for idx, file_item in enumerate(files):
                try:
                    file_hash = self._compute_file_hash(file_item)
                    hash_map[file_hash.digest].append(file_item)
                    
                    if progress_callback:
                        progress_callback(idx + 1, len(files))
                        
                except Exception as e:
                    error_msg = f"Cannot hash {file_item.name}: {e}"
                    errors.append(error_msg)
                    logger.warning(error_msg)
            
            # Group duplicates (only groups with 2+ files)
            duplicate_groups = []
            for hash_digest, file_list in hash_map.items():
                if len(file_list) >= 2:
                    # Recreate FileHash from digest (same algorithm for all in group)
                    file_hash = FileHash(digest=hash_digest, algorithm=self.hash_algorithm)
                    group = DuplicateGroup(
                        hash=file_hash,
                        files=file_list,
                        original=file_list[0],  # First file is the "keeper"
                    )
                    duplicate_groups.append(group)
            
            logger.info(
                f"Found {len(duplicate_groups)} duplicate groups with "
                f"{sum(len(g.files) for g in duplicate_groups)} total duplicate files"
            )
            
            if errors:
                logger.warning(f"Duplicate detection had {len(errors)} errors")
            
            return duplicate_groups
            
        except Exception as e:
            logger.error(f"Duplicate detection failed: {e}", exc_info=True)
            raise DuplicateDetectionError(
                reason=f"Duplicate detection failed: {str(e)}"
            )

    def _compute_file_hash(self, file_item: FileItem) -> FileHash:
        """Compute hash for a single file.
        
        Args:
            file_item: FileItem to hash
            
        Returns:
            FileHash object with computed hash value
        """
        try:
            # FileReader.compute_hash already returns a FileHash object
            return self.file_reader.compute_hash(
                file_item.path.path,
                algorithm=self.hash_algorithm,
            )
        except Exception as e:
            logger.error(f"Failed to hash {file_item.path.path}: {e}")
            raise

    def get_duplicate_statistics(
        self,
        duplicate_groups: List[DuplicateGroup],
    ) -> Dict:
        """Get statistics about detected duplicates.
        
        Args:
            duplicate_groups: List of DuplicateGroup objects
            
        Returns:
            Dictionary with statistics:
            {
                'total_groups': int,
                'total_duplicates': int,
                'total_duplicate_files': int,
                'wasted_space_bytes': int,
                'wasted_space_human': str,
                'largest_group': int,
                'most_common_size': str,
            }
        """
        if not duplicate_groups:
            return {
                'total_groups': 0,
                'total_duplicates': 0,
                'total_duplicate_files': 0,
                'wasted_space_bytes': 0,
                'wasted_space_human': '0 B',
                'largest_group': 0,
                'most_common_size': '0 B',
            }
        
        total_groups = len(duplicate_groups)
        total_duplicate_files = sum(len(g.files) for g in duplicate_groups)
        total_duplicates = sum(len(g.duplicates) for g in duplicate_groups)
        wasted_space = sum(g.total_size.bytes for g in duplicate_groups)
        largest_group = max(len(g.files) for g in duplicate_groups)
        
        # Find most common file size
        size_counts = defaultdict(int)
        for group in duplicate_groups:
            if group.files:
                size_counts[group.files[0].size.bytes] += 1
        most_common_size_bytes = max(size_counts, key=size_counts.get) if size_counts else 0
        
        return {
            'total_groups': total_groups,
            'total_duplicates': total_duplicates,
            'total_duplicate_files': total_duplicate_files,
            'wasted_space_bytes': wasted_space,
            'wasted_space_human': self._format_bytes(wasted_space),
            'largest_group': largest_group,
            'most_common_size': self._format_bytes(most_common_size_bytes),
        }

    def filter_by_size(
        self,
        duplicate_groups: List[DuplicateGroup],
        min_size: int,
        max_size: Optional[int] = None,
    ) -> List[DuplicateGroup]:
        """Filter duplicate groups by file size.
        
        Args:
            duplicate_groups: List of DuplicateGroup objects
            min_size: Minimum file size in bytes
            max_size: Maximum file size in bytes (None = no limit)
            
        Returns:
            Filtered list of DuplicateGroup objects
        """
        filtered = []
        for group in duplicate_groups:
            if group.files:
                size = group.files[0].size.bytes
                if size >= min_size and (max_size is None or size <= max_size):
                    filtered.append(group)
        
        logger.info(f"Filtered to {len(filtered)} groups by size ({min_size}-{max_size} bytes)")
        return filtered

    def filter_by_extension(
        self,
        duplicate_groups: List[DuplicateGroup],
        extensions: List[str],
    ) -> List[DuplicateGroup]:
        """Filter duplicate groups by file extension.
        
        Args:
            duplicate_groups: List of DuplicateGroup objects
            extensions: List of extensions to include (e.g., ['.jpg', '.png'])
            
        Returns:
            Filtered list of DuplicateGroup objects
        """
        extensions_lower = {ext.lower() for ext in extensions}
        filtered = []
        
        for group in duplicate_groups:
            # Check if any file in group matches extension
            if any(file_item.extension.lower() in extensions_lower 
                   for file_item in group.files):
                filtered.append(group)
        
        logger.info(f"Filtered to {len(filtered)} groups by extension {extensions}")
        return filtered

    @staticmethod
    def _format_bytes(bytes_value: int) -> str:
        """Format byte value as human-readable string.
        
        Args:
            bytes_value: Number of bytes
            
        Returns:
            Formatted string (e.g., '1.5 MB')
        """
        for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
            if bytes_value < 1024:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024
        return f"{bytes_value:.1f} PB"
