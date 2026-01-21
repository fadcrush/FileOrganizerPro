"""Duplicate management endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from src.backend.database import get_db
from src.backend.models.operation import Operation, FileRecord, OperationStatus
from src.backend.models.user import User
from src.backend.middleware.auth import get_current_user


router = APIRouter(prefix="/api/v1/duplicates", tags=["duplicates"])


class DuplicateFile(BaseModel):
    """Duplicate file information."""
    
    path: str = Field(..., description="File path")
    size_bytes: int = Field(..., description="File size in bytes")
    modified_at: float = Field(..., description="Last modified timestamp")


class DuplicateGroup(BaseModel):
    """Group of duplicate files."""
    
    hash_value: str = Field(..., description="File hash (MD5/SHA256)")
    file_count: int = Field(..., description="Number of duplicates")
    total_size_bytes: int = Field(..., description="Total size of all duplicates")
    average_size_bytes: int = Field(..., description="Average file size")
    files: List[DuplicateFile] = Field(..., description="List of duplicate files")


class DuplicatesResponse(BaseModel):
    """Duplicates listing response."""
    
    operation_id: UUID = Field(..., description="Operation ID")
    total_groups: int = Field(..., description="Number of duplicate groups")
    total_duplicates: int = Field(..., description="Total duplicate files")
    total_size_bytes: int = Field(..., description="Total space from duplicates")
    duplicates: List[DuplicateGroup] = Field(..., description="Duplicate groups")


@router.get("/{operation_id}", response_model=DuplicatesResponse)
async def get_duplicates(
    operation_id: UUID,
    limit: Optional[int] = None,
    offset: int = 0,
    min_size_bytes: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DuplicatesResponse:
    """
    Get duplicates found in an operation.
    
    Query Parameters:
    - limit: Maximum number of duplicate groups to return
    - offset: Number of groups to skip
    - min_size_bytes: Only show duplicates larger than this size
    
    Returns:
    - Duplicate groups with file listings
    - Total statistics (count, size)
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
    
    # Get all file records for this operation
    file_records = db.query(FileRecord).filter(
        FileRecord.operation_id == operation_id,
        FileRecord.status == "completed",
    ).all()
    
    # Group by hash (duplicates have same hash)
    hash_groups = {}
    for record in file_records:
        hash_val = record.file_hash or "unknown"
        if hash_val not in hash_groups:
            hash_groups[hash_val] = []
        hash_groups[hash_val].append(record)
    
    # Filter to only duplicates (groups with 2+ files)
    duplicate_groups = []
    for hash_val, records in hash_groups.items():
        if len(records) >= 2:
            # Filter by minimum size
            if min(r.file_size_bytes for r in records) >= min_size_bytes:
                total_size = sum(r.file_size_bytes for r in records)
                avg_size = total_size // len(records)
                
                duplicate_groups.append({
                    "hash_value": hash_val,
                    "file_count": len(records),
                    "total_size_bytes": total_size,
                    "average_size_bytes": avg_size,
                    "files": [
                        DuplicateFile(
                            path=r.new_path or r.original_path,
                            size_bytes=r.file_size_bytes,
                            modified_at=r.modified_at or 0.0,
                        )
                        for r in records
                    ],
                })
    
    # Sort by total size (largest first)
    duplicate_groups.sort(
        key=lambda x: x["total_size_bytes"],
        reverse=True,
    )
    
    # Apply pagination
    total_groups = len(duplicate_groups)
    if limit:
        duplicate_groups = duplicate_groups[offset:offset + limit]
    else:
        duplicate_groups = duplicate_groups[offset:]
    
    # Calculate totals
    total_duplicates = sum(g["file_count"] for g in duplicate_groups)
    total_size = sum(g["total_size_bytes"] for g in duplicate_groups)
    
    return DuplicatesResponse(
        operation_id=operation_id,
        total_groups=total_groups,
        total_duplicates=total_duplicates,
        total_size_bytes=total_size,
        duplicates=[DuplicateGroup(**g) for g in duplicate_groups],
    )


@router.delete("/{operation_id}/{hash_value}")
async def delete_duplicates(
    operation_id: UUID,
    hash_value: str,
    keep_original: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Delete duplicate files for a given hash.
    
    Parameters:
    - operation_id: Operation containing the duplicates
    - hash_value: Hash of duplicates to delete
    - keep_original: If True, keep the first file and delete others
    
    Returns:
    - Number of files deleted
    - Total space freed
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
    
    # Get file records matching hash
    file_records = db.query(FileRecord).filter(
        FileRecord.operation_id == operation_id,
        FileRecord.file_hash == hash_value,
    ).all()
    
    if not file_records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No duplicates found for this hash",
        )
    
    # Mark duplicates for deletion (skip first one if keep_original)
    deleted_count = 0
    space_freed = 0
    
    for idx, record in enumerate(file_records):
        if keep_original and idx == 0:
            continue  # Keep the first one
        
        # TODO: Implement actual file deletion via StorageProvider
        record.status = "deleted"
        space_freed += record.file_size_bytes
        deleted_count += 1
    
    db.commit()
    
    return {
        "deleted_count": deleted_count,
        "space_freed_bytes": space_freed,
        "operation_id": str(operation_id),
    }
