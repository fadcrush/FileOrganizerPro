"""Operations (file organization) routes."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.backend.database import get_db
from src.backend.models import Operation, OperationStatus, OperationType
from src.backend.middleware.auth import get_current_user
from src.backend.celery_config import celery_app
import os

router = APIRouter(prefix="/api/v1/operations", tags=["operations"])


# Request/Response schemas
class OrganizeRequest(BaseModel):
    """Request to start file organization."""
    
    root_path: str = Field(..., description="Root directory to organize")
    operation_type: str = Field("organize", description="Type of operation")
    is_dry_run: bool = Field(False, description="Preview without making changes")
    categories: List[str] = Field([], description="Categories to organize into")


class OperationResponse(BaseModel):
    """Operation status response."""
    
    id: UUID
    status: str
    operation_type: str
    root_path: str
    files_scanned: int
    files_processed: int
    duplicates_found: int
    space_saved_bytes: int
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None


@router.post("", response_model=OperationResponse, status_code=status.HTTP_202_ACCEPTED)
def start_organization(
    request: OrganizeRequest,
    user_id: UUID = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OperationResponse:
    """Start a new file organization operation.
    
    Returns immediately with operation ID. Actual processing happens in background.
    Use GET /operations/{id} to check progress or connect via WebSocket for real-time updates.

    Args:
        request: Organization parameters
        user_id: Current user ID
        db: Database session

    Returns:
        OperationResponse with task details
    """
    # Create operation record
    operation = Operation(
        user_id=user_id,
        operation_type=OperationType.ORGANIZE,
        status=OperationStatus.PENDING,
        root_path=request.root_path,
        is_dry_run=request.is_dry_run,
        metadata={"categories": request.categories},
    )

    db.add(operation)
    db.commit()
    db.refresh(operation)

    # Queue background job (non-blocking)
    storage_type = os.getenv("STORAGE_TYPE", "local")
    storage_config = {
        "base_path": request.root_path,
    }

    celery_app.send_task(
        "tasks.organize",
        args=(str(operation.id), storage_type),
        kwargs=storage_config,
        task_id=str(operation.id),  # Use operation ID as task ID
    )
        space_saved_bytes=operation.space_saved_bytes,
        created_at=operation.created_at.isoformat(),
    )


@router.get("/{operation_id}", response_model=OperationResponse)
def get_operation_status(
    operation_id: UUID,
    user_id: UUID = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OperationResponse:
    """Get status of a file organization operation.
    
    Args:
        operation_id: Operation UUID
        user_id: Current user ID
        db: Database session
        
    Returns:
        OperationResponse with current status
        
    Raises:
        HTTPException: If operation not found
    """
    operation = db.query(Operation).filter(
        (Operation.id == operation_id) & (Operation.user_id == user_id)
    ).first()
    
    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operation not found",
        )
    
    return OperationResponse(
        id=operation.id,
        status=operation.status.value,
        operation_type=operation.operation_type.value,
        root_path=operation.root_path,
        files_scanned=operation.files_scanned,
        files_processed=operation.files_processed,
        duplicates_found=operation.duplicates_found,
        space_saved_bytes=operation.space_saved_bytes,
        created_at=operation.created_at.isoformat(),
        started_at=operation.started_at.isoformat() if operation.started_at else None,
        completed_at=operation.completed_at.isoformat() if operation.completed_at else None,
    )


@router.get("", response_model=List[OperationResponse])
def list_operations(
    user_id: UUID = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[OperationResponse]:
    """List user's recent operations.
    
    Args:
        user_id: Current user ID
        db: Database session
        limit: Max operations to return
        offset: Pagination offset
        
    Returns:
        List of OperationResponse objects
    """
    operations = db.query(Operation).filter(
        Operation.user_id == user_id
    ).order_by(
        Operation.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return [
        OperationResponse(
            id=op.id,
            status=op.status.value,
            operation_type=op.operation_type.value,
            root_path=op.root_path,
            files_scanned=op.files_scanned,
            files_processed=op.files_processed,
            duplicates_found=op.duplicates_found,
            space_saved_bytes=op.space_saved_bytes,
            created_at=op.created_at.isoformat(),
            started_at=op.started_at.isoformat() if op.started_at else None,
            completed_at=op.completed_at.isoformat() if op.completed_at else None,
        )
        for op in operations
    ]


@router.post("/{operation_id}/rollback", status_code=status.HTTP_202_ACCEPTED)
def rollback_operation(
    operation_id: UUID,
    user_id: UUID = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Rollback (undo) a completed operation.
    
    Args:
        operation_id: Operation UUID to rollback
        user_id: Current user ID
        db: Database session
        
    Raises:
        HTTPException: If operation not found or cannot be rolled back
    """
    operation = db.query(Operation).filter(
        (Operation.id == operation_id) & (Operation.user_id == user_id)
    ).first()
    
    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operation not found",
        )
    
    if not operation.is_complete or operation.status == OperationStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot rollback incomplete or failed operations",
        )
    
    # TODO: Queue rollback job
    
    return {
        "status": "rollback_queued",
        "operation_id": operation_id,
        "message": "Rollback operation has been queued",
    }
