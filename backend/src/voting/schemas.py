"""
Voting Schemas
Pydantic schemas for election-related API requests and responses.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from src.voting.models import (
    ElectionStatus,
    VotingMethod,
    NominationStatus,
)


# =============================================================================
# Base Schemas
# =============================================================================

class ElectionBase(BaseModel):
    """Base election schema with common fields."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    voting_start: datetime
    voting_end: datetime
    eligible_voter_criteria: Optional[Dict[str, Any]] = None
    is_secret_voting: Optional[bool] = True
    require_verified_voter_id: Optional[bool] = False


# =============================================================================
# Election Position Schemas
# =============================================================================

class ElectionPositionCreate(BaseModel):
    """Schema for creating an election position."""
    name: str = Field(..., min_length=1, max_length=255)
    name_ta: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    voting_method: Optional[str] = Field(default=VotingMethod.FPTP.value)
    seats_available: Optional[int] = Field(default=1, ge=1)
    min_membership_months: Optional[int] = Field(default=0, ge=0)
    max_candidates: Optional[int] = Field(default=100, ge=1)


class ElectionPositionUpdate(BaseModel):
    """Schema for updating an election position."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    name_ta: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    voting_method: Optional[str] = None
    seats_available: Optional[int] = Field(None, ge=1)
    min_membership_months: Optional[int] = Field(None, ge=0)
    max_candidates: Optional[int] = Field(None, ge=1)


class ElectionPositionResponse(BaseModel):
    """Schema for election position response."""
    id: UUID
    name: str
    name_ta: Optional[str] = None
    description: Optional[str] = None
    voting_method: str
    seats_available: int
    min_membership_months: int
    max_candidates: int
    created_at: datetime
    
    # Computed fields
    candidates_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Election Create/Update Schemas
# =============================================================================

class ElectionCreate(ElectionBase):
    """Schema for creating a new election."""
    unit_id: Optional[UUID] = None
    nominations_start: Optional[datetime] = None
    nominations_end: Optional[datetime] = None
    status: Optional[str] = Field(default=ElectionStatus.DRAFT.value)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "District President Election 2024",
                "description": "Election for the position of District President",
                "unit_id": "uuid",
                "nominations_start": "2024-04-01T00:00:00+05:30",
                "nominations_end": "2024-04-07T23:59:59+05:30",
                "voting_start": "2024-04-10T08:00:00+05:30",
                "voting_end": "2024-04-10T20:00:00+05:30",
                "eligible_voter_criteria": {
                    "min_membership_months": 6,
                    "status": ["active"]
                },
                "is_secret_voting": True
            }
        }
    }


class ElectionUpdate(BaseModel):
    """Schema for updating an election."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    nominations_start: Optional[datetime] = None
    nominations_end: Optional[datetime] = None
    voting_start: Optional[datetime] = None
    voting_end: Optional[datetime] = None
    eligible_voter_criteria: Optional[Dict[str, Any]] = None
    is_secret_voting: Optional[bool] = None
    require_verified_voter_id: Optional[bool] = None
    status: Optional[str] = None


# =============================================================================
# Election Response Schemas
# =============================================================================

class ElectionResponse(BaseModel):
    """Schema for election response."""
    id: UUID
    title: str
    description: Optional[str] = None
    unit_id: Optional[UUID] = None
    nominations_start: Optional[datetime] = None
    nominations_end: Optional[datetime] = None
    voting_start: datetime
    voting_end: datetime
    eligible_voter_criteria: Dict[str, Any]
    status: str
    is_secret_voting: bool
    require_verified_voter_id: bool
    results_published_at: Optional[datetime] = None
    created_by_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ElectionDetailResponse(ElectionResponse):
    """Detailed election response with relationships."""
    # Counts
    positions_count: int = 0
    candidates_count: int = 0
    nominations_count: int = 0
    total_votes: int = 0
    
    # Relationships (loaded on demand)
    unit_name: Optional[str] = None
    created_by_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Election List/Pagination Schemas
# =============================================================================

