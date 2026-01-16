"""
Workers Router
API routes for background task processing.
"""

from datetime import datetime, timezone
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import NotFoundError, BusinessError

from src.workers.schemas import (
    TaskCreate,
    TaskResponse,
    TaskResponseMinimal,
    TaskListResponse,
    TaskUpdate,
    TaskHistoryResponse,
    TaskHistoryListResponse,
    TaskActionResponse,
    TaskCancelRequest,
    TaskRetryRequest,
    TaskEnqueueResponse,
    TaskStatistics,
    ScheduledTaskCreate,
    ScheduledTaskResponse,
    ScheduledTaskResponseMinimal,
    ScheduledTaskListResponse,
    ScheduledTaskUpdate,
    ApiResponse,
)
from src.workers.deps import (
    get_task_by_id,
    get_task_for_update,
    get_scheduled_task_by_id,
    get_scheduled_task_for_update,
    check_task_permission,
)
from src.workers.crud import TaskQueueCRUD, TaskHistoryCRUD, ScheduledTaskCRUD
from src.workers.models import TaskQueue, TaskStatus, TaskType, ScheduledTask
from src.workers import tasks
from src.auth.models import User


router = APIRouter(prefix="/workers", tags=["Workers"])


# =============================================================================
# Health Check
# =============================================================================

@router.get("/health")
async def workers_health_check():
    """Health check endpoint for workers service."""
    return {"status": "healthy", "service": "workers"}


# =============================================================================
# Task Queue Endpoints
# =============================================================================

@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    priority: Optional[int] = Query(None, ge=1, le=5),
    search: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_task_permission("workers:read")),
):
    """
    List queued tasks with pagination and filters.
    """
    tasks_list, total = await TaskQueueCRUD.get_tasks_paginated(
        db, page, limit, status, task_type, priority, search, from_date, to_date
    )
    
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    
    return TaskListResponse(
        tasks=[TaskResponseMinimal.model_validate(t) for t in tasks_list],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.post("/tasks", response_model=TaskEnqueueResponse, status_code=status.HTTP_201_CREATED)
async def enqueue_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_task_permission("workers:write")),
):
    """
    Enqueue a new task for background processing.
    """
    task_data.metadata["created_by_id"] = str(current_user.id)
    
    task = await TaskQueueCRUD.create(db, task_data, created_by_id=current_user.id)
    
    try:
        from src.workers.celery import celery_app
        
        task_mapping = {
            TaskType.SMS_NOTIFICATION.value: tasks.send_sms,
            TaskType.EMAIL_NOTIFICATION.value: tasks.send_email,
            TaskType.PUSH_NOTIFICATION.value: tasks.send_push_notification,
            TaskType.BULK_OPERATION.value: tasks.bulk_operation,
            TaskType.ML_INFERENCE.value: tasks.ml_inference,
        }
        
        celery_task = task_mapping.get(task_data.task_type)
        
        if celery_task:
            celery_task.delay(
                task_id=str(task.id),
                payload=task.payload
            )
        
        task_status = TaskStatus.QUEUED.value
        
    except Exception:
        task_status = TaskStatus.PENDING.value
        await TaskQueueCRUD.update_status(db, task.id, task_status)
    
    return TaskEnqueueResponse(
        success=True,
        message="Task enqueued successfully",
        task_id=task.id,
        task_status=task_status,
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task: TaskQueue = Depends(get_task_by_id),
):
    """Get a specific task by ID."""
    return TaskResponse.model_validate(task)


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    task_data: TaskUpdate,
    task: TaskQueue = Depends(get_task_for_update),
    db: AsyncSession = Depends(get_db),
):
    """Update a task."""
    if task.status not in [TaskStatus.PENDING.value, TaskStatus.QUEUED.value]:
        raise BusinessError(message="Can only update pending or queued tasks")
    
    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    await db.commit()
    await db.refresh(task)
    
    return TaskResponse.model_validate(task)


