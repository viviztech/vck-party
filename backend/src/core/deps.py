"""
FastAPI Dependencies
Common dependencies for authentication, authorization, and pagination.
"""

from typing import Annotated, Optional

from fastapi import Depends, Header, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    InvalidTokenError,
    TokenExpiredError,
)
from src.core.security import verify_access_token

# HTTP Bearer scheme for JWT
security = HTTPBearer(auto_error=False)


# =============================================================================
# Authentication Dependencies
# =============================================================================

async def get_current_user_id(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials],
        Depends(security)
    ]
) -> str:
    """
    Get current user ID from JWT token.
    Raises AuthenticationError if token is invalid or missing.
    """
    if not credentials:
        raise AuthenticationError("Authorization header missing")

    token = credentials.credentials
    payload = verify_access_token(token)

    if not payload:
        raise InvalidTokenError()

    user_id = payload.get("sub")
    if not user_id:
        raise InvalidTokenError()

    return user_id


async def get_current_user_optional(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials],
        Depends(security)
    ]
) -> Optional[str]:
    """
    Get current user ID if token is provided, otherwise return None.
    Does not raise error for missing token.
    """
    if not credentials:
        return None

    token = credentials.credentials
    payload = verify_access_token(token)

    if not payload:
        return None

    return payload.get("sub")


async def get_current_member(
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get current member from database.
    Returns the member associated with the authenticated user.
    """
    from src.members.repository import MemberRepository

    repo = MemberRepository(db)
    member = await repo.get_by_user_id(user_id)

    if not member:
        raise AuthenticationError("Member not found")

    return member


# =============================================================================
# Authorization Dependencies
# =============================================================================

class PermissionChecker:
    """Check if user has required permission."""

    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    async def __call__(
        self,
        user_id: Annotated[str, Depends(get_current_user_id)],
        db: Annotated[AsyncSession, Depends(get_db)]
    ) -> bool:
        """Check permission and raise error if not allowed."""
        from src.members.repository import MemberRepository

        repo = MemberRepository(db)
        has_permission = await repo.check_permission(
            user_id,
            self.required_permission
        )

        if not has_permission:
            raise AuthorizationError(
                f"Permission '{self.required_permission}' required"
            )

        return True


class UnitAccessChecker:
    """Check if user has access to a specific organization unit."""

    def __init__(self, required_role: Optional[str] = None):
        self.required_role = required_role

    async def __call__(
        self,
        unit_id: str,
        user_id: Annotated[str, Depends(get_current_user_id)],
        db: Annotated[AsyncSession, Depends(get_db)]
    ) -> bool:
        """Check unit access and raise error if not allowed."""
        from src.members.repository import MemberRepository

        repo = MemberRepository(db)
        has_access = await repo.check_unit_access(
            user_id,
            unit_id,
            self.required_role
        )

        if not has_access:
            raise AuthorizationError("Access to this unit is not allowed")

        return True


# =============================================================================
# Pagination Dependencies
# =============================================================================

class PaginationParams:
    """Pagination parameters."""

    def __init__(
        self,
        page: Annotated[int, Query(ge=1, description="Page number")] = 1,
        limit: Annotated[
            int,
            Query(ge=1, le=settings.MAX_PAGE_SIZE, description="Items per page")
        ] = settings.DEFAULT_PAGE_SIZE,
    ):
        self.page = page
        self.limit = limit
        self.offset = (page - 1) * limit


# =============================================================================
# Language Dependency
# =============================================================================

async def get_language(
    accept_language: Annotated[
        Optional[str],
        Header(alias="Accept-Language")
    ] = "en"
) -> str:
    """Get preferred language from header."""
    if not accept_language:
        return "en"

    # Parse Accept-Language header (simplified)
    lang = accept_language.split(",")[0].split("-")[0].lower()

    # Supported languages
    supported = ["en", "ta", "hi"]
    return lang if lang in supported else "en"


# =============================================================================
# Type Aliases for Common Dependencies
# =============================================================================

# Database session
DBSession = Annotated[AsyncSession, Depends(get_db)]

# Current user ID (required)
CurrentUserId = Annotated[str, Depends(get_current_user_id)]

# Current user ID (optional)
OptionalUserId = Annotated[Optional[str], Depends(get_current_user_optional)]

# Pagination
Pagination = Annotated[PaginationParams, Depends()]

# Language
Language = Annotated[str, Depends(get_language)]
