"""Report generation endpoints."""

from typing import Optional, Literal
from uuid import UUID
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import json

from src.backend.database import get_db
from src.backend.models.operation import Operation, FileRecord
from src.backend.models.user import User
from src.backend.middleware.auth import get_current_user


router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


class StatsSummary(BaseModel):
    """Operation statistics summary."""
    
    total_files_scanned: int = Field(..., description="Total files processed")
    total_files_moved: int = Field(..., description="Files successfully moved")
    total_files_failed: int = Field(..., description="Files that failed")
    total_files_skipped: int = Field(..., description="Files skipped")
    total_size_bytes: int = Field(..., description="Total size of organized files")
    duplicates_found: int = Field(..., description="Number of duplicate groups")
    duplicate_files: int = Field(..., description="Total duplicate files detected")
    space_saved_bytes: int = Field(..., description="Space saved from duplicates")


class CategoryStats(BaseModel):
    """Statistics for a single category."""
    
    category: str = Field(..., description="Category name")
    file_count: int = Field(..., description="Files in category")
    total_size_bytes: int = Field(..., description="Total size in category")
    percentage: float = Field(..., description="Percentage of total")


class ReportData(BaseModel):
    """Complete report data."""
    
    operation_id: UUID = Field(..., description="Operation ID")
    operation_type: str = Field(..., description="Type of operation")
    status: str = Field(..., description="Operation status")
    start_time: Optional[datetime] = Field(None, description="Start timestamp")
    end_time: Optional[datetime] = Field(None, description="End timestamp")
    duration_seconds: Optional[float] = Field(None, description="Duration in seconds")
    
    stats: StatsSummary = Field(..., description="Overall statistics")
    category_breakdown: list[CategoryStats] = Field(..., description="Per-category breakdown")
    
    top_categories: list[CategoryStats] = Field(..., description="Top 5 categories by size")
    largest_files: list[dict] = Field(..., description="Top 10 largest files")