class ElectionListResponse(BaseModel):
    """Paginated election list response."""
    elections: List[ElectionResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class ElectionSearchFilters(BaseModel):
    """Filters for election search."""
    search: Optional[str] = None
    status: Optional[List[str]] = None
    unit_id: Optional[UUID] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    upcoming: Optional[bool] = None


# =============================================================================
# Election Workflow Schemas
# =============================================================================

class ElectionPublishRequest(BaseModel):
    """Request to publish an election (open for nominations)."""
    pass


class ElectionStartVotingRequest(BaseModel):
    """Request to start voting phase."""
    pass


class ElectionEndVotingRequest(BaseModel):
    """Request to end voting phase."""
    pass


class ElectionWorkflowResponse(BaseModel):
    """Response for workflow actions."""
    success: bool
    message: str
    election: ElectionResponse


# =============================================================================
# Nomination Schemas
# =============================================================================

class ElectionNominationCreate(BaseModel):
    """Schema for creating a nomination."""
    position_id: UUID
    manifesto: Optional[str] = None
    photo_url: Optional[str] = None


class ElectionNominationUpdate(BaseModel):
    """Schema for updating a nomination."""
    manifesto: Optional[str] = None
    photo_url: Optional[str] = None


class ElectionNominationApprove(BaseModel):
    """Schema for approving a nomination."""
    approved: bool
    rejection_reason: Optional[str] = None


class ElectionNominationResponse(BaseModel):
    """Schema for nomination response."""
    id: UUID
    election_id: UUID
    position_id: UUID
    member_id: UUID
    manifesto: Optional[str] = None
    photo_url: Optional[str] = None
    status: str
    nominated_at: datetime
    approved_by_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    
    # Member info
    member_name: Optional[str] = None
    member_photo_url: Optional[str] = None
    position_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Candidate Schemas
# =============================================================================

class ElectionCandidateResponse(BaseModel):
    """Schema for candidate response."""
    id: UUID
    election_id: UUID
    position_id: UUID
    member_id: UUID
    manifesto: Optional[str] = None
    photo_url: Optional[str] = None
    votes_count: int
    nominated_at: datetime
    approved_by_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    
    # Member info
    member_name: Optional[str] = None
    member_photo_url: Optional[str] = None
    position_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class ElectionCandidatesResponse(BaseModel):
    """Response for list of candidates."""
    candidates: List[ElectionCandidateResponse]
    total: int
    position_id: Optional[UUID] = None


# =============================================================================
# Voting Schemas
# =============================================================================

class VoteCastRequest(BaseModel):
    """Schema for casting a vote."""
    candidate_id: UUID
    # For ranked choice voting:
    rank: Optional[int] = Field(default=1, ge=1)


class VoteReceiptResponse(BaseModel):
    """Response after casting a vote."""
    success: bool
    vote_receipt_number: str
    message: str
    voted_at: datetime


class VoteVerificationRequest(BaseModel):
    """Request to verify a vote."""
    vote_receipt_number: str


class VoteVerificationResponse(BaseModel):
    """Response for vote verification."""
    is_valid: bool
    election_id: UUID
    election_title: str
    vote_receipt_number: str
    voted_at: Optional[datetime] = None
    message: str


class VotingStatusResponse(BaseModel):
    """Response showing voting status for current user."""
    can_vote: bool
    has_voted: bool
    election_id: UUID
    election_title: str
    positions: List[Dict[str, Any]]


# =============================================================================
# Election Results Schemas
# =============================================================================

class ElectionResultCandidate(BaseModel):
    """Individual candidate result."""
    candidate_id: UUID
    member_id: UUID
    member_name: str
    member_photo_url: Optional[str] = None
    votes_received: int
    percentage: float
    rank: int
    is_winner: bool


class ElectionResultPosition(BaseModel):
    """Results for a specific position."""
    position_id: UUID
    position_name: str
    voting_method: str
    seats_available: int
    total_votes: int
    candidates: List[ElectionResultCandidate]


class ElectionResultsResponse(BaseModel):
    """Complete election results response."""
    election_id: UUID
    election_title: str
    status: str
    total_voters: int
    total_votes_cast: int
    turnout_percentage: float
    results_published_at: Optional[datetime] = None
    positions: List[ElectionResultPosition]
    calculated_at: datetime


class CalculateResultsRequest(BaseModel):
    """Request to calculate election results."""
    pass


# =============================================================================
# Voter Registry Schemas
# =============================================================================

class ElectionVoterResponse(BaseModel):
    """Schema for voter registry entry."""
    id: UUID
    election_id: UUID
    member_id: UUID
    vote_receipt_number: str
    voted_at: datetime
    
    # Member info
    member_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class ElectionVotersListResponse(BaseModel):
    """Response for list of voters."""
    voters: List[ElectionVoterResponse]
    total: int


# =============================================================================
# Common Response Schemas
# =============================================================================

class ApiResponse(BaseModel):
    """Generic API response."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class ElectionStats(BaseModel):
    """Schema for election statistics."""
    total_elections: int
    active_elections: int
    upcoming_elections: int
    completed_elections: int
    
    # By status
    by_status: Dict[str, int]
    
    # Recent activity
    elections_this_month: int


class ElectionStatsResponse(BaseModel):
    """Schema for election statistics response."""
    stats: ElectionStats
    generated_at: datetime
