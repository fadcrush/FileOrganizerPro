"""Unit tests for authentication service."""

import pytest
from datetime import datetime, timedelta
import jwt

from src.backend.services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from src.backend.database import SessionLocal
from src.backend.models import User
from src.backend.config import settings


@pytest.fixture
def db_session():
    """Create database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TestPasswordHashing:
    """Tests for password hashing."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "secure_password_123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 20
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "secure_password_123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed)
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "secure_password_123"
        hashed = hash_password(password)
        
        assert not verify_password("wrong_password", hashed)
    
    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes."""
        password = "same_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Should be different due to salt
        assert hash1 != hash2
        
        # But both should verify
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


class TestJWTTokens:
    """Tests for JWT token creation and verification."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        user_id = "user-123"
        token = create_access_token(user_id)
        
        assert token is not None
        assert isinstance(token, str)
        assert token.count('.') == 2  # JWT format: header.payload.signature
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        user_id = "user-123"
        token = create_refresh_token(user_id)
        
        assert token is not None
        assert isinstance(token, str)
        assert token.count('.') == 2
    
    def test_access_token_has_correct_expiry(self):
        """Test that access token has correct expiry."""
        user_id = "user-123"
        token = create_access_token(user_id)
        
        # Decode without verification to check payload
        payload = jwt.decode(token, options={"verify_signature": False})
        
        assert "exp" in payload
        assert payload["sub"] == user_id
    
    def test_refresh_token_has_longer_expiry(self):
        """Test that refresh token has longer expiry than access token."""
        user_id = "user-123"
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)
        
        access_payload = jwt.decode(access_token, options={"verify_signature": False})
        refresh_payload = jwt.decode(refresh_token, options={"verify_signature": False})
        
        access_exp = access_payload["exp"]
        refresh_exp = refresh_payload["exp"]
        
        assert refresh_exp > access_exp
    
    def test_verify_valid_token(self):
        """Test verifying a valid token."""
        user_id = "user-123"
        token = create_access_token(user_id)
        
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
    
    def test_verify_invalid_token(self):
        """Test verifying an invalid token."""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(jwt.InvalidTokenError):
            verify_token(invalid_token)
    
    def test_verify_expired_token(self):
        """Test verifying an expired token."""
        user_id = "user-123"
        
        # Create a token with negative expiry (already expired)
        payload = {
            "sub": user_id,
            "exp": datetime.utcnow() - timedelta(hours=1),
        }
        
        expired_token = jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm="HS256",
        )
        
        with pytest.raises(jwt.ExpiredSignatureError):
            verify_token(expired_token)


class TestTokenIntegration:
    """Tests for token lifecycle."""
    
    def test_token_creation_and_verification_flow(self):
        """Test complete token creation and verification flow."""
        user_id = "user-123"
        
        # Create token
        token = create_access_token(user_id)
        
        # Verify token
        payload = verify_token(token)
        
        # Check payload
        assert payload["sub"] == user_id
        assert "exp" in payload
        assert "iat" in payload
    
    def test_access_and_refresh_token_flow(self):
        """Test access token refresh flow."""
        user_id = "user-123"
        
        # Create tokens
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)
        
        # Both should be verifiable
        access_payload = verify_token(access_token)
        refresh_payload = verify_token(refresh_token)
        
        assert access_payload["sub"] == user_id
        assert refresh_payload["sub"] == user_id
