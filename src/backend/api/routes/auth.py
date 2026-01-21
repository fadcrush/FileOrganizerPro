"""Authentication routes for signup and login."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from src.backend.database import get_db
from src.backend.models import User
from src.backend.services.auth import (
    authenticate_user,
    create_user,
    create_access_token,
    create_refresh_token,
    verify_token,
)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


# Request/Response schemas
class SignupRequest(BaseModel):
    """User signup request."""
    
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=100, description="Unique username")
    password: str = Field(..., min_length=8, description="Password (min 8 chars)")
    full_name: str = Field("", max_length=255, description="Full name (optional)")


class LoginRequest(BaseModel):
    """User login request."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="Password")


class TokenResponse(BaseModel):
    """Token response for login/signup."""
    
    access_token: str = Field(..., description="JWT access token (expires in 30 min)")
    refresh_token: str = Field(..., description="JWT refresh token (expires in 7 days)")
    token_type: str = Field("bearer", description="Token type")
    user_id: UUID = Field(..., description="User ID")
    subscription_tier: str = Field(..., description="User subscription tier")


class UserResponse(BaseModel):
    """User profile response."""
    
    id: UUID
    email: str
    username: str
    full_name: str
    subscription_tier: str
    storage_quota_gb: int
    storage_used_bytes: int
    is_active: bool
    created_at: str


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(request: SignupRequest) -> TokenResponse:
    """Register a new user account.
    
    Returns JWT access and refresh tokens on success.
    
    Args:
        request: Signup credentials
        
    Returns:
        TokenResponse with JWT tokens and user info
        
    Raises:
        HTTPException: If email or username already exists
    """
    # Create new user
    user = create_user(
        email=request.email,
        username=request.username,
        password=request.password,
        full_name=request.full_name,
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already exists",
        )
    
    # Generate tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id,
        subscription_tier=user.subscription_tier,
    )


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest) -> TokenResponse:
    """Authenticate user and return JWT tokens.
    
    Args:
        request: Login credentials (email + password)
        
    Returns:
        TokenResponse with JWT tokens
        
    Raises:
        HTTPException: If credentials are invalid
    """
    user = authenticate_user(request.email, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    # Generate tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id,
        subscription_tier=user.subscription_tier,
    )


@router.post("/refresh")
def refresh(request: dict) -> TokenResponse:
    """Refresh access token using refresh token.
    
    Args:
        request: JSON with "refresh_token" field
        
    Returns:
        TokenResponse with new access token
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    refresh_token = request.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing refresh_token",
        )
    
    result = verify_token(refresh_token)
    
    if result is None or result[1] != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    user_id, _ = result
    
    # Generate new access token
    access_token = create_access_token(user_id)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,  # Can also generate new refresh token
        user_id=user_id,
        subscription_tier="free",  # Would need to fetch from DB
    )


@router.get("/me", response_model=UserResponse)
def get_profile(user_id: UUID = Depends(get_current_user), db: Session = Depends(get_db)) -> UserResponse:
    """Get current user profile.
    
    Requires authentication via Authorization header.
    
    Args:
        user_id: Current user ID (from token)
        db: Database session
        
    Returns:
        UserResponse with profile data
        
    Raises:
        HTTPException: If user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name or "",
        subscription_tier=user.subscription_tier,
        storage_quota_gb=user.storage_quota_gb,
        storage_used_bytes=user.storage_used_bytes,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
    )


# Import dependency
from src.backend.middleware.auth import get_current_user
