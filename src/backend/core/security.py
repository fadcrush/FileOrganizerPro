"""
Phase 3 Week 4: Security Hardening

Comprehensive security features:
- Input validation and sanitization
- SQL injection prevention (via ORM)
- Path traversal protection
- XSS prevention
- CORS configuration
- Error message sanitization
- Security headers

Usage:
    from src.backend.core.security import (
        validate_file_path,
        sanitize_input,
        SecurityHeaders,
    )
    
    # Use in endpoints
    safe_path = validate_file_path(user_input_path)
    clean_input = sanitize_input(user_input)
"""

import os
import re
from pathlib import Path
from typing import Optional, List
from urllib.parse import quote, unquote
import logging
from datetime import datetime, timedelta

from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class SecurityValidator:
    """Input validation and security checks"""
    
    # Configuration
    MAX_PATH_LENGTH = 260  # Windows MAX_PATH
    MAX_FILENAME_LENGTH = 255
    MAX_INPUT_LENGTH = 10000
    MAX_SEARCH_QUERY_LENGTH = 1000
    
    # Allowed characters
    ALLOWED_PATH_CHARS = r"^[a-zA-Z0-9_\-. /\\()[\]{}@]+"
    ALLOWED_FILENAME_CHARS = r"^[a-zA-Z0-9_\-. ()[\]{}@]+"
    
    # Dangerous patterns
    DANGEROUS_PATTERNS = [
        r"\.\.[\\/]",  # Path traversal
        r"\.\.%",      # Encoded path traversal
        r";rm\s",      # Command injection
        r"\$\(",       # Command substitution
        r"`.*`",       # Backticks (command execution)
        r"\|\|",       # Pipe (command chaining)
        r"&&",         # And (command chaining)
    ]
    
    @staticmethod
    def validate_file_path(path: str, user_base_dir: Optional[str] = None) -> str:
        """
        Validate and sanitize file path.
        
        Args:
            path: File path to validate
            user_base_dir: Base directory for user (for containment check)
        
        Returns:
            Sanitized path
        
        Raises:
            HTTPException: If path is invalid
        """
        if not path or not isinstance(path, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid path"
            )
        
        # Check length
        if len(path) > SecurityValidator.MAX_PATH_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Path too long"
            )
        
        # Decode if encoded
        try:
            path = unquote(path)
        except:
            pass
        
        # Check for dangerous patterns
        for pattern in SecurityValidator.DANGEROUS_PATTERNS:
            if re.search(pattern, path, re.IGNORECASE):
                logger.warning(f"Dangerous pattern detected in path: {path}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid characters in path"
                )
        
        # Check for null bytes
        if "\x00" in path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Null bytes not allowed"
            )
        
        # Normalize path
        try:
            normalized = str(Path(path).resolve())
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid path"
            )
        
        # Check containment if base directory specified
        if user_base_dir:
            base = Path(user_base_dir).resolve()
            requested = Path(normalized).resolve()
            
            try:
                requested.relative_to(base)
            except ValueError:
                logger.warning(
                    f"Path traversal attempt: {path} outside {user_base_dir}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
        
        return normalized
    
    @staticmethod
    def validate_filename(filename: str) -> str:
        """
        Validate and sanitize filename.
        
        Args:
            filename: Filename to validate
        
        Returns:
            Sanitized filename
        
        Raises:
            HTTPException: If filename is invalid
        """
        if not filename or not isinstance(filename, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename"
            )
        
        # Check length
        if len(filename) > SecurityValidator.MAX_FILENAME_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename too long"
            )
        
        # Remove path components
        filename = os.path.basename(filename)
        
        # Remove dangerous characters
        filename = re.sub(r'[<>:"|?*\x00]', '', filename)
        
        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')
        
        if not filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename"
            )
        
        return filename
    
    @staticmethod
    def sanitize_input(input_str: str, max_length: int = MAX_INPUT_LENGTH) -> str:
        """
        Sanitize user input to prevent XSS.
        
        Args:
            input_str: Input to sanitize
            max_length: Maximum length
        
        Returns:
            Sanitized input
        """
        if not isinstance(input_str, str):
            return ""
        
        # Truncate
        input_str = input_str[:max_length]
        
        # Remove dangerous HTML/JavaScript
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'on\w+\s*=',  # Event handlers
            r'javascript:',
            r'data:text/html',
        ]
        
        for pattern in dangerous_patterns:
            input_str = re.sub(pattern, '', input_str, flags=re.IGNORECASE)
        
        # Remove null bytes
        input_str = input_str.replace('\x00', '')
        
        return input_str.strip()
    
    @staticmethod
    def validate_search_query(query: str) -> str:
        """
        Validate search query.
        
        Args:
            query: Search query
        
        Returns:
            Validated query
        
        Raises:
            HTTPException: If query is invalid
        """
        if not query or not isinstance(query, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid search query"
            )
        
        # Check length
        if len(query) > SecurityValidator.MAX_SEARCH_QUERY_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query too long"
            )
        
        # Sanitize
        query = SecurityValidator.sanitize_input(query)
        
        # Check for dangerous patterns
        if "%" * 5 in query or "_" * 5 in query:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid search pattern"
            )
        
        return query
    
    @staticmethod
    def validate_email(email: str) -> str:
        """
        Validate email address.
        
        Args:
            email: Email to validate
        
        Returns:
            Validated email
        
        Raises:
            HTTPException: If email is invalid
        """
        if not email or not isinstance(email, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email"
            )
        
        # Basic email validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        # Check length
        if len(email) > 254:  # RFC 5321
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email too long"
            )
        
        return email.lower().strip()
    
    @staticmethod
    def validate_pagination(page: int, page_size: int) -> tuple:
        """Validate pagination parameters"""
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page must be >= 1"
            )
        
        if page_size < 1 or page_size > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be between 1 and 1000"
            )
        
        return page, page_size


