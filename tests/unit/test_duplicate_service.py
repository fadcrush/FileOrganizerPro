"""Unit tests for DuplicateService.

Tests cover:
- Duplicate detection using MD5/SHA256
- Duplicate grouping
- Statistics calculation
- Filtering by size and extension
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

from fileorganizer_pro.services.duplicate_service import DuplicateService
from fileorganizer_pro.domain.entities import FileItem
from fileorganizer_pro.domain.value_objects import FilePath, FileSize, Timestamp
from fileorganizer_pro.infrastructure.filesystem import FileReader


class TestDuplicateService:
    """Tests for DuplicateService."""

    @pytest.fixture
    def duplicate_service(self):
        """Create DuplicateService instance."""
        return DuplicateService(hash_algorithm="md5")

    @pytest.fixture
    def sample_file_items(self):
        """Create sample FileItem objects for testing."""
        return [
            FileItem(
                path=FilePath("/path/to/file1.txt"),
                name="file1.txt",
                size=FileSize(1024),
                created_at=Timestamp(datetime.now()),
                modified_at=Timestamp(datetime.now()),
                extension=".txt",
            ),
            FileItem(
                path=FilePath("/path/to/file2.txt"),
                name="file2.txt",
                size=FileSize(1024),
                created_at=Timestamp(datetime.now()),
                modified_at=Timestamp(datetime.now()),
                extension=".txt",
            ),
            FileItem(
                path=FilePath("/path/to/unique.txt"),
                name="unique.txt",
                size=FileSize(2048),
                created_at=Timestamp(datetime.now()),
                modified_at=Timestamp(datetime.now()),
                extension=".txt",
            ),
        ]

    def test_hash_algorithm_validation(self):
        """Test that invalid hash algorithm raises error."""
        with pytest.raises(ValueError):
            DuplicateService(hash_algorithm="invalid")

    def test_duplicate_detection_with_real_files(self):
        """Test duplicate detection with actual files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create two files with same content (duplicates)
            file1 = Path(tmpdir) / "dup1.txt"
            file2 = Path(tmpdir) / "dup2.txt"
            unique = Path(tmpdir) / "unique.txt"
            
            content = "This is duplicate content"
            file1.write_text(content)
            file2.write_text(content)
            unique.write_text("Different content")
            
            # Create FileItem objects
            files = [
                FileItem(
                    path=FilePath(str(file1)),
                    name="dup1.txt",
                    size=FileSize(len(content.encode())),
                    created_at=Timestamp(datetime.now()),
                    modified_at=Timestamp(datetime.now()),
                    extension=".txt",
                ),
                FileItem(
                    path=FilePath(str(file2)),
                    name="dup2.txt",
                    size=FileSize(len(content.encode())),
                    created_at=Timestamp(datetime.now()),
                    modified_at=Timestamp(datetime.now()),
                    extension=".txt",
                ),
                FileItem(
                    path=FilePath(str(unique)),
                    name="unique.txt",
                    size=FileSize(len("Different content".encode())),
                    created_at=Timestamp(datetime.now()),
                    modified_at=Timestamp(datetime.now()),
                    extension=".txt",
                ),
            ]
            
            service = DuplicateService(hash_algorithm="md5")
            groups = service.detect_duplicates(files)
            
            # Should find 1 duplicate group
            assert len(groups) == 1
            assert len(groups[0].files) == 2

    def test_detect_duplicates_no_progress_callback(self, duplicate_service, sample_file_items):
        """Test duplicate detection without progress callback."""
        with patch.object(duplicate_service.file_reader, 'compute_hash') as mock_hash:
            # Mock hash values: files 1 and 2 same, file 3 different
            mock_hash.side_effect = [
                "hash_abc",  # file1
                "hash_abc",  # file2 (same)
                "hash_xyz",  # unique
            ]
            
            groups = duplicate_service.detect_duplicates(sample_file_items)
            
            assert len(groups) == 1
            assert len(groups[0].files) == 2

    def test_detect_duplicates_with_progress_callback(self, duplicate_service, sample_file_items):
        """Test duplicate detection with progress callback."""
        progress_calls = []
        
        def progress_cb(current, total):
            progress_calls.append((current, total))
        
        with patch.object(duplicate_service.file_reader, 'compute_hash') as mock_hash:
            mock_hash.side_effect = ["hash1", "hash2", "hash3"]
            
            groups = duplicate_service.detect_duplicates(
                sample_file_items,
                progress_callback=progress_cb
            )
            
            # Progress should be called for each file
            assert len(progress_calls) == 3

    def test_no_duplicates(self, duplicate_service, sample_file_items):
        """Test when no duplicates are found."""
        with patch.object(duplicate_service.file_reader, 'compute_hash') as mock_hash:
            # All different hashes
            mock_hash.side_effect = ["hash_a", "hash_b", "hash_c"]
            
            groups = duplicate_service.detect_duplicates(sample_file_items)
            
            # No duplicates (groups need 2+ files)
            assert len(groups) == 0

    def test_multiple_duplicate_groups(self, duplicate_service):
        """Test detecting multiple separate duplicate groups."""
        files = [
            FileItem(
                path=FilePath(f"/path/to/file{i}.txt"),
                name=f"file{i}.txt",
                size=FileSize(1024),
                created_at=Timestamp(datetime.now()),
                modified_at=Timestamp(datetime.now()),
                extension=".txt",
            )
            for i in range(6)
        ]
        
        with patch.object(duplicate_service.file_reader, 'compute_hash') as mock_hash:
            # Create 2 groups: 3 files with hash_a, 2 with hash_b, 1 unique
            mock_hash.side_effect = [
                "hash_a",  # file0 (group 1)
                "hash_a",  # file1 (group 1)
                "hash_a",  # file2 (group 1)
                "hash_b",  # file3 (group 2)
                "hash_b",  # file4 (group 2)
                "hash_c",  # file5 (unique)
            ]
            
            groups = duplicate_service.detect_duplicates(files)
            
            assert len(groups) == 2
            assert len(groups[0].files) == 3
            assert len(groups[1].files) == 2

    def test_get_duplicate_statistics_empty(self, duplicate_service):
        """Test statistics for empty duplicate list."""
        stats = duplicate_service.get_duplicate_statistics([])
        
        assert stats['total_groups'] == 0
        assert stats['total_duplicates'] == 0
        assert stats['wasted_space_bytes'] == 0

    def test_get_duplicate_statistics(self, duplicate_service):
        """Test duplicate statistics calculation."""
        files = [
            FileItem(
                path=FilePath(f"/path/to/file{i}.txt"),
                name=f"file{i}.txt",
                size=FileSize(1000),
                created_at=Timestamp(datetime.now()),
                modified_at=Timestamp(datetime.now()),
                extension=".txt",
            )
            for i in range(3)
        ]
        
        with patch.object(duplicate_service.file_reader, 'compute_hash') as mock_hash:
            # 3 identical files
            mock_hash.side_effect = ["hash_a", "hash_a", "hash_a"]
            
            groups = duplicate_service.detect_duplicates(files)
            stats = duplicate_service.get_duplicate_statistics(groups)
            
            assert stats['total_groups'] == 1
            assert stats['total_duplicate_files'] == 3
            assert stats['total_duplicates'] == 2  # 3 - 1
            assert stats['wasted_space_bytes'] == 2000  # 1000 * 2 (keeping original)
            assert stats['largest_group'] == 3

    def test_filter_by_size(self, duplicate_service):
        """Test filtering duplicates by file size."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files of different sizes
            file1 = Path(tmpdir) / "dup1.txt"
            file2 = Path(tmpdir) / "dup2.txt"
            file3 = Path(tmpdir) / "dup3.txt"
            
            content = "dup"
            file1.write_text(content)
            file2.write_text(content)
            file3.write_text(content + " different")
            
            files = [
                FileItem(
                    path=FilePath(str(file1)),
                    name="dup1.txt",
                    size=FileSize(len(content.encode())),
                    created_at=Timestamp(datetime.now()),
                    modified_at=Timestamp(datetime.now()),
                    extension=".txt",
                ),
                FileItem(
                    path=FilePath(str(file2)),
                    name="dup2.txt",
                    size=FileSize(len(content.encode())),
                    created_at=Timestamp(datetime.now()),
                    modified_at=Timestamp(datetime.now()),
                    extension=".txt",
                ),
                FileItem(
                    path=FilePath(str(file3)),
                    name="dup3.txt",
                    size=FileSize(len((content + " different").encode())),
                    created_at=Timestamp(datetime.now()),
                    modified_at=Timestamp(datetime.now()),
                    extension=".txt",
                ),
            ]
            
            service = DuplicateService()
            groups = service.detect_duplicates(files)
            
            # Filter to only small files (< 10 bytes)
            filtered = service.filter_by_size(groups, min_size=0, max_size=10)
            
            assert len(filtered) <= len(groups)

    def test_filter_by_extension(self, duplicate_service):
        """Test filtering duplicates by extension."""
        files = [
            FileItem(
                path=FilePath(f"/path/to/file{i}.{'txt' if i < 2 else 'jpg'}"),
                name=f"file{i}.{'txt' if i < 2 else 'jpg'}",
                size=FileSize(1024),
                created_at=Timestamp(datetime.now()),
                modified_at=Timestamp(datetime.now()),
                extension=f".{'txt' if i < 2 else 'jpg'}",
            )
            for i in range(3)
        ]
        
        with patch.object(duplicate_service.file_reader, 'compute_hash') as mock_hash:
            # file0 and file1 are duplicates (txt), file2 is different
            mock_hash.side_effect = ["hash_a", "hash_a", "hash_c"]
            
            groups = duplicate_service.detect_duplicates(files)
            
            # Filter to only .txt files
            filtered = duplicate_service.filter_by_extension(groups, ['.txt'])
            
            assert len(filtered) == 1

    def test_format_bytes(self, duplicate_service):
        """Test byte formatting utility."""
        assert "B" in duplicate_service._format_bytes(512)
        assert "KB" in duplicate_service._format_bytes(1024 * 500)
        assert "MB" in duplicate_service._format_bytes(1024 * 1024 * 10)
        assert "GB" in duplicate_service._format_bytes(1024 * 1024 * 1024)
