"""
Event Models
SQLAlchemy models for events, campaigns, and related entities.
"""

from datetime import datetime, timezone
from typing import List, TYPE_CHECKING
import uuid
import enum

from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, Integer, 
    ForeignKey, Table, Enum, Float, JSON, ARRAY, Numeric
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from src.core.database import Base


# =============================================================================
# Enums
# =============================================================================

class EventType(str, enum.Enum):
    """Types of events."""
    RALLY = "rally"
    MEETING = "meeting"
    PROTEST = "protest"
    CAMPAIGN = "campaign"
    TRAINING = "training"
    CELEBRATION = "celebration"
    DOOR_TO_DOOR = "door_to_door"
    PHONE_BANKING = "phone_banking"
    VOLUNTEER_MEETUP = "volunteer_meetup"
    FUNDRAISER = "fundraiser"
    PRESS_CONFERENCE = "press_conference"
    OTHER = "other"


class EventStatus(str, enum.Enum):
    """Event status."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AttendanceStatus(str, enum.Enum):
    """Attendance status for event participants."""
    REGISTERED = "registered"
    CONFIRMED = "confirmed"
    ATTENDED = "attended"
    NO_SHOW = "no_show"
    CANCELLED = "cancelled"


class TaskStatus(str, enum.Enum):
    """Task status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CampaignStatus(str, enum.Enum):
    """Campaign status."""
    PLANNING = "planning"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# =============================================================================
# Association Tables
# =============================================================================

# Event-Participants association (many-to-many)
event_participants = Table(
    "event_participants",
    Base.metadata,
    Column("event_id", ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
    Column("member_id", ForeignKey("members.id", ondelete="CASCADE"), primary_key=True),
    Column("registered_at", DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
    Column("status", String(20), default=AttendanceStatus.REGISTERED.value),
    Column("is_organizer", Boolean, default=False),
    Column("notes", Text, nullable=True),
)


# =============================================================================
# Event Model
# =============================================================================

class Event(Base):
    """
    Event model for campaign events and activities.
    
    Events can be rallies, meetings, door-to-door campaigns, etc.
    """
    __tablename__ = "events"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Basic info
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    title_ta: Mapped[str] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    description_ta: Mapped[str] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, default=EventType.OTHER.value)
    
    # Organization
    unit_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organization_units.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Schedule
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Location
    venue_name: Mapped[str] = mapped_column(String(255), nullable=True)
    venue_address: Mapped[str] = mapped_column(Text, nullable=True)
    geo_location: Mapped[str] = mapped_column(Text, nullable=True)  # JSON for GeoJSON Point
    geo_fence_radius: Mapped[int] = mapped_column(Integer, default=100)  # meters for check-in
    
    # Capacity
    max_attendees: Mapped[int] = mapped_column(Integer, nullable=True)
    registration_required: Mapped[bool] = mapped_column(Boolean, default=False)
    registration_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Media
    banner_url: Mapped[str] = mapped_column(Text, nullable=True)
    media_urls: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=EventStatus.DRAFT.value,
        nullable=False,
        index=True
    )
    
    # Extra data
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
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
    unit: Mapped["OrganizationUnit"] = relationship("OrganizationUnit", foreign_keys=[unit_id])
    created_by: Mapped["Member"] = relationship("Member", foreign_keys=[created_by_id])
    participants: Mapped[List["Member"]] = relationship(
        "Member",
        secondary=event_participants,
        back_populates="events"
    )
    attendance_records: Mapped[List["EventAttendance"]] = relationship(
        "EventAttendance",
        back_populates="event",
        cascade="all, delete-orphan"
    )
    tasks: Mapped[List["EventTask"]] = relationship(
        "EventTask",
        back_populates="event",
        cascade="all, delete-orphan"
    )
    budget: Mapped["EventBudget"] = relationship(
        "EventBudget",
        back_populates="event",
        uselist=False,
        cascade="all, delete-orphan"
    )
    feedback: Mapped[List["EventFeedback"]] = relationship(
        "EventFeedback",
        back_populates="event",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Event(id={self.id}, title={self.title}, type={self.type}, status={self.status})>"


# =============================================================================
# Event Attendance Model
# =============================================================================

class EventAttendance(Base):
    """
    Event attendance records with check-in/check-out.
    """
    __tablename__ = "event_attendance"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=AttendanceStatus.REGISTERED.value,
        nullable=False
    )
    
    # Check-in/out times
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    check_in_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    check_in_location: Mapped[str] = mapped_column(Text, nullable=True)  # JSON for GeoJSON Point
    check_out_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Notes
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    
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
    event: Mapped["Event"] = relationship("Event", back_populates="attendance_records")
    member: Mapped["Member"] = relationship("Member")
    
    def __repr__(self) -> str:
        return f"<EventAttendance(id={self.id}, event_id={self.event_id}, member_id={self.member_id}, status={self.status})>"


