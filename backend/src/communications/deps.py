"""
Communications Dependencies
FastAPI dependencies for communications routes.
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
from src.communications.models import (
    Announcement,
    Forum,
    ForumPost,
    Grievance,
)
from src.communications.crud import (
    AnnouncementCRUD,
    ForumCRUD,
    ForumPostCRUD,
    GrievanceCRUD,
)


# =============================================================================
# Announcement Dependencies
# =============================================================================

async def get_announcement_by_id(
    announcement_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Announcement:
    """
    Get an announcement by ID.
    
    Raises:
        NotFoundError: If announcement not found
    """
    announcement = await AnnouncementCRUD.get_with_targets(
        db, announcement_id
    )
    if not announcement:
        raise NotFoundError(
            resource="Announcement",
            resource_id=str(announcement_id)
        )
    return announcement


async def check_announcement_permission(
    request: Request,
    announcement: Announcement = Depends(get_announcement_by_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Announcement:
    """
    Check if current user can modify the announcement.
    
    Users can modify:
    - Their own announcements
    - Admins with appropriate permissions
    - Users with 'communications:write' permission
    """
    # Get member profile
    member = await MemberCRUD.get_by_id(db, Member, current_user.id)
    
    # Check if user is the creator
    if announcement.created_by_id == member.id:
        return announcement
    
    # Check for admin role
    if current_user.is_admin():
        return announcement
    
    # Check for communications:write permission
    if not current_user.has_permission("communications:write"):
        raise AuthorizationError(
            message="You don't have permission to modify this announcement"
        )
    
    return announcement


# =============================================================================
# Forum Dependencies
# =============================================================================

async def get_forum_by_id(
    forum_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Forum:
    """
    Get a forum by ID.
    
    Raises:
        NotFoundError: If forum not found
    """
    forum = await ForumCRUD.get_by_id(db, Forum, forum_id)
    if not forum or forum.is_deleted:
        raise NotFoundError(resource="Forum", resource_id=str(forum_id))
    return forum


async def check_forum_access(
    request: Request,
    forum: Forum = Depends(get_forum_by_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Forum:
    """
    Check if current user can access the forum.
    
    Visibility rules:
    - Public: Anyone
    - Members only: Authenticated members
    - District only: Members in the district
    - Private: Only invited members (not implemented)
    """
    member = await MemberCRUD.get_by_id(db, Member, current_user.id)
    
    # Public forums are accessible to all
    if forum.visibility == "public":
        return forum
    
    # Check if authenticated for other visibility levels
    if not member:
        raise AuthenticationError("Please login to access this forum")
    
    # Members only
    if forum.visibility == "members_only":
        return forum
    
    # District only - check if member belongs to the district
    if forum.visibility == "district_only":
        if forum.unit_id:
            # Check if member is in the same unit
            member_units = getattr(member, 'units', [])
            unit_ids = [mu.unit_id for mu in member_units]
            if forum.unit_id not in unit_ids:
                raise AuthorizationError(
                    message="This forum is only for members of a specific district"
                )
        return forum
    
    # Private - not yet implemented
    return forum


async def check_forum_moderator_permission(
    request: Request,
    forum: Forum = Depends(get_forum_by_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Forum:
    """
    Check if current user can moderate the forum.
    
    Moderators can:
    - Forum creator
    - Admins
    - Users with 'forum:moderate' permission
    """
    member = await MemberCRUD.get_by_id(db, Member, current_user.id)
    
    # Check if user is the creator
    if forum.created_by_id == member.id:
        return forum
    
    # Check for admin role
    if current_user.is_admin():
        return forum
    
    # Check for forum:moderate permission
    if not current_user.has_permission("forum:moderate"):
        raise AuthorizationError(
            message="You don't have permission to moderate this forum"
        )
    
    return forum


async def check_forum_locked(
    forum: Forum = Depends(get_forum_by_id),
) -> Forum:
    """
    Check if forum is locked.
    
    Raises:
        AuthorizationError: If forum is locked
    """
    if forum.is_locked:
        raise AuthorizationError(
            message="This forum is locked and no new posts can be added"
        )
    return forum


# =============================================================================
# Forum Post Dependencies
# =============================================================================

async def get_post_by_id(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ForumPost:
    """
    Get a forum post by ID.
    
    Raises:
        NotFoundError: If post not found
    """
    post = await ForumPostCRUD.get_by_id(db, ForumPost, post_id)
    if not post or post.is_deleted:
        raise NotFoundError(resource="ForumPost", resource_id=str(post_id))
    return post


async def check_post_access(
    request: Request,
    post: ForumPost = Depends(get_post_by_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ForumPost:
    """
    Check if current user can view the post.
    """
    # Hidden posts are only visible to moderators
    if post.is_hidden:
        member = await MemberCRUD.get_by_id(db, Member, current_user.id)
        
        if not member:
            raise AuthorizationError("This post is hidden")
        
        if current_user.is_admin():
            return post
        
        if current_user.has_permission("forum:moderate"):
            return post
        
        raise AuthorizationError("This post is hidden")
    
    return post


async def check_post_ownership(
    request: Request,
    post: ForumPost = Depends(get_post_by_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ForumPost:
    """
    Check if current user owns the post.
    
    Raises:
        AuthorizationError: If user doesn't own the post
    """
    member = await MemberCRUD.get_by_id(db, Member, current_user.id)
    
    if post.author_id == member.id:
        return post
    
    if current_user.is_admin():
        return post
    
    raise AuthorizationError("You don't have permission to modify this post")


async def check_post_moderator(
    request: Request,
    post: ForumPost = Depends(get_post_by_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ForumPost:
    """
    Check if current user can moderate the post.
    """
    member = await MemberCRUD.get_by_id(db, Member, current_user.id)
    
    # Check if user is the author
    if post.author_id == member.id:
        return post
    
    # Check for admin role
    if current_user.is_admin():
        return post
    
    # Check for forum:moderate permission
    if not current_user.has_permission("forum:moderate"):
        raise AuthorizationError(
            message="You don't have permission to moderate this post"
        )
    
    return post


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
    grievance = await GrievanceCRUD.get_with_details(db, grievance_id)
    if not grievance:
        raise NotFoundError(resource="Grievance", resource_id=str(grievance_id))
    return grievance


async def check_grievance_access(
    request: Request,
    grievance: Grievance = Depends(get_grievance_by_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Grievance:
    """
    Check if current user can view the grievance.
    
    Access rules:
    - Submitter can view their own grievances
    - Assigned handler can view assigned grievances
    - Admins can view all
    - Users with 'grievances:read' can view all
    """
    member = await MemberCRUD.get_by_id(db, Member, current_user.id)
    
    # Submitter can view
    if grievance.member_id == member.id:
        return grievance
    
    # Assigned handler can view
    if grievance.assigned_to_id == member.id:
        return grievance
    
    # Check for admin role
    if current_user.is_admin():
        return grievance
    
    # Check for grievances:read permission
    if not current_user.has_permission("grievances:read"):
        raise AuthorizationError(
            message="You don't have permission to view this grievance"
        )
    
    return grievance


async def check_grievance_handler_permission(
    request: Request,
    grievance: Grievance = Depends(get_grievance_by_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Grievance:
    """
    Check if current user can handle/modify the grievance.
    
    Handlers can:
    - Assigned handler
    - Admins
    - Users with 'grievances:handle' permission
    """
    member = await MemberCRUD.get_by_id(db, Member, current_user.id)
    
    # Assigned handler can modify
    if grievance.assigned_to_id == member.id:
        return grievance
    
    # Check for admin role
    if current_user.is_admin():
        return grievance
    
    # Check for grievances:handle permission
    if not current_user.has_permission("grievances:handle"):
        raise AuthorizationError(
            message="You don't have permission to handle grievances"
        )
    
    return grievance


async def check_grievance_submitter(
    request: Request,
    grievance: Grievance = Depends(get_grievance_by_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Grievance:
    """
    Check if current user submitted the grievance.
    
    Raises:
        AuthorizationError: If user didn't submit the grievance
    """
    member = await MemberCRUD.get_by_id(db, Member, current_user.id)
    
    if grievance.member_id == member.id:
        return grievance
    
    if current_user.is_admin():
        return grievance
    
    raise AuthorizationError(
        message="You can only modify your own grievances"
    )


# =============================================================================
# Comment Dependencies
# =============================================================================

async def get_comment_by_id(
    comment_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a comment by ID.
    
    Raises:
        NotFoundError: If comment not found
    """
    from src.communications.models import ForumComment
    from src.communications.crud import ForumCommentCRUD
    
    comment = await ForumCommentCRUD.get_by_id(db, ForumComment, comment_id)
    if not comment or comment.is_deleted:
        raise NotFoundError(resource="ForumComment", resource_id=str(comment_id))
    return comment


