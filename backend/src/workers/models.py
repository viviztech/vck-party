"""
Workers Models
SQLAlchemy models for background task processing.
"""

from datetime import datetime, timezone
from typing import List, TYPE_CHECKING
import uuid

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Enum, JSON, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.core.database import Base
import enum


# =============================================================================
# Enums
# =============================================================================

class TaskStatus(str, enum.Enum):
    """Task execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(int, enum.Enum):
    """Task priority levels (lower number = higher priority)."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BULK = 5


class TaskType(str, enum.Enum):
    """Types of background tasks."""
    SMS_NOTIFICATION = "sms_notification"
    EMAIL_NOTIFICATION = "email_notification"
    PUSH_NOTIFICATION = "push_notification"
    BULK_OPERATION = "bulk_operation"
    ML_INFERENCE = "ml_inference"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    REPORT_GENERATION = "report_generation"
    CLEANUP = "cleanup"
    SYNC = "sync"
    OTHER = "other"


class ScheduledTaskStatus(str, enum.Enum):
    """Scheduled task status."""
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"


# =============================================================================
# Task Queue Model
# =============================================================================

class TaskQueue(Base):
    """
    Task queue model for background task processing.
    
    Stores queued tasks with their type, status, payload, and metadata.
    """
    __tablename__ = "task_queue"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Task identification
    task_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    task_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Task status
    status: Mapped[str] = mapped_column(
        String(20),
        default=TaskStatus.PENDING.value,
        nullable=False,
        index=True
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        default=TaskPriority.NORMAL.value,
        nullable=False,
        index=True
    )
    
    # Task payload (JSON)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # Execution tracking
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    worker_id: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Results
    result: Mapped[dict] = mapped_column(JSON, default=dict, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    error_traceback: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Timing
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    history: Mapped[List["TaskHistory"]] = relationship(
        "TaskHistory",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_task_queue_status_priority", "status", "priority"),
        Index("idx_task_queue_type_status", "task_type", "status"),
        Index("idx_task_queue_scheduled", "scheduled_at", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<TaskQueue(id={self.id}, type={self.task_type}, status={self.status})>"


# =============================================================================
# Task History Model
# =============================================================================

class TaskHistory(Base):
    """
    Task history model for tracking task execution history.
    
    Records each attempt at executing a task for audit and debugging.
    """
    __tablename__ = "task_history"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Reference to task
    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("task_queue.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Execution info
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Worker info
    worker_id: Mapped[str] = mapped_column(String(255), nullable=True)
    worker_host: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    
    # Results
    input_payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=True)
    output_result: Mapped[dict] = mapped_column(JSON, default=dict, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    error_traceback: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    task: Mapped["TaskQueue"] = relationship("TaskQueue", back_populates="history")
    
    # Indexes
    __table_args__ = (
        Index("idx_task_history_task_created", "task_id", "created_at"),
        Index("idx_task_history_status", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<TaskHistory(id={self.id}, task_id={self.task_id}, attempt={self.attempt_number})>"


# =============================================================================
# Scheduled Task Model
# =============================================================================

class ScheduledTask(Base):
    """
    Scheduled task model for cron-based scheduled tasks.
    
    Manages recurring tasks that run on a schedule.
    """
    __tablename__ = "scheduled_tasks"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Task identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Task configuration
    task_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    task_name: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # Schedule (cron expression)
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=ScheduledTaskStatus.ACTIVE.value,
        nullable=False,
        index=True
    )
    
    # Execution settings
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    retry_delay_seconds: Mapped[int] = mapped_column(Integer, default=60)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=300)
    
    # Last execution info
    last_run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    last_run_status: Mapped[str] = mapped_column(String(20), nullable=True)
    last_run_result: Mapped[dict] = mapped_column(JSON, default=dict, nullable=True)
    last_error: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Next execution
    next_run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    
    # Created by
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])
    
    # Indexes
    __table_args__ = (
        Index("idx_scheduled_tasks_status_next", "status", "next_run_at"),
    )
    
    def __repr__(self) -> str:
        return f"<ScheduledTask(id={self.id}, name={self.name}, cron={self.cron_expression})>"


# =============================================================================
# Import for relationships (avoid circular imports)
# =============================================================================

if TYPE_CHECKING:
    from src.auth.models import User
