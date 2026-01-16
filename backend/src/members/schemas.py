"""
Member Schemas
Pydantic schemas for member-related API requests and responses.
"""

from datetime import datetime, date
from typing import List, Optional, Any, Dict
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict

from src.members.models import (
    MembershipStatus,
    MembershipType,
    Gender,
    DocumentType,
    RelationshipType,
)


# =============================================================================
# Base Schemas
# =============================================================================

class MemberBase(BaseModel):
    """Base member schema with common fields."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    first_name_ta: Optional[str] = Field(None, max_length=100)
    last_name_ta: Optional[str] = Field(None, max_length=100)
    phone: str = Field(..., min_length=10, max_length=15)
    email: Optional[EmailStr] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None


# =============================================================================
# Member Create/Update Schemas
# =============================================================================

class MemberCreate(MemberBase):
    """Schema for creating a new member."""
    # Address
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    constituency: Optional[str] = Field(None, max_length=100)
    ward: Optional[str] = Field(None, max_length=50)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=10)
    
    # Political info
    voter_id: Optional[str] = Field(None, max_length=50)
    blood_group: Optional[str] = Field(None, max_length=5)
    education: Optional[str] = Field(None, max_length=100)
    occupation: Optional[str] = Field(None, max_length=100)
    
    # Membership
    membership_type: Optional[str] = Field(default="ordinary")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "first_name": "Karthik",
                "last_name": "Kumar",
                "first_name_ta": "கார்த்திக்",
                "last_name_ta": "குமார்",
                "phone": "+919876543210",
                "email": "karthik@example.com",
                "date_of_birth": "1990-05-15",
                "gender": "male",
                "address_line1": "123 Main Street",
                "city": "Chennai",
                "district": "Chennai",
                "pincode": "600001",
                "voter_id": "ABC1234567",
                "occupation": "Engineer"
            }
        }
    }


class MemberUpdate(BaseModel):
    """Schema for updating member information."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    first_name_ta: Optional[str] = Field(None, max_length=100)
    last_name_ta: Optional[str] = Field(None, max_length=100)
    photo_url: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    email: Optional[EmailStr] = None
    alternate_phone: Optional[str] = Field(None, min_length=10, max_length=15)
    
    # Address
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    constituency: Optional[str] = Field(None, max_length=100)
    ward: Optional[str] = Field(None, max_length=50)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=10)
    
    # Political info
    voter_id: Optional[str] = Field(None, max_length=50)
    blood_group: Optional[str] = Field(None, max_length=5)
    education: Optional[str] = Field(None, max_length=100)
    occupation: Optional[str] = Field(None, max_length=100)
    organization: Optional[str] = Field(None, max_length=255)
    
    # Status
    status: Optional[str] = None
    membership_type: Optional[str] = None


# =============================================================================
# Member Response Schemas
# =============================================================================

class MemberResponse(MemberBase):
    """Schema for member response."""
    id: UUID
    membership_number: str
    photo_url: Optional[str] = None
    alternate_phone: Optional[str] = None
    
    # Address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    constituency: Optional[str] = None
    ward: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    
    # Political info
    voter_id: Optional[str] = None
    blood_group: Optional[str] = None
    education: Optional[str] = None
    occupation: Optional[str] = None
    organization: Optional[str] = None
    
    # Status
    status: str
    membership_type: str
    joined_at: datetime
    verified_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class MemberDetailResponse(MemberResponse):
    """Detailed member response with relationships."""
    address_line2: Optional[str] = None
    user_id: Optional[UUID] = None
    photo_url: Optional[str] = None
    date_of_birth: Optional[date] = None
    
    # Tags and skills
    tags: List[str] = []
    skills: List[Dict[str, Any]] = []
    
    # Statistics
    engagement_score: Optional[int] = None
    badges_count: int = 0
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Member List/Pagination Schemas
# =============================================================================

