"""
Workers Schemas
Pydantic schemas for background task processing.
"""

from datetime import datetime
from typing import List, Optional, Any, Dict
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict

from src.workers.models import TaskStatus, TaskPriority, TaskType, ScheduledTaskStatus


# =============================================================================
# Task Schemas
# =============================================================================

class TaskBase(BaseModel):
    """Base task schema with common fields."""
    task_type: str
    task_name: str = Field(..., min_length=1, max_length=255)
    payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskCreate(TaskBase):
    """Schema for creating a new task."""
    priority: int = Field(default=3, ge=1, le=5)
    max_retries: int = Field(default=3, ge=0, le=10)
    scheduled_at: Optional[datetime] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "task_type": "sms_notification",
                "task_name": "Send SMS to members",
                "payload": {
                    "recipients": ["+919876543210", "+919876543211"],
                    "message": "Hello, this is a test message"
                },
                "priority": 3,
                "max_retries": 3
            }
        }
    }


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    status: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    payload: Optional[Dict[str, Any]] = None


class TaskResponse(TaskBase):
    """Task response schema."""
    id: UUID
    status: str
    priority: int
    retry_count: int
    max_retries: int
    worker_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TaskResponseMinimal(BaseModel):
    """Minimal task response for lists."""
    id: UUID
    task_type: str
    task_name: str
    status: str
    priority: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    """Paginated task list response."""
    tasks: List[TaskResponseMinimal]
    total: int
    page: int
    limit: int
    total_pages: int


# =============================================================================
# Task History Schemas
# =============================================================================

class TaskHistoryResponse(BaseModel):
    """Task history response schema."""
    id: UUID
    task_id: UUID
    attempt_number: int
    status: str
    worker_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    output_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TaskHistoryListResponse(BaseModel):
    """Task history list response."""
    history: List[TaskHistoryResponse]
    total: int


# =============================================================================
# Scheduled Task Schemas
# =============================================================================

class ScheduledTaskBase(BaseModel):
    """Base scheduled task schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    task_type: str
    task_name: str = Field(..., min_length=1, max_length=255)
    payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScheduledTaskCreate(ScheduledTaskBase):
    """Schema for creating a scheduled task."""
    cron_expression: str = Field(..., min_length=1, max_length=100)
    timezone: str = Field(default="UTC")
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay_seconds: int = Field(default=60, ge=0)
    timeout_seconds: int = Field(default=300, ge=0)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Daily Summary Report",
                "description": "Generate daily summary report",
                "task_type": "report_generation",
                "task_name": "Generate Daily Summary",
                "payload": {"report_type": "daily_summary"},
                "cron_expression": "0 8 * * *",
                "timezone": "Asia/Kolkata",
                "max_retries": 3
            }
        }
    }


class ScheduledTaskUpdate(BaseModel):
    """Schema for updating a scheduled task."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    cron_expression: Optional[str] = Field(None, min_length=1, max_length=100)
    timezone: Optional[str] = None
    status: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    retry_delay_seconds: Optional[int] = Field(None, ge=0)
    timeout_seconds: Optional[int] = Field(None, ge=0)


class ScheduledTaskResponse(ScheduledTaskBase):
    """Scheduled task response schema."""
    id: UUID
    status: str
    cron_expression: str
    timezone: str
    max_retries: int
    retry_delay_seconds: int
    timeout_seconds: int
    last_run_at: Optional[datetime] = None
    last_run_status: Optional[str] = None
    last_run_result: Optional[Dict[str, Any]] = None
    last_error: Optional[str] = None
    next_run_at: Optional[datetime] = None
    created_by_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ScheduledTaskResponseMinimal(BaseModel):
    """Minimal scheduled task response for lists."""
    id: UUID
    name: str
    task_type: str
    status: str
    cron_expression: str
    next_run_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class ScheduledTaskListResponse(BaseModel):
    """Paginated scheduled task list response."""
    tasks: List[ScheduledTaskResponseMinimal]
    total: int
    page: int
    limit: int
    total_pages: int


# =============================================================================
# Task Search Filters
# =============================================================================

class TaskSearchFilters(BaseModel):
    """Search filters for tasks."""
    status: Optional[str] = None
    task_type: Optional[str] = None
    priority: Optional[int] = None
    worker_id: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    search: Optional[str] = None


class ScheduledTaskSearchFilters(BaseModel):
    """Search filters for scheduled tasks."""
    status: Optional[str] = None
    task_type: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    search: Optional[str] = None


# =============================================================================
# Action Schemas
# =============================================================================

class TaskActionResponse(BaseModel):
    """Response for task actions."""
    success: bool
    message: str
    task_id: UUID


class TaskCancelRequest(BaseModel):
    """Request to cancel a task."""
    reason: Optional[str] = None


class TaskRetryRequest(BaseModel):
    """Request to retry a task."""
    reset_retry_count: bool = True


class TaskEnqueueResponse(BaseModel):
    """Response when enqueuing a task."""
    success: bool
    message: str
    task_id: UUID
    task_status: str


# =============================================================================
# Task Statistics Schemas
# =============================================================================

class TaskStatistics(BaseModel):
    """Task statistics."""
    total_tasks: int
    pending_tasks: int
    queued_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int
    cancelled_tasks: int
    avg_execution_time_ms: Optional[float] = None
    success_rate: Optional[float] = None


class WorkerStatistics(BaseModel):
    """Worker statistics."""
    active_workers: int
    total_tasks_processed: int
    tasks_per_minute: float
    avg_queue_time_ms: Optional[float] = None


# =============================================================================
# API Response Schemas
# =============================================================================

class ApiResponse(BaseModel):
    """Generic API response."""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Error API response."""
    success: bool = False
    error: dict
