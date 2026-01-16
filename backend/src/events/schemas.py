"""
Event Schemas
Pydantic schemas for event-related API requests and responses.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from src.events.models import (
    EventType,
    EventStatus,
    AttendanceStatus,
    TaskStatus,
    CampaignStatus,
)


# =============================================================================
# Base Schemas
# =============================================================================

class EventBase(BaseModel):
    """Base event schema with common fields."""
    title: str = Field(..., min_length=1, max_length=255)
    title_ta: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    description_ta: Optional[str] = None
    type: str = Field(default=EventType.OTHER.value)
    start_time: datetime
    end_time: Optional[datetime] = None
    venue_name: Optional[str] = Field(None, max_length=255)
    venue_address: Optional[str] = None
    geo_location: Optional[str] = None  # JSON string for GeoJSON Point
    geo_fence_radius: Optional[int] = Field(default=100, ge=10, le=5000)
    max_attendees: Optional[int] = Field(None, ge=1)
    registration_required: Optional[bool] = False
    registration_deadline: Optional[datetime] = None
    banner_url: Optional[str] = None
    media_urls: Optional[List[str]] = None


# =============================================================================
# Event Create/Update Schemas
# =============================================================================

class EventCreate(EventBase):
    """Schema for creating a new event."""
    unit_id: Optional[UUID] = None
    status: Optional[str] = Field(default=EventStatus.DRAFT.value)
    metadata: Optional[Dict[str, Any]] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "District General Meeting",
                "title_ta": "மாவட்ட பொதுக்கூட்டம்",
                "description": "Monthly meeting of all district members",
                "type": "meeting",
                "unit_id": "uuid",
                "start_time": "2024-03-15T18:00:00+05:30",
                "end_time": "2024-03-15T20:00:00+05:30",
                "venue_name": "Party Office Hall",
                "venue_address": "123 Anna Salai, Chennai",
                "geo_location": {"type": "Point", "coordinates": [80.2707, 13.0827]},
                "max_attendees": 200,
                "registration_required": True,
                "registration_deadline": "2024-03-14T23:59:59+05:30"
            }
        }
    }


class EventUpdate(BaseModel):
    """Schema for updating an event."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    title_ta: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    description_ta: Optional[str] = None
    type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    venue_name: Optional[str] = Field(None, max_length=255)
    venue_address: Optional[str] = None
    geo_location: Optional[str] = None
    geo_fence_radius: Optional[int] = Field(None, ge=10, le=5000)
    max_attendees: Optional[int] = Field(None, ge=1)
    registration_required: Optional[bool] = None
    registration_deadline: Optional[datetime] = None
    banner_url: Optional[str] = None
    media_urls: Optional[List[str]] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# =============================================================================
# Event Response Schemas
# =============================================================================

class EventResponse(EventBase):
    """Schema for event response."""
    id: UUID
    unit_id: Optional[UUID] = None
    created_by_id: Optional[UUID] = None
    status: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class EventDetailResponse(EventResponse):
    """Detailed event response with relationships."""
    # Counts
    participants_count: int = 0
    attendance_count: int = 0
    tasks_count: int = 0
    feedback_count: int = 0
    
    # Relationships (loaded on demand)
    creator_name: Optional[str] = None
    unit_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Event List/Pagination Schemas
# =============================================================================