class MemberListResponse(BaseModel):
    """Paginated member list response."""
    members: List[MemberResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class MemberSearchFilters(BaseModel):
    """Filters for member search."""
    search: Optional[str] = None  # Search by name, phone, email, voter_id
    status: Optional[List[str]] = None
    membership_type: Optional[List[str]] = None
    district: Optional[str] = None
    constituency: Optional[str] = None
    ward: Optional[str] = None
    tags: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    education: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None


# =============================================================================
# Member Profile Schemas
# =============================================================================

class MemberProfileBase(BaseModel):
    """Base profile schema."""
    mother_tongue: Optional[str] = None
    religion: Optional[str] = None
    caste_category: Optional[str] = None
    nationality: Optional[str] = None
    
    # Social media
    facebook_url: Optional[str] = None
    twitter_url: Optional[str] = None
    instagram_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    
    # Emergency contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    
    # Preferences
    communication_preference: Optional[str] = None
    language_preference: Optional[str] = None
    interested_areas: Optional[List[str]] = None
    
    # Political background
    previous_party_affiliation: Optional[str] = None
    joined_from_which_party: Optional[str] = None
    political_influence_level: Optional[str] = None
    
    # Volunteer preferences
    volunteer_availability: Optional[str] = None
    preferred_roles: Optional[List[str]] = None
    max_travel_distance_km: Optional[int] = None
    
    # Additional info
    hobbies_interests: Optional[List[str]] = None
    achievements_recognitions: Optional[str] = None


class MemberProfileCreate(MemberProfileBase):
    """Schema for creating member profile."""
    pass


class MemberProfileUpdate(MemberProfileBase):
    """Schema for updating member profile."""
    # Consent fields
    photo_consent: Optional[bool] = None
    data_sharing_consent: Optional[bool] = None


class MemberProfileResponse(MemberProfileBase):
    """Schema for member profile response."""
    id: UUID
    member_id: UUID
    
    # Consent
    photo_consent: bool
    data_sharing_consent: bool
    terms_accepted_at: Optional[datetime] = None
    privacy_policy_accepted_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Member Family Schemas
# =============================================================================

class MemberFamilyCreate(BaseModel):
    """Schema for adding family relationship."""
    related_member_id: UUID
    relationship_type: str
    notes: Optional[str] = None


class MemberFamilyUpdate(BaseModel):
    """Schema for updating family relationship."""
    relationship_type: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class MemberFamilyResponse(BaseModel):
    """Schema for family relationship response."""
    id: UUID
    member_id: UUID
    related_member_id: UUID
    relationship_type: str
    related_member: MemberResponse  # Basic info about related member
    notes: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class FamilyTreeNode(BaseModel):
    """Schema for family tree node."""
    member_id: UUID
    name: str
    relationship_type: str
    children: List["FamilyTreeNode"] = []
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Member Document Schemas
# =============================================================================

class MemberDocumentCreate(BaseModel):
    """Schema for creating/updating document."""
    document_type: str
    file_name: str
    file_path: str
    file_url: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None


class MemberDocumentResponse(BaseModel):
    """Schema for document response."""
    id: UUID
    member_id: UUID
    document_type: str
    file_name: str
    file_url: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    is_verified: bool
    verified_at: Optional[datetime] = None
    verified_by: Optional[UUID] = None
    verification_notes: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Member Tag Schemas
# =============================================================================

class MemberTagAdd(BaseModel):
    """Schema for adding tags to a member."""
    tag_ids: List[UUID]


class MemberTagResponse(BaseModel):
    """Schema for tag response."""
    id: UUID
    name: str
    description: Optional[str] = None
    color: str
    created_at: datetime


# =============================================================================
# Member Note Schemas
# =============================================================================

class MemberNoteCreate(BaseModel):
    """Schema for creating a note."""
    title: Optional[str] = Field(None, max_length=200)
    content: str
    category: Optional[str] = None
    is_private: Optional[bool] = True


class MemberNoteUpdate(BaseModel):
    """Schema for updating a note."""
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = None
    category: Optional[str] = None


class MemberNoteResponse(BaseModel):
    """Schema for note response."""
    id: UUID
    member_id: UUID
    author_id: Optional[UUID] = None
    author_name: Optional[str] = None
    title: Optional[str] = None
    content: str
    category: Optional[str] = None
    is_private: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Membership History Schemas
# =============================================================================

class MembershipHistoryResponse(BaseModel):
    """Schema for membership history response."""
    id: UUID
    member_id: UUID
    action: str
    action_description: Optional[str] = None
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    performed_by: Optional[UUID] = None
    performed_by_name: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Member Statistics Schemas
# =============================================================================

class MemberStats(BaseModel):
    """Schema for member statistics."""
    total_members: int
    active_members: int
    pending_members: int
    suspended_members: int
    expelled_members: int
    
    # Demographics
    by_status: Dict[str, int]
    by_membership_type: Dict[str, int]
    by_gender: Dict[str, int]
    by_district: Dict[str, int]
    by_occupation: Dict[str, int]
    
    # Trends
    new_this_month: int
    new_this_year: int
    growth_percentage_month: float
    growth_percentage_year: float


class MemberStatsResponse(BaseModel):
    """Schema for member statistics response."""
    stats: MemberStats
    generated_at: datetime


# =============================================================================
# Bulk Operations Schemas
# =============================================================================

class MemberBulkImport(BaseModel):
    """Schema for bulk import request."""
    members: List[MemberCreate]
    assign_default_tags: bool = True
    notify_new_members: bool = True


class MemberBulkImportResult(BaseModel):
    """Schema for bulk import result."""
    total: int
    successful: int
    failed: int
    errors: List[Dict[str, Any]] = []


class MemberExportRequest(BaseModel):
    """Schema for export request."""
    filters: Optional[MemberSearchFilters] = None
    fields: Optional[List[str]] = None  # Fields to include in export
    format: str = "csv"  # csv, excel, json


# =============================================================================
# Helper/Association Schemas
# =============================================================================

class MemberSkillCreate(BaseModel):
    """Schema for adding a skill to a member."""
    skill_id: UUID
    proficiency_level: int = Field(1, ge=1, le=5)
    years_experience: int = Field(0, ge=0)


class MemberSkillResponse(BaseModel):
    """Schema for skill response."""
    id: UUID
    name: str
    category: str
    proficiency_level: int
    years_experience: int
    
    model_config = ConfigDict(from_attributes=True)


class MemberUnitInfo(BaseModel):
    """Schema for member's unit membership info."""
    unit_id: UUID
    unit_name: str
    unit_type: str
    position: Optional[str] = None
    is_primary: bool


# =============================================================================
# Update forward references
# =============================================================================

FamilyTreeNode.model_rebuild()
