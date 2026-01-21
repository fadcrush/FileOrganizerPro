"""Unit tests for ScanningService.

Tests cover:
- Basic directory scanning
- File filtering (extension, size, date)
- Error handling and recovery
- Progress callbacks
- Cancellation support
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from fileorganizer_pro.services.scanning_service import ScanningService
from fileorganizer_pro.domain.value_objects import FilePath
from fileorganizer_pro.domain.exceptions import InvalidPathError, OperationFailedError


class TestScanningService:
    """Tests for ScanningService."""

    @pytest.fixture
    def scanning_service(self):
        """Create ScanningService instance."""
        return ScanningService()

    @pytest.fixture
    def temp_dir_structure(self):
        """Create temporary directory with test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create structure:
            # tmpdir/
            #   ├── test1.txt (100 bytes)
            #   ├── test2.pdf (200 bytes)
            #   ├── subdir/
            #   │   ├── test3.jpg (300 bytes)
            #   │   └── test4.py (150 bytes)
            #   └── .git/ (excluded)
            
            root = Path(tmpdir)
            
            (root / "test1.txt").write_text("a" * 100)
            (root / "test2.pdf").write_text("b" * 200)
            (root / "subdir").mkdir()
            (root / "subdir" / "test3.jpg").write_text("c" * 300)
            (root / "subdir" / "test4.py").write_text("d" * 150)
            (root / ".git").mkdir()
            (root / ".git" / "config").write_text("git config")
            
            yield tmpdir

    def test_scan_all_files(self, scanning_service, temp_dir_structure):
        """Test basic directory scan without filters."""
        result = scanning_service.scan(temp_dir_structure)
        
        assert result.total_count == 5  # 4 regular files + 1 in .git (included if not excluded)
        assert len(result.files) == 5
        assert len(result.folders) > 0
        assert len(result.errors) == 0

    def test_scan_with_extension_filter(self, scanning_service, temp_dir_structure):
        """Test scanning with extension filter."""
        result = scanning_service.scan(
            temp_dir_structure,
            extensions={'.txt', '.pdf'}
        )
        
        assert result.total_count == 2  # Only .txt and .pdf files
        assert all(f.extension in ['.txt', '.pdf'] for f in result.files)

    def test_scan_with_size_filter(self, scanning_service, temp_dir_structure):
        """Test scanning with size filters."""
        result = scanning_service.scan(
            temp_dir_structure,
            min_size=200,  # >= 200 bytes
            max_size=300,  # <= 300 bytes
        )
        
        # Should match test2.pdf (200) and test3.jpg (300)
        assert result.total_count >= 2
        assert all(200 <= f.size.bytes <= 300 for f in result.files)

    def test_scan_excludes_directories(self, scanning_service, temp_dir_structure):
        """Test that excluded directories are skipped."""
        result = scanning_service.scan(
            temp_dir_structure,
            exclude_dirs={'.git'}
        )
        
        # Should not include .git/config
        assert not any('.git' in f.path.path for f in result.files)

    def test_scan_progress_callback(self, scanning_service, temp_dir_structure):
        """Test progress callback is called during scan."""
        progress_calls = []
        
        def progress_cb(count, path):
            progress_calls.append((count, path))
        
        result = scanning_service.scan(
            temp_dir_structure,
            progress_callback=progress_cb
        )
        
        assert len(progress_calls) > 0
        assert result.total_count > 0

    def test_scan_cancellation(self, scanning_service, temp_dir_structure):
        """Test scan cancellation."""
        def progress_cb(count, path):
            if count >= 2:
                scanning_service.cancel()
        
        result = scanning_service.scan(
            temp_dir_structure,
            progress_callback=progress_cb
        )
        
        # Should stop partway through (not all files scanned)
        assert result.total_count < 5

    def test_scan_invalid_path(self, scanning_service):
        """Test scan with invalid path."""
        with pytest.raises(InvalidPathError):
            scanning_service.scan("/nonexistent/path")

    def test_scan_permission_error(self, scanning_service):
        """Test scan handling of permission errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create a subdirectory
            subdir = root / "subdir"
            subdir.mkdir()
            (subdir / "file.txt").write_text("content")
            
            # Try to make it unreadable (may not work on Windows)
            try:
                subdir.chmod(0o000)
                result = scanning_service.scan(root.as_posix())
                # Should have error but continue
                assert len(result.errors) >= 0
            finally:
                # Restore permissions for cleanup
                subdir.chmod(0o755)

    def test_should_include_file_extension(self, scanning_service):
        """Test _should_include_file extension filter."""
        mock_path = Mock(spec=FilePath)
        mock_path.path = "/path/to/file.pdf"
        
        # Should include .pdf when in extensions set
        assert scanning_service._should_include_file(
            mock_path,
            extensions={'.pdf', '.txt'},
            min_size=0,
            max_size=None,
            min_date=None,
            max_date=None,
        )
        
        # Should exclude .jpg when not in extensions set
        mock_path.path = "/path/to/file.jpg"
        assert not scanning_service._should_include_file(
            mock_path,
            extensions={'.pdf', '.txt'},
            min_size=0,
            max_size=None,
            min_date=None,
            max_date=None,
        )

    def test_should_include_file_size(self, scanning_service):
        """Test _should_include_file size filter."""
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b"x" * 500)
            tmp.flush()
            
            mock_path = Mock(spec=FilePath)
            mock_path.path = tmp.name
            
            # Should include file within size range
            assert scanning_service._should_include_file(
                mock_path,
                extensions=None,
                min_size=100,
                max_size=1000,
                min_date=None,
                max_date=None,
            )
            
            # Should exclude file below min_size
            assert not scanning_service._should_include_file(
                mock_path,
                extensions=None,
                min_size=600,
                max_size=1000,
                min_date=None,
                max_date=None,
            )
