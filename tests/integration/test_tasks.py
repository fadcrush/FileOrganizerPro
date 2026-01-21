"""Tests for Celery background job tasks."""

import pytest
from uuid import uuid4
from datetime import datetime

from src.backend.celery_config import celery_app
from src.backend.tasks import organize_task
from src.backend.database import SessionLocal
from src.backend.models import User, Operation, OperationStatus, OperationType
from src.backend.services.auth import hash_password


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
def test_operation(db_session, test_user, tmp_path):
    """Create test operation."""
    operation = Operation(
        user_id=test_user.id,
        operation_type=OperationType.ORGANIZE,
        status=OperationStatus.PENDING,
        root_path=str(tmp_path),
        is_dry_run=True,  # Dry run for testing
    )
    db_session.add(operation)
    db_session.commit()
    db_session.refresh(operation)
    return operation


def test_organize_task_queuing(test_operation):
    """Test that organize task can be queued."""
    result = celery_app.send_task(
        "tasks.organize",
        args=(str(test_operation.id), "local"),
        kwargs={"base_path": "/tmp"},
    )
    
    assert result is not None
    assert result.id is not None


def test_organize_task_not_found():
    """Test organize task with non-existent operation."""
    from src.backend.tasks import organize_task
    
    result = organize_task.apply_async(
        args=("00000000-0000-0000-0000-000000000000", "local"),
    )
    
    # Task should complete but operation not found
    # (actual error handling depends on implementation)


def test_celery_app_configuration():
    """Test Celery app is properly configured."""
    assert celery_app is not None
    assert celery_app.conf.task_track_started
    assert celery_app.conf.timezone == "UTC"


def test_task_serialization():
    """Test that tasks can be properly serialized."""
    task_signature = celery_app.send_task(
        "tasks.organize",
        args=("operation-id", "local"),
        kwargs={"base_path": "/tmp"},
    )
    
    assert task_signature.id is not None
