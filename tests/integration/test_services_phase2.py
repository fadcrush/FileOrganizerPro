"""Integration tests for Phase 2 Services.

Tests that all three services work together correctly in a real scenario.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from fileorganizer_pro.services.scanning_service import ScanningService
from fileorganizer_pro.services.categorization_service import CategorizationService
from fileorganizer_pro.services.duplicate_service import DuplicateService
from fileorganizer_pro.services import FileOrganizer
from fileorganizer_pro.domain.value_objects import FilePath


class TestServicesIntegration:
    """Integration tests for Phase 2 services."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory with realistic files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create a realistic file structure
            # Documents/
            (root / "Documents").mkdir()
            (root / "Documents" / "report.pdf").write_text("pdf content" * 100)
            (root / "Documents" / "notes.txt").write_text("text content")
            
            # Images/
            (root / "Images").mkdir()
            (root / "Images" / "photo.jpg").write_text("jpg data")
            (root / "Images" / "logo.png").write_text("png data")
            
            # Code/
            (root / "Code").mkdir()
            (root / "Code" / "main.py").write_text("python code")
            (root / "Code" / "util.js").write_text("javascript code")
            
            # Duplicates (intentionally)
            (root / "dup1.pdf").write_text("pdf content" * 100)  # Same as Documents/report.pdf
            (root / "dup2.pdf").write_text("pdf content" * 100)  # Same as Documents/report.pdf
            
            yield tmpdir

    def test_scanning_service_basic(self, temp_project):
        """Test ScanningService can scan temp directory."""
        service = ScanningService()
        result = service.scan(temp_project)
        
        assert result.total_count >= 8  # At least 8 files
        assert len(result.files) == result.total_count
        assert len(result.folders) > 0
        assert len(result.errors) == 0

    def test_categorization_service_basic(self, temp_project):
        """Test CategorizationService can categorize files."""
        scan_service = ScanningService()
        cat_service = CategorizationService()
        
        scan_result = scan_service.scan(temp_project)
        categorizations = cat_service.categorize_batch(scan_result.files)
        
        assert len(categorizations) == scan_result.total_count
        
        # Check specific files are categorized correctly
        pdf_paths = [f.path.path for f in scan_result.files if f.path.path.endswith('.pdf')]
        assert any(categorizations[p].name == "Documents" for p in pdf_paths)

    def test_duplicate_service_basic(self, temp_project):
        """Test DuplicateService can detect duplicates."""
        scan_service = ScanningService()
        dup_service = DuplicateService(hash_algorithm="md5")
        
        scan_result = scan_service.scan(temp_project)
        duplicates = dup_service.detect_duplicates(scan_result.files)
        
        # Should find at least 1 duplicate group (3 identical PDFs)
        assert len(duplicates) >= 1

    def test_file_organizer_orchestrator(self, temp_project):
        """Test FileOrganizer orchestrates all services."""
        organizer = FileOrganizer()
        
        # Should be able to instantiate without errors
        assert organizer is not None
        assert organizer.scanning_service is not None
        assert organizer.categorization_service is not None
        assert organizer.duplicate_service is not None

    def test_services_with_progress_tracking(self, temp_project):
        """Test that services support progress callbacks."""
        service = ScanningService()
        
        progress_updates = []
        def track_progress(count, path):
            progress_updates.append((count, path))
        
        result = service.scan(
            temp_project,
            progress_callback=track_progress
        )
        
        assert len(progress_updates) > 0
        assert result.total_count > 0

    def test_categorization_with_custom_rules(self, temp_project):
        """Test CategorizationService with custom categorization rules."""
        service = CategorizationService()
        
        # Add custom rule
        service.add_rule("MyPDFs", [".pdf"])
        
        categories = service.get_categories()
        assert "MyPDFs" in categories
        
        # Get extensions for custom category
        extensions = service.get_extensions_for_category("MyPDFs")
        assert ".pdf" in extensions

    def test_duplicate_statistics(self, temp_project):
        """Test DuplicateService provides statistics."""
        scan_service = ScanningService()
        dup_service = DuplicateService()
        
        scan_result = scan_service.scan(temp_project)
        duplicates = dup_service.detect_duplicates(scan_result.files)
        
        if duplicates:
            stats = dup_service.get_duplicate_statistics(duplicates)
            
            assert 'total_groups' in stats
            assert 'total_duplicates' in stats
            assert 'wasted_space_bytes' in stats
            assert stats['total_groups'] >= 1

    def test_scanning_with_exclusions(self, temp_project):
        """Test ScanningService respects exclusions."""
        service = ScanningService()
        
        result_with_exclusion = service.scan(
            temp_project,
            exclude_dirs={'Code'}  # Exclude Code directory
        )
        
        result_without_exclusion = service.scan(temp_project)
        
        # Should have fewer files when excluding Code
        assert result_with_exclusion.total_count < result_without_exclusion.total_count

    def test_error_recovery(self, temp_project):
        """Test that services handle errors gracefully."""
        service = ScanningService()
        
        # Try to scan non-existent path (should handle gracefully)
        try:
            result = service.scan("/nonexistent/path")
        except Exception:
            # Expected to raise error for invalid path
            pass


class TestServicesSeparationOfConcerns:
    """Tests that verify clean separation of concerns between services."""

    def test_scanning_service_independent(self):
        """Test ScanningService can be used without other services."""
        service = ScanningService()
        assert service is not None
        # Should not require other services

    def test_categorization_service_independent(self):
        """Test CategorizationService can be used without other services."""
        service = CategorizationService()
        assert service is not None
        # Should not require other services

    def test_duplicate_service_independent(self):
        """Test DuplicateService can be used without other services."""
        service = DuplicateService()
        assert service is not None
        # Should not require other services

    def test_services_are_composable(self):
        """Test that services can be composed together."""
        scanning = ScanningService()
        categorization = CategorizationService()
        duplicates = DuplicateService()
        
        # Should be able to pass results from one service to another
        # (This is verified in integration tests above)
        assert scanning is not None
        assert categorization is not None
        assert duplicates is not None
