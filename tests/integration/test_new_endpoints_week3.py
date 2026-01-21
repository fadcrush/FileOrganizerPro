"""Tests for new API endpoints (Week 3)."""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from src.backend.api.main import app
from src.backend.database import SessionLocal
from src.backend.models import User, Operation, FileRecord
from src.backend.services.auth import hash_password, create_access_token


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Create database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db_session):
    """Create test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash=hash_password("password123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user):
    """Create JWT token for test user."""
    return create_access_token(test_user.id)


@pytest.fixture
def auth_headers(auth_token):
    """Create authorization headers."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def test_operation_with_files(db_session, test_user):
    """Create test operation with file records."""
    operation = Operation(
        user_id=test_user.id,
        operation_type="organize",
        status="completed",
        root_path="/test/path",
        files_scanned=100,
        files_processed=95,
        duplicates_found=5,
    )
    db_session.add(operation)
    db_session.commit()
    
    # Add file records
    files_data = [
        ("document1.pdf", "Documents", 1024000, "abc123"),
        ("document2.pdf", "Documents", 1024000, "abc123"),  # Duplicate
        ("image1.jpg", "Images", 2048000, "def456"),
        ("image2.jpg", "Images", 2048000, "def456"),  # Duplicate
        ("image3.jpg", "Images", 1024000, "ghi789"),
        ("video.mp4", "Videos", 10240000, "jkl012"),
        ("code.py", "Code", 51200, "mno345"),
    ]
    
    for idx, (path, category, size, hash_val) in enumerate(files_data):
        record = FileRecord(
            operation_id=operation.id,
            original_path=f"/unsorted/{path}",
            new_path=f"/{category}/{path}",
            category=category,
            file_size_bytes=size,
            file_hash=hash_val,
            status="completed",
        )
        db_session.add(record)
    
    db_session.commit()
    db_session.refresh(operation)
    return operation


