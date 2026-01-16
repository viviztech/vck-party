"""
Grievance Models
SQLAlchemy models for grievance management system.
"""

from datetime import datetime, timezone
from typing import List, TYPE_CHECKING
import uuid
import enum

from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, Integer, 
    ForeignKey, Enum, JSON, Text
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from src.core.database import Base


# =============================================================================
# Enums
# =============================================================================

class GrievanceStatus(str, enum.Enum):
    """Grievance status enum."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    UNDER_INVESTIGATION = "under_investigation"
    PENDING_ACTION = "pending_action"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"
    REJECTED = "rejected"


class GrievancePriority(str, enum.Enum):
    """Grievance priority enum."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class GrievanceCategoryType(str, enum.Enum):
    """Grievance category type enum."""
    FINANCIAL = "financial"
    ORGANIZATIONAL = "organizational"
    PERSONAL = "personal"
    POLITICAL = "political"
    ADMINISTRATIVE = "administrative"
    DISCIPLINARY = "disciplinary"
    ELECTION_RELATED = "election_related"
    INFRASTRUCTURE = "infrastructure"
    OTHER = "other"


class AssignmentType(str, enum.Enum):
    """Assignment type enum."""
    DIRECT = "direct"
    CLAIMED = "claimed"
    ESCALATED = "escalated"
    DELEGATED = "delegated"


class EscalationLevel(str, enum.Enum):
    """Escalation level enum."""
    LEVEL_1 = "level_1"
    LEVEL_2 = "level_2"
    LEVEL_3 = "level_3"
    LEVEL_4 = "level_4"


# =============================================================================
# Grievance Category Model
# =============================================================================

class GrievanceCategory(Base):
    """
    Grievance category definition.
    Categories help classify and route grievances to appropriate handlers.
    """
    __tablename__ = "grievance_categories"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    category_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=GrievanceCategoryType.OTHER.value
    )
    
    # SLA settings (in hours)
    response_sla_hours: Mapped[int] = mapped_column(Integer, default=24)
    resolution_sla_hours: Mapped[int] = mapped_column(Integer, default=72)
    
    # Assignment settings
    default_assignee_role: Mapped[str] = mapped_column(String(100), nullable=True)
    escalation_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Priority defaults
    default_priority: Mapped[str] = mapped_column(
        String(20),
        default=GrievancePriority.MEDIUM.value
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
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
    grievances: Mapped[List["Grievance"]] = relationship(
        "Grievance",
        back_populates="category",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<GrievanceCategory(id={self.id}, name={self.name}, type={self.category_type})>"


# =============================================================================
# Grievance Model
# =============================================================================

class Grievance(Base):
    """
    Main grievance entity.
    Represents a member complaint or issue submitted to the party.
    """
    __tablename__ = "grievances"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Reference number
    reference_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    
    # Submitter info
    submitted_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    submitted_by_name: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # Contact info
    contact_phone: Mapped[str] = mapped_column(String(15), nullable=True)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=True)
    preferred_contact: Mapped[str] = mapped_column(String(20), nullable=True)  # phone, email, both
    
    # Category and Priority
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("grievance_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    priority: Mapped[str] = mapped_column(
        String(20),
        default=GrievancePriority.MEDIUM.value,
        nullable=False,
        index=True
    )
    
    # Subject and Description
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Location info (where the issue occurred)
    district: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    constituency: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    ward: Mapped[str] = mapped_column(String(50), nullable=True)
    specific_location: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Status tracking
    status: Mapped[str] = mapped_column(
        String(30),
        default=GrievanceStatus.SUBMITTED.value,
        nullable=False,
        index=True
    )
    
    # Current assignment
    current_assignee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    current_assignee_name: Mapped[str] = mapped_column(String(200), nullable=True)
    
    # Related entities
    related_member_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    related_event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Attachments (stored as JSON array of file info)
    attachments: Mapped[dict] = mapped_column(JSON, default=list)
    
    # Anonymous submission flag
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Confidential flag
    is_confidential: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Internal notes (visible only to handlers)
    internal_notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Resolution info
    resolution_summary: Mapped[str] = mapped_column(Text, nullable=True)
    resolution_template_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("grievance_resolutions.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Ratings
    submitter_rating: Mapped[int] = mapped_column(Integer, nullable=True)  # 1-5 rating
    
    # Extra data
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    investigation_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    category: Mapped["GrievanceCategory"] = relationship(
        "GrievanceCategory",
        back_populates="grievances"
    )
    assignments: Mapped[List["GrievanceAssignment"]] = relationship(
        "GrievanceAssignment",
        back_populates="grievance",
        cascade="all, delete-orphan"
    )
    escalations: Mapped[List["GrievanceEscalation"]] = relationship(
        "GrievanceEscalation",
        back_populates="grievance",
        cascade="all, delete-orphan"
    )
    sla: Mapped["GrievanceSLA"] = relationship(
        "GrievanceSLA",
        back_populates="grievance",
        uselist=False,
        cascade="all, delete-orphan"
    )
    resolutions: Mapped[List["GrievanceResolution"]] = relationship(
        "GrievanceResolution",
        back_populates="grievance",
        cascade="all, delete-orphan"
    )
    
    # Self-referential for submitter
    submitter: Mapped["Member"] = relationship(
        "Member",
        foreign_keys=[submitted_by_id],
        remote_side=[id]
    )
    assignee: Mapped["Member"] = relationship(
        "Member",
        foreign_keys=[current_assignee_id],
        remote_side=[id]
    )
    related_member: Mapped["Member"] = relationship(
        "Member",
        foreign_keys=[related_member_id],
        remote_side=[id]
    )
    
    def get_full_subject(self) -> str:
        """Get full subject with reference number."""
        return f"[{self.reference_number}] {self.subject}"
    
    def __repr__(self) -> str:
        return f"<Grievance(id={self.id}, ref={self.reference_number}, status={self.status})>"


# =============================================================================
# Grievance Assignment Model
# =============================================================================

class GrievanceAssignment(Base):
    """
    Grievance assignment history.
    Tracks all assignments (current and historical) for a grievance.
    """
    __tablename__ = "grievance_assignments"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    grievance_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("grievances.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Assignee info
    assignee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    assignee_name: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # Assignment details
    assignment_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AssignmentType.DIRECT.value
    )
    assigned_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    assigned_by_name: Mapped[str] = mapped_column(String(200), nullable=True)
    
    # Previous assignee (for tracking reassignment)
    previous_assignee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True
    )
    previous_assignee_name: Mapped[str] = mapped_column(String(200), nullable=True)
    
    # Reason for assignment
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Is this the current assignment?
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    unassigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    grievance: Mapped["Grievance"] = relationship("Grievance", back_populates="assignments")
    
    def __repr__(self) -> str:
        return f"<GrievanceAssignment(id={self.id}, grievance_id={self.grievance_id}, assignee={self.assignee_name})>"


# =============================================================================
# Grievance Escalation Model
# =============================================================================

class GrievanceEscalation(Base):
    """
    Grievance escalation history and rules.
    Tracks escalations and stores escalation configuration.
    """
    __tablename__ = "grievance_escalations"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    grievance_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("grievances.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Escalation details
    escalation_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=EscalationLevel.LEVEL_1.value
    )
    escalation_reason: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # From/to info
    escalated_from_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    escalated_from_name: Mapped[str] = mapped_column(String(200), nullable=True)
    
    escalated_to_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    escalated_to_name: Mapped[str] = mapped_column(String(200), nullable=True)
    
    # Escalation trigger
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=True)  # sla_breach, manual, auto
    trigger_notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Is this the current escalation?
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Resolution of escalation (when resolved)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Timestamps
    escalated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    grievance: Mapped["Grievance"] = relationship("Grievance", back_populates="escalations")
    
    def __repr__(self) -> str:
        return f"<GrievanceEscalation(id={self.id}, grievance_id={self.grievance_id}, level={self.escalation_level})>"


