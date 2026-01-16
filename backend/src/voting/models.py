"""
Voting Models
SQLAlchemy models for elections, candidates, nominations, votes, and results.
"""

from datetime import datetime, timezone
from typing import List, TYPE_CHECKING
import uuid
import enum

from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, Integer, 
    ForeignKey, Table, Enum, JSON, Numeric
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from src.core.database import Base


# =============================================================================
# Enums
# =============================================================================

class ElectionStatus(str, enum.Enum):
    """Election status workflow."""
    DRAFT = "draft"
    NOMINATIONS_OPEN = "nominations_open"
    VOTING_OPEN = "voting_open"
    CLOSED = "closed"
    RESULTS_DECLARED = "results_declared"


class VotingMethod(str, enum.Enum):
    """Voting methods for elections."""
    FPTP = "fptp"  # First Past The Post
    RANKED_CHOICE = "ranked_choice"  # Ranked Choice / Instant Runoff
    APPROVAL = "approval"  # Approval Voting


class NominationStatus(str, enum.Enum):
    """Nomination status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


# =============================================================================
# Association Tables
# =============================================================================

# Election-Position association (many-to-many)
election_position_association = Table(
    "election_position_association",
    Base.metadata,
    Column("election_id", ForeignKey("elections.id", ondelete="CASCADE"), primary_key=True),
    Column("position_id", ForeignKey("election_positions.id", ondelete="CASCADE"), primary_key=True),
)


# =============================================================================
# Election Position Model
# =============================================================================

class ElectionPosition(Base):
    """
    Positions contested in an election.
    
    Example: President, Vice-President, Secretary, etc.
    """
    __tablename__ = "election_positions"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Position details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ta: Mapped[str] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Voting configuration
    voting_method: Mapped[str] = mapped_column(
        String(20),
        default=VotingMethod.FPTP.value,
        nullable=False
    )
    seats_available: Mapped[int] = mapped_column(Integer, default=1)
    
    # Eligibility criteria for candidates
    min_membership_months: Mapped[int] = mapped_column(Integer, default=0)
    max_candidates: Mapped[int] = mapped_column(Integer, default=100)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    elections: Mapped[List["Election"]] = relationship(
        "Election",
        secondary=election_position_association,
        back_populates="positions"
    )
    candidates: Mapped[List["ElectionCandidate"]] = relationship(
        "ElectionCandidate",
        back_populates="position",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<ElectionPosition(id={self.id}, name={self.name}, seats={self.seats_available})>"


# =============================================================================
# Election Model
# =============================================================================

class Election(Base):
    """
    Election model for party internal elections.
    
    Elections can be for various positions at different organizational levels.
    """
    __tablename__ = "elections"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Basic info
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Organization context
    unit_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organization_units.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Election timeline
    nominations_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    nominations_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    voting_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    voting_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Voter eligibility criteria (JSON)
    eligible_voter_criteria: Mapped[dict] = mapped_column(
        JSON, 
        default=dict
    )
    # Example: {
    #     "min_membership_months": 6,
    #     "status": ["active"],
    #     "positions": [],  # specific positions allowed to vote
    #     "units": []  # specific units allowed
    # }
    
    # Election configuration
    status: Mapped[str] = mapped_column(
        String(30),
        default=ElectionStatus.DRAFT.value,
        nullable=False,
        index=True
    )
    is_secret_voting: Mapped[bool] = mapped_column(Boolean, default=True)
    require_verified_voter_id: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Results configuration
    results_published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Audit fields
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
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
    positions: Mapped[List["ElectionPosition"]] = relationship(
        "ElectionPosition",
        secondary=election_position_association,
        back_populates="elections"
    )
    nominations: Mapped[List["ElectionNomination"]] = relationship(
        "ElectionNomination",
        back_populates="election",
        cascade="all, delete-orphan"
    )
    candidates: Mapped[List["ElectionCandidate"]] = relationship(
        "ElectionCandidate",
        back_populates="election",
        cascade="all, delete-orphan"
    )
    votes: Mapped[List["Vote"]] = relationship(
        "Vote",
        back_populates="election",
        cascade="all, delete-orphan"
    )
    vote_proofs: Mapped[List["VoteProof"]] = relationship(
        "VoteProof",
        back_populates="election",
        cascade="all, delete-orphan"
    )
    results: Mapped[List["ElectionResult"]] = relationship(
        "ElectionResult",
        back_populates="election",
        cascade="all, delete-orphan"
    )
    voters: Mapped[List["ElectionVoter"]] = relationship(
        "ElectionVoter",
        back_populates="election",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Election(id={self.id}, title={self.title}, status={self.status})>"


# =============================================================================
# Election Nomination Model
# =============================================================================

class ElectionNomination(Base):
    """
    Nomination applications for election candidates.
    
    Members apply to be candidates through nominations.
    """
    __tablename__ = "election_nominations"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    
    # References
    election_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("elections.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    position_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("election_positions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Nomination details
    manifesto: Mapped[str] = mapped_column(Text, nullable=True)
    photo_url: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20),
        default=NominationStatus.PENDING.value,
        nullable=False,
        index=True
    )
    
    # Approval tracking
    nominated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    approved_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True
    )
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=True)
    
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
    election: Mapped["Election"] = relationship("Election", back_populates="nominations")
    position: Mapped["ElectionPosition"] = relationship("ElectionPosition")
    member: Mapped["Member"] = relationship("Member", foreign_keys=[member_id])
    approved_by: Mapped["Member"] = relationship("Member", foreign_keys=[approved_by_id])
    
    def __repr__(self) -> str:
        return f"<ElectionNomination(id={self.id}, election_id={self.election_id}, member_id={self.member_id}, status={self.status})>"


# =============================================================================
# Election Candidate Model
# =============================================================================

class ElectionCandidate(Base):
    """
    Approved candidates for an election position.
    
    Created from approved nominations.
    """
    __tablename__ = "election_candidates"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    
    # References
    election_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("elections.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    position_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("election_positions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Candidate details
    manifesto: Mapped[str] = mapped_column(Text, nullable=True)
    photo_url: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Vote count (updated after results)
    votes_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    nominated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    approved_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True
    )
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    election: Mapped["Election"] = relationship("Election", back_populates="candidates")
    position: Mapped["ElectionPosition"] = relationship("ElectionPosition", back_populates="candidates")
    member: Mapped["Member"] = relationship("Member")
    approved_by: Mapped["Member"] = relationship("Member", foreign_keys=[approved_by_id])
    votes: Mapped[List["Vote"]] = relationship(
        "Vote",
        back_populates="candidate",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<ElectionCandidate(id={self.id}, election_id={self.election_id}, member_id={self.member_id})>"


# =============================================================================
# Vote Model
# =============================================================================

class Vote(Base):
    """
    Individual vote cast in an election.
    
    This stores the actual vote but uses cryptographic hashing to maintain
    voter secrecy while providing verifiability.
    """
    __tablename__ = "election_votes"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    
    # References
    election_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("elections.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("election_candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Vote verification (cryptographic proof)
    vote_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # Hash combines: election_id + voter_id + salt + timestamp
    
    # Ranked choice voting support (optional)
    rank: Mapped[int] = mapped_column(Integer, default=1)
    # For ranked choice: 1 = first choice, 2 = second choice, etc.
    
    # Timestamps
    voted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    election: Mapped["Election"] = relationship("Election", back_populates="votes")
    candidate: Mapped["ElectionCandidate"] = relationship("ElectionCandidate", back_populates="votes")
    proof: Mapped["VoteProof"] = relationship(
        "VoteProof",
        back_populates="vote",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Vote(id={self.id}, election_id={self.election_id}, candidate_id={self.candidate_id})>"


# =============================================================================
# Vote Proof Model (Blockchain/Cryptographic Verification)
# =============================================================================

class VoteProof(Base):
    """
    Cryptographic proof for vote integrity and verifiability.
    
    This can be extended to integrate with blockchain for immutable records.
    """
    __tablename__ = "vote_proofs"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    
    # References
    election_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("elections.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    vote_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("election_votes.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    
    # Proof data
    proof_type: Mapped[str] = mapped_column(String(50), default="hash")
    # Types: "hash", "merkle", "blockchain", "zkp"
    
    proof_data: Mapped[dict] = mapped_column(JSON, default=dict)
    # For hash: { "hash": "...", "salt": "..." }
    # For merkle: { "merkle_root": "...", "proof": [...] }
    # For blockchain: { "tx_hash": "...", "block_number": 123, "network": "..." }
    
    # Verification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    election: Mapped["Election"] = relationship("Election", back_populates="vote_proofs")
    vote: Mapped["Vote"] = relationship("Vote", back_populates="proof")
    
    def __repr__(self) -> str:
        return f"<VoteProof(id={self.id}, election_id={self.election_id}, proof_type={self.proof_type})>"


# =============================================================================
# Election Voter Registry
# =============================================================================

class ElectionVoter(Base):
    """
    Registry of eligible voters who have voted.
    
    Tracks who voted (for preventing double voting) but not what they voted.
    """
    __tablename__ = "election_voters"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    
    election_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("elections.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Vote receipt number (for voter verification)
    vote_receipt_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    # Timestamps
    voted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    election: Mapped["Election"] = relationship("Election", back_populates="voters")
    member: Mapped["Member"] = relationship("Member")
    
    def __repr__(self) -> str:
        return f"<ElectionVoter(id={self.id}, election_id={self.election_id}, member_id={self.member_id})>"


# =============================================================================
# Election Result Model
# =============================================================================

class ElectionResult(Base):
    """
    Aggregated election results by position.
    
    Stores the final results after calculation.
    """
    __tablename__ = "election_results"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    
    # References
    election_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("elections.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    position_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("election_positions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("election_candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Result data
    votes_received: Mapped[int] = mapped_column(Integer, default=0)
    percentage: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    rank: Mapped[int] = mapped_column(Integer, default=0)
    is_winner: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Detailed breakdown (for ranked choice)
    round_data: Mapped[dict] = mapped_column(JSON, default=dict)
    # Example: { "round_1": { "votes": 100, "percentage": 45.5 }, ... }
    
    # Timestamps
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    election: Mapped["Election"] = relationship("Election", back_populates="results")
    position: Mapped["ElectionPosition"] = relationship("ElectionPosition")
    candidate: Mapped["ElectionCandidate"] = relationship("ElectionCandidate")
    
    def __repr__(self) -> str:
        return f"<ElectionResult(id={self.id}, election_id={self.election_id}, candidate_id={self.candidate_id}, votes={self.votes_received})>"


# =============================================================================
# Import for relationships (avoid circular imports)
# =============================================================================

if TYPE_CHECKING:
    from src.auth.models import User, Member
    from src.hierarchy.models import OrganizationUnit
