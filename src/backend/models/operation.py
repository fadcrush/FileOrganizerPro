"""Organization operation models tracking file organization tasks."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Enum as SQLEnum, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSON

from src.backend.database import Base


class OperationStatus(str, Enum):
    """Status of an organization operation."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OperationType(str, Enum):
    """Type of organization operation."""

    ORGANIZE = "organize"
    DUPLICATE_CLEANUP = "duplicate_cleanup"
    ROLLBACK = "rollback"
    PREVIEW = "preview"


class Operation(Base):
    """Tracks file organization operations for auditing and progress tracking."""

    __tablename__ = "operations"
    __table_args__ = (
        Index("idx_user_status", "user_id", "status"),
        Index("idx_user_created", "user_id", "created_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Operation details
    operation_type = Column(SQLEnum(OperationType), nullable=False)
    status = Column(SQLEnum(OperationStatus), default=OperationStatus.PENDING, nullable=False)

    # Root directory being organized
    root_path = Column(String(1024), nullable=False)
    is_dry_run = Column(Boolean, default=False, nullable=False)

    # Results
    files_scanned = Column(Integer, default=0, nullable=False)
    files_processed = Column(Integer, default=0, nullable=False)
    files_skipped = Column(Integer, default=0, nullable=False)
    space_saved_bytes = Column(BigInteger, default=0, nullable=False)
    duplicates_found = Column(Integer, default=0, nullable=False)

    # Error tracking
    error_message = Column(String(1024), nullable=True)
    error_count = Column(Integer, default=0, nullable=False)

    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Metadata
    metadata = Column(JSON, default=dict, nullable=False)  # Custom data (categories used, etc.)

    def __repr__(self) -> str:
        return f"<Operation(id={self.id}, type={self.operation_type}, status={self.status})>"

    @property
    def duration_seconds(self) -> Optional[float]:
        """Get operation duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_complete(self) -> bool:
        """Check if operation is complete."""
        return self.status in (OperationStatus.COMPLETED, OperationStatus.FAILED, OperationStatus.CANCELLED)


class FileRecord(Base):
    """Tracks individual file movements for rollback capability."""

    __tablename__ = "file_records"
    __table_args__ = (
        Index("idx_operation_user", "operation_id", "user_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operation_id = Column(UUID(as_uuid=True), ForeignKey("operations.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # File details
    original_path = Column(String(1024), nullable=False)
    new_path = Column(String(1024), nullable=True)  # NULL if not moved
    file_name = Column(String(255), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    file_hash = Column(String(64), nullable=True)  # SHA256 hash

    # Categorization
    category = Column(String(100), nullable=True)
    is_duplicate = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<FileRecord(id={self.id}, file={self.file_name}, new_path={self.new_path})>"
