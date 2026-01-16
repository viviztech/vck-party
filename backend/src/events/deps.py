"""
Event Dependencies
FastAPI dependencies for event-related routes.
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import (
    NotFoundError,
    AuthorizationError,
    ValidationError,
)
from src.core.security import get_current_user
from src.auth.models import User
from src.events.models import Event, EventStatus, EventTask
from src.events.crud import EventCRUD


# =============================================================================
# Event Dependencies
# =============================================================================

async def get_event_by_id(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Event:
    """
    Get an event by ID.
    
    Raises:
        NotFoundError: If event not found
    """
    # Try cache first
    from src.core import redis
    cached = await redis.get_event(str(event_id))
    if cached:
        return cached
    
    event = await EventCRUD.get_by_id(db, Event, event_id)
    if not event or event.is_deleted:
        raise NotFoundError(resource="Event", resource_id=str(event_id))
    
    # Cache the event
    await redis.cache_event(event_id, event)
    
    return event


async def get_event_task_by_id(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> EventTask:
    """
    Get an event task by ID.
    
    Raises:
        NotFoundError: If task not found
    """
    from src.events.crud import EventTaskCRUD
    task = await EventTaskCRUD.get_by_id(db, EventTask, task_id)
    if not task:
        raise NotFoundError(resource="EventTask", resource_id=str(task_id))
    return task


# =============================================================================
# Permission Dependencies
# =============================================================================

async def check_event_view_permission(
    request: Request,
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Event:
    """
    Check if current user can view the event.
    
    Users can view:
    - Published events
    - Events in their organization unit
    - Events they created
    - Users with 'events:read' permission
    """
    event = await EventCRUD.get_by_id(db, Event, event_id)
    if not event or event.is_deleted:
        raise NotFoundError(resource="Event", resource_id=str(event_id))
    
    # Draft events are only visible to creators and admins
    if event.status == EventStatus.DRAFT.value:
        if event.created_by_id:
            # Check if user is the creator
            if hasattr(current_user, 'member_profile') and current_user.member_profile:
                if event.created_by_id == current_user.member_profile.id:
                    return event
            
            # Check for admin role
            if current_user.is_admin():
                return event
            
            # Check for events:read permission
            if not current_user.has_permission("events:read"):
                raise AuthorizationError("You don't have permission to view draft events")
    
    return event


async def check_event_edit_permission(
    request: Request,
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Event:
    """
    Check if current user can edit the event.
    
    Users can edit:
    - Events they created
    - Users with 'events:write' permission
    - Admin users
    """
    event = await EventCRUD.get_by_id(db, Event, event_id)
    if not event or event.is_deleted:
        raise NotFoundError(resource="Event", resource_id=str(event_id))
    
    # Check if user is the creator
    is_creator = False
    if hasattr(current_user, 'member_profile') and current_user.member_profile:
        if event.created_by_id == current_user.member_profile.id:
            is_creator = True
    
    # Check for admin role
    is_admin = current_user.is_admin()
    
    # Check for events:write permission
    has_permission = current_user.has_permission("events:write")
    
    if not (is_creator or is_admin or has_permission):
        raise AuthorizationError("You don't have permission to edit this event")
    
    return event


async def check_event_delete_permission(
    request: Request,
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Event:
    """
    Check if current user can delete the event.
    
    Only users with 'events:delete' permission or admin role can delete events.
    """
    event = await EventCRUD.get_by_id(db, Event, event_id)
    if not event or event.is_deleted:
        raise NotFoundError(resource="Event", resource_id=str(event_id))
    
    # Check for admin role
    if current_user.is_admin():
        return event
    
    # Check for events:delete permission
    if not current_user.has_permission("events:delete"):
        raise AuthorizationError("You don't have permission to delete events")
    
    return event


async def check_task_edit_permission(
    request: Request,
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EventTask:
    """
    Check if current user can edit the task.
    
    Users can edit:
    - Tasks they are assigned to
    - Events they created (tasks within their events)
    - Users with 'events:write' permission
    """
    from src.events.crud import EventTaskCRUD
    
    task = await EventTaskCRUD.get_by_id(db, EventTask, task_id)
    if not task:
        raise NotFoundError(resource="EventTask", resource_id=str(task_id))
    
    # Check if user is assigned to the task
    is_assigned = False
    if hasattr(current_user, 'member_profile') and current_user.member_profile:
        if task.assigned_to_id == current_user.member_profile.id:
            is_assigned = True
    
    # Check if user created the event (and thus can manage tasks)
    event = await EventCRUD.get_by_id(db, Event, task.event_id)
    is_event_creator = False
    if event and hasattr(current_user, 'member_profile') and current_user.member_profile:
        if event.created_by_id == current_user.member_profile.id:
            is_event_creator = True
    
    # Check for admin role
    is_admin = current_user.is_admin()
    
    # Check for events:write permission
    has_permission = current_user.has_permission("events:write")
    
    if not (is_assigned or is_event_creator or is_admin or has_permission):
        raise AuthorizationError("You don't have permission to edit this task")
    
    return task


# =============================================================================
# Optional Event
# =============================================================================

async def get_optional_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Optional[Event]:
    """
    Get an event by ID if it exists.
    
    Returns None instead of raising exception.
    """
    event = await EventCRUD.get_by_id(db, Event, event_id)
    if event and not event.is_deleted:
        return event
    return None


# =============================================================================
# Active Event Check
# =============================================================================

async def get_active_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Event:
    """
    Get an event that is not cancelled or completed.
    
    Raises:
        ValidationError: If event is cancelled or completed
    """
    event = await get_event_by_id(event_id, db)
    
    if event.status == EventStatus.CANCELLED.value:
        raise ValidationError("Event has been cancelled")
    
    if event.status == EventStatus.COMPLETED.value:
        raise ValidationError("Event has already been completed")
    
    return event


# =============================================================================
# Registration Check
# =============================================================================

async def check_registration_open(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Event:
    """
    Check if event registration is still open.
    
    Raises:
        ValidationError: If registration is closed
    """
    event = await get_active_event(event_id, db)
    
    if event.registration_required and event.registration_deadline:
        if datetime.now(timezone.utc) > event.registration_deadline:
            raise ValidationError("Event registration deadline has passed")
    
    return event


# Import datetime for timezone
from datetime import datetime, timezone
