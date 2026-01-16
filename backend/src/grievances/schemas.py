"""
Grievance Schemas
Pydantic schemas for grievance-related API requests and responses.
"""

from datetime import datetime, date
from typing import List, Optional, Any, Dict
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict

from src.grievances.models import (
    GrievanceStatus,
    GrievancePriority,
    GrievanceCategoryType,
    AssignmentType,
    EscalationLevel,
)


# =============================================================================
# Base Schemas
# =============================================================================

class GrievanceBase(BaseModel):
    """Base grievance schema with common fields."""
    subject: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=10)
    priority: Optional[str] = None
    district: Optional[str] = None
    constituency: Optional[str] = None
    ward: Optional[str] = None
    specific_location: Optional[str] = None


# =============================================================================
# Grievance Category Schemas
# =============================================================================

class GrievanceCategoryCreate(BaseModel):
    """Schema for creating a grievance category."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    category_type: Optional[str] = Field(default=GrievanceCategoryType.OTHER.value)
    response_sla_hours: Optional[int] = Field(default=24, ge=1)
    resolution_sla_hours: Optional[int] = Field(default=72, ge=1)
    default_assignee_role: Optional[str] = None
    escalation_enabled: Optional[bool] = True
    default_priority: Optional[str] = Field(default=GrievancePriority.MEDIUM.value)
    display_order: Optional[int] = 0


class GrievanceCategoryUpdate(BaseModel):
    """Schema for updating a grievance category."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    category_type: Optional[str] = None
    response_sla_hours: Optional[int] = Field(None, ge=1)
    resolution_sla_hours: Optional[int] = Field(None, ge=1)
    default_assignee_role: Optional[str] = None
    escalation_enabled: Optional[bool] = None
    default_priority: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class GrievanceCategoryResponse(BaseModel):
    """Schema for grievance category response."""
    id: UUID
    name: str
    description: Optional[str] = None
    category_type: str
    response_sla_hours: int
    resolution_sla_hours: int
    default_assignee_role: Optional[str] = None
    escalation_enabled: bool
    default_priority: str
    is_active: bool
    display_order: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class GrievanceCategoryListResponse(BaseModel):
    """Paginated category list response."""
    categories: List[GrievanceCategoryResponse]
    total: int


# =============================================================================
# Grievance Create/Update Schemas
# =============================================================================

class GrievanceCreate(GrievanceBase):
    """Schema for creating a new grievance."""
    category_id: Optional[UUID] = None
    contact_phone: Optional[str] = Field(None, min_length=10, max_length=15)
    contact_email: Optional[str] = None
    preferred_contact: Optional[str] = Field(None, max_length=20)
    related_member_id: Optional[UUID] = None
    related_event_id: Optional[UUID] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    is_anonymous: Optional[bool] = False
    is_confidential: Optional[bool] = False
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "subject": "Issue with membership registration",
                "description": "I submitted my membership application 2 months ago but haven't received any update.",
                "priority": "high",
                "category_id": "123e4567-e89b-12d3-a456-426614174000",
                "district": "Chennai",
                "constituency": "Anna Nagar",
                "contact_phone": "+919876543210"
            }
        }
    }


class GrievanceUpdate(BaseModel):
    """Schema for updating a grievance."""
    subject: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    category_id: Optional[UUID] = None
    priority: Optional[str] = None
    district: Optional[str] = None
    constituency: Optional[str] = None
    ward: Optional[str] = None
    specific_location: Optional[str] = None
    related_member_id: Optional[UUID] = None
    related_event_id: Optional[UUID] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    is_anonymous: Optional[bool] = None
    is_confidential: Optional[bool] = None
    internal_notes: Optional[str] = None
    status: Optional[str] = None


# =============================================================================
# Grievance Response Schemas
# =============================================================================

class GrievanceResponse(BaseModel):
    """Schema for grievance response."""
    id: UUID
    reference_number: str
    submitted_by_id: Optional[UUID] = None
    submitted_by_name: str
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    preferred_contact: Optional[str] = None
    category_id: Optional[UUID] = None
    priority: str
    subject: str
    description: str
    district: Optional[str] = None
    constituency: Optional[str] = None
    ward: Optional[str] = None
    specific_location: Optional[str] = None
    status: str
    current_assignee_id: Optional[UUID] = None
    current_assignee_name: Optional[str] = None
    related_member_id: Optional[UUID] = None
    related_event_id: Optional[UUID] = None
    attachments: List[Dict[str, Any]] = []
    is_anonymous: bool
    is_confidential: bool
    internal_notes: Optional[str] = None
    resolution_summary: Optional[str] = None
    submitter_rating: Optional[int] = None
    submitted_at: datetime
    acknowledged_at: Optional[datetime] = None
    investigation_started_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class GrievanceDetailResponse(GrievanceResponse):
    """Detailed grievance response with relationships."""
    category: Optional[GrievanceCategoryResponse] = None
    current_assignee: Optional["MemberBasicResponse"] = None
    sla: Optional["GrievanceSLAResponse"] = None
    
    model_config = ConfigDict(from_attributes=True)