async def check_comment_ownership(
    request: Request,
    comment = Depends(get_comment_by_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Check if current user owns the comment.
    """
    member = await MemberCRUD.get_by_id(db, Member, current_user.id)
    
    if comment.author_id == member.id:
        return comment
    
    if current_user.is_admin():
        return comment
    
    if current_user.has_permission("forum:moderate"):
        return comment
    
    raise AuthorizationError(
        message="You don't have permission to modify this comment"
    )


# =============================================================================
# Current Member Helper
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
    member = await MemberCRUD.get_by_id(db, Member, current_user.id)
    if not member:
        raise NotFoundError(
            resource="Member",
            resource_id="Current user has no member profile"
        )
    return member


# =============================================================================
# Pagination Dependencies
# =============================================================================

def get_pagination_params(
    page: int = 1,
    limit: int = 20,
) -> tuple[int, int]:
    """
    Get pagination parameters with validation.
    
    Returns:
        Tuple of (page, limit)
    """
    page = max(page, 1)
    limit = min(max(limit, 1), 100)
    return page, limit


# =============================================================================
# Search Filter Dependencies
# =============================================================================

async def get_announcement_filters(
    unit_id: UUID = None,
    target_scope: str = None,
    announcement_type: str = None,
    is_pinned: bool = None,
    is_sent: bool = None,
    search: str = None,
    from_date: str = None,
    to_date: str = None,
) -> dict:
    """Get announcement filters from query parameters."""
    from datetime import datetime
    
    filters = {}
    if unit_id:
        filters["unit_id"] = unit_id
    if target_scope:
        filters["target_scope"] = target_scope
    if announcement_type:
        filters["announcement_type"] = announcement_type
    if is_pinned is not None:
        filters["is_pinned"] = is_pinned
    if is_sent is not None:
        filters["is_sent"] = is_sent
    if search:
        filters["search"] = search
    if from_date:
        filters["from_date"] = datetime.fromisoformat(from_date)
    if to_date:
        filters["to_date"] = datetime.fromisoformat(to_date)
    
    return filters


async def get_forum_filters(
    unit_id: UUID = None,
    visibility: str = None,
    category: str = None,
    is_locked: bool = None,
    search: str = None,
) -> dict:
    """Get forum filters from query parameters."""
    filters = {}
    if unit_id:
        filters["unit_id"] = unit_id
    if visibility:
        filters["visibility"] = visibility
    if category:
        filters["category"] = category
    if is_locked is not None:
        filters["is_locked"] = is_locked
    if search:
        filters["search"] = search
    
    return filters


async def get_grievance_filters(
    unit_id: UUID = None,
    status: str = None,
    priority: str = None,
    category: str = None,
    assigned_to_id: UUID = None,
    search: str = None,
    from_date: str = None,
    to_date: str = None,
) -> dict:
    """Get grievance filters from query parameters."""
    from datetime import datetime
    
    filters = {}
    if unit_id:
        filters["unit_id"] = unit_id
    if status:
        filters["status"] = status
    if priority:
        filters["priority"] = priority
    if category:
        filters["category"] = category
    if assigned_to_id:
        filters["assigned_to_id"] = assigned_to_id
    if search:
        filters["search"] = search
    if from_date:
        filters["from_date"] = datetime.fromisoformat(from_date)
    if to_date:
        filters["to_date"] = datetime.fromisoformat(to_date)
    
    return filters
