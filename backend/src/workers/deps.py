"""
Workers Dependencies
FastAPI dependencies for background task processing.
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import NotFoundError, AuthorizationError
from src.workers.models import TaskQueue, ScheduledTask
from src.workers.crud import TaskQueueCRUD, ScheduledTaskCRUD
from src.auth.models import User
from src.auth.deps import get_current_user, get_current_active_user


# =============================================================================
# Task Dependencies
# =============================================================================

async def get_task_by_id(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> TaskQueue:
    """
    Get a task by ID with authorization check.
    
    Args:
        task_id: The task UUID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        TaskQueue object
        
    Raises:
        NotFoundError: If task not found
        AuthorizationError: If user doesn't have permission
    """
    task = await TaskQueueCRUD.get_by_id(db, TaskQueue, task_id)
    
    if not task:
        raise NotFoundError(resource="Task", resource_id=str(task_id))
    
    # Check if user has access to this task
    # Admins can access all tasks
    if current_user.is_admin():
        return task
    
    # Check if user created the task or is in the metadata
    task_metadata = task.metadata or {}
    created_by = task_metadata.get("created_by_id")
    
    if created_by and str(created_by) == str(current_user.id):
        return task
    
    # Check if user has worker management permissions
    if not current_user.has_permission("workers:read"):
        raise AuthorizationError("You don't have permission to access this task")
    
    return task


async def get_task_for_update(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> TaskQueue:
    """
    Get a task by ID for update operations with authorization check.
    
    Only admins or task creators can update tasks.
    """
    task = await TaskQueueCRUD.get_by_id(db, TaskQueue, task_id)
    
    if not task:
        raise NotFoundError(resource="Task", resource_id=str(task_id))
    
    # Admins can update any task
    if current_user.is_admin():
        return task
    
    # Check if user created the task
    task_metadata = task.metadata or {}
    created_by = task_metadata.get("created_by_id")
    
    if created_by and str(created_by) == str(current_user.id):
        return task
    
    # Check if user has worker management permissions
    if not current_user.has_permission("workers:write"):
        raise AuthorizationError("You don't have permission to update this task")
    
    return task


# =============================================================================
# Scheduled Task Dependencies
# =============================================================================

async def get_scheduled_task_by_id(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ScheduledTask:
    """
    Get a scheduled task by ID with authorization check.
    
    Args:
        task_id: The scheduled task UUID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        ScheduledTask object
        
    Raises:
        NotFoundError: If task not found
        AuthorizationError: If user doesn't have permission
    """
    task = await ScheduledTaskCRUD.get_by_id(db, ScheduledTask, task_id)
    
    if not task:
        raise NotFoundError(resource="ScheduledTask", resource_id=str(task_id))
    
    # Admins can access all scheduled tasks
    if current_user.is_admin():
        return task
    
    # Check if user created the task
    if task.created_by_id and str(task.created_by_id) == str(current_user.id):
        return task
    
    # Check if user has worker management permissions
    if not current_user.has_permission("workers:read"):
        raise AuthorizationError("You don't have permission to access this scheduled task")
    
    return task


async def get_scheduled_task_for_update(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ScheduledTask:
    """
    Get a scheduled task by ID for update operations with authorization check.
    
    Only admins or task creators can update scheduled tasks.
    """
    task = await ScheduledTaskCRUD.get_by_id(db, ScheduledTask, task_id)
    
    if not task:
        raise NotFoundError(resource="ScheduledTask", resource_id=str(task_id))
    
    # Admins can update any scheduled task
    if current_user.is_admin():
        return task
    
    # Check if user created the task
    if task.created_by_id and str(task.created_by_id) == str(current_user.id):
        return task
    
    # Check if user has worker management permissions
    if not current_user.has_permission("workers:write"):
        raise AuthorizationError("You don't have permission to update this scheduled task")
    
    return task


# =============================================================================
# Permission Dependencies
# =============================================================================

def check_task_permission(required_permission: str):
    """
    Create a dependency that checks if user has the specified task permission.
    
    Args:
        required_permission: Permission name (e.g., 'workers:read', 'workers:write')
        
    Returns:
        Dependency function
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        # Admin has all permissions
        if current_user.is_admin():
            return current_user
        
        if not current_user.has_permission(required_permission):
            raise AuthorizationError(
                message=f"Permission '{required_permission}' is required"
            )
        return current_user
    
    return permission_checker


# =============================================================================
# Task Type Validation
# =============================================================================

async def validate_task_type(
    task_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> str:
    """
    Validate that the task type is allowed.
    
    Args:
        task_type: The task type string
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Validated task type
        
    Raises:
        HTTPException: If task type is not allowed
    """
    from src.workers.models import TaskType
    
    # Check if it's a valid task type
    try:
        valid_type = TaskType(task_type)
        return valid_type.value
    except ValueError:
        # Check for custom task types (not in enum)
        allowed_custom_types = ["custom_task"]
        if task_type in allowed_custom_types:
            return task_type
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_TASK_TYPE",
                    "message": f"Invalid task type: {task_type}",
                    "details": {
                        "allowed_types": [t.value for t in TaskType]
                    }
                }
            }
        )


# =============================================================================
# Worker Statistics Access
# =============================================================================

async def get_worker_statistics_access(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Check if user can access worker statistics.
    
    Only admins or users with workers:read permission can view statistics.
    """
    if current_user.is_admin():
        return current_user
    
    if not current_user.has_permission("workers:read"):
        raise AuthorizationError("Worker statistics access denied")
    
    return current_user
