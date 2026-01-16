"""
Communications Schemas
Pydantic schemas for communications module.
"""

from datetime import datetime
from typing import List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict

from src.communications.models import (
    AnnouncementScope,
    AnnouncementType,
    ForumVisibility,
    GrievanceStatus,
    GrievancePriority,
    CommunicationChannel,
    ReactionType,
)


# =============================================================================
# Pagination Schemas
# =============================================================================

class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    items: List[Any]
    total: int
    page: int
    limit: int
    total_pages: int


# =============================================================================
# Announcement Schemas
# =============================================================================

class AnnouncementTargetCreate(BaseModel):
    """Schema for creating announcement targets."""
    unit_id: UUID
    unit_type: str = Field(..., description="district, constituency, booth, etc.")


class AnnouncementBase(BaseModel):
    """Base announcement schema."""
    title: str = Field(..., min_length=1, max_length=255)
    title_ta: Optional[str] = Field(None, max_length=255)
    content: str = Field(..., min_length=1)
    content_ta: Optional[str] = None
    unit_id: Optional[UUID] = None
    target_scope: str = Field(
        default=AnnouncementScope.ALL.value,
        description="all, state, district, constituency, booth"
    )
    send_push: bool = True
    send_sms: bool = False
    send_email: bool = False
    publish_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    image_url: Optional[str] = None
    attachment_urls: List[str] = []
    announcement_type: str = Field(
        default=AnnouncementType.GENERAL.value,
        description="general, urgent, event, campaign, member_update"
    )
    is_pinned: bool = False


class AnnouncementCreate(AnnouncementBase):
    """Schema for creating an announcement."""
    target_units: Optional[List[UUID]] = Field(
        None,
        description="Specific unit IDs to target within the scope"
    )


class AnnouncementUpdate(BaseModel):
    """Schema for updating an announcement."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    title_ta: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    content_ta: Optional[str] = None
    target_scope: Optional[str] = None
    send_push: Optional[bool] = None
    send_sms: Optional[bool] = None
    send_email: Optional[bool] = None
    publish_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    image_url: Optional[str] = None
    attachment_urls: Optional[List[str]] = None
    announcement_type: Optional[str] = None
    is_pinned: Optional[bool] = None


class AnnouncementTargetResponse(BaseModel):
    """Announcement target response schema."""
    id: UUID
    unit_id: UUID
    unit_type: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AnnouncementResponse(AnnouncementBase):
    """Announcement response schema."""
    id: UUID
    created_by_id: Optional[UUID] = None
    is_sent: bool
    sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    targets: List[AnnouncementTargetResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


class AnnouncementDetailResponse(AnnouncementResponse):
    """Detailed announcement response with full info."""
    metadata: Optional[dict] = None


class AnnouncementListResponse(BaseModel):
    """Paginated announcement list response."""
    announcements: List[AnnouncementResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# =============================================================================
# Announcement Send Schema
# =============================================================================

class AnnouncementSend(BaseModel):
    """Schema for sending an announcement."""
    announcement_id: UUID


class AnnouncementSendResult(BaseModel):
    """Result of sending an announcement."""
    success: bool
    message: str
    recipient_count: int
    channels: dict


# =============================================================================
# Forum Schemas
# =============================================================================

class ForumBase(BaseModel):
    """Base forum schema."""
    name: str = Field(..., min_length=1, max_length=255)
    name_ta: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    description_ta: Optional[str] = None
    unit_id: Optional[UUID] = None
    visibility: str = Field(
        default=ForumVisibility.MEMBERS_ONLY.value,
        description="public, members_only, district_only, private"
    )
    is_moderated: bool = True
    allow_anonymous: bool = False
    category: Optional[str] = Field(None, max_length=50)
    tags: List[str] = []
    cover_image_url: Optional[str] = None
    icon_url: Optional[str] = None


class ForumCreate(ForumBase):
    """Schema for creating a forum."""
    pass


class ForumUpdate(BaseModel):
    """Schema for updating a forum."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    name_ta: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    description_ta: Optional[str] = None
    visibility: Optional[str] = None
    is_moderated: Optional[bool] = None
    allow_anonymous: Optional[bool] = None
    category: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = None
    cover_image_url: Optional[str] = None
    icon_url: Optional[str] = None
    is_locked: Optional[bool] = None