@router.post("/tasks/{task_id}/cancel", response_model=TaskActionResponse)
async def cancel_task(
    task_id: UUID,
    cancel_request: TaskCancelRequest = None,
    task: TaskQueue = Depends(get_task_for_update),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a pending or queued task."""
    try:
        await TaskQueueCRUD.cancel(db, task_id, reason=cancel_request.reason if cancel_request else None)
    except BusinessError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())
    
    return TaskActionResponse(
        success=True,
        message="Task cancelled successfully",
        task_id=task_id,
    )


@router.post("/tasks/{task_id}/retry", response_model=TaskActionResponse)
async def retry_task(
    task_id: UUID,
    retry_request: TaskRetryRequest = None,
    task: TaskQueue = Depends(get_task_for_update),
    db: AsyncSession = Depends(get_db),
):
    """Retry a failed task."""
    try:
        await TaskQueueCRUD.retry(
            db, task_id,
            reset_retry_count=retry_request.reset_retry_count if retry_request else True
        )
        
        try:
            from src.workers.celery import celery_app
            from src.workers import tasks as worker_tasks
            
            task_mapping = {
                TaskType.SMS_NOTIFICATION.value: worker_tasks.send_sms,
                TaskType.EMAIL_NOTIFICATION.value: worker_tasks.send_email,
                TaskType.PUSH_NOTIFICATION.value: worker_tasks.send_push_notification,
                TaskType.BULK_OPERATION.value: worker_tasks.bulk_operation,
                TaskType.ML_INFERENCE.value: worker_tasks.ml_inference,
            }
            
            celery_task = task_mapping.get(task.task_type)
            
            if celery_task:
                celery_task.delay(
                    task_id=str(task.id),
                    payload=task.payload
                )
                
        except Exception:
            pass
        
    except BusinessError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())
    
    return TaskActionResponse(
        success=True,
        message="Task retry queued",
        task_id=task_id,
    )


# =============================================================================
# Task History Endpoints
# =============================================================================

@router.get("/tasks/{task_id}/history", response_model=TaskHistoryListResponse)
async def get_task_history(
    task_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_task_permission("workers:read")),
):
    """Get execution history for a specific task."""
    history, total = await TaskHistoryCRUD.get_history_paginated(
        db, page, limit, task_id=task_id
    )
    
    return TaskHistoryListResponse(
        history=[TaskHistoryResponse.model_validate(h) for h in history],
        total=total,
    )


@router.get("/history", response_model=TaskHistoryListResponse)
async def list_task_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    task_id: Optional[UUID] = None,
    status: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_task_permission("workers:read")),
):
    """List task execution history with filters."""
    history, total = await TaskHistoryCRUD.get_history_paginated(
        db, page, limit, task_id, status, from_date, to_date
    )
    
    return TaskHistoryListResponse(
        history=[TaskHistoryResponse.model_validate(h) for h in history],
        total=total,
    )


# =============================================================================
# Scheduled Task Endpoints
# =============================================================================

@router.get("/scheduled", response_model=ScheduledTaskListResponse)
async def list_scheduled_tasks(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    search: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_task_permission("workers:read")),
):
    """List scheduled tasks with pagination and filters."""
    tasks_list, total = await ScheduledTaskCRUD.get_tasks_paginated(
        db, page, limit, status, task_type, search, from_date, to_date
    )
    
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    
    return ScheduledTaskListResponse(
        tasks=[ScheduledTaskResponseMinimal.model_validate(t) for t in tasks_list],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.post("/scheduled", response_model=ScheduledTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_scheduled_task(
    task_data: ScheduledTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_task_permission("workers:write")),
):
    """Create a new scheduled task."""
    task = await ScheduledTaskCRUD.create(db, task_data, created_by_id=current_user.id)
    return ScheduledTaskResponse.model_validate(task)


@router.get("/scheduled/{task_id}", response_model=ScheduledTaskResponse)
async def get_scheduled_task(
    task: ScheduledTask = Depends(get_scheduled_task_by_id),
):
    """Get a specific scheduled task by ID."""
    return ScheduledTaskResponse.model_validate(task)


@router.put("/scheduled/{task_id}", response_model=ScheduledTaskResponse)
async def update_scheduled_task(
    task_id: UUID,
    task_data: ScheduledTaskUpdate,
    task: ScheduledTask = Depends(get_scheduled_task_for_update),
    db: AsyncSession = Depends(get_db),
):
    """Update a scheduled task."""
    updated_task = await ScheduledTaskCRUD.update(db, task_id, task_data)
    
    if not updated_task:
        raise NotFoundError(resource="ScheduledTask", resource_id=str(task_id))
    
    return ScheduledTaskResponse.model_validate(updated_task)


@router.post("/scheduled/{task_id}/pause", response_model=ApiResponse)
async def pause_scheduled_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_task_permission("workers:write")),
):
    """Pause a scheduled task."""
    try:
        await ScheduledTaskCRUD.pause(db, task_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())
    
    return ApiResponse(
        success=True,
        message="Scheduled task paused",
    )


@router.post("/scheduled/{task_id}/resume", response_model=ApiResponse)
async def resume_scheduled_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_task_permission("workers:write")),
):
    """Resume a paused scheduled task."""
    try:
        await ScheduledTaskCRUD.resume(db, task_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())
    except BusinessError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())
    
    return ApiResponse(
        success=True,
        message="Scheduled task resumed",
    )


@router.delete("/scheduled/{task_id}", response_model=ApiResponse)
async def delete_scheduled_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_task_permission("workers:write")),
):
    """Delete a scheduled task."""
    deleted = await ScheduledTaskCRUD.delete(db, ScheduledTask, task_id)
    
    if not deleted:
        raise NotFoundError(resource="ScheduledTask", resource_id=str(task_id))
    
    return ApiResponse(
        success=True,
        message="Scheduled task deleted",
    )


# =============================================================================
# Statistics Endpoints
# =============================================================================

@router.get("/statistics", response_model=TaskStatistics)
async def get_task_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_task_permission("workers:read")),
):
    """Get task queue statistics."""
    stats = await TaskQueueCRUD.get_statistics(db)
    
    return TaskStatistics(
        total_tasks=stats.get("total_tasks", 0),
        pending_tasks=stats.get("pending", 0),
        queued_tasks=stats.get("queued", 0),
        running_tasks=stats.get("running", 0),
        completed_tasks=stats.get("completed", 0),
        failed_tasks=stats.get("failed", 0),
        cancelled_tasks=stats.get("cancelled", 0),
        success_rate=stats.get("success_rate"),
    )
