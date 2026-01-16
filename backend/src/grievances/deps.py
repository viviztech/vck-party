"""
Grievance Dependencies
FastAPI dependencies for grievance-related routes.
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
from src.members.models import Member
from src.members.crud import MemberCRUD
from src.grievances.models import (
    Grievance,
    GrievanceStatus,
)
from src.grievances.crud import GrievanceCRUD


# =============================================================================
# Grievance Dependencies
# =============================================================================

async def get_grievance_by_id(
    grievance_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Grievance:
    """
    Get a grievance by ID.
    
    Raises:
        NotFoundError: If grievance not found
    """
    grievance = await GrievanceCRUD.get_by_id(db, grievance_id)
    if not grievance or grievance.is_deleted:
        raise NotFoundError(resource="Grievance", resource_id=str(grievance_id))
    return grievance


async def get_active_grievance(
    grievance_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Grievance:
    """
    Get an active (non-deleted) grievance by ID.
    
    Raises:
        NotFoundError: If grievance not found
    """
    grievance = await get_grievance_by_id(grievance_id, db)
    return grievance


# =============================================================================
# Permission Dependencies
# =============================================================================

async def check_grievance_view_permission(
    request: Request,
    grievance_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Grievance:
    """
    Check if current user can view the grievance.
    
    Users can view:
    - Their own submitted grievances
    - All grievances if they have 'grievances:read' permission
    - Assigned grievances if they are the handler
    """
    grievance = await GrievanceCRUD.get_by_id(db, grievance_id)
    if not grievance or grievance.is_deleted:
        raise NotFoundError(resource="Grievance", resource_id=str(grievance_id))
    
    # Check if user submitted this grievance
    if grievance.submitted_by_id and str(grievance.submitted_by_id) == str(current_user.id):
        return grievance
    
    # Check if user is assigned to this grievance
    if grievance.current_assignee_id and str(grievance.current_assignee_id) == str(current_user.id):
        return grievance
    
    # Check for admin role (has all permissions)
    if current_user.is_admin():
        return grievance
    
    # Check for grievances:read permission
    if not current_user.has_permission("grievances:read"):
        raise AuthorizationError("You don't have permission to view grievances")
    
    # For confidential grievances, check for additional permission
    if grievance.is_confidential:
        if not current_user.has_permission("grievances:confidential"):
            raise AuthorizationError("You don't have permission to view confidential grievances")
    
    return grievance


async def check_grievance_handler_permission(
    request: Request,
    grievance_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Grievance:
    """
    Check if current user can handle/modify the grievance.
    
    Users can handle:
    - Assigned handlers
    - Users with 'grievances:write' permission
    - Admins
    """
    grievance = await GrievanceCRUD.get_by_id(db, grievance_id)
    if not grievance or grievance.is_deleted:
        raise NotFoundError(resource="Grievance", resource_id=str(grievance_id))
    
    # Check if user is the assigned handler
    if grievance.current_assignee_id and str(grievance.current_assignee_id) == str(current_user.id):
        return grievance
    
    # Check for admin role
    if current_user.is_admin():
        return grievance
    
    # Check for grievances:write permission
    if not current_user.has_permission("grievances:write"):
        raise AuthorizationError("You don't have permission to handle grievances")
    
    return grievance


async def check_grievance_edit_permission(
    request: Request,
    grievance_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Grievance:
    """
    Check if current user can edit the grievance.
    
    Users can edit:
    - Their own submitted grievances (limited fields)
    - Assigned handlers
    - Users with 'grievances:write' permission
    - Admins
    """
    grievance = await GrievanceCRUD.get_by_id(db, grievance_id)
    if not grievance or grievance.is_deleted:
        raise NotFoundError(resource="Grievance", resource_id=str(grievance_id))
    
    # Check if user is the assigned handler
    if grievance.current_assignee_id and str(grievance.current_assignee_id) == str(current_user.id):
        return grievance
    
    # Check for admin role
    if current_user.is_admin():
        return grievance
    
    # Check for grievances:write permission
    if not current_user.has_permission("grievances:write"):
        raise AuthorizationError("You don't have permission to edit grievances")
    
    return grievance


async def check_grievance_delete_permission(
    request: Request,
    grievance_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Grievance:
    """
    Check if current user can delete the grievance.
    
    Only users with 'grievances:delete' permission can delete grievances.
    """
    grievance = await GrievanceCRUD.get_by_id(db, grievance_id)
    if not grievance or grievance.is_deleted:
        raise NotFoundError(resource="Grievance", resource_id=str(grievance_id))
    
    # Check for admin role
    if current_user.is_admin():
        return grievance
    
    # Check for grievances:delete permission
    if not current_user.has_permission("grievances:delete"):
        raise AuthorizationError("You don't have permission to delete grievances")
    
    return grievance


async def check_grievance_assignment_permission(
    request: Request,
    grievance_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Grievance:
    """
    Check if current user can assign/reassign the grievance.
    
    Users can assign:
    - Current handlers
    - Users with 'grievances:assign' permission
    - Admins
    """
    grievance = await GrievanceCRUD.get_by_id(db, grievance_id)
    if not grievance or grievance.is_deleted:
        raise NotFoundError(resource="Grievance", resource_id=str(grievance_id))
    
    # Check if user is the assigned handler
    if grievance.current_assignee_id and str(grievance.current_assignee_id) == str(current_user.id):
        return grievance
    
    # Check for admin role
    if current_user.is_admin():
        return grievance
    
    # Check for grievances:assign permission
    if not current_user.has_permission("grievances:assign"):
        raise AuthorizationError("You don't have permission to assign grievances")
    
    return grievance


# =============================================================================
# Optional Grievance
# =============================================================================

async def get_optional_grievance(
    grievance_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Optional[Grievance]:
    """
    Get a grievance by ID if it exists.
    
    Returns None instead of raising exception.
    """
    grievance = await GrievanceCRUD.get_by_id(db, grievance_id)
    if grievance and not grievance.is_deleted:
        return grievance
    return None


# =============================================================================
# Submitter Dependencies
# =============================================================================

async def get_current_member_from_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Optional[Member]:
    """
    Get the member profile for the current authenticated user.
    
    Returns None if user doesn't have a member profile.
    """
    if not current_user.member_profile:
        return None
    return current_user.member_profile


async def require_current_member(
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
# Status Validation Dependencies
# =============================================================================

def validate_grievance_status(
    current_status: str,
    allowed_statuses: List[str],
    operation: str = "perform this action"
):
    """
    Validate that a grievance can transition to a new status.
    
    Raises:
        AuthorizationError: If status transition is not allowed
    """
    if current_status not in allowed_statuses:
        raise AuthorizationError(
            message=f"Cannot {operation} from status '{current_status}'. Allowed statuses: {', '.join(allowed_statuses)}"
        )


# =============================================================================
# Pagination Dependencies
# =============================================================================

def getGrievancePaginationParams(
    page: int = 1,
    limit: int = 20,
) -> tuple[int, int]:
    """
    Get pagination parameters with validation for grievances.
    
    Returns:
        Tuple of (page, limit)
    """
    page = max(page, 1)
    limit = min(max(limit, 1), 100)  # Max 100 items per page
    return page, limit


# =============================================================================
# Assignee Validation
# =============================================================================

async def validate_assignee(
    assignee_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Member:
    """
    Validate that the assignee exists and is active.
    
    Raises:
        NotFoundError: If member not found
        AuthorizationError: If member is not active
    """
    from src.members.models import MembershipStatus
    
    member = await MemberCRUD.get_by_id(db, Member, assignee_id)
    if not member or member.is_deleted:
        raise NotFoundError(resource="Member", resource_id=str(assignee_id))
    
    if member.status != MembershipStatus.ACTIVE.value:
        raise AuthorizationError("Assignee must be an active member")
    
    return member
