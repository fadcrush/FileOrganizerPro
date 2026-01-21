"""Category management endpoints."""

from typing import List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.backend.database import get_db
from src.backend.models.user import User
from src.backend.middleware.auth import get_current_user


router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


class CategoryRules(BaseModel):
    """File matching rules for a category."""
    
    extensions: List[str] = Field(..., description="File extensions (e.g., ['.pdf', '.doc'])")
    keywords: List[str] = Field(default_factory=list, description="Keywords in filename")


class CategoryRequest(BaseModel):
    """Category creation/update request."""
    
    name: str = Field(..., min_length=1, max_length=50, description="Category name")
    description: Optional[str] = Field(None, max_length=200)
    rules: CategoryRules = Field(..., description="Matching rules")
    color: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$", description="Hex color")
    icon: Optional[str] = Field(None, max_length=50, description="Icon name/emoji")


class CategoryResponse(BaseModel):
    """Category response model."""
    
    id: str = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    description: Optional[str] = Field(None)
    rules: CategoryRules = Field(..., description="Matching rules")
    color: Optional[str] = Field(None)
    icon: Optional[str] = Field(None)
    is_custom: bool = Field(..., description="Whether this is a custom category")
    file_count: int = Field(default=0, description="Files in this category")


class CategoriesResponse(BaseModel):
    """List of categories response."""
    
    categories: List[CategoryResponse] = Field(..., description="All categories")
    custom_count: int = Field(..., description="Number of custom categories")


# In-memory storage for demo (would be database in production)
CUSTOM_CATEGORIES = {}

DEFAULT_CATEGORIES = {
    "documents": CategoryResponse(
        id="documents",
        name="Documents",
        description="Word docs, PDFs, spreadsheets",
        rules=CategoryRules(extensions=[".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"]),
        is_custom=False,
        file_count=0,
    ),
    "images": CategoryResponse(
        id="images",
        name="Images",
        description="Photo and image files",
        rules=CategoryRules(extensions=[".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"]),
        is_custom=False,
        file_count=0,
    ),
    "videos": CategoryResponse(
        id="videos",
        name="Videos",
        description="Video files",
        rules=CategoryRules(extensions=[".mp4", ".avi", ".mkv", ".mov", ".wmv"]),
        is_custom=False,
        file_count=0,
    ),
    "audio": CategoryResponse(
        id="audio",
        name="Audio",
        description="Audio files",
        rules=CategoryRules(extensions=[".mp3", ".wav", ".flac", ".aac", ".m4a"]),
        is_custom=False,
        file_count=0,
    ),
    "code": CategoryResponse(
        id="code",
        name="Code",
        description="Source code files",
        rules=CategoryRules(extensions=[".py", ".js", ".java", ".cpp", ".cs", ".php"]),
        is_custom=False,
        file_count=0,
    ),
}


@router.get("", response_model=CategoriesResponse)
async def list_categories(
    include_defaults: bool = True,
    current_user: User = Depends(get_current_user),
) -> CategoriesResponse:
    """
    List all available categories.
    
    Query Parameters:
    - include_defaults: Include default categories (default: true)
    
    Returns:
    - All categories (default + custom)
    - Count of custom categories
    """
    categories = []
    
    if include_defaults:
        categories.extend(DEFAULT_CATEGORIES.values())
    
    categories.extend(CUSTOM_CATEGORIES.values())
    
    return CategoriesResponse(
        categories=categories,
        custom_count=len(CUSTOM_CATEGORIES),
    )


@router.post("", response_model=CategoryResponse, status_code=201)
async def create_category(
    request: CategoryRequest,
    current_user: User = Depends(get_current_user),
) -> CategoryResponse:
    """
    Create a custom category.
    
    Parameters:
    - name: Category name (unique)
    - description: Category description
    - rules: File matching rules (extensions, keywords)
    - color: Hex color for UI display
    - icon: Icon name or emoji
    
    Returns:
    - Created category with ID
    """
    # Check for duplicate names
    existing_names = {
        cat.name.lower() for cat in DEFAULT_CATEGORIES.values()
    } | {cat.name.lower() for cat in CUSTOM_CATEGORIES.values()}
    
    if request.name.lower() in existing_names:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category '{request.name}' already exists",
        )
    
    # Validate rules
    if not request.rules.extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one extension is required",
        )
    
    # Create category
    category_id = str(uuid4())
    category = CategoryResponse(
        id=category_id,
        name=request.name,
        description=request.description,
        rules=request.rules,
        color=request.color,
        icon=request.icon,
        is_custom=True,
        file_count=0,
    )
    
    CUSTOM_CATEGORIES[category_id] = category
    
    return category


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: str,
    current_user: User = Depends(get_current_user),
) -> CategoryResponse:
    """Get a specific category by ID."""
    # Check default categories
    if category_id in DEFAULT_CATEGORIES:
        return DEFAULT_CATEGORIES[category_id]
    
    # Check custom categories
    if category_id in CUSTOM_CATEGORIES:
        return CUSTOM_CATEGORIES[category_id]
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Category not found",
    )


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str,
    request: CategoryRequest,
    current_user: User = Depends(get_current_user),
) -> CategoryResponse:
    """
    Update a custom category.
    
    Note: Default categories cannot be modified
    """
    # Cannot modify default categories
    if category_id in DEFAULT_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Default categories cannot be modified",
        )
    
    if category_id not in CUSTOM_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    
    # Validate rules
    if not request.rules.extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one extension is required",
        )
    
    # Update category
    category = CUSTOM_CATEGORIES[category_id]
    category.name = request.name
    category.description = request.description
    category.rules = request.rules
    category.color = request.color
    category.icon = request.icon
    
    return category


@router.delete("/{category_id}", status_code=204)
async def delete_category(
    category_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Delete a custom category.
    
    Note: Default categories cannot be deleted
    """
    # Cannot delete default categories
    if category_id in DEFAULT_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Default categories cannot be deleted",
        )
    
    if category_id not in CUSTOM_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    
    del CUSTOM_CATEGORIES[category_id]
    return None


@router.post("/{category_id}/reset", response_model=CategoryResponse)
async def reset_category(
    category_id: str,
    current_user: User = Depends(get_current_user),
) -> CategoryResponse:
    """
    Reset a category to default rules.
    
    Only works for default categories.
    """
    if category_id not in DEFAULT_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found or is not a default category",
        )
    
    return DEFAULT_CATEGORIES[category_id]
