"""File operations listing endpoints."""

from typing import List, Optional, Literal
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel, Field

from src.backend.database import get_db
from src.backend.models.operation import Operation, FileRecord
from src.backend.models.user import User
from src.backend.middleware.auth import get_current_user


router = APIRouter(prefix="/api/v1/files", tags=["files"])


class FileOperation(BaseModel):
    """Single file operation record."""
    
    id: UUID = Field(..., description="Record ID")
    original_path: str = Field(..., description="Original file path")
    new_path: Optional[str] = Field(None, description="New file path after organization")
    category: Optional[str] = Field(None, description="Assigned category")
    status: str = Field(..., description="Operation status: completed, failed, skipped")
    size_bytes: int = Field(..., description="File size in bytes")
    error_message: Optional[str] = Field(None, description="Error if status is failed")
    created_at: datetime = Field(..., description="Record creation timestamp")


class FileOperationsResponse(BaseModel):
    """File operations listing response."""
    
    operation_id: UUID = Field(..., description="Parent operation ID")
    total_files: int = Field(..., description="Total file records")
    files_completed: int = Field(..., description="Successfully processed files")
    files_failed: int = Field(..., description="Failed file operations")
    files_skipped: int = Field(..., description="Skipped files")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Results per page")
    total_pages: int = Field(..., description="Total number of pages")
    files: List[FileOperation] = Field(..., description="File records for current page")


@router.get("", response_model=FileOperationsResponse)
async def list_files(
    operation_id: UUID,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(100, ge=1, le=1000, description="Results per page"),
    status_filter: Optional[Literal["completed", "failed", "skipped"]] = None,
    category_filter: Optional[str] = None,
    min_size_bytes: int = Query(0, ge=0, description="Minimum file size"),
    sort_by: Literal["created_at", "size_bytes", "path"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileOperationsResponse:
    """
    List file operations from a completed task.
    
    Query Parameters:
    - operation_id: Parent operation UUID
    - page: Page number (1-indexed)
    - page_size: Results per page (1-1000)
    - status_filter: Filter by status (completed, failed, skipped)
    - category_filter: Filter by category
    - min_size_bytes: Only show files larger than this
    - sort_by: Sort field (created_at, size_bytes, path)
    - sort_order: Sort direction (asc, desc)
    
    Returns:
    - Paginated file records
    - Status counts
    """
    # Verify operation exists and belongs to user
    operation = db.query(Operation).filter(
        Operation.id == operation_id,
        Operation.user_id == current_user.id,
    ).first()
    
    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operation not found",
        )
    
    # Build query
    query = db.query(FileRecord).filter(
        FileRecord.operation_id == operation_id,
        FileRecord.file_size_bytes >= min_size_bytes,
    )
    
    # Apply status filter
    if status_filter:
        query = query.filter(FileRecord.status == status_filter)
    
    # Apply category filter
    if category_filter:
        query = query.filter(FileRecord.category == category_filter)
    
    # Count totals before pagination
    total_files = query.count()
    
    # Apply sorting
    sort_column = {
        "created_at": FileRecord.created_at,
        "size_bytes": FileRecord.file_size_bytes,
        "path": FileRecord.new_path,
    }.get(sort_by, FileRecord.created_at)
    
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    # Apply pagination
    offset = (page - 1) * page_size
    total_pages = (total_files + page_size - 1) // page_size
    
    file_records = query.offset(offset).limit(page_size).all()
    
    # Count by status
    status_query = db.query(FileRecord).filter(
        FileRecord.operation_id == operation_id
    )
    files_completed = status_query.filter(FileRecord.status == "completed").count()
    files_failed = status_query.filter(FileRecord.status == "failed").count()
    files_skipped = status_query.filter(FileRecord.status == "skipped").count()
    
    return FileOperationsResponse(
        operation_id=operation_id,
        total_files=total_files,
        files_completed=files_completed,
        files_failed=files_failed,
        files_skipped=files_skipped,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        files=[
            FileOperation(
                id=record.id,
                original_path=record.original_path,
                new_path=record.new_path,
                category=record.category,
                status=record.status,
                size_bytes=record.file_size_bytes,
                error_message=record.error_message,
                created_at=record.created_at,
            )
            for record in file_records
        ],
    )


@router.get("/search", response_model=FileOperationsResponse)
async def search_files(
    operation_id: UUID,
    query: str = Query(..., min_length=1, description="Search query (path, category, or hash)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileOperationsResponse:
    """
    Search file operations by path, category, or hash.
    
    Parameters:
    - operation_id: Parent operation UUID
    - query: Search string
    - page: Page number
    - page_size: Results per page
    
    Returns:
    - Matching file records
    """
    # Verify operation
    operation = db.query(Operation).filter(
        Operation.id == operation_id,
        Operation.user_id == current_user.id,
    ).first()
    
    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operation not found",
        )
    
    # Search in multiple fields
    search_query = db.query(FileRecord).filter(
        FileRecord.operation_id == operation_id,
    ).filter(
        (FileRecord.original_path.ilike(f"%{query}%")) |
        (FileRecord.new_path.ilike(f"%{query}%")) |
        (FileRecord.category.ilike(f"%{query}%")) |
        (FileRecord.file_hash.ilike(f"%{query}%"))
    )
    
    total_files = search_query.count()
    offset = (page - 1) * page_size
    total_pages = (total_files + page_size - 1) // page_size
    
    file_records = search_query.offset(offset).limit(page_size).all()
    
    return FileOperationsResponse(
        operation_id=operation_id,
        total_files=total_files,
        files_completed=0,
        files_failed=0,
        files_skipped=0,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        files=[
            FileOperation(
                id=record.id,
                original_path=record.original_path,
                new_path=record.new_path,
                category=record.category,
                status=record.status,
                size_bytes=record.file_size_bytes,
                error_message=record.error_message,
                created_at=record.created_at,
            )
            for record in file_records
        ],
    )
