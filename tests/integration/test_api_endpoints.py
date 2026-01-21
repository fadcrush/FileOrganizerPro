"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from src.backend.api.main import app
from src.backend.database import SessionLocal, init_db
from src.backend.models import User, Operation, APIKey, OperationStatus, OperationType
from src.backend.services.auth import hash_password, create_access_token


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Initialize database before tests."""
    init_db()


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
        full_name="Test User",
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


class TestAuthEndpoints:
    """Tests for authentication endpoints."""
    
    def test_signup(self, client):
        """Test user signup."""
        response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "secure_password_123",
                "full_name": "New User",
            },
        )
        
        assert response.status_code == 201
        assert "access_token" in response.json()
        assert "refresh_token" in response.json()
        assert response.json()["token_type"] == "bearer"
    
    def test_signup_duplicate_email(self, client, test_user):
        """Test signup with duplicate email."""
        response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": test_user.email,
                "username": "different_user",
                "password": "secure_password_123",
                "full_name": "Different User",
            },
        )
        
        assert response.status_code == 400
    
    def test_login(self, client, test_user):
        """Test user login."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "password123",
            },
        )
        
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert "refresh_token" in response.json()
    
    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "wrong_password",
            },
        )
        
        assert response.status_code == 401
    
    def test_get_profile(self, client, auth_headers, test_user):
        """Test getting user profile."""
        response = client.get(
            "/api/v1/auth/me",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
    
    def test_get_profile_unauthorized(self, client):
        """Test accessing profile without auth."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401


class TestOperationsEndpoints:
    """Tests for file operations endpoints."""
    
    def test_start_organization(self, client, auth_headers, tmp_path):
        """Test starting file organization."""
        response = client.post(
            "/api/v1/operations",
            headers=auth_headers,
            json={
                "root_path": str(tmp_path),
                "operation_type": "organize",
                "organization_mode": "category_year",
            },
        )
        
        assert response.status_code == 202
        assert "operation_id" in response.json()
    
    def test_list_operations(self, client, auth_headers, db_session, test_user):
        """Test listing operations."""
        # Create test operation
        operation = Operation(
            user_id=test_user.id,
            operation_type=OperationType.ORGANIZE,
            status=OperationStatus.COMPLETED,
            root_path="/test/path",
        )
        db_session.add(operation)
        db_session.commit()
        
        response = client.get(
            "/api/v1/operations",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "operations" in data
        assert len(data["operations"]) > 0
    
    def test_get_operation_status(self, client, auth_headers, db_session, test_user):
        """Test getting operation status."""
        # Create test operation
        operation = Operation(
            user_id=test_user.id,
            operation_type=OperationType.ORGANIZE,
            status=OperationStatus.RUNNING,
            root_path="/test/path",
            files_scanned=100,
            files_processed=50,
        )
        db_session.add(operation)
        db_session.commit()
        
        response = client.get(
            f"/api/v1/operations/{operation.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["files_scanned"] == 100
    
    def test_rollback_operation(self, client, auth_headers, db_session, test_user):
        """Test rolling back an operation."""
        # Create completed operation
        operation = Operation(
            user_id=test_user.id,
            operation_type=OperationType.ORGANIZE,
            status=OperationStatus.COMPLETED,
            root_path="/test/path",
        )
        db_session.add(operation)
        db_session.commit()
        
        response = client.post(
            f"/api/v1/operations/{operation.id}/rollback",
            headers=auth_headers,
        )
        
        assert response.status_code in [200, 202]  # Accepted or OK


class TestHealthEndpoints:
    """Tests for health check endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_api_status(self, client):
        """Test API status endpoint."""
        response = client.get("/api/v1/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "version" in data


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_invalid_json(self, client, auth_headers):
        """Test handling of invalid JSON."""
        response = client.post(
            "/api/v1/operations",
            headers=auth_headers,
            content="invalid json {",
        )
        
        assert response.status_code == 422
    
    def test_missing_required_field(self, client, auth_headers):
        """Test handling of missing required field."""
        response = client.post(
            "/api/v1/operations",
            headers=auth_headers,
            json={"operation_type": "organize"},  # Missing root_path
        )
        
        assert response.status_code == 422
    
    def test_not_found(self, client, auth_headers):
        """Test handling of not found resource."""
        response = client.get(
            "/api/v1/operations/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        
        assert response.status_code == 404