class EventListResponse(BaseModel):
    """Paginated event list response."""
    events: List[EventResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class EventSearchFilters(BaseModel):
    """Filters for event search."""
    search: Optional[str] = None
    type: Optional[List[str]] = None
    status: Optional[List[str]] = None
    unit_id: Optional[UUID] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    upcoming: Optional[bool] = None  # If true, only return future events


# =============================================================================
# Event Type Schemas
# =============================================================================

class EventTypeResponse(BaseModel):
    """Schema for event type response."""
    value: str
    label: str
    description: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Event Participant Schemas
# =============================================================================

class EventParticipantCreate(BaseModel):
    """Schema for adding a participant to an event."""
    member_id: UUID
    is_organizer: Optional[bool] = False
    notes: Optional[str] = None


class EventParticipantResponse(BaseModel):
    """Schema for participant response."""
    id: UUID
    event_id: UUID
    member_id: UUID
    status: str
    registered_at: datetime
    is_organizer: bool
    notes: Optional[str] = None
    
    # Member info
    member_name: Optional[str] = None
    member_phone: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class EventParticipantUpdate(BaseModel):
    """Schema for updating participant status."""
    status: Optional[str] = None
    is_organizer: Optional[bool] = None
    notes: Optional[str] = None


# =============================================================================
# Event Attendance Schemas
# =============================================================================

class EventAttendanceCreate(BaseModel):
    """Schema for creating attendance record."""
    member_id: UUID
    status: Optional[str] = AttendanceStatus.REGISTERED.value


class EventAttendanceResponse(BaseModel):
    """Schema for attendance response."""
    id: UUID
    event_id: UUID
    member_id: UUID
    status: str
    registered_at: datetime
    check_in_time: Optional[datetime] = None
    check_in_location: Optional[str] = None
    check_out_time: Optional[datetime] = None
    notes: Optional[str] = None
    
    # Member info
    member_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class CheckInRequest(BaseModel):
    """Schema for check-in request."""
    location: Optional[str] = None  # JSON string for GeoJSON Point


class CheckInResponse(BaseModel):
    """Schema for check-in response."""
    success: bool
    status: str
    check_in_time: datetime
    message: str


# =============================================================================
# Event Task Schemas
# =============================================================================

class EventTaskCreate(BaseModel):
    """Schema for creating an event task."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    assigned_to_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    due_date: Optional[datetime] = None
    priority: Optional[int] = Field(default=5, ge=1, le=10)
    metadata: Optional[Dict[str, Any]] = None


class EventTaskUpdate(BaseModel):
    """Schema for updating an event task."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    assigned_to_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    due_date: Optional[datetime] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EventTaskResponse(BaseModel):
    """Schema for task response."""
    id: UUID
    event_id: UUID
    title: str
    description: Optional[str] = None
    assigned_to_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    due_date: Optional[datetime] = None
    priority: int
    status: str
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Related info
    assigned_to_name: Optional[str] = None
    unit_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Event Budget Schemas
# =============================================================================

class EventBudgetCreate(BaseModel):
    """Schema for creating event budget."""
    estimated_cost: Optional[float] = 0
    actual_cost: Optional[float] = 0
    currency: Optional[str] = "INR"
    categories: Optional[Dict[str, float]] = None
    notes: Optional[str] = None


class EventBudgetUpdate(BaseModel):
    """Schema for updating event budget."""
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    currency: Optional[str] = None
    categories: Optional[Dict[str, float]] = None
    notes: Optional[str] = None


class EventBudgetResponse(BaseModel):
    """Schema for budget response."""
    id: UUID
    event_id: UUID
    estimated_cost: float
    actual_cost: float
    currency: str
    categories: Dict[str, float]
    approved_by_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Event Feedback Schemas
# =============================================================================

class EventFeedbackCreate(BaseModel):
    """Schema for creating event feedback."""
    rating: Optional[int] = Field(None, ge=1, le=5)
    feedback_type: Optional[str] = None
    comments: Optional[str] = None
    would_recommend: Optional[bool] = None
    highlights: Optional[List[str]] = None
    improvements: Optional[List[str]] = None
    is_anonymous: Optional[bool] = False


class EventFeedbackResponse(BaseModel):
    """Schema for feedback response."""
    id: UUID
    event_id: UUID
    member_id: UUID
    rating: Optional[int] = None
    feedback_type: Optional[str] = None
    comments: Optional[str] = None
    would_recommend: Optional[bool] = None
    highlights: List[str]
    improvements: List[str]
    is_anonymous: bool
    created_at: datetime
    
    # Member info (not included if anonymous)
    member_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Event Statistics Schemas
# =============================================================================

class EventStats(BaseModel):
    """Schema for event statistics."""
    total_events: int
    upcoming_events: int
    completed_events: int
    ongoing_events: int
    
    # By type
    by_type: Dict[str, int]
    
    # By status
    by_status: Dict[str, int]
    
    # Attendance stats
    total_participants: int
    avg_attendance: float
    total_registrations: int
    
    # Recent activity
    events_this_month: int
    events_this_week: int


class EventStatsResponse(BaseModel):
    """Schema for event statistics response."""
    stats: EventStats
    generated_at: datetime


class EventAnalyticsResponse(BaseModel):
    """Schema for single event analytics."""
    event_id: UUID
    registrations: int
    attended: int
    no_shows: int
    attendance_rate: float
    
    # By unit
    by_unit: List[Dict[str, Any]]
    
    # Check-in timeline
    check_in_timeline: List[Dict[str, Any]]
    
    # Feedback summary
    avg_rating: Optional[float] = None
    total_feedback: int


# =============================================================================
# Campaign Schemas
# =============================================================================

class CampaignCreate(BaseModel):
    """Schema for creating a campaign."""
    name: str = Field(..., min_length=1, max_length=255)
    name_ta: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    description_ta: Optional[str] = None
    unit_id: Optional[UUID] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    goals: Optional[Dict[str, Any]] = None
    budget: Optional[float] = None
    status: Optional[str] = CampaignStatus.PLANNING.value


class CampaignUpdate(BaseModel):
    """Schema for updating a campaign."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    name_ta: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    description_ta: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    goals: Optional[Dict[str, Any]] = None
    budget: Optional[float] = None
    status: Optional[str] = None


class CampaignResponse(BaseModel):
    """Schema for campaign response."""
    id: UUID
    name: str
    name_ta: Optional[str] = None
    description: Optional[str] = None
    unit_id: Optional[UUID] = None
    created_by_id: Optional[UUID] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    goals: Dict[str, Any]
    budget: Optional[float] = None
    status: str
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    tasks_count: int = 0
    completed_tasks: int = 0
    progress_percentage: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class CampaignTaskCreate(BaseModel):
    """Schema for creating campaign task."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    assigned_to_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    due_date: Optional[datetime] = None
    priority: Optional[int] = Field(default=5, ge=1, le=10)


class CampaignTaskUpdate(BaseModel):
    """Schema for updating campaign task."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    assigned_to_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    due_date: Optional[datetime] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    status: Optional[str] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    metrics: Optional[Dict[str, Any]] = None


class CampaignTaskResponse(BaseModel):
    """Schema for campaign task response."""
    id: UUID
    campaign_id: UUID
    title: str
    description: Optional[str] = None
    assigned_to_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    due_date: Optional[datetime] = None
    priority: int
    status: str
    completed_at: Optional[datetime] = None
    progress: int
    metrics: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    # Related info
    assigned_to_name: Optional[str] = None
    unit_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Upcoming Events Schemas
# =============================================================================

class UpcomingEventsResponse(BaseModel):
    """Schema for upcoming events response."""
    events: List[EventResponse]
    total: int
    from_date: datetime
    to_date: Optional[datetime] = None


# =============================================================================
# Common Response Schemas
# =============================================================================

class ApiResponse(BaseModel):
    """Generic API response."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