class ForumResponse(ForumBase):
    """Forum response schema."""
    id: UUID
    created_by_id: Optional[UUID] = None
    is_pinned: bool
    is_locked: bool
    posts_count: int
    members_count: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ForumDetailResponse(ForumResponse):
    """Detailed forum response."""
    locked_at: Optional[datetime] = None
    locked_by_id: Optional[UUID] = None
    is_deleted: bool
    metadata: Optional[dict] = None


class ForumListResponse(BaseModel):
    """Paginated forum list response."""
    forums: List[ForumResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# =============================================================================
# Forum Post Schemas
# =============================================================================

class ForumPostBase(BaseModel):
    """Base forum post schema."""
    title: Optional[str] = Field(None, max_length=255)
    content: str = Field(..., min_length=1)
    content_ta: Optional[str] = None
    is_anonymous: bool = False
    image_urls: List[str] = []
    attachment_urls: List[str] = []


class ForumPostCreate(ForumPostBase):
    """Schema for creating a forum post."""
    forum_id: UUID
    parent_id: Optional[UUID] = None  # For replies


class ForumPostUpdate(BaseModel):
    """Schema for updating a forum post."""
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    content_ta: Optional[str] = None
    image_urls: Optional[List[str]] = None
    attachment_urls: Optional[List[str]] = None


class ForumPostModeration(BaseModel):
    """Schema for moderating a post."""
    action: str = Field(..., description="pin, unpin, hide, unhide, lock, unlock")
    reason: Optional[str] = None


class ForumPostResponse(ForumPostBase):
    """Forum post response schema."""
    id: UUID
    forum_id: UUID
    author_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None
    is_pinned: bool
    is_locked: bool
    is_hidden: bool
    views_count: int
    comments_count: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ForumPostDetailResponse(ForumPostResponse):
    """Detailed forum post response."""
    hidden_reason: Optional[str] = None
    hidden_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    metadata: Optional[dict] = None


class ForumPostListResponse(BaseModel):
    """Paginated forum post list response."""
    posts: List[ForumPostResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# =============================================================================
# Forum Comment Schemas
# =============================================================================

class ForumCommentBase(BaseModel):
    """Base forum comment schema."""
    content: str = Field(..., min_length=1)
    is_anonymous: bool = False
    image_url: Optional[str] = None


class ForumCommentCreate(ForumCommentBase):
    """Schema for creating a comment."""
    post_id: UUID
    parent_id: Optional[UUID] = None  # For nested replies


class ForumCommentUpdate(BaseModel):
    """Schema for updating a comment."""
    content: Optional[str] = Field(None, min_length=1)
    image_url: Optional[str] = None


class ForumCommentResponse(ForumCommentBase):
    """Forum comment response schema."""
    id: UUID
    post_id: UUID
    parent_id: Optional[UUID] = None
    author_id: Optional[UUID] = None
    is_approved: bool
    is_hidden: bool
    reactions_count: int
    replies_count: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ForumCommentDetailResponse(ForumCommentResponse):
    """Detailed comment response with nested data."""
    hidden_reason: Optional[str] = None
    approved_at: Optional[datetime] = None
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    metadata: Optional[dict] = None


class ForumCommentListResponse(BaseModel):
    """Paginated comment list response."""
    comments: List[ForumCommentResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# =============================================================================
# Forum Reaction Schemas
# =============================================================================

class ForumReactionCreate(BaseModel):
    """Schema for creating a reaction."""
    post_id: Optional[UUID] = None
    comment_id: Optional[UUID] = None
    reaction_type: str = Field(..., description="like, love, laugh, wow, sad, angry")


class ForumReactionResponse(BaseModel):
    """Forum reaction response schema."""
    id: UUID
    post_id: Optional[UUID] = None
    comment_id: Optional[UUID] = None
    member_id: UUID
    reaction_type: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Grievance Schemas
# =============================================================================

class GrievanceBase(BaseModel):
    """Base grievance schema."""
    category: str = Field(..., min_length=1, max_length=100)
    subject: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    unit_id: Optional[UUID] = None
    priority: str = Field(
        default=GrievancePriority.MEDIUM.value,
        description="low, medium, high, urgent"
    )
    attachments: List[str] = []


class GrievanceCreate(GrievanceBase):
    """Schema for creating a grievance."""
    pass


class GrievanceUpdate(BaseModel):
    """Schema for updating a grievance (not status updates)."""
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    subject: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    priority: Optional[str] = None


class GrievanceStatusUpdate(BaseModel):
    """Schema for updating grievance status."""
    status: str = Field(
        ...,
        description="submitted, acknowledged, in_progress, resolved, closed, rejected"
    )
    notes: Optional[str] = None
    internal_notes: Optional[str] = None  # Not visible to member
    resolution_summary: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)  # For resolved status


class GrievanceAssignment(BaseModel):
    """Schema for assigning a grievance to a handler."""
    assigned_to_id: UUID


class GrievanceResponse(GrievanceBase):
    """Grievance response schema."""
    id: UUID
    ticket_number: str
    member_id: Optional[UUID] = None
    status: str
    assigned_to_id: Optional[UUID] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    member_feedback: Optional[str] = None
    rating: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class GrievanceDetailResponse(GrievanceResponse):
    """Detailed grievance response."""
    resolution_summary: Optional[str] = None
    metadata: Optional[dict] = None
    updates: List["GrievanceUpdateResponse"] = []
    attachments_rel: List["GrievanceAttachmentResponse"] = []


class GrievanceUpdateResponse(BaseModel):
    """Grievance update response schema."""
    id: UUID
    status_from: Optional[str] = None
    status_to: str
    notes: Optional[str] = None
    updated_by_id: Optional[UUID] = None
    internal_notes: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class GrievanceAttachmentResponse(BaseModel):
    """Grievance attachment response schema."""
    id: UUID
    file_name: str
    file_url: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    uploaded_by_id: Optional[UUID] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class GrievanceListResponse(BaseModel):
    """Paginated grievance list response."""
    grievances: List[GrievanceResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class GrievanceTicketResponse(BaseModel):
    """Grievance ticket confirmation response."""
    grievance_id: UUID
    ticket_number: str
    status: str
    message: str


# =============================================================================
# Communication Search Filters
# =============================================================================

class AnnouncementFilters(BaseModel):
    """Search filters for announcements."""
    unit_id: Optional[UUID] = None
    target_scope: Optional[str] = None
    announcement_type: Optional[str] = None
    is_pinned: Optional[bool] = None
    is_sent: Optional[bool] = None
    created_by_id: Optional[UUID] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    search: Optional[str] = None


class ForumFilters(BaseModel):
    """Search filters for forums."""
    unit_id: Optional[UUID] = None
    visibility: Optional[str] = None
    category: Optional[str] = None
    is_locked: Optional[bool] = None
    search: Optional[str] = None


class ForumPostFilters(BaseModel):
    """Search filters for forum posts."""
    forum_id: Optional[UUID] = None
    author_id: Optional[UUID] = None
    is_pinned: Optional[bool] = None
    is_hidden: Optional[bool] = None
    search: Optional[str] = None


class GrievanceFilters(BaseModel):
    """Search filters for grievances."""
    member_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    assigned_to_id: Optional[UUID] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    search: Optional[str] = None


# =============================================================================
# Communication Statistics
# =============================================================================

class CommunicationStats(BaseModel):
    """Communication statistics."""
    total_announcements: int
    announcements_this_month: int
    total_forums: int
    total_posts: int
    total_comments: int
    total_grievances: int
    pending_grievances: int
    resolved_grievances: int
    grievances_by_category: dict
    grievances_by_priority: dict
    communication_channel_stats: dict


class AnnouncementStats(BaseModel):
    """Announcement statistics."""
    total: int
    sent: int
    scheduled: int
    by_type: dict
    by_scope: dict


class ForumStats(BaseModel):
    """Forum statistics."""
    total_forums: int
    total_posts: int
    total_comments: int
    most_active_forums: List[dict]
    top_contributors: List[dict]


class GrievanceStats(BaseModel):
    """Grievance statistics."""
    total: int
    by_status: dict
    by_priority: dict
    by_category: dict
    average_resolution_time_hours: float
    satisfaction_score: float


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


# =============================================================================
# Rebuild forward references
# =============================================================================

GrievanceDetailResponse.model_rebuild()
