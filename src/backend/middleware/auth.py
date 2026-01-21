"""Authentication middleware for FastAPI application."""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials

from src.backend.services.auth import verify_token

security = HTTPBearer()


async def get_current_user(request: Request) -> Optional[UUID]:
    """Extract and verify user from request headers.
    
    Usage as FastAPI dependency:
        @app.get("/protected")
        async def protected_route(user_id: UUID = Depends(get_current_user)):
            return {"user_id": user_id}
    
    Args:
        request: FastAPI request object
        
    Returns:
        User UUID if token is valid
        
    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    auth_header = request.headers.get("Authorization")
    
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract bearer token
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    
    # Verify token
    result = verify_token(token)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id, token_type = result
    
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


class RateLimitMiddleware:
    """Simple rate limiting middleware (use Redis for production)."""

    def __init__(self, app, requests_per_minute: int = 60):
        self.app = app
        self.requests_per_minute = requests_per_minute
        self.requests = {}  # In-memory store (replace with Redis in production)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract client IP
        client_ip = scope.get("client", ("unknown",))[0]
        
        # Simple counter (would use Redis in production)
        # TODO: Implement Redis-based rate limiting
        
        await self.app(scope, receive, send)
