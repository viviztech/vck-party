"""
Workers CRUD Operations
CRUD operations for background task processing.
"""

import math
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Type, TypeVar
from uuid import UUID

from sqlalchemy import select, update, delete, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import NotFoundError, ValidationError, BusinessError
from src.workers.models import TaskQueue, TaskHistory, ScheduledTask, TaskStatus, TaskType
from src.workers.schemas import TaskCreate, TaskUpdate, ScheduledTaskCreate, ScheduledTaskUpdate


# =============================================================================
# Base CRUD Class
# =============================================================================

T = TypeVar("T")

class CRUDBase:
    """Base CRUD class with common operations."""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, model: Type[T], id: UUID) -> Optional[T]:
        """Get a record by ID."""
        result = await db.execute(
            select(model).where(model.id == id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all(
        db: AsyncSession,
        model: Type[T],
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        descending: bool = False
    ) -> List[T]:
        """Get all records with pagination."""
        query = select(model)
        
        if order_by:
            order_field = getattr(model, order_by, None)
            if order_field:
                if descending:
                    query = query.order_by(order_field.desc())
                else:
                    query = query.order_by(order_field.asc())
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def count(db: AsyncSession, model: Type[T]) -> int:
        """Count all records."""
        result = await db.execute(select(func.count(model.id)))
        return result.scalar_one() or 0
    
    @staticmethod
    async def delete(db: AsyncSession, model: Type[T], id: UUID) -> bool:
        """Delete a record by ID."""
        record = await CRUDBase.get_by_id(db, model, id)
        if record:
            await db.delete(record)
            await db.commit()
            return True
        return False


# =============================================================================
# Task Queue CRUD
# =============================================================================

class TaskQueueCRUD(CRUDBase):
    """CRUD operations for task queue."""
    
    @staticmethod
    async def create(db: AsyncSession, task_data: TaskCreate, created_by_id: UUID = None) -> TaskQueue:
        """Create a new task in the queue."""
        task = TaskQueue(
            task_type=task_data.task_type,
            task_name=task_data.task_name,
            payload=task_data.payload,
            metadata=task_data.payload,
            priority=task_data.priority,
            max_retries=task_data.max_retries,
            scheduled_at=task_data.scheduled_at,
            status=TaskStatus.PENDING.value if task_data.scheduled_at else TaskStatus.QUEUED.value,
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task
    
    @staticmethod
    async def get_with_history(db: AsyncSession, task_id: UUID) -> Optional[TaskQueue]:
        """Get a task with its execution history."""
        result = await db.execute(
            select(TaskQueue)
            .where(TaskQueue.id == task_id)
            .options(selectinload(TaskQueue.history).order_by(TaskHistory.created_at.desc()))
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_status(
        db: AsyncSession,
        task_id: UUID,
        status: str,
        worker_id: str = None,
        result: dict = None,
        error_message: str = None,
        error_traceback: str = None
    ) -> Optional[TaskQueue]:
        """Update task status and related fields."""
        task = await TaskQueueCRUD.get_by_id(db, TaskQueue, task_id)
        if not task:
            return None
        
        task.status = status
        if worker_id:
            task.worker_id = worker_id
        if result:
            task.result = result
        if error_message:
            task.error_message = error_message
        if error_traceback:
            task.error_traceback = error_traceback
        
        if status == TaskStatus.RUNNING.value and not task.started_at:
            task.started_at = datetime.now(timezone.utc)
        
        if status in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, TaskStatus.CANCELLED.value]:
            task.completed_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(task)
        return task
    
    @staticmethod
    async def cancel(db: AsyncSession, task_id: UUID, reason: str = None) -> Optional[TaskQueue]:
        """Cancel a task."""
        task = await TaskQueueCRUD.get_by_id(db, TaskQueue, task_id)
        if not task:
            raise NotFoundError(resource="Task", resource_id=str(task_id))
        
        if task.status in [TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value, TaskStatus.RUNNING.value]:
            if task.status == TaskStatus.RUNNING.value:
                raise BusinessError(message="Cannot cancel a running task")
            raise BusinessError(message=f"Task is already {task.status}")
        
        task.status = TaskStatus.CANCELLED.value
        task.error_message = reason or "Cancelled by user"
        task.completed_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(task)
        return task
    
    @staticmethod
    async def retry(db: AsyncSession, task_id: UUID, reset_retry_count: bool = True) -> Optional[TaskQueue]:
        """Retry a failed task."""
        task = await TaskQueueCRUD.get_by_id(db, TaskQueue, task_id)
        if not task:
            raise NotFoundError(resource="Task", resource_id=str(task_id))
        
        if task.status != TaskStatus.FAILED.value:
            raise BusinessError(message="Can only retry failed tasks")
        
        if task.retry_count >= task.max_retries:
            raise BusinessError(message="Maximum retry attempts reached")
        
        if reset_retry_count:
            task.retry_count = 0
        
        task.retry_count += 1
        task.status = TaskStatus.QUEUED.value
        task.error_message = None
        task.error_traceback = None
        task.started_at = None
        task.completed_at = None
        
        await db.commit()
        await db.refresh(task)
        return task
    
    @staticmethod
    async def get_pending_tasks(
        db: AsyncSession,
        limit: int = 100,
        task_type: str = None
    ) -> List[TaskQueue]:
        """Get pending tasks for processing."""
        query = (
            select(TaskQueue)
            .where(TaskQueue.status.in_([TaskStatus.PENDING.value, TaskStatus.QUEUED.value]))
            .order_by(TaskQueue.priority.asc(), TaskQueue.created_at.asc())
            .limit(limit)
        )
        
        if task_type:
            query = query.where(TaskQueue.task_type == task_type)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_tasks_paginated(
        db: AsyncSession,
        page: int = 1,
        limit: int = 20,
        status: str = None,
        task_type: str = None,
        priority: int = None,
        search: str = None,
        from_date: datetime = None,
        to_date: datetime = None
    ) -> Tuple[List[TaskQueue], int]:
        """Get tasks with pagination and filters."""
        query = select(TaskQueue)
        
        # Apply filters
        if status:
            query = query.where(TaskQueue.status == status)
        
        if task_type:
            query = query.where(TaskQueue.task_type == task_type)
        
        if priority:
            query = query.where(TaskQueue.priority == priority)
        
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (TaskQueue.task_name.ilike(search_term)) |
                (TaskQueue.task_type.ilike(search_term))
            )
        
        if from_date:
            query = query.where(TaskQueue.created_at >= from_date)
        
        if to_date:
            query = query.where(TaskQueue.created_at <= to_date)
        
        # Get total count
        count_query = select(func.count(TaskQueue.id)).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit).order_by(TaskQueue.created_at.desc())
        
        result = await db.execute(query)
        tasks = list(result.scalars().all())
        
        return tasks, total
    
    @staticmethod
    async def get_statistics(db: AsyncSession) -> dict:
        """Get task statistics."""
        # Count by status
        status_counts = {}
        for status in TaskStatus:
            result = await db.execute(
                select(func.count(TaskQueue.id))
                .where(TaskQueue.status == status.value)
            )
            status_counts[status.value] = result.scalar() or 0
        
        # Calculate success rate
        completed = status_counts.get(TaskStatus.COMPLETED.value, 0)
        failed = status_counts.get(TaskStatus.FAILED.value, 0)
        total = completed + failed
        success_rate = (completed / total * 100) if total > 0 else 0
        
        return {
            **status_counts,
            "total_tasks": sum(status_counts.values()),
            "success_rate": round(success_rate, 2)
        }


# =============================================================================
# Task History CRUD
# =============================================================================

class TaskHistoryCRUD(CRUDBase):
    """CRUD operations for task history."""
    
    @staticmethod
    async def create(
        db: AsyncSession,
        task_id: UUID,
        status: str,
        attempt_number: int = 1,
        worker_id: str = None,
        input_payload: dict = None,
        output_result: dict = None,
        error_message: str = None,
        error_traceback: str = None,
        started_at: datetime = None,
        completed_at: datetime = None
    ) -> TaskHistory:
        """Create a task history record."""
        history = TaskHistory(
            task_id=task_id,
            attempt_number=attempt_number,
            status=status,
            worker_id=worker_id,
            input_payload=input_payload,
            output_result=output_result,
            error_message=error_message,
            error_traceback=error_traceback,
            started_at=started_at or datetime.now(timezone.utc),
            completed_at=completed_at,
        )
        
        # Calculate duration if completed
        if completed_at and started_at:
            history.duration_ms = int((completed_at - started_at).total_seconds() * 1000)
        
        db.add(history)
        await db.commit()
        await db.refresh(history)
        return history
    
    @staticmethod
    async def get_by_task_id(
        db: AsyncSession,
        task_id: UUID,
        skip: int = 0,
        limit: int = 50
    ) -> List[TaskHistory]:
        """Get task history by task ID."""
        result = await db.execute(
            select(TaskHistory)
            .where(TaskHistory.task_id == task_id)
            .order_by(TaskHistory.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_history_paginated(
        db: AsyncSession,
        page: int = 1,
        limit: int = 20,
        task_id: UUID = None,
        status: str = None,
        from_date: datetime = None,
        to_date: datetime = None
    ) -> Tuple[List[TaskHistory], int]:
        """Get task history with pagination and filters."""
        query = select(TaskHistory)
        
        if task_id:
            query = query.where(TaskHistory.task_id == task_id)
        
        if status:
            query = query.where(TaskHistory.status == status)
        
        if from_date:
            query = query.where(TaskHistory.created_at >= from_date)
        
        if to_date:
            query = query.where(TaskHistory.created_at <= to_date)
        
        # Get total count
        count_query = select(func.count(TaskHistory.id)).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit).order_by(TaskHistory.created_at.desc())
        
        result = await db.execute(query)
        history = list(result.scalars().all())
        
        return history, total
    
    @staticmethod
    async def get_recent_failures(
        db: AsyncSession,
        limit: int = 10,
        hours: int = 24
    ) -> List[TaskHistory]:
        """Get recent task failures."""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        result = await db.execute(
            select(TaskHistory)
            .where(TaskHistory.status == TaskStatus.FAILED.value)
            .where(TaskHistory.created_at >= since)
            .order_by(TaskHistory.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def update(
        db: AsyncSession,
        history_id: UUID,
        status: str = None,
        completed_at: datetime = None,
        duration_ms: int = None,
        output_result: dict = None,
        error_message: str = None,
        error_traceback: str = None
    ) -> Optional[TaskHistory]:
        """Update a task history record."""
        history = await TaskHistoryCRUD.get_by_id(db, TaskHistory, history_id)
        if not history:
            return None
        
        if status:
            history.status = status
        if completed_at:
            history.completed_at = completed_at
        if duration_ms:
            history.duration_ms = duration_ms
        if output_result:
            history.output_result = output_result
        if error_message:
            history.error_message = error_message
        if error_traceback:
            history.error_traceback = error_traceback
        
        await db.commit()
        await db.refresh(history)
        return history


# =============================================================================
# Scheduled Task CRUD
# =============================================================================

class ScheduledTaskCRUD(CRUDBase):
    """CRUD operations for scheduled tasks."""
    
    @staticmethod
    async def create(
        db: AsyncSession,
        task_data: ScheduledTaskCreate,
        created_by_id: UUID = None
    ) -> ScheduledTask:
        """Create a new scheduled task."""
        from croniter import croniter
        
        # Validate cron expression
        if not croniter.is_valid(task_data.cron_expression):
            raise ValidationError(message="Invalid cron expression")
        
        # Calculate next run time
        cron = croniter(task_data.cron_expression, datetime.now(timezone.utc))
        next_run = cron.get_next(datetime)
        
        task = ScheduledTask(
            name=task_data.name,
            description=task_data.description,
            task_type=task_data.task_type,
            task_name=task_data.task_name,
            payload=task_data.payload,
            metadata=task_data.metadata,
            cron_expression=task_data.cron_expression,
            timezone=task_data.timezone,
            max_retries=task_data.max_retries,
            retry_delay_seconds=task_data.retry_delay_seconds,
            timeout_seconds=task_data.timeout_seconds,
            next_run_at=next_run,
            created_by_id=created_by_id,
        )
        
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task
    
    @staticmethod
    async def update(
        db: AsyncSession,
        task_id: UUID,
        task_data: ScheduledTaskUpdate
    ) -> Optional[ScheduledTask]:
        """Update a scheduled task."""
        task = await ScheduledTaskCRUD.get_by_id(db, ScheduledTask, task_id)
        if not task:
            return None
        
        update_data = task_data.model_dump(exclude_unset=True)
        
        # Handle cron expression change
        if "cron_expression" in update_data:
            cron_expr = update_data["cron_expression"]
            if not croniter.is_valid(cron_expr):
                raise ValidationError(message="Invalid cron expression")
            
            from croniter import croniter
            cron = croniter(cron_expr, datetime.now(timezone.utc))
            task.next_run_at = cron.get_next(datetime)
        
        for field, value in update_data.items():
            if field != "cron_expression":
                setattr(task, field, value)
        
        await db.commit()
        await db.refresh(task)
        return task
    
    @staticmethod
    async def pause(db: AsyncSession, task_id: UUID) -> Optional[ScheduledTask]:
        """Pause a scheduled task."""
        task = await ScheduledTaskCRUD.get_by_id(db, ScheduledTask, task_id)
        if not task:
            raise NotFoundError(resource="ScheduledTask", resource_id=str(task_id))
        
        task.status = "paused"
        await db.commit()
        await db.refresh(task)
        return task
    
    @staticmethod
    async def resume(db: AsyncSession, task_id: UUID) -> Optional[ScheduledTask]:
        """Resume a paused scheduled task."""
        task = await ScheduledTaskCRUD.get_by_id(db, ScheduledTask, task_id)
        if not task:
            raise NotFoundError(resource="ScheduledTask", resource_id=str(task_id))
        
        if task.status != "paused":
            raise BusinessError(message="Can only resume paused tasks")
        
        # Recalculate next run
        from croniter import croniter
        cron = croniter(task.cron_expression, datetime.now(timezone.utc))
        task.next_run_at = cron.get_next(datetime)
        
        task.status = "active"
        await db.commit()
        await db.refresh(task)
        return task
    
    @staticmethod
    async def get_due_tasks(db: AsyncSession) -> List[ScheduledTask]:
        """Get scheduled tasks that are due for execution."""
        now = datetime.now(timezone.utc)
        
        result = await db.execute(
            select(ScheduledTask)
            .where(ScheduledTask.status == "active")
            .where(ScheduledTask.next_run_at <= now)
            .order_by(ScheduledTask.next_run_at.asc())
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def update_after_execution(
        db: AsyncSession,
        task_id: UUID,
        status: str,
        result: dict = None,
        error: str = None
    ) -> Optional[ScheduledTask]:
        """Update a scheduled task after execution."""
        task = await ScheduledTaskCRUD.get_by_id(db, ScheduledTask, task_id)
        if not task:
            return None
        
        task.last_run_at = datetime.now(timezone.utc)
        task.last_run_status = status
        task.last_run_result = result
        task.last_error = error
        
        # Calculate next run
        from croniter import croniter
        cron = croniter(task.cron_expression, datetime.now(timezone.utc))
        task.next_run_at = cron.get_next(datetime)
        
        await db.commit()
        await db.refresh(task)
        return task
    
    @staticmethod
    async def get_tasks_paginated(
        db: AsyncSession,
        page: int = 1,
        limit: int = 20,
        status: str = None,
        task_type: str = None,
        search: str = None,
        from_date: datetime = None,
        to_date: datetime = None
    ) -> Tuple[List[ScheduledTask], int]:
        """Get scheduled tasks with pagination and filters."""
        query = select(ScheduledTask)
        
        # Apply filters
        if status:
            query = query.where(ScheduledTask.status == status)
        
        if task_type:
            query = query.where(ScheduledTask.task_type == task_type)
        
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (ScheduledTask.name.ilike(search_term)) |
                (ScheduledTask.description.ilike(search_term))
            )
        
        if from_date:
            query = query.where(ScheduledTask.created_at >= from_date)
        
        if to_date:
            query = query.where(ScheduledTask.created_at <= to_date)
        
        # Get total count
        count_query = select(func.count(ScheduledTask.id)).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit).order_by(ScheduledTask.next_run_at.asc())
        
        result = await db.execute(query)
        tasks = list(result.scalars().all())
        
        return tasks, total
