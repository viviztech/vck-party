"""
Communications Models
SQLAlchemy models for announcements, forums, posts, comments, and grievances.
"""

from datetime import datetime, timezone
from typing import List, TYPE_CHECKING
import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Integer, Enum, JSON, ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.core.database import Base
import enum


# =============================================================================
# Enums
# =============================================================================

class AnnouncementScope(str, enum.Enum):
    """Announcement scope levels."""
    ALL = "all"
    STATE = "state"
    DISTRICT = "district"
    CONSTITUENCY = "constituency"
    BOOTH = "booth"


class AnnouncementType(str, enum.Enum):
    """Announcement types."""
    GENERAL = "general"
    URGENT = "urgent"
    EVENT = "event"
    CAMPAIGN = "campaign"
    MEMBER_UPDATE = "member_update"


class ForumVisibility(str, enum.Enum):
    """Forum visibility levels."""
    PUBLIC = "public"
    MEMBERS_ONLY = "members_only"
    DISTRICT_ONLY = "district_only"
    PRIVATE = "private"


class GrievanceStatus(str, enum.Enum):
    """Grievance status workflow."""
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REJECTED = "rejected"


class GrievancePriority(str, enum.Enum):
    """Grievance priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class CommunicationChannel(str, enum.Enum):
    """Communication channels for logging."""
    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"
    IN_APP = "in_app"


class ReactionType(str, enum.Enum):
    """Reaction types for posts/comments."""
    LIKE = "like"
    LOVE = "love"
    LAUGH = "laugh"
    WOW = "wow"
    SAD = "sad"
    ANGRY = "angry"


# =============================================================================
# Announcement Models
# =============================================================================

class Announcement(Base):
    """
    Announcements for communication with members.
    
    Supports targeting by organization hierarchy level (state, district, etc.)
    """
    __tablename__ = "announcements"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    title_ta: Mapped[str] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_ta: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Organization
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organization_units.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    target_scope: Mapped[str] = mapped_column(
        String(20),
        default=AnnouncementScope.ALL.value
    )
    
    # Delivery channels
    send_push: Mapped[bool] = mapped_column(Boolean, default=True)
    send_sms: Mapped[bool] = mapped_column(Boolean, default=False)
    send_email: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Scheduling
    publish_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Media
    image_url: Mapped[str] = mapped_column(Text, nullable=True)
    attachment_urls: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)
    
    # Display
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    announcement_type: Mapped[str] = mapped_column(
        String(20),
        default=AnnouncementType.GENERAL.value
    )
    
    # Status
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Extra data
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict)
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
    created_by: Mapped["Member"] = relationship("Member", back_populates="announcements")
    unit: Mapped["OrganizationUnit"] = relationship("OrganizationUnit")
    targets: Mapped[List["AnnouncementTarget"]] = relationship(
        "AnnouncementTarget",
        back_populates="announcement",
        cascade="all, delete-orphan"
    )
    logs: Mapped[List["CommunicationLog"]] = relationship(
        "CommunicationLog",
        back_populates="announcement"
    )
    
    def __repr__(self) -> str:
        return f"<Announcement(id={self.id}, title={self.title})>"


class AnnouncementTarget(Base):
    """
    Targeted districts/constituencies/wards for announcements.
    
    Allows precise targeting within a scope level.
    """
    __tablename__ = "announcement_targets"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    announcement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("announcements.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Target specification
    unit_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organization_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    unit_type: Mapped[str] = mapped_column(String(20), nullable=False)  # district, constituency, etc.
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    announcement: Mapped["Announcement"] = relationship("Announcement", back_populates="targets")
    unit: Mapped["OrganizationUnit"] = relationship("OrganizationUnit")
    
    def __repr__(self) -> str:
        return f"<AnnouncementTarget(id={self.id}, unit_id={self.unit_id})>"


# =============================================================================
# Forum Models
# =============================================================================

class Forum(Base):
    """
    Discussion forums organized by topic/region.
    
    Forums can be public, member-only, or private.
    """
    __tablename__ = "forums"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
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
    
    # Visibility and moderation
    visibility: Mapped[str] = mapped_column(
        String(20),
        default=ForumVisibility.MEMBERS_ONLY.value
    )
    is_moderated: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Moderation flags
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    locked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Statistics
    posts_count: Mapped[int] = mapped_column(Integer, default=0)
    members_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Media
    cover_image_url: Mapped[str] = mapped_column(Text, nullable=True)
    icon_url: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Category/tags for organization
    category: Mapped[str] = mapped_column(String(50), nullable=True)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String(50)), default=list)
    
    # Soft delete for posts/comments
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Extra data
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict)
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
    unit: Mapped["OrganizationUnit"] = relationship("OrganizationUnit")
    created_by: Mapped["Member"] = relationship("Member", foreign_keys=[created_by_id])
    locked_by: Mapped["Member"] = relationship("Member", foreign_keys=[locked_by_id])
    posts: Mapped[List["ForumPost"]] = relationship(
        "ForumPost",
        back_populates="forum",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Forum(id={self.id}, name={self.name})>"


class ForumPost(Base):
    """
    Posts in forums.
    
    Supports threading, reactions, and moderation.
    """
    __tablename__ = "forum_posts"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    forum_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("forums.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Content
    title: Mapped[str] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_ta: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Author
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Threading
    parent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("forum_posts.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Moderation
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    hidden_reason: Mapped[str] = mapped_column(Text, nullable=True)
    hidden_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True
    )
    hidden_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Moderated by
    approved_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True
    )
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Statistics
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    comments_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Media
    image_urls: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)
    attachment_urls: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)
    
    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Extra data
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict)
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
    forum: Mapped["Forum"] = relationship("Forum", back_populates="posts")
    author: Mapped["Member"] = relationship("Member", foreign_keys=[author_id])
    parent: Mapped["ForumPost"] = relationship("ForumPost", remote_side=[id], back_populates="replies")
    replies: Mapped[List["ForumPost"]] = relationship("ForumPost", remote_side=[parent_id], back_populates="parent")
    hidden_by: Mapped["Member"] = relationship("Member", foreign_keys=[hidden_by_id])
    approved_by: Mapped["Member"] = relationship("Member", foreign_keys=[approved_by_id])
    comments: Mapped[List["ForumComment"]] = relationship(
        "ForumComment",
        back_populates="post",
        cascade="all, delete-orphan"
    )
    reactions: Mapped[List["ForumReaction"]] = relationship(
        "ForumReaction",
        back_populates="post",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<ForumPost(id={self.id}, title={self.title})>"


class ForumComment(Base):
    """
    Comments on forum posts.
    
    Supports single-level nesting.
    """
    __tablename__ = "forum_comments"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("forum_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    parent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("forum_comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Author
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Moderation
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True)
    approved_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True
    )
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    hidden_reason: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Statistics
    reactions_count: Mapped[int] = mapped_column(Integer, default=0)
    replies_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Media
    image_url: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Extra data
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict)
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
    post: Mapped["ForumPost"] = relationship("ForumPost", back_populates="comments")
    parent: Mapped["ForumComment"] = relationship("ForumComment", remote_side=[id], back_populates="replies")
    replies: Mapped[List["ForumComment"]] = relationship("ForumComment", remote_side=[parent_id], back_populates="parent")
    author: Mapped["Member"] = relationship("Member", foreign_keys=[author_id])
    approved_by: Mapped["Member"] = relationship("Member", foreign_keys=[approved_by_id])
    reactions: Mapped[List["ForumReaction"]] = relationship(
        "ForumReaction",
        back_populates="comment",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<ForumComment(id={self.id})>"


class ForumReaction(Base):
    """
    Reactions to forum posts and comments.
    """
    __tablename__ = "forum_reactions"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("forum_posts.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    comment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("forum_comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Reaction
    member_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    reaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    post: Mapped["ForumPost"] = relationship("ForumPost", back_populates="reactions")
    comment: Mapped["ForumComment"] = relationship("ForumComment", back_populates="reactions")
    member: Mapped["Member"] = relationship("Member")
    
    def __repr__(self) -> str:
        return f"<ForumReaction(id={self.id}, type={self.reaction_type})>"


# =============================================================================
# Grievance Models
# =============================================================================

class ForumGrievance(Base):
    """
    Member grievances with status tracking.
    
    Supports workflow-based status updates.
    """
    __tablename__ = "forum_grievances"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    ticket_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True
    )
    
    # Submitter
    member_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organization_units.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Content
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Status workflow
    priority: Mapped[str] = mapped_column(
        String(20),
        default=GrievancePriority.MEDIUM.value
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=GrievanceStatus.SUBMITTED.value,
        index=True
    )
    
    # Assignment
    assigned_to_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Resolution
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[str] = mapped_column(Text, nullable=True)
    resolution_summary: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Feedback
    member_feedback: Mapped[str] = mapped_column(Text, nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=True)  # 1-5 rating
    
    # Media
    attachments: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)
    
    # Extra data
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict)
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
    member: Mapped["Member"] = relationship("Member", foreign_keys=[member_id])
    unit: Mapped["OrganizationUnit"] = relationship("OrganizationUnit")
    assigned_to: Mapped["Member"] = relationship("Member", foreign_keys=[assigned_to_id])
    updates: Mapped[List["GrievanceUpdate"]] = relationship(
        "GrievanceUpdate",
        back_populates="grievance",
        cascade="all, delete-orphan"
    )
    attachments_rel: Mapped[List["GrievanceAttachment"]] = relationship(
        "GrievanceAttachment",
        back_populates="grievance",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Grievance(id={self.id}, ticket={self.ticket_number})>"


class GrievanceUpdate(Base):
    """
    Status updates on grievances.
    
    Tracks the complete history of status changes.
    """
    __tablename__ = "grievance_updates"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    grievance_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("grievances.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Update details
    status_from: Mapped[str] = mapped_column(String(20), nullable=True)
    status_to: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Author
    updated_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Internal notes (not visible to member)
    internal_notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Attachments
    attachment_urls: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    grievance: Mapped["Grievance"] = relationship("Grievance", back_populates="updates")
    updated_by: Mapped["Member"] = relationship("Member")
    
    def __repr__(self) -> str:
        return f"<GrievanceUpdate(id={self.id}, status={self.status_to})>"


class GrievanceAttachment(Base):
    """
    Attachments for grievances.
    
    Stores file information for grievance attachments.
    """
    __tablename__ = "grievance_attachments"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    grievance_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("grievances.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # File info
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=True)  # bytes
    
    # Uploaded by
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    grievance: Mapped["Grievance"] = relationship("Grievance", back_populates="attachments_rel")
    uploaded_by: Mapped["Member"] = relationship("Member")
    
    def __repr__(self) -> str:
        return f"<GrievanceAttachment(id={self.id}, file={self.file_name})>"


# =============================================================================
# Communication Log Model
# =============================================================================

class CommunicationLog(Base):
    """
    Logs of SMS, email, push notifications sent.
    
    Tracks delivery status and analytics.
    """
    __tablename__ = "communication_logs"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    announcement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("announcements.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Communication details
    channel: Mapped[str] = mapped_column(String(20), nullable=False)  # sms, email, push
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    recipient_phone: Mapped[str] = mapped_column(String(15), nullable=True)
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Content
    subject: Mapped[str] = mapped_column(String(255), nullable=True)
    content_preview: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Delivery status
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, sent, delivered, failed
    status_message: Mapped[str] = mapped_column(Text, nullable=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=True)  # Provider's message ID
    
    # Timing
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Analytics
    click_count: Mapped[int] = mapped_column(Integer, default=0)
    open_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Error tracking
    error_code: Mapped[str] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    announcement: Mapped["Announcement"] = relationship("Announcement", back_populates="logs")
    recipient: Mapped["Member"] = relationship("Member")
    
    def __repr__(self) -> str:
        return f"<CommunicationLog(id={self.id}, channel={self.channel})>"


# =============================================================================
# Import for relationships (avoid circular imports)
# =============================================================================

if TYPE_CHECKING:
    from src.members.models import Member
    from src.hierarchy.models import OrganizationUnit