# =============================================================================
# Grievance SLA Model
# =============================================================================

class GrievanceSLA(Base):
    """
    SLA tracking for grievances.
    Stores SLA deadlines and tracks compliance.
    """
    __tablename__ = "grievance_slas"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    grievance_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("grievances.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    
    # SLA targets (in hours from submission)
    response_deadline_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    resolution_deadline_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Actual timestamps
    response_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolution_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Actual completion times
    responded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # SLA status
    response_sla_met: Mapped[bool] = mapped_column(nullable=True)
    resolution_sla_met: Mapped[bool] = mapped_column(nullable=True)
    
    # SLA breach tracking
    response_breach_count: Mapped[int] = mapped_column(Integer, default=0)
    resolution_breach_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Extension history (JSON array)
    extensions: Mapped[dict] = mapped_column(JSON, default=list)
    
    # Pause/hold tracking
    is_on_hold: Mapped[bool] = mapped_column(Boolean, default=False)
    hold_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    total_hold_duration_hours: Mapped[float] = mapped_column(default=0.0)
    
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
    grievance: Mapped["Grievance"] = relationship("Grievance", back_populates="sla")
    
    def __repr__(self) -> str:
        return f"<GrievanceSLA(id={self.id}, grievance_id={self.grievance_id})>"


# =============================================================================
# Grievance Resolution Model
# =============================================================================

class GrievanceResolution(Base):
    """
    Grievance resolution templates and history.
    Stores resolution actions and can be used as templates.
    """
    __tablename__ = "grievance_resolutions"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    grievance_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("grievances.id", ondelete="CASCADE"),
        nullable=True,  # Nullable for template resolutions
        index=True
    )
    
    # Resolution details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    resolution_type: Mapped[str] = mapped_column(String(50), nullable=True)  # action_taken, response, update
    
    # Template flag
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # For templates: category association
    applicable_category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("grievance_categories.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Resolution by
    resolved_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    resolved_by_name: Mapped[str] = mapped_column(String(200), nullable=True)
    
    # Action taken
    action_taken: Mapped[str] = mapped_column(Text, nullable=True)
    follow_up_required: Mapped[bool] = mapped_column(Boolean, default=False)
    follow_up_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Feedback
    submitter_feedback: Mapped[str] = mapped_column(Text, nullable=True)
    handler_notes: Mapped[str] = mapped_column(Text, nullable=True)
    
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
    grievance: Mapped["Grievance"] = relationship("Grievance", back_populates="resolutions")
    
    def __repr__(self) -> str:
        return f"<GrievanceResolution(id={self.id}, title={self.title})>"


# =============================================================================
# Import for relationships (avoid circular imports)
# =============================================================================

if TYPE_CHECKING:
    from src.auth.models import User
    from src.members.models import Member
