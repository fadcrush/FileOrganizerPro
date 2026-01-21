"""Tests for WebSocket operations endpoint."""

import pytest
import json
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime

from src.backend.api.main import app
from src.backend.database import SessionLocal
from src.backend.models import User, Operation, OperationStatus, OperationType
from src.backend.services.auth import create_access_token, hash_password


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


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
def test_operation(db_session, test_user):
    """Create test operation."""
    operation = Operation(
        user_id=test_user.id,
        operation_type=OperationType.ORGANIZE,
        status=OperationStatus.RUNNING,
        root_path="/test/path",
        files_scanned=100,
        files_processed=50,
        duplicates_found=5,
    )
    db_session.add(operation)
    db_session.commit()
    db_session.refresh(operation)
    return operation


def test_websocket_connection(client, auth_token, test_operation):
    """Test WebSocket connection."""
    with client.websocket_connect(
        f"/ws/operations/{test_operation.id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    ) as websocket:
        # Should receive initial status
        data = websocket.receive_json()
        assert data["type"] == "status"
        assert data["status"] == "running"


def test_websocket_invalid_operation_id(client, auth_token):
    """Test WebSocket with invalid operation ID."""
    with pytest.raises(Exception):
        with client.websocket_connect(
            "/ws/operations/invalid-id",
            headers={"Authorization": f"Bearer {auth_token}"},
        ) as websocket:
            websocket.receive_json()


def test_websocket_progress_updates(client, auth_token, test_operation):
    """Test receiving progress updates."""
    with client.websocket_connect(
        f"/ws/operations/{test_operation.id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    ) as websocket:
        # Receive initial status
        data = websocket.receive_json(timeout=2)
        assert data["type"] == "status"
        
        # Receive progress update
        data = websocket.receive_json(timeout=2)
        assert data["type"] == "progress"
        assert "files_scanned" in data
        assert "files_processed" in data


@pytest.fixture
def db_session():
    """Create database session for tests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
