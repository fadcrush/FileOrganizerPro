"""Unit tests for CategorizationService.

Tests cover:
- Basic file categorization by extension
- Batch categorization
- Custom rule addition/removal
- Configuration loading/saving
- Category management
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock

from fileorganizer_pro.services.categorization_service import (
    CategorizationService,
    DEFAULT_CATEGORY_MAPPINGS,
)
from fileorganizer_pro.domain.entities import FileItem
from fileorganizer_pro.domain.value_objects import FilePath, Category, FileSize, Timestamp
from fileorganizer_pro.domain.exceptions import CategoryNotFoundError
from datetime import datetime


class TestCategorizationService:
    """Tests for CategorizationService."""

    @pytest.fixture
    def categorization_service(self):
        """Create CategorizationService instance."""
        return CategorizationService()

    @pytest.fixture
    def sample_file_item(self):
        """Create sample FileItem for testing."""
        return FileItem(
            path=FilePath("/path/to/document.pdf"),
            size=FileSize(1024),
            modified=Timestamp(datetime.now()),
        )

    def test_categorize_pdf(self, categorization_service, sample_file_item):
        """Test categorization of PDF file."""
        category = categorization_service.categorize(sample_file_item)
        assert category.value == "Documents"

    def test_categorize_image(self, categorization_service):
        """Test categorization of image file."""
        file_item = FileItem(
            path=FilePath("/path/to/photo.jpg"),
            size=FileSize(2048),
            modified=Timestamp(datetime.now()),
        )
        
        category = categorization_service.categorize(file_item)
        assert category.value == "Images"

    def test_categorize_code(self, categorization_service):
        """Test categorization of code file."""
        file_item = FileItem(
            path=FilePath("/path/to/script.py"),
            name="script.py",
            size=FileSize(512),
            created_at=Timestamp(datetime.now()),
            modified_at=Timestamp(datetime.now()),
            extension=".py",
        )
        
        category = categorization_service.categorize(file_item)
        assert category.value == "Code"

    def test_categorize_unknown(self, categorization_service):
        """Test categorization of unknown file type."""
        file_item = FileItem(
            path=FilePath("/path/to/unknown.xyz"),
            name="unknown.xyz",
            size=FileSize(256),
            created_at=Timestamp(datetime.now()),
            modified_at=Timestamp(datetime.now()),
            extension=".xyz",
        )
        
        category = categorization_service.categorize(file_item)
        assert category.value == "Other"

    def test_categorize_batch(self, categorization_service):
        """Test batch categorization of multiple files."""
        files = [
            FileItem(
                path=FilePath(f"/path/to/file{i}.{ext}"),
                name=f"file{i}.{ext}",
                size=FileSize(1024),
                created_at=Timestamp(datetime.now()),
                modified_at=Timestamp(datetime.now()),
                extension=f".{ext}",
            )
            for i, ext in enumerate(['pdf', 'jpg', 'py', 'xyz'])
        ]
        
        results = categorization_service.categorize_batch(files)
        
        assert len(results) == 4
        assert results["/path/to/file0.pdf"] == Category("Documents")
        assert results["/path/to/file1.jpg"] == Category("Images")
        assert results["/path/to/file2.py"] == Category("Code")
        assert results["/path/to/file3.xyz"] == Category("Other")

    def test_add_rule(self, categorization_service):
        """Test adding custom categorization rule."""
        categorization_service.add_rule("Custom", [".custom", ".test"])
        
        file_item = FileItem(
            path=FilePath("/path/to/file.custom"),
            name="file.custom",
            size=FileSize(100),
            created_at=Timestamp(datetime.now()),
            modified_at=Timestamp(datetime.now()),
            extension=".custom",
        )
        
        category = categorization_service.categorize(file_item)
        assert category.value == "Custom"

    def test_add_rule_normalizes_extensions(self, categorization_service):
        """Test that add_rule normalizes extensions (adds dot if missing)."""
        categorization_service.add_rule("Normalized", ["ext1", ".ext2"])
        
        # Both with and without dot should work
        file1 = FileItem(
            path=FilePath("/path/to/file.ext1"),
            name="file.ext1",
            size=FileSize(100),
            created_at=Timestamp(datetime.now()),
            modified_at=Timestamp(datetime.now()),
            extension=".ext1",
        )
        
        file2 = FileItem(
            path=FilePath("/path/to/file.ext2"),
            name="file.ext2",
            size=FileSize(100),
            created_at=Timestamp(datetime.now()),
            modified_at=Timestamp(datetime.now()),
            extension=".ext2",
        )
        
        assert categorization_service.categorize(file1).value == "Normalized"
        assert categorization_service.categorize(file2).value == "Normalized"

    def test_remove_rule_specific_extensions(self, categorization_service):
        """Test removing specific extensions from a category."""
        # Add custom rule
        categorization_service.add_rule("TestCat", [".test1", ".test2"])
        
        # Verify it works
        file_item = FileItem(
            path=FilePath("/path/to/file.test1"),
            name="file.test1",
            size=FileSize(100),
            created_at=Timestamp(datetime.now()),
            modified_at=Timestamp(datetime.now()),
            extension=".test1",
        )
        assert categorization_service.categorize(file_item).value == "TestCat"
        
        # Remove specific extension
        categorization_service.remove_rule("TestCat", [".test1"])
        
        # Should now categorize as "Other"
        assert categorization_service.categorize(file_item).value == "Other"

    def test_remove_entire_category(self, categorization_service):
        """Test removing entire category."""
        categorization_service.add_rule("ToDelete", [".del"])
        
        file_item = FileItem(
            path=FilePath("/path/to/file.del"),
            name="file.del",
            size=FileSize(100),
            created_at=Timestamp(datetime.now()),
            modified_at=Timestamp(datetime.now()),
            extension=".del",
        )
        
        assert categorization_service.categorize(file_item).value == "ToDelete"
        
        # Remove entire category
        categorization_service.remove_rule("ToDelete")
        
        assert categorization_service.categorize(file_item).value == "Other"

    def test_get_categories(self, categorization_service):
        """Test getting list of available categories."""
        categories = categorization_service.get_categories()
        
        assert isinstance(categories, list)
        assert "Documents" in categories
        assert "Images" in categories
        assert "Code" in categories

    def test_get_extensions_for_category(self, categorization_service):
        """Test getting extensions for a category."""
        extensions = categorization_service.get_extensions_for_category("Documents")
        
        assert isinstance(extensions, list)
        assert ".pdf" in extensions
        assert ".doc" in extensions

    def test_get_extensions_nonexistent_category(self, categorization_service):
        """Test getting extensions for nonexistent category."""
        with pytest.raises(CategoryNotFoundError):
            categorization_service.get_extensions_for_category("NonExistent")

    def test_load_from_config(self, categorization_service):
        """Test loading category mappings from JSON config."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config = {
                "Custom1": [".c1"],
                "Custom2": [".c2", ".c3"],
            }
            json.dump(config, f)
            f.flush()
            
            categorization_service.load_from_config(f.name)
            
            categories = categorization_service.get_categories()
            assert "Custom1" in categories
            assert "Custom2" in categories
            
            # Clean up
            Path(f.name).unlink()

    def test_save_to_config(self, categorization_service):
        """Test saving category mappings to JSON config."""
        categorization_service.add_rule("SaveTest", [".save"])
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
        
        try:
            categorization_service.save_to_config(config_path)
            
            # Load it back
            with open(config_path, 'r') as f:
                loaded = json.load(f)
            
            assert "SaveTest" in loaded
            assert ".save" in loaded["SaveTest"]
        finally:
            Path(config_path).unlink()

    def test_case_insensitive_matching(self, categorization_service):
        """Test that extension matching is case-insensitive."""
        file_item1 = FileItem(
            path=FilePath("/path/to/file.PDF"),
            name="file.PDF",
            size=FileSize(100),
            created_at=Timestamp(datetime.now()),
            modified_at=Timestamp(datetime.now()),
            extension=".PDF",
        )
        
        file_item2 = FileItem(
            path=FilePath("/path/to/file.pdf"),
            name="file.pdf",
            size=FileSize(100),
            created_at=Timestamp(datetime.now()),
            modified_at=Timestamp(datetime.now()),
            extension=".pdf",
        )
        
        # Both should categorize as Documents
        assert categorization_service.categorize(file_item1).value == "Documents"
        assert categorization_service.categorize(file_item2).value == "Documents"