class TestDuplicatesEndpoints:
    """Tests for duplicate listing endpoints."""
    
    def test_get_duplicates(self, client, auth_headers, test_operation_with_files):
        """Test getting duplicates for an operation."""
        response = client.get(
            f"/api/v1/duplicates/{test_operation_with_files.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "duplicates" in data
        assert data["total_groups"] >= 1
        assert data["total_duplicates"] >= 2
    
    def test_get_duplicates_with_limit(self, client, auth_headers, test_operation_with_files):
        """Test duplicates with pagination limit."""
        response = client.get(
            f"/api/v1/duplicates/{test_operation_with_files.id}?limit=1",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["duplicates"]) <= 1
    
    def test_get_duplicates_unauthorized(self, client, test_operation_with_files):
        """Test unauthorized access to duplicates."""
        response = client.get(
            f"/api/v1/duplicates/{test_operation_with_files.id}",
        )
        
        assert response.status_code == 401
    
    def test_get_duplicates_not_found(self, client, auth_headers):
        """Test getting duplicates for non-existent operation."""
        fake_id = uuid4()
        response = client.get(
            f"/api/v1/duplicates/{fake_id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 404


class TestFilesEndpoints:
    """Tests for file operations listing endpoints."""
    
    def test_list_files(self, client, auth_headers, test_operation_with_files):
        """Test listing files for an operation."""
        response = client.get(
            f"/api/v1/files?operation_id={test_operation_with_files.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "files" in data
        assert data["total_files"] > 0
        assert data["files_completed"] > 0
    
    def test_list_files_with_pagination(self, client, auth_headers, test_operation_with_files):
        """Test file listing with pagination."""
        response = client.get(
            f"/api/v1/files?operation_id={test_operation_with_files.id}&page=1&page_size=2",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert len(data["files"]) <= 2
    
    def test_list_files_with_category_filter(self, client, auth_headers, test_operation_with_files):
        """Test file listing with category filter."""
        response = client.get(
            f"/api/v1/files?operation_id={test_operation_with_files.id}&category_filter=Images",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(f["category"] == "Images" for f in data["files"])
    
    def test_search_files(self, client, auth_headers, test_operation_with_files):
        """Test searching files."""
        response = client.get(
            f"/api/v1/files/search?operation_id={test_operation_with_files.id}&query=document",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["files"]) > 0


class TestReportsEndpoints:
    """Tests for report generation endpoints."""
    
    def test_get_report(self, client, auth_headers, test_operation_with_files):
        """Test getting report for an operation."""
        response = client.get(
            f"/api/v1/reports/{test_operation_with_files.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "stats" in data
        assert data["stats"]["total_files_scanned"] > 0
        assert data["stats"]["duplicate_files"] >= 0
        assert "category_breakdown" in data
    
    def test_get_report_stats(self, client, auth_headers, test_operation_with_files):
        """Test report statistics accuracy."""
        response = client.get(
            f"/api/v1/reports/{test_operation_with_files.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        stats = data["stats"]
        
        # Verify statistics
        assert stats["total_files_scanned"] > 0
        assert stats["duplicate_files"] >= 0
        assert stats["space_saved_bytes"] >= 0
    
    def test_export_report_json(self, client, auth_headers, test_operation_with_files):
        """Test exporting report as JSON."""
        response = client.get(
            f"/api/v1/reports/{test_operation_with_files.id}/export?format=json",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert data["format"] == "json"
    
    def test_export_report_csv(self, client, auth_headers, test_operation_with_files):
        """Test exporting report as CSV."""
        response = client.get(
            f"/api/v1/reports/{test_operation_with_files.id}/export?format=csv",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
    
    def test_export_report_html(self, client, auth_headers, test_operation_with_files):
        """Test exporting report as HTML."""
        response = client.get(
            f"/api/v1/reports/{test_operation_with_files.id}/export?format=html",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


class TestCategoriesEndpoints:
    """Tests for category management endpoints."""
    
    def test_list_categories(self, client, auth_headers):
        """Test listing all categories."""
        response = client.get(
            "/api/v1/categories",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert len(data["categories"]) > 0
    
    def test_create_custom_category(self, client, auth_headers):
        """Test creating a custom category."""
        response = client.post(
            "/api/v1/categories",
            headers=auth_headers,
            json={
                "name": "Custom Documents",
                "description": "My custom docs",
                "rules": {
                    "extensions": [".txt", ".md"],
                    "keywords": ["draft"],
                },
                "color": "#FF5733",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Custom Documents"
        assert data["is_custom"] is True
        assert "id" in data
    
    def test_create_category_duplicate_name(self, client, auth_headers):
        """Test creating category with duplicate name."""
        # Create first category
        client.post(
            "/api/v1/categories",
            headers=auth_headers,
            json={
                "name": "Test Category",
                "rules": {"extensions": [".test"]},
            },
        )
        
        # Try to create another with same name
        response = client.post(
            "/api/v1/categories",
            headers=auth_headers,
            json={
                "name": "Test Category",
                "rules": {"extensions": [".test2"]},
            },
        )
        
        assert response.status_code == 400
    
    def test_get_category(self, client, auth_headers):
        """Test getting a specific category."""
        # First get list to find a category ID
        list_response = client.get("/api/v1/categories", headers=auth_headers)
        category_id = list_response.json()["categories"][0]["id"]
        
        # Get specific category
        response = client.get(
            f"/api/v1/categories/{category_id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == category_id
    
    def test_delete_custom_category(self, client, auth_headers):
        """Test deleting a custom category."""
        # Create category
        create_response = client.post(
            "/api/v1/categories",
            headers=auth_headers,
            json={
                "name": "Deletable Category",
                "rules": {"extensions": [".del"]},
            },
        )
        category_id = create_response.json()["id"]
        
        # Delete it
        response = client.delete(
            f"/api/v1/categories/{category_id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 204
        
        # Verify it's deleted
        verify_response = client.get(
            f"/api/v1/categories/{category_id}",
            headers=auth_headers,
        )
        assert verify_response.status_code == 404
    
    def test_cannot_delete_default_category(self, client, auth_headers):
        """Test that default categories cannot be deleted."""
        response = client.delete(
            "/api/v1/categories/documents",
            headers=auth_headers,
        )
        
        assert response.status_code == 403
