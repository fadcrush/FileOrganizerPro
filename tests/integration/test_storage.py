"""Tests for cloud storage providers."""

import pytest
from pathlib import Path

from src.backend.storage import (
    LocalStorageProvider,
    create_storage_provider,
    StorageFile,
)


@pytest.fixture
def storage(tmp_path):
    """Create LocalStorageProvider for testing."""
    return LocalStorageProvider(str(tmp_path))


@pytest.mark.asyncio
async def test_local_storage_write_read(storage, tmp_path):
    """Test writing and reading files."""
    test_path = "test_file.txt"
    test_content = b"Hello, World!"
    
    # Write
    await storage.write_file(test_path, test_content)
    
    # Verify file exists
    assert (tmp_path / test_path).exists()
    
    # Read
    content = await storage.read_file(test_path)
    assert content == test_content


@pytest.mark.asyncio
async def test_local_storage_list_files(storage, tmp_path):
    """Test listing files."""
    # Create test files
    (tmp_path / "file1.txt").write_text("content1")
    (tmp_path / "file2.txt").write_text("content2")
    
    # List files
    files = await storage.list_files(".", recursive=False)
    
    assert len(files) == 2
    assert all(isinstance(f, StorageFile) for f in files)


@pytest.mark.asyncio
async def test_local_storage_move_file(storage, tmp_path):
    """Test moving files."""
    source_path = "source.txt"
    dest_path = "dest.txt"
    
    # Create source file
    await storage.write_file(source_path, b"content")
    
    # Move file
    await storage.move_file(source_path, dest_path)
    
    # Verify
    assert not (tmp_path / source_path).exists()
    assert (tmp_path / dest_path).exists()


@pytest.mark.asyncio
async def test_local_storage_delete_file(storage, tmp_path):
    """Test deleting files."""
    test_path = "delete_me.txt"
    
    # Create file
    await storage.write_file(test_path, b"content")
    assert (tmp_path / test_path).exists()
    
    # Delete
    await storage.delete_file(test_path)
    assert not (tmp_path / test_path).exists()


@pytest.mark.asyncio
async def test_local_storage_file_hash(storage, tmp_path):
    """Test computing file hash."""
    test_path = "test.txt"
    content = b"test content"
    
    await storage.write_file(test_path, content)
    
    hash_value = await storage.get_file_hash(test_path, "sha256")
    
    assert hash_value is not None
    assert len(hash_value) == 64  # SHA256 hex digest length


@pytest.mark.asyncio
async def test_storage_provider_factory():
    """Test storage provider factory."""
    # Create local provider
    provider = create_storage_provider("local", base_path="/tmp")
    assert isinstance(provider, LocalStorageProvider)


@pytest.mark.asyncio
async def test_storage_path_traversal_protection(storage):
    """Test protection against directory traversal attacks."""
    # Try to access file outside base directory
    with pytest.raises(ValueError):
        await storage.read_file("../../etc/passwd")