# =============================================================================
# Event Task Model
# =============================================================================

class EventTask(Base):
    """
    Tasks assigned for events.
    """
    __tablename__ = "event_tasks"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Task info
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Assignment
    assigned_to_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organization_units.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Scheduling
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=5)  # 1=highest, 10=lowest
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=TaskStatus.PENDING.value,
        nullable=False,
        index=True
    )
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Extra data
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict)
    
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
    event: Mapped["Event"] = relationship("Event", back_populates="tasks")
    assigned_to: Mapped["Member"] = relationship("Member", foreign_keys=[assigned_to_id])
    unit: Mapped["OrganizationUnit"] = relationship("OrganizationUnit")
    
    def __repr__(self) -> str:
        return f"<EventTask(id={self.id}, title={self.title}, status={self.status})>"


# =============================================================================
# Event Budget Model
# =============================================================================

class EventBudget(Base):
    """
    Budget tracking for events.
    """
    __tablename__ = "event_budgets"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    
    # Budget details
    estimated_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    actual_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    
    # Breakdown
    categories: Mapped[dict] = mapped_column(JSON, default=dict)  # {"venue": 5000, "food": 3000, ...}
    
    # Approval
    approved_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True
    )
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Notes
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    
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
    event: Mapped["Event"] = relationship("Event", back_populates="budget")
    approved_by: Mapped["Member"] = relationship("Member", foreign_keys=[approved_by_id])
    
    def __repr__(self) -> str:
        return f"<EventBudget(id={self.id}, event_id={self.event_id}, estimated={self.estimated_cost})>"


# =============================================================================
# Event Feedback Model
# =============================================================================

class EventFeedback(Base):
    """
    Feedback from event participants.
    """
    __tablename__ = "event_feedback"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Feedback content
    rating: Mapped[int] = mapped_column(Integer, nullable=True)  # 1-5 stars
    feedback_type: Mapped[str] = mapped_column(String(50), nullable=True)  # general, suggestion, complaint
    comments: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Engagement metrics
    would_recommend: Mapped[bool] = mapped_column(Boolean, nullable=True)
    highlights: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)
    improvements: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)
    
    # Extra data
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict)
    
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
    event: Mapped["Event"] = relationship("Event", back_populates="feedback")
    member: Mapped["Member"] = relationship("Member")
    
    def __repr__(self) -> str:
        return f"<EventFeedback(id={self.id}, event_id={self.event_id}, rating={self.rating})>"


# =============================================================================
# Campaign Model
# =============================================================================

class Campaign(Base):
    """
    Campaign model for organizing coordinated activities.
    """
    __tablename__ = "campaigns"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ta: Mapped[str] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    description_ta: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Organization
    unit_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organization_units.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Schedule
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Goals (JSON)
    goals: Mapped[dict] = mapped_column(JSON, default=dict)  # {target_voters: 10000, door_visits: 5000}
    
    # Budget
    budget: Mapped[float] = mapped_column(Numeric(12, 2), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=CampaignStatus.PLANNING.value,
        nullable=False,
        index=True
    )
    
    # Extra data
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict)
    
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
    unit: Mapped["OrganizationUnit"] = relationship("OrganizationUnit", foreign_keys=[unit_id])
    created_by: Mapped["Member"] = relationship("Member", foreign_keys=[created_by_id])
    tasks: Mapped[List["CampaignTask"]] = relationship(
        "CampaignTask",
        back_populates="campaign",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Campaign(id={self.id}, name={self.name}, status={self.status})>"


# =============================================================================
# Campaign Task Model
# =============================================================================

class CampaignTask(Base):
    """
    Tasks within a campaign.
    """
    __tablename__ = "campaign_tasks"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Task info
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Assignment
    assigned_to_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organization_units.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Scheduling
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=5)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Progress metrics
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100 percentage
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)  # {visited: 50, remaining: 100}
    
    # Extra data
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict)
    
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
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="tasks")
    assigned_to: Mapped["Member"] = relationship("Member", foreign_keys=[assigned_to_id])
    unit: Mapped["OrganizationUnit"] = relationship("OrganizationUnit")
    
    def __repr__(self) -> str:
        return f"<CampaignTask(id={self.id}, title={self.title}, status={self.status})>"


# =============================================================================
# Import for relationships (avoid circular imports)
# =============================================================================

if TYPE_CHECKING:
    from src.auth.models import User, Member
    from src.hierarchy.models import OrganizationUnit
    from src.members.models import Member
