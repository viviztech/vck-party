"""
Auth Dependencies
FastAPI dependencies for authentication and authorization.
"""

from typing import Optional, List
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    InsufficientPermissionsError,
)
from src.core.security import verify_access_token, decode_token
from src.auth.models import User, Role, Permission
from src.auth.crud import UserCRUD, RoleCRUD


# =============================================================================
# Security Scheme
# =============================================================================

bearer_scheme = HTTPBearer(auto_error=False)


# =============================================================================
# Token Extraction
# =============================================================================

async def get_token_from_header(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> Optional[str]:
    """Extract token from Authorization header."""
    if credentials:
        return credentials.credentials
    return None


# =============================================================================
# Current User Dependencies
# =============================================================================

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = Depends(get_token_from_header)
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    Raises:
        AuthenticationError: If no valid token is provided
    """
    if not token:
        raise AuthenticationError("Not authenticated")
    
    payload = verify_access_token(token)
    if not payload:
        raise AuthenticationError("Invalid or expired token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload")
    
    user = await UserCRUD.get_by_id(db, User, UUID(user_id))
    if not user:
        raise AuthenticationError("User not found")
    
    if not user.is_active:
        raise AuthenticationError("Account is disabled")
    
    # Store user in request state for access in other routes
    request.state.user = user
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user.
    
    This dependency extends get_current_user with an additional check
    for account status.
    """
    if current_user.status != "active":
        raise AuthenticationError("Account is not active")
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get the current verified user.
    
    This dependency extends get_current_active_user with a check
    for email/phone verification.
    """
    if not current_user.is_verified:
        raise AuthenticationError("Email/phone not verified")
    return current_user


# =============================================================================
# Role-Based Dependencies
# =============================================================================

async def get_current_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get the current admin user.
    
    Raises:
        AuthorizationError: If user is not an admin
    """
    if not current_user.is_admin():
        raise AuthorizationError("Admin access required")
    return current_user


def require_roles(allowed_roles: List[str]):
    """
    Create a dependency that checks if user has any of the specified roles.
    
    Args:
        allowed_roles: List of role names that are allowed access
        
    Returns:
        Dependency function
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if not any(current_user.has_role(role) for role in allowed_roles):
            raise AuthorizationError(
                message=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    
    return role_checker


# =============================================================================
# Permission-Based Dependencies
# =============================================================================

def require_permission(permission: str):
    """
    Create a dependency that checks if user has the specified permission.
    
    Args:
        permission: Permission name (e.g., 'users:read', 'admin:all')
        
    Returns:
        Dependency function
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        # Admin has all permissions
        if current_user.is_admin():
            return current_user
        
        if not current_user.has_permission(permission):
            raise InsufficientPermissionsError(required_permission=permission)
        return current_user
    
    return permission_checker


def require_any_permission(permissions: List[str]):
    """
    Create a dependency that checks if user has any of the specified permissions.
    
    Args:
        permissions: List of permission names
        
    Returns:
        Dependency function
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        # Admin has all permissions
        if current_user.is_admin():
            return current_user
        
        if not any(current_user.has_permission(p) for p in permissions):
            raise InsufficientPermissionsError(
                required_permission=f"Any of: {', '.join(permissions)}"
            )
        return current_user
    
    return permission_checker


def require_all_permissions(permissions: List[str]):
    """
    Create a dependency that checks if user has all specified permissions.
    
    Args:
        permissions: List of permission names
        
    Returns:
        Dependency function
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        # Admin has all permissions
        if current_user.is_admin():
            return current_user
        
        if not all(current_user.has_permission(p) for p in permissions):
            missing = [p for p in permissions if not current_user.has_permission(p)]
            raise InsufficientPermissionsError(
                required_permission=f"Missing: {', '.join(missing)}"
            )
        return current_user
    
    return permission_checker


# =============================================================================
# Optional Authentication
# =============================================================================

async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = Depends(get_token_from_header)
) -> Optional[User]:
    """
    Get the current user if authenticated, otherwise return None.
    
    This is useful for endpoints that support both authenticated
    and unauthenticated access.
    """
    if not token:
        return None
    
    payload = verify_access_token(token)
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    user = await UserCRUD.get_by_id(db, User, UUID(user_id))
    if not user or not user.is_active:
        return None
    
    request.state.user = user
    return user


# =============================================================================
# Device Info Extraction
# =============================================================================

def get_device_info(request: Request) -> dict:
    """
    Extract device information from request headers.
    
    Returns:
        Dictionary with device information
    """
    user_agent = request.headers.get("user-agent", "")
    
    device_info = {
        "device_id": request.headers.get("x-device-id"),
        "device_type": request.headers.get("x-device-type"),
        "app_version": request.headers.get("x-app-version"),
        "os_version": request.headers.get("x-os-version"),
        "browser": extract_browser(user_agent),
    }
    
    # Remove None values
    return {k: v for k, v in device_info.items() if v is not None}


def extract_browser(user_agent: str) -> Optional[str]:
    """Extract browser name from user agent string."""
    user_agent = user_agent.lower()
    if "chrome" in user_agent and "chromium" not in user_agent:
        return "Chrome"
    elif "firefox" in user_agent:
        return "Firefox"
    elif "safari" in user_agent and "chrome" not in user_agent:
        return "Safari"
    elif "edge" in user_agent:
        return "Edge"
    elif "opera" in user_agent or "opr" in user_agent:
        return "Opera"
    return None


# =============================================================================
# Request Info Dependencies
# =============================================================================

async def get_client_ip(request: Request) -> str:
    """Get client IP address from request."""
    # Check for forwarded headers (behind proxy)
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    
    # Fallback to direct connection
    if request.client:
        return request.client.host
    
    return "unknown"


# =============================================================================
# Rate Limiting
# =============================================================================

from src.core import redis


async def check_auth_rate_limit(
    request: Request,
    limit: int = 10,
    window: int = 60
) -> None:
    """
    Check if request is within rate limit for auth endpoints.
    
    Raises:
        RateLimitError: If rate limit exceeded
    """
    ip = await get_client_ip(request)
    key = f"rate:auth:{ip}"
    
    is_allowed, remaining = await redis.check_rate_limit(key, limit, window)
    
    # Set rate limit headers
    request.state.rate_limit_remaining = remaining
    request.state.rate_limit_limit = limit
    
    if not is_allowed:
        from src.core.exceptions import RateLimitError
        raise RateLimitError(retry_after=window)
