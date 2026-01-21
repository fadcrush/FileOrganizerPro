"""Authentication service with JWT token management."""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import uuid

from passlib.context import CryptContext
from jwt import encode, decode, ExpiredSignatureError, InvalidTokenError

from src.backend.database import SessionLocal
from src.backend.models import User

# Password hashing context (bcrypt, 12 rounds for security)
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
        
    Returns:
        True if passwords match
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: uuid.UUID, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token.
    
    Args:
        user_id: User ID to encode in token
        expires_delta: Optional custom expiration time
        
    Returns:
        JWT token string
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    expire = datetime.now(timezone.utc) + expires_delta
    
    to_encode = {
        "sub": str(user_id),
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    
    encoded_jwt = encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(user_id: uuid.UUID) -> str:
    """Create a JWT refresh token.
    
    Args:
        user_id: User ID to encode in token
        
    Returns:
        JWT refresh token string
    """
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    
    encoded_jwt = encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Tuple[uuid.UUID, str]]:
    """Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Tuple of (user_id, token_type) if valid, None if invalid
        
    Raises:
        InvalidTokenError: If token is invalid
        ExpiredSignatureError: If token is expired
    """
    try:
        payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type is None:
            return None
        
        return uuid.UUID(user_id), token_type
    except (InvalidTokenError, ExpiredSignatureError, ValueError):
        return None


def authenticate_user(email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password.
    
    Args:
        email: User email address
        password: Plain text password
        
    Returns:
        User object if authentication successful, None otherwise
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        return user
    finally:
        db.close()


def create_user(email: str, username: str, password: str, full_name: str = "") -> Optional[User]:
    """Create a new user account.
    
    Args:
        email: User email address (must be unique)
        username: Username (must be unique)
        password: Plain text password
        full_name: User full name (optional)
        
    Returns:
        Created User object if successful, None if user exists
    """
    db = SessionLocal()
    try:
        # Check if user already exists
        existing = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing:
            return None
        
        # Create new user
        user = User(
            email=email,
            username=username,
            password_hash=hash_password(password),
            full_name=full_name,
            subscription_tier="free",
            storage_quota_gb=5,
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    except Exception:
        db.rollback()
        return None
    finally:
        db.close()


def get_user_by_id(user_id: uuid.UUID) -> Optional[User]:
    """Get user by ID.
    
    Args:
        user_id: User UUID
        
    Returns:
        User object if found, None otherwise
    """
    db = SessionLocal()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()