class SecurityHeaders:
    """Security headers configuration"""
    
    HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'"
        ),
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "microphone=(), "
            "payment=()"
        ),
    }
    
    @staticmethod
    def add_to_response(response):
        """Add security headers to response"""
        for header, value in SecurityHeaders.HEADERS.items():
            response.headers[header] = value
        return response


class SecurityMiddleware:
    """Security middleware for all requests"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, request: Request, call_next):
        """Process request through security checks"""
        try:
            # Add security headers
            response = await call_next(request)
            response = SecurityHeaders.add_to_response(response)
            return response
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Security error: {e}")
            # Return generic error (don't expose stack trace)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )


class ErrorSanitizer:
    """Sanitize error messages for responses"""
    
    # Safe error messages for different status codes
    SAFE_MESSAGES = {
        400: "Bad request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not found",
        429: "Too many requests",
        500: "Internal server error",
        503: "Service unavailable",
    }
    
    @staticmethod
    def sanitize_error_response(status_code: int, detail: str = None) -> dict:
        """
        Create sanitized error response.
        
        Args:
            status_code: HTTP status code
            detail: Original error detail
        
        Returns:
            Sanitized error dict
        """
        safe_message = ErrorSanitizer.SAFE_MESSAGES.get(
            status_code,
            "An error occurred"
        )
        
        # Log original error internally
        if detail:
            logger.warning(f"Error {status_code}: {detail}")
        
        return {
            "error": safe_message,
            "status": status_code,
            "timestamp": datetime.utcnow().isoformat(),
        }


class AuditLogger:
    """Log security-relevant events"""
    
    @staticmethod
    def log_auth_attempt(user_id: str, success: bool, reason: str = None):
        """Log authentication attempt"""
        logger.info(
            f"Auth attempt: user={user_id}, success={success}, reason={reason}"
        )
    
    @staticmethod
    def log_access_denied(user_id: str, resource: str, reason: str):
        """Log access denial"""
        logger.warning(
            f"Access denied: user={user_id}, resource={resource}, reason={reason}"
        )
    
    @staticmethod
    def log_suspicious_activity(user_id: str, activity: str):
        """Log suspicious activity"""
        logger.warning(
            f"Suspicious activity: user={user_id}, activity={activity}"
        )
    
    @staticmethod
    def log_rate_limit_exceeded(user_id: str, endpoint: str, requests: int):
        """Log rate limit exceeded"""
        logger.warning(
            f"Rate limit exceeded: user={user_id}, endpoint={endpoint}, "
            f"requests={requests}"
        )