@router.get("/{operation_id}", response_model=ReportData)
async def get_report(
    operation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReportData:
    """
    Get complete report for an operation.
    
    Returns:
    - Overall statistics
    - Category breakdown
    - Top files and categories
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
    
    # Get all file records
    file_records = db.query(FileRecord).filter(
        FileRecord.operation_id == operation_id,
    ).all()
    
    # Calculate statistics
    total_files = len(file_records)
    files_completed = sum(1 for r in file_records if r.status == "completed")
    files_failed = sum(1 for r in file_records if r.status == "failed")
    files_skipped = sum(1 for r in file_records if r.status == "skipped")
    
    total_size = sum(r.file_size_bytes for r in file_records)
    
    # Count duplicates
    hash_groups = {}
    for record in file_records:
        if record.file_hash:
            if record.file_hash not in hash_groups:
                hash_groups[record.file_hash] = []
            hash_groups[record.file_hash].append(record)
    
    duplicates_found = sum(1 for g in hash_groups.values() if len(g) > 1)
    duplicate_files = sum(len(g) for g in hash_groups.values() if len(g) > 1)
    
    # Space from duplicates (all but first in each group)
    space_saved = sum(
        sum(r.file_size_bytes for r in g[1:])
        for g in hash_groups.values() if len(g) > 1
    )
    
    # Category breakdown
    category_counts = {}
    category_sizes = {}
    
    for record in file_records:
        if record.status == "completed" and record.category:
            cat = record.category
            category_counts[cat] = category_counts.get(cat, 0) + 1
            category_sizes[cat] = category_sizes.get(cat, 0) + record.file_size_bytes
    
    category_breakdown = [
        CategoryStats(
            category=cat,
            file_count=category_counts.get(cat, 0),
            total_size_bytes=category_sizes.get(cat, 0),
            percentage=(category_sizes.get(cat, 0) / total_size * 100) if total_size > 0 else 0,
        )
        for cat in sorted(category_counts.keys())
    ]
    
    # Top categories by size
    top_categories = sorted(
        category_breakdown,
        key=lambda x: x.total_size_bytes,
        reverse=True,
    )[:5]
    
    # Largest files
    largest_files = sorted(
        file_records,
        key=lambda r: r.file_size_bytes,
        reverse=True,
    )[:10]
    
    largest_files_data = [
        {
            "path": f.new_path or f.original_path,
            "size_bytes": f.file_size_bytes,
            "category": f.category,
            "size_mb": f.file_size_bytes / (1024 * 1024),
        }
        for f in largest_files
    ]
    
    # Calculate duration
    duration_seconds = None
    if operation.created_at and operation.updated_at:
        duration_seconds = (operation.updated_at - operation.created_at).total_seconds()
    
    return ReportData(
        operation_id=operation_id,
        operation_type=operation.operation_type,
        status=operation.status,
        start_time=operation.created_at,
        end_time=operation.updated_at,
        duration_seconds=duration_seconds,
        stats=StatsSummary(
            total_files_scanned=total_files,
            total_files_moved=files_completed,
            total_files_failed=files_failed,
            total_files_skipped=files_skipped,
            total_size_bytes=total_size,
            duplicates_found=duplicates_found,
            duplicate_files=duplicate_files,
            space_saved_bytes=space_saved,
        ),
        category_breakdown=category_breakdown,
        top_categories=top_categories,
        largest_files=largest_files_data,
    )


@router.get("/{operation_id}/export")
async def export_report(
    operation_id: UUID,
    format: Literal["json", "csv", "html"] = "json",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Export report in various formats.
    
    Parameters:
    - operation_id: Operation to report on
    - format: Export format (json, csv, html)
    
    Returns:
    - Report file in requested format
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
    
    # Get report data
    report = await get_report(operation_id, current_user, db)
    
    if format == "json":
        return {
            "content": report.dict(),
            "format": "json",
        }
    
    elif format == "csv":
        # Generate CSV
        csv_content = "Path,Category,Size (bytes),Status\n"
        
        file_records = db.query(FileRecord).filter(
            FileRecord.operation_id == operation_id,
        ).all()
        
        for record in file_records:
            path = record.new_path or record.original_path
            path = path.replace(",", "\\,")  # Escape commas
            csv_content += f"{path},{record.category},{record.file_size_bytes},{record.status}\n"
        
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=report_{operation_id}.csv"
            },
        )
    
    elif format == "html":
        # Generate HTML report
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>FileOrganizer Report - {operation_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .stat {{ font-size: 18px; font-weight: bold; color: #2196F3; }}
                .category-section {{ margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>File Organization Report</h1>
            <p>Operation ID: {operation_id}</p>
            <p>Status: {report.status}</p>
            <p>Duration: {report.duration_seconds:.1f} seconds</p>
            
            <div class="category-section">
                <h2>Statistics</h2>
                <table>
                    <tr>
                        <td>Files Scanned</td>
                        <td class="stat">{report.stats.total_files_scanned}</td>
                    </tr>
                    <tr>
                        <td>Files Moved</td>
                        <td class="stat">{report.stats.total_files_moved}</td>
                    </tr>
                    <tr>
                        <td>Duplicates Found</td>
                        <td class="stat">{report.stats.duplicate_files}</td>
                    </tr>
                    <tr>
                        <td>Space Saved</td>
                        <td class="stat">{report.stats.space_saved_bytes / (1024*1024):.2f} MB</td>
                    </tr>
                </table>
            </div>
            
            <div class="category-section">
                <h2>Top Categories</h2>
                <table>
                    <tr>
                        <th>Category</th>
                        <th>Files</th>
                        <th>Size (MB)</th>
                    </tr>
        """
        
        for cat in report.top_categories:
            html_content += f"""
                    <tr>
                        <td>{cat.category}</td>
                        <td>{cat.file_count}</td>
                        <td>{cat.total_size_bytes / (1024*1024):.2f}</td>
                    </tr>
            """
        
        html_content += """
                </table>
            </div>
        </body>
        </html>
        """
        
        return StreamingResponse(
            iter([html_content]),
            media_type="text/html",
            headers={
                "Content-Disposition": f"attachment; filename=report_{operation_id}.html"
            },
        )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid format. Supported: json, csv, html",
        )
