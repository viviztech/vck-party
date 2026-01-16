"""
Member Models
SQLAlchemy models for members and related entities.
"""

from datetime import datetime, date, timezone
from typing import List, TYPE_CHECKING
import uuid
import enum

from sqlalchemy import (
    Column, String, Boolean, DateTime, Date, Text, Integer, 
    ForeignKey, Table, Enum, Float, JSON, ARRAY
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from src.core.database import Base


# =============================================================================
# Enums
# =============================================================================

class MembershipStatus(str, enum.Enum):
    """Member status enum."""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPELLED = "expelled"
    RESIGNED = "resigned"


class MembershipType(str, enum.Enum):
    """Type of membership."""
    ORDINARY = "ordinary"
    LIFE = "life"
    ASSOCIATE = "associate"
    HONORARY = "honorary"


class Gender(str, enum.Enum):
    """Gender options."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class DocumentType(str, enum.Enum):
    """Types of member documents."""
    AADHAR = "aadhar"
    VOTER_ID = "voter_id"
    PHOTO = "photo"
    ADDRESS_PROOF = "address_proof"
    OCCUPATION_PROOF = "occupation_proof"
    OTHER = "other"


class RelationshipType(str, enum.Enum):
    """Family relationship types."""
    SPOUSE = "spouse"
    PARENT = "parent"
    CHILD = "child"
    SIBLING = "sibling"
    OTHER = "other"


# =============================================================================
# Association Tables
# =============================================================================

# Member-Tags association
member_tags = Table(
    "member_tags",
    Base.metadata,
    Column("member_id", ForeignKey("members.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("member_tag_definitions.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
)

# Member-Skills association
member_skills = Table(
    "member_skills",
    Base.metadata,
    Column("member_id", ForeignKey("members.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", ForeignKey("member_skill_definitions.id", ondelete="CASCADE"), primary_key=True),
    Column("proficiency_level", Integer, default=1),  # 1-5 scale
    Column("years_experience", Integer, default=0),
    Column("created_at", DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
)


# =============================================================================
# Tag Definition Model
# =============================================================================

class MemberTagDefinition(Base):
    """Tag definition for categorizing members."""
    __tablename__ = "member_tag_definitions"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    color: Mapped[str] = mapped_column(String(7), default="#3498db")  # Hex color
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    members: Mapped[List["Member"]] = relationship(
        "Member",
        secondary=member_tags,
        back_populates="tags"
    )
    
    def __repr__(self) -> str:
        return f"<MemberTagDefinition(id={self.id}, name={self.name})>"


# =============================================================================
# Skill Definition Model
# =============================================================================

class MemberSkillDefinition(Base):
    """Skill definition for volunteer matching."""
    __tablename__ = "member_skill_definitions"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., 'communication', 'technical', 'leadership'
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    def __repr__(self) -> str:
        return f"<MemberSkillDefinition(id={self.id}, name={self.name})>"


# =============================================================================
# Member Model
# =============================================================================

class Member(Base):
    """
    Member model - core entity for party members.
    
    Extends User model with member-specific information.
    """
    __tablename__ = "members"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    membership_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    
    # Personal information
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=True)
    first_name_ta: Mapped[str] = mapped_column(String(100), nullable=True)
    last_name_ta: Mapped[str] = mapped_column(String(100), nullable=True)
    photo_url: Mapped[str] = mapped_column(Text, nullable=True)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=True)
    gender: Mapped[str] = mapped_column(String(20), nullable=True)
    
    # Contact
    phone: Mapped[str] = mapped_column(String(15), unique=True, index=True, nullable=False)
    alternate_phone: Mapped[str] = mapped_column(String(15), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Address
    address_line1: Mapped[str] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[str] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    district: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    constituency: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    ward: Mapped[str] = mapped_column(String(50), nullable=True, index=True)
    state: Mapped[str] = mapped_column(String(100), default="Tamil Nadu")
    pincode: Mapped[str] = mapped_column(String(10), nullable=True)
    
    # Political/Identity info
    voter_id: Mapped[str] = mapped_column(String(50), nullable=True, index=True)
    aadhar_hash: Mapped[str] = mapped_column(String(255), nullable=True)  # Hashed for privacy
    blood_group: Mapped[str] = mapped_column(String(5), nullable=True)
    
    # Demographics & Occupation
    education: Mapped[str] = mapped_column(String(100), nullable=True)
    occupation: Mapped[str] = mapped_column(String(100), nullable=True)
    organization: Mapped[str] = mapped_column(String(255), nullable=True)  # Current organization
    
    # Membership details
    status: Mapped[str] = mapped_column(
        String(20),
        default=MembershipStatus.PENDING.value,
        nullable=False,
        index=True
    )
    membership_type: Mapped[str] = mapped_column(
        String(20),
        default=MembershipType.ORDINARY.value,
        nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True
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
    user: Mapped["User"] = relationship("User", back_populates="member_profile", foreign_keys=[user_id])
    profile: Mapped["MemberProfile"] = relationship(
        "MemberProfile", 
        back_populates="member", 
        uselist=False,
        cascade="all, delete-orphan"
    )
    family_relations: Mapped[List["MemberFamily"]] = relationship(
        "MemberFamily",
        foreign_keys="MemberFamily.member_id",
        back_populates="member",
        cascade="all, delete-orphan"
    )
    related_as: Mapped[List["MemberFamily"]] = relationship(
        "MemberFamily",
        foreign_keys="MemberFamily.related_member_id",
        back_populates="related_member",
        cascade="all, delete-orphan"
    )
    documents: Mapped[List["MemberDocument"]] = relationship(
        "MemberDocument",
        back_populates="member",
        cascade="all, delete-orphan"
    )
    tags: Mapped[List["MemberTagDefinition"]] = relationship(
        "MemberTagDefinition",
        secondary=member_tags,
        back_populates="members"
    )
    skills: Mapped[List["MemberSkillDefinition"]] = relationship(
        "MemberSkillDefinition",
        secondary=member_skills,
        back_populates="members"
    )
    notes: Mapped[List["MemberNote"]] = relationship(
        "MemberNote",
        back_populates="member",
        cascade="all, delete-orphan"
    )
    history: Mapped[List["MembershipHistory"]] = relationship(
        "MembershipHistory",
        back_populates="member",
        cascade="all, delete-orphan"
    )
    
    # Self-referential for verification
    verified_members: Mapped[List["Member"]] = relationship(
        "Member",
        foreign_keys=[verified_by],
        back_populates="verified_by_member"
    )
    verified_by_member: Mapped["Member"] = relationship(
        "Member",
        remote_side=[id],
        foreign_keys=[verified_by],
        back_populates="verified_members"
    )
    
    def get_full_name(self) -> str:
        """Get full name of the member."""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name
    
    def get_full_name_ta(self) -> str:
        """Get full Tamil name of the member."""
        if self.last_name_ta:
            return f"{self.first_name_ta} {self.last_name_ta}"
        return self.first_name_ta or ""
    
    def __repr__(self) -> str:
        return f"<Member(id={self.id}, name={self.get_full_name()}, membership_number={self.membership_number})>"


# =============================================================================
# Member Profile Model (Extended Details)
# =============================================================================

class MemberProfile(Base):
    """
    Extended profile information for members.
    Contains detailed personal, demographic, and preference information.
    """
    __tablename__ = "member_profiles"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    
    # Demographics
    mother_tongue: Mapped[str] = mapped_column(String(50), nullable=True)
    religion: Mapped[str] = mapped_column(String(50), nullable=True)
    caste_category: Mapped[str] = mapped_column(String(50), nullable=True)
    nationality: Mapped[str] = mapped_column(String(50), default="Indian")
    
    # Social media
    facebook_url: Mapped[str] = mapped_column(Text, nullable=True)
    twitter_url: Mapped[str] = mapped_column(Text, nullable=True)
    instagram_url: Mapped[str] = mapped_column(Text, nullable=True)
    linkedin_url: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Emergency contact
    emergency_contact_name: Mapped[str] = mapped_column(String(200), nullable=True)
    emergency_contact_phone: Mapped[str] = mapped_column(String(15), nullable=True)
    emergency_contact_relationship: Mapped[str] = mapped_column(String(50), nullable=True)
    
    # Preferences
    communication_preference: Mapped[str] = mapped_column(String(20), default="both")  # sms, email, both
    language_preference: Mapped[str] = mapped_column(String(10), default="ta")  # ta, en, both
    interested_areas: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)  # e.g., ['events', 'social_media', 'fundraising']
    
    # Political background
    previous_party_affiliation: Mapped[str] = mapped_column(String(100), nullable=True)
    joined_from_which_party: Mapped[str] = mapped_column(String(100), nullable=True)
    political_influence_level: Mapped[str] = mapped_column(String(20), nullable=True)  # low, medium, high
    
    # Volunteer preferences
    volunteer_availability: Mapped[str] = mapped_column(String(20), nullable=True)  # weekdays, weekends, flexible
    preferred_roles: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)  # e.g., ['event_coordinator', 'social_media', 'door_to_door']
    max_travel_distance_km: Mapped[int] = mapped_column(Integer, nullable=True)
    
    # Additional info
    hobbies_interests: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    achievements_recognitions: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Consent
    photo_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    data_sharing_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    terms_accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    privacy_policy_accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
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
    member: Mapped["Member"] = relationship("Member", back_populates="profile")
    
    def __repr__(self) -> str:
        return f"<MemberProfile(member_id={self.member_id})>"


# =============================================================================
# Member Family Model
# =============================================================================

class MemberFamily(Base):
    """
    Family relationships for members.
    Supports hierarchical queries using PostgreSQL ltree for family trees.
    """
    __tablename__ = "member_families"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    related_member_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    relationship_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )
    
    # For hierarchical family tree (use String for compatibility, can be changed to ltree with extension)
    path: Mapped[str] = mapped_column(String(100), nullable=True)  # e.g., "1.5.3" for grandparent->parent->child
    
    # Metadata
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
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
    member: Mapped["Member"] = relationship(
        "Member",
        foreign_keys=[member_id],
        back_populates="family_relations"
    )
    related_member: Mapped["Member"] = relationship(
        "Member",
        foreign_keys=[related_member_id],
        back_populates="related_as"
    )
    
    def __repr__(self) -> str:
        return f"<MemberFamily(id={self.id}, member_id={self.member_id}, related_member_id={self.related_member_id}, type={self.relationship_type})>"


# =============================================================================
# Member Document Model
# =============================================================================

class MemberDocument(Base):
    """
    Documents for members (IDs, photos, proofs).
    """
    __tablename__ = "member_documents"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # File info
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_url: Mapped[str] = mapped_column(Text, nullable=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=True)  # in bytes
    
    # Verification status
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True
    )
    verification_notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Extra data
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
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
    member: Mapped["Member"] = relationship("Member", back_populates="documents")
    
    def __repr__(self) -> str:
        return f"<MemberDocument(id={self.id}, member_id={self.member_id}, type={self.document_type})>"


# =============================================================================
# Member Note Model
# =============================================================================

class MemberNote(Base):
    """
    Internal notes about members by staff.
    """
    __tablename__ = "member_notes"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    title: Mapped[str] = mapped_column(String(200), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=True)  # e.g., 'follow_up', 'feedback', 'issue'
    
    # Visibility
    is_private: Mapped[bool] = mapped_column(Boolean, default=True)  # Only visible to certain roles
    
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
    member: Mapped["Member"] = relationship("Member", back_populates="notes")
    author: Mapped["Member"] = relationship(
        "Member",
        foreign_keys=[author_id],
        remote_side=[id]
    )
    
    def __repr__(self) -> str:
        return f"<MemberNote(id={self.id}, member_id={self.member_id}, category={self.category})>"


# =============================================================================
# Membership History Model
# =============================================================================

class MembershipHistory(Base):
    """
    History of membership status changes and important events.
    """
    __tablename__ = "membership_history"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Event info
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., 'status_change', 'verification', 'transfer'
    action_description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Status tracking
    previous_status: Mapped[str] = mapped_column(String(20), nullable=True)
    new_status: Mapped[str] = mapped_column(String(20), nullable=True)
    
    # Actor info
    performed_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    performed_by_name: Mapped[str] = mapped_column(String(200), nullable=True)
    
    # Additional details
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    member: Mapped["Member"] = relationship("Member", back_populates="history")
    performer: Mapped["Member"] = relationship(
        "Member",
        foreign_keys=[performed_by],
        remote_side=[id]
    )
    
    def __repr__(self) -> str:
        return f"<MembershipHistory(id={self.id}, member_id={self.member_id}, action={self.action})>"


# =============================================================================
# Import for relationships (avoid circular imports)
# =============================================================================

if TYPE_CHECKING:
    from src.auth.models import User