class GrievanceListResponse(BaseModel):
    """Paginated grievance list response."""
    grievances: List[GrievanceResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# =============================================================================
# Grievance Search Filters
# =============================================================================

class GrievanceSearchFilters(BaseModel):
    """Filters for grievance search."""
    search: Optional[str] = None  # Search by subject, description, reference
    status: Optional[List[str]] = None
    priority: Optional[List[str]] = None
    category_id: Optional[UUID] = None
    category_type: Optional[str] = None
    district: Optional[str] = None
    constituency: Optional[str] = None
    submitted_by_id: Optional[UUID] = None
    assignee_id: Optional[UUID] = None
    is_anonymous: Optional[bool] = None
    is_confidential: Optional[bool] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    overdue: Optional[bool] = None


# =============================================================================
# Grievance Assignment Schemas
# =============================================================================

class GrievanceAssignmentCreate(BaseModel):
    """Schema for creating an assignment."""
    assignee_id: UUID
    assignment_type: Optional[str] = Field(default=AssignmentType.DIRECT.value)
    reason: Optional[str] = None
    notes: Optional[str] = None


class GrievanceAssignmentClaim(BaseModel):
    """Schema for claiming a grievance."""
    notes: Optional[str] = None


class GrievanceAssignmentResponse(BaseModel):
    """Schema for assignment response."""
    id: UUID
    grievance_id: UUID
    assignee_id: Optional[UUID] = None
    assignee_name: str
    assignment_type: str
    assigned_by_id: Optional[UUID] = None
    assigned_by_name: Optional[str] = None
    previous_assignee_id: Optional[UUID] = None
    previous_assignee_name: Optional[str] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    is_current: bool
    assigned_at: datetime
    unassigned_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class GrievanceAssignmentHistoryResponse(BaseModel):
    """Full assignment history for a grievance."""
    grievance_id: UUID
    current_assignment: Optional[GrievanceAssignmentResponse] = None
    history: List[GrievanceAssignmentResponse]


# =============================================================================
# Grievance Escalation Schemas
# =============================================================================

class GrievanceEscalationCreate(BaseModel):
    """Schema for creating an escalation."""
    escalation_level: str
    escalation_reason: Optional[str] = None
    escalated_to_id: UUID
    trigger_type: Optional[str] = "manual"
    trigger_notes: Optional[str] = None


class GrievanceEscalationResponse(BaseModel):
    """Schema for escalation response."""
    id: UUID
    grievance_id: UUID
    escalation_level: str
    escalation_reason: Optional[str] = None
    escalated_from_id: Optional[UUID] = None
    escalated_from_name: Optional[str] = None
    escalated_to_id: Optional[UUID] = None
    escalated_to_name: Optional[str] = None
    trigger_type: Optional[str] = None
    trigger_notes: Optional[str] = None
    is_active: bool
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    escalated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Grievance SLA Schemas
# =============================================================================

class GrievanceSLACreate(BaseModel):
    """Schema for creating SLA."""
    response_deadline_hours: int = Field(..., ge=1)
    resolution_deadline_hours: int = Field(..., ge=1)


class GrievanceSLAUpdate(BaseModel):
    """Schema for updating SLA."""
    response_deadline_hours: Optional[int] = Field(None, ge=1)
    resolution_deadline_hours: Optional[int] = Field(None, ge=1)
    is_on_hold: Optional[bool] = None


class GrievanceSLAResponse(BaseModel):
    """Schema for SLA response."""
    id: UUID
    grievance_id: UUID
    response_deadline_hours: int
    resolution_deadline_hours: int
    response_due_at: datetime
    resolution_due_at: datetime
    responded_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    response_sla_met: Optional[bool] = None
    resolution_sla_met: Optional[bool] = None
    response_breach_count: int
    resolution_breach_count: int
    is_on_hold: bool
    total_hold_duration_hours: float
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class GrievanceSLAStatus(BaseModel):
    """SLA status for a grievance."""
    is_overdue: bool
    response_status: str  # pending, met, breached
    resolution_status: str  # pending, met, breached
    response_time_remaining_hours: Optional[float] = None
    resolution_time_remaining_hours: Optional[float] = None


# =============================================================================
# Grievance Resolution Schemas
# =============================================================================

class GrievanceResolutionCreate(BaseModel):
    """Schema for creating a resolution."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    resolution_type: Optional[str] = None
    is_template: Optional[bool] = False
    applicable_category_id: Optional[UUID] = None
    action_taken: Optional[str] = None
    follow_up_required: Optional[bool] = False
    follow_up_date: Optional[datetime] = None
    handler_notes: Optional[str] = None


class GrievanceResolutionUpdate(BaseModel):
    """Schema for updating a resolution."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    resolution_type: Optional[str] = None
    is_template: Optional[bool] = None
    applicable_category_id: Optional[UUID] = None
    action_taken: Optional[str] = None
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[datetime] = None
    submitter_feedback: Optional[str] = None
    handler_notes: Optional[str] = None


class GrievanceResolutionResponse(BaseModel):
    """Schema for resolution response."""
    id: UUID
    grievance_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    resolution_type: Optional[str] = None
    is_template: bool
    applicable_category_id: Optional[UUID] = None
    resolved_by_id: Optional[UUID] = None
    resolved_by_name: Optional[str] = None
    action_taken: Optional[str] = None
    follow_up_required: bool
    follow_up_date: Optional[datetime] = None
    submitter_feedback: Optional[str] = None
    handler_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Grievance Statistics Schemas
# =============================================================================

class GrievanceStats(BaseModel):
    """Schema for grievance statistics."""
    total_grievances: int
    by_status: Dict[str, int]
    by_priority: Dict[str, int]
    by_category: Dict[str, int]
    by_district: Dict[str, int]
    
    # SLA metrics
    response_sla_compliance: float
    resolution_sla_compliance: float
    overdue_count: int
    
    # Trends
    submitted_today: int
    submitted_this_week: int
    submitted_this_month: int
    resolved_today: int
    resolved_this_week: int
    resolved_this_month: int
    
    # Average times (in hours)
    avg_response_time_hours: float
    avg_resolution_time_hours: float


class GrievanceStatsResponse(BaseModel):
    """Schema for statistics response."""
    stats: GrievanceStats
    generated_at: datetime


# =============================================================================
# Grievance Dashboard Schemas
# =============================================================================

class GrievanceDashboard(BaseModel):
    """Schema for dashboard data."""
    # Summary
    total_open: int
    total_pending: int
    total_resolved: int
    total_closed: int
    
    # By priority
    critical_count: int
    urgent_count: int
    high_count: int
    medium_count: int
    low_count: int
    
    # SLA alerts
    response_breached_today: int
    resolution_breached_today: int
    approaching_deadline: int
    
    # My metrics
    assigned_to_me: int
    my_pending: int
    my_resolved_today: int
    my_escalated: int
    
    # Recent
    recently_submitted: List[GrievanceResponse]
    recently_resolved: List[GrievanceResponse]
    overdue_grievances: List[GrievanceResponse]


class GrievanceDashboardResponse(BaseModel):
    """Schema for dashboard response."""
    dashboard: GrievanceDashboard
    generated_at: datetime


# =============================================================================
# Workflow Action Schemas
# =============================================================================

class GrievanceAcknowledge(BaseModel):
    """Schema for acknowledging a grievance."""
    notes: Optional[str] = None


class GrievanceInvestigate(BaseModel):
    """Schema for starting investigation."""
    notes: Optional[str] = None


class GrievanceResolve(BaseModel):
    """Schema for resolving a grievance."""
    resolution_summary: str = Field(..., min_length=10)
    resolution_template_id: Optional[UUID] = None
    action_taken: Optional[str] = None
    notes: Optional[str] = None
    follow_up_required: Optional[bool] = False
    follow_up_date: Optional[datetime] = None


class GrievanceClose(BaseModel):
    """Schema for closing a grievance."""
    notes: Optional[str] = None


class GrievanceReopen(BaseModel):
    """Schema for reopening a grievance."""
    reason: str = Field(..., min_length=10)
    notes: Optional[str] = None


class GrievanceReject(BaseModel):
    """Schema for rejecting a grievance."""
    reason: str = Field(..., min_length=10)
    notes: Optional[str] = None


class GrievanceSubmitFeedback(BaseModel):
    """Schema for submitting feedback."""
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None


# =============================================================================
# Helper Schemas
# =============================================================================

class MemberBasicResponse(BaseModel):
    """Basic member info for embedded responses."""
    id: UUID
    membership_number: str
    first_name: str
    last_name: Optional[str] = None
    phone: str
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Update forward references
# =============================================================================

GrievanceDetailResponse.model_rebuild()
