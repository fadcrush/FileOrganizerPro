"""Tests for async services."""

import pytest
import asyncio
from pathlib import Path

from src.backend.async_services import (
    AsyncScanningService,
    AsyncCategorizationService,
    AsyncDuplicateService,
    create_async_services,
)
from fileorganizer_pro.core.entities import FileItem, FilePath, FileSize


@pytest.fixture
def async_services():
    """Create async service instances."""
    return create_async_services()


@pytest.mark.asyncio
async def test_async_scanning_service(tmp_path):
    """Test AsyncScanningService.scan_async()."""
    # Create test files
    test_file1 = tmp_path / "document.pdf"
    test_file1.write_bytes(b"PDF content")
    
    test_file2 = tmp_path / "image.jpg"
    test_file2.write_bytes(b"JPEG content")
    
    # Scan asynchronously
    service = AsyncScanningService()
    result = await service.scan_async(str(tmp_path))
    
    assert result is not None
    assert len(result.files) == 2
    assert all(f.size.bytes > 0 for f in result.files)


@pytest.mark.asyncio
async def test_async_categorization_service(async_services):
    """Test AsyncCategorizationService.categorize_async()."""
    _, categorizer, _ = async_services
    
    # Create test file item
    file_item = FileItem(
        path=FilePath("/test/document.pdf"),
        size=FileSize(bytes=1024),
        modified=1234567890.0,
    )
    
    # Categorize asynchronously
    category = await categorizer.categorize_async(file_item)
    
    assert category is not None
    assert category.name == "Documents"


@pytest.mark.asyncio
async def test_async_duplicate_service(async_services, tmp_path):
    """Test AsyncDuplicateService.detect_duplicates_async()."""
    _, _, duplicates = async_services
    
    # Create duplicate files
    content = b"duplicate content"
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    
    file1.write_bytes(content)
    file2.write_bytes(content)
    
    # Create file items
    items = [
        FileItem(
            path=FilePath(str(file1)),
            size=FileSize(bytes=len(content)),
            modified=1234567890.0,
        ),
        FileItem(
            path=FilePath(str(file2)),
            size=FileSize(bytes=len(content)),
            modified=1234567890.0,
        ),
    ]
    
    # Detect duplicates asynchronously
    groups = await duplicates.detect_duplicates_async(items)
    
    assert len(groups) > 0
    assert sum(len(g.duplicates) for g in groups) == 2


@pytest.mark.asyncio
async def test_concurrent_async_operations(async_services, tmp_path):
    """Test multiple async operations running concurrently."""
    scanner, categorizer, duplicates = async_services
    
    # Create multiple test files
    files = []
    for i in range(5):
        f = tmp_path / f"file{i}.txt"
        f.write_bytes(f"content {i}".encode())
        files.append(f)
    
    # Run multiple async operations concurrently
    results = await asyncio.gather(
        scanner.scan_async(str(tmp_path)),
        categorizer.categorize_batch_async([
            FileItem(
                path=FilePath(str(f)),
                size=FileSize(bytes=f.stat().st_size),
                modified=f.stat().st_mtime,
            )
            for f in files
        ]),
        duplicates.detect_duplicates_async([
            FileItem(
                path=FilePath(str(f)),
                size=FileSize(bytes=f.stat().st_size),
                modified=f.stat().st_mtime,
            )
            for f in files
        ]),
    )
    
    assert len(results) == 3
    assert results[0] is not None  # scan result
    assert results[1] is not None  # categorization result
    assert results[2] is not None  # duplicates result


@pytest.mark.asyncio
async def test_async_service_error_handling(async_services):
    """Test error handling in async services."""
    scanner, _, _ = async_services
    
    # Try to scan non-existent directory
    with pytest.raises(Exception):
        await scanner.scan_async("/non/existent/path")
