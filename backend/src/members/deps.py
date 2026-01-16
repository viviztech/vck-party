"""
Member Dependencies
FastAPI dependencies for member-related routes.
"""

from typing import Optional, List
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import (
    NotFoundError,
    AuthorizationError,
    AuthenticationError,
)
from src.core.security import get_current_user
from src.auth.models import User
from src.members.models import Member, MembershipStatus
from src.members.crud import MemberCRUD


# =============================================================================
# Member Dependencies
# =============================================================================

async def get_member_by_id(
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Member:
    """
    Get a member by ID.
    
    Raises:
        NotFoundError: If member not found
    """
    member = await MemberCRUD.get_by_id(db, Member, member_id)
    if not member or member.is_deleted:
        raise NotFoundError(resource="Member", resource_id=str(member_id))
    return member


async def get_active_member_by_id(
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Member:
    """
    Get an active member by ID.
    
    Raises:
        NotFoundError: If member not found
        AuthorizationError: If member is not active
    """
    member = await get_member_by_id(member_id, db)
    if member.status != MembershipStatus.ACTIVE.value:
        raise AuthorizationError("Member is not active")
    return member


# =============================================================================
# Permission Dependencies
# =============================================================================

async def check_member_view_permission(
    request: Request,
    member_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Member:
    """
    Check if current user can view the member.
    
    Users can view:
    - Their own member profile
    - All members if they have 'members:read' permission
    - Members in their hierarchy scope (if implemented)
    """
    # Get member
    member = await MemberCRUD.get_by_id(db, Member, member_id)
    if not member or member.is_deleted:
        raise NotFoundError(resource="Member", resource_id=str(member_id))
    
    # Check if user is the member
    if member.user_id == current_user.id:
        return member
    
    # Check for admin role (has all permissions)
    if current_user.is_admin():
        return member
    
    # Check for members:read permission
    if not current_user.has_permission("members:read"):
        raise AuthorizationError("You don't have permission to view members")
    
    return member


async def check_member_edit_permission(
    request: Request,
    member_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Member:
    """
    Check if current user can edit the member.
    
    Users can edit:
    - Their own member profile (limited fields)
    - All members if they have 'members:write' permission
    """
    # Get member
    member = await MemberCRUD.get_by_id(db, Member, member_id)
    if not member or member.is_deleted:
        raise NotFoundError(resource="Member", resource_id=str(member_id))
    
    # Check if user is the member
    if member.user_id == current_user.id:
        # Users can only edit their own profile, not status, etc.
        # More granular permissions can be added per endpoint
        return member
    
    # Check for admin role
    if current_user.is_admin():
        return member
    
    # Check for members:write permission
    if not current_user.has_permission("members:write"):
        raise AuthorizationError("You don't have permission to edit members")
    
    return member


async def check_member_delete_permission(
    request: Request,
    member_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Member:
    """
    Check if current user can delete the member.
    
    Only users with 'members:delete' permission can delete members.
    """
    # Get member
    member = await MemberCRUD.get_by_id(db, Member, member_id)
    if not member or member.is_deleted:
        raise NotFoundError(resource="Member", resource_id=str(member_id))
    
    # Check for admin role
    if current_user.is_admin():
        return member
    
    # Check for members:delete permission
    if not current_user.has_permission("members:delete"):
        raise AuthorizationError("You don't have permission to delete members")
    
    return member


# =============================================================================
# Optional Member
# =============================================================================

async def get_optional_member(
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Optional[Member]:
    """
    Get a member by ID if it exists.
    
    Returns None instead of raising exception.
    """
    member = await MemberCRUD.get_by_id(db, Member, member_id)
    if member and not member.is_deleted:
        return member
    return None


# =============================================================================
# Member from Current User
# =============================================================================

async def get_current_member(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Member:
    """
    Get the member profile for the current authenticated user.
    
    Raises:
        NotFoundError: If user doesn't have a member profile
    """
    if not current_user.member_profile:
        raise NotFoundError(resource="Member", resource_id="Current user has no member profile")
    return current_user.member_profile


# =============================================================================
# Pagination Dependencies
# =============================================================================

def getPaginationParams(
    page: int = 1,
    limit: int = 20,
) -> tuple[int, int]:
    """
    Get pagination parameters with validation.
    
    Returns:
        Tuple of (page, limit)
    """
    page = max(page, 1)
    limit = min(max(limit, 1), 100)  # Max 100 items per page
    return page, limit
