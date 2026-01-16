"""
Hierarchy Models
SQLAlchemy models for the political party hierarchy (district → constituency → ward → booth).
Uses PostgreSQL ltree extension for hierarchical queries.
"""

from datetime import datetime, timezone
from typing import List, TYPE_CHECKING
import uuid
import enum

from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, Integer, 
    ForeignKey, Table, Enum, Float, JSON
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from src.core.database import Base


# =============================================================================
# Enums
# =============================================================================

class HierarchyLevel(str, enum.Enum):
    """Hierarchy level enum."""
    DISTRICT = "district"
    CONSTITUENCY = "constituency"
    WARD = "ward"
    BOOTH = "booth"


class ConstituencyType(str, enum.Enum):
    """Types of constituencies."""
    ASSEMBLY = "assembly"  # State assembly
    PARLIAMENT = "parliament"  # Lok Sabha (national parliament)
    BOTH = "both"  # Both types


# =============================================================================
# Association Tables
# =============================================================================

# Hierarchy relations - parent-child relationships
hierarchy_relations = Table(
    "hierarchy_relations",
    Base.metadata,
    Column("parent_id", UUID(as_uuid=True), ForeignKey("districts.id", ondelete="CASCADE"), primary_key=True),
    Column("child_id", UUID(as_uuid=True), primary_key=True),
    Column("relation_type", String(50), default="contains"),
    Column("created_at", DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
)


# =============================================================================
# District Model
# =============================================================================

class District(Base):
    """
    District model - top-level administrative division.
    
    Represents a district in the political hierarchy.
    """
    __tablename__ = "districts"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_ta: Mapped[str] = mapped_column(String(100), nullable=True)  # Tamil name
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)  # e.g., "CHN", "MDU"
    
    # Geographic information
    state: Mapped[str] = mapped_column(String(100), default="Tamil Nadu")
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    
    # Administrative
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
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
    constituencies: Mapped[List["Constituency"]] = relationship(
        "Constituency",
        back_populates="district",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<District(id={self.id}, name={self.name}, code={self.code})>"


# =============================================================================
# Constituency Model
# =============================================================================

class Constituency(Base):
    """
    Constituency model - assembly or parliament seats within a district.
    
    Represents an electoral constituency (assembly or parliament).
    """
    __tablename__ = "constituencies"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    district_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("districts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_ta: Mapped[str] = mapped_column(String(100), nullable=True)  # Tamil name
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)  # e.g., "CHN.NORTH"
    
    # Constituency type
    constituency_type: Mapped[str] = mapped_column(
        String(20),
        default=ConstituencyType.ASSEMBLY.value
    )
    
    # Electoral information
    electorate_count: Mapped[int] = mapped_column(Integer, default=0)  # Total voters
    polling_stations_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Geographic information
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    
    # Administrative
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
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
    district: Mapped["District"] = relationship("District", back_populates="constituencies")
    wards: Mapped[List["Ward"]] = relationship(
        "Ward",
        back_populates="constituency",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Constituency(id={self.id}, name={self.name}, code={self.code})>"


# =============================================================================
# Ward Model
# =============================================================================

class Ward(Base):
    """
    Ward model - municipal wards within a constituency.
    
    Represents a municipal ward/local administrative area within a constituency.
    """
    __tablename__ = "wards"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    constituency_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("constituencies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_ta: Mapped[str] = mapped_column(String(100), nullable=True)  # Tamil name
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)  # e.g., "CHN.NORTH.001"
    
    # Ward number for easy reference
    ward_number: Mapped[int] = mapped_column(Integer, nullable=True)
    
    # Geographic information
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    
    # Administrative
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
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
    constituency: Mapped["Constituency"] = relationship("Constituency", back_populates="wards")
    booths: Mapped[List["Booth"]] = relationship(
        "Booth",
        back_populates="ward",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Ward(id={self.id}, name={self.name}, code={self.code})>"


# =============================================================================
# Booth Model
# =============================================================================

class Booth(Base):
    """
    Booth model - polling stations within a ward.
    
    Represents a polling station/booth for voting purposes.
    This is the lowest level in the hierarchy.
    """
    __tablename__ = "booths"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    ward_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("wards.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ta: Mapped[str] = mapped_column(String(255), nullable=True)  # Tamil name
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)  # e.g., "CHN.NORTH.001.101"
    
    # Booth number (polling station number)
    booth_number: Mapped[int] = mapped_column(Integer, nullable=True)
    
    # Location details
    polling_location_name: Mapped[str] = mapped_column(String(255), nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Geographic coordinates
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    
    # Voter information
    male_voters: Mapped[int] = mapped_column(Integer, default=0)
    female_voters: Mapped[int] = mapped_column(Integer, default=0)
    other_voters: Mapped[int] = mapped_column(Integer, default=0)
    total_voters: Mapped[int] = mapped_column(Integer, default=0)
    
    # Administrative
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
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
    ward: Mapped["Ward"] = relationship("Ward", back_populates="booths")
    
    def __repr__(self) -> str:
        return f"<Booth(id={self.id}, name={self.name}, code={self.code})>"
    
    @property
    def voter_count(self) -> int:
        """Calculate total voters."""
        return self.male_voters + self.female_voters + self.other_voters


# =============================================================================
# ZipCodeMapping Model
# =============================================================================

class ZipCodeMapping(Base):
    """
    ZipCodeMapping model - maps postal codes to hierarchy elements.
    
    Provides lookup from pincode to the appropriate district/constituency/ward/booth.
    """
    __tablename__ = "zipcode_mapping"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Pincode
    pincode: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    
    # Mapped hierarchy elements
    district_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("districts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    constituency_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("constituencies.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    ward_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("wards.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    booth_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("booths.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Area names for reference
    area_name: Mapped[str] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Administrative
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
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
    
    def __repr__(self) -> str:
        return f"<ZipCodeMapping(id={self.id}, pincode={self.pincode})>"


# =============================================================================
# Import for relationships (avoid circular imports)
# =============================================================================

if TYPE_CHECKING:
    from src.auth.models import User


# =============================================================================
# OrganizationUnit Model
# =============================================================================

class OrganizationUnit(Base):
    """
    OrganizationUnit model for organizational units.
    
    Can be linked to different hierarchy levels (district, constituency, etc.)
    for organizational management and reporting.
    """
    __tablename__ = "organization_units"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Unit identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ta: Mapped[str] = mapped_column(String(255), nullable=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    unit_type: Mapped[str] = mapped_column(String(50), nullable=False)  # district, constituency, ward, booth, custom
    
    # Hierarchy linkage (optional - can link to any level)
    district_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("districts.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    constituency_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("constituencies.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    ward_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("wards.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    booth_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("booths.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Parent unit for nested organization structure
    parent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organization_units.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Contact information
    contact_person: Mapped[str] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str] = mapped_column(String(15), nullable=True)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
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
    district: Mapped["District"] = relationship("District", foreign_keys=[district_id])
    constituency: Mapped["Constituency"] = relationship("Constituency", foreign_keys=[constituency_id])
    ward: Mapped["Ward"] = relationship("Ward", foreign_keys=[ward_id])
    booth: Mapped["Booth"] = relationship("Booth", foreign_keys=[booth_id])
    parent: Mapped["OrganizationUnit"] = relationship("OrganizationUnit", remote_side=[id], back_populates="children")
    children: Mapped[List["OrganizationUnit"]] = relationship("OrganizationUnit", back_populates="parent")
    
    def __repr__(self) -> str:
        return f"<OrganizationUnit(id={self.id}, name={self.name}, type={self.unit_type})>"
