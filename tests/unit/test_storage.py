"""Unit tests for storage providers."""

import pytest
from pathlib import Path

from src.backend.storage import LocalStorageProvider, StorageFile


class TestLocalStorageProvider:
    """Tests for LocalStorageProvider."""
    
    @pytest.fixture
    def provider(self, tmp_path):
        """Create LocalStorageProvider for testing."""
        return LocalStorageProvider(str(tmp_path))
    
    def test_initialization(self, provider, tmp_path):
        """Test provider initialization."""
        assert provider.base_path == str(tmp_path)
    
    def test_validate_path_safe(self, provider):
        """Test that safe paths are validated."""
        safe_paths = [
            "file.txt",
            "folder/file.txt",
            "folder/subfolder/file.txt",
        ]
        
        for path in safe_paths:
            # Should not raise
            provider._validate_path(path)
    
    def test_validate_path_unsafe(self, provider):
        """Test that unsafe paths are rejected."""
        unsafe_paths = [
            "../etc/passwd",
            "../../etc/passwd",
            "/etc/passwd",
            "folder/../../etc/passwd",
        ]
        
        for path in unsafe_paths:
            with pytest.raises(ValueError):
                provider._validate_path(path)
    
    @pytest.mark.asyncio
    async def test_file_exists(self, provider, tmp_path):
        """Test exists() method."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        # Should exist
        assert await provider.exists("test.txt")
        
        # Should not exist
        assert not await provider.exists("nonexistent.txt")
    
    @pytest.mark.asyncio
    async def test_write_and_read_file(self, provider, tmp_path):
        """Test writing and reading files."""
        test_path = "test_file.txt"
        test_content = b"Hello, World!"
        
        # Write file
        await provider.write_file(test_path, test_content)
        
        # File should exist
        assert (tmp_path / test_path).exists()
        
        # Read file
        content = await provider.read_file(test_path)
        assert content == test_content
    
    @pytest.mark.asyncio
    async def test_list_files(self, provider, tmp_path):
        """Test listing files."""
        # Create test files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file3.txt").write_text("content3")
        
        # List non-recursive
        files = await provider.list_files(".", recursive=False)
        assert len(files) >= 2
        assert all(isinstance(f, StorageFile) for f in files)
        
        # List recursive
        files_recursive = await provider.list_files(".", recursive=True)
        assert len(files_recursive) >= 3
    
    @pytest.mark.asyncio
    async def test_move_file(self, provider, tmp_path):
        """Test moving files."""
        source_path = "source.txt"
        dest_path = "dest.txt"
        
        # Create source file
        await provider.write_file(source_path, b"content")
        
        # Move file
        await provider.move_file(source_path, dest_path)
        
        # Source should not exist
        assert not (tmp_path / source_path).exists()
        
        # Destination should exist
        assert (tmp_path / dest_path).exists()
    
    @pytest.mark.asyncio
    async def test_delete_file(self, provider, tmp_path):
        """Test deleting files."""
        test_path = "delete_me.txt"
        
        # Create file
        await provider.write_file(test_path, b"content")
        assert (tmp_path / test_path).exists()
        
        # Delete file
        await provider.delete_file(test_path)
        assert not (tmp_path / test_path).exists()
    
    @pytest.mark.asyncio
    async def test_file_hash_md5(self, provider, tmp_path):
        """Test computing MD5 hash."""
        test_path = "test.txt"
        content = b"test content"
        
        await provider.write_file(test_path, content)
        
        hash_value = await provider.get_file_hash(test_path, "md5")
        
        assert hash_value is not None
        assert len(hash_value) == 32  # MD5 hex digest length
    
    @pytest.mark.asyncio
    async def test_file_hash_sha256(self, provider, tmp_path):
        """Test computing SHA256 hash."""
        test_path = "test.txt"
        content = b"test content"
        
        await provider.write_file(test_path, content)
        
        hash_value = await provider.get_file_hash(test_path, "sha256")
        
        assert hash_value is not None
        assert len(hash_value) == 64  # SHA256 hex digest length
    
    @pytest.mark.asyncio
    async def test_storage_file_properties(self, provider, tmp_path):
        """Test StorageFile properties."""
        test_path = "test.txt"
        content = b"test content"
        
        await provider.write_file(test_path, content)
        
        files = await provider.list_files(".", recursive=False)
        
        assert len(files) > 0
        
        test_file = next((f for f in files if "test.txt" in f.path), None)
        assert test_file is not None
        assert test_file.size_bytes == len(content)
        assert test_file.modified_at > 0
        assert not test_file.is_dir
