"""
Voting CRUD Operations
CRUD operations for elections, nominations, voting, and results.
"""

import hashlib
import secrets
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Type, TypeVar, Dict, Any
from uuid import UUID

from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import (
    NotFoundError,
    AlreadyExistsError,
    ValidationError,
    BusinessError,
)
from src.voting.models import (
    Election,
    ElectionPosition,
    ElectionCandidate,
    ElectionNomination,
    Vote,
    VoteProof,
    ElectionVoter,
    ElectionResult,
    ElectionStatus,
    VotingMethod,
    NominationStatus,
    election_position_association,
)
from src.voting.schemas import (
    ElectionCreate,
    ElectionUpdate,
    ElectionSearchFilters,
    ElectionPositionCreate,
    ElectionPositionUpdate,
    ElectionNominationCreate,
)


# =============================================================================
# Base CRUD Class
# =============================================================================

T = TypeVar("T")

class CRUDBase:
    """Base CRUD class with common operations."""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, model: Type[T], id: UUID) -> Optional[T]:
        """Get a record by ID."""
        result = await db.execute(
            select(model).where(model.id == id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all(
        db: AsyncSession,
        model: Type[T],
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        descending: bool = False
    ) -> List[T]:
        """Get all records with pagination."""
        query = select(model)
        
        if order_by:
            order_field = getattr(model, order_by, None)
            if order_field:
                if descending:
                    query = query.order_by(order_field.desc())
                else:
                    query = query.order_by(order_field.asc())
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def count(db: AsyncSession, model, **filters) -> int:
        """Count records with optional filters."""
        query = select(func.count(model.id))
        for field, value in filters.items():
            query = query.where(getattr(model, field) == value)
        result = await db.execute(query)
        return result.scalar() or 0


# =============================================================================
# Election Position CRUD
# =============================================================================

class ElectionPositionCRUD(CRUDBase):
    """CRUD operations for election positions."""
    
    @staticmethod
    async def create(db: AsyncSession, position_data: ElectionPositionCreate) -> ElectionPosition:
        """Create a new election position."""
        position = ElectionPosition(
            name=position_data.name,
            name_ta=position_data.name_ta,
            description=position_data.description,
            voting_method=position_data.voting_method or VotingMethod.FPTP.value,
            seats_available=position_data.seats_available,
            min_membership_months=position_data.min_membership_months,
            max_candidates=position_data.max_candidates,
        )
        
        db.add(position)
        await db.commit()
        await db.refresh(position)
        return position
    
    @staticmethod
    async def update(
        db: AsyncSession,
        position_id: UUID,
        position_data: ElectionPositionUpdate
    ) -> Optional[ElectionPosition]:
        """Update an election position."""
        position = await ElectionPositionCRUD.get_by_id(db, ElectionPosition, position_id)
        if not position:
            return None
        
        update_data = position_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(position, field, value)
        
        await db.commit()
        await db.refresh(position)
        return position
    
    @staticmethod
    async def get_by_election(
        db: AsyncSession,
        election_id: UUID
    ) -> List[ElectionPosition]:
        """Get all positions for an election."""
        result = await db.execute(
            select(ElectionPosition)
            .join(election_position_association)
            .where(election_position_association.c.election_id == election_id)
        )
        return list(result.scalars().all())


# =============================================================================
# Election CRUD
# =============================================================================

class ElectionCRUD(CRUDBase):
    """CRUD operations for elections."""
    
    @staticmethod
    async def create(db: AsyncSession, election_data: ElectionCreate, created_by_id: UUID = None) -> Election:
        """Create a new election."""
        election = Election(
            title=election_data.title,
            description=election_data.description,
            unit_id=election_data.unit_id,
            nominations_start=election_data.nominations_start,
            nominations_end=election_data.nominations_end,
            voting_start=election_data.voting_start,
            voting_end=election_data.voting_end,
            eligible_voter_criteria=election_data.eligible_voter_criteria or {},
            status=election_data.status or ElectionStatus.DRAFT.value,
            is_secret_voting=election_data.is_secret_voting,
            require_verified_voter_id=election_data.require_verified_voter_id,
            created_by_id=created_by_id,
        )
        
        db.add(election)
        await db.commit()
        await db.refresh(election)
        return election
    
    @staticmethod
    async def update(
        db: AsyncSession,
        election_id: UUID,
        election_data: ElectionUpdate
    ) -> Optional[Election]:
        """Update an election."""
        election = await ElectionCRUD.get_by_id(db, Election, election_id)
        if not election:
            return None
        
        update_data = election_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(election, field, value)
        
        await db.commit()
        await db.refresh(election)
        return election
    
    @staticmethod
    async def get_detailed(db: AsyncSession, election_id: UUID) -> Optional[Election]:
        """Get election with all relationships loaded."""
        result = await db.execute(
            select(Election)
            .where(Election.id == election_id)
            .options(
                selectinload(Election.positions),
                selectinload(Election.candidates),
                selectinload(Election.nominations),
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def search(
        db: AsyncSession,
        filters: ElectionSearchFilters,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Election], int]:
        """Search elections with filters."""
        query = select(Election)
        
        # Text search
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    Election.title.ilike(search_term),
                    Election.description.ilike(search_term),
                )
            )
        
        # Status filter
        if filters.status:
            query = query.where(Election.status.in_(filters.status))
        
        # Unit filter
        if filters.unit_id:
            query = query.where(Election.unit_id == filters.unit_id)
        
        # Date range filters
        if filters.from_date:
            query = query.where(Election.voting_start >= filters.from_date)
        if filters.to_date:
            query = query.where(Election.voting_start <= filters.to_date)
        
        # Upcoming elections
        if filters.upcoming:
            now = datetime.now(timezone.utc)
            query = query.where(Election.voting_start > now)
            query = query.where(Election.status != ElectionStatus.CLOSED.value)
        
        # Get total count
        count_query = select(func.count(Election.id)).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit).order_by(Election.voting_start.desc())
        
        result = await db.execute(query)
        elections = list(result.scalars().all())
        
        return elections, total
    
    @staticmethod
    async def soft_delete(db: AsyncSession, election_id: UUID) -> bool:
        """Soft delete an election."""
        election = await ElectionCRUD.get_by_id(db, Election, election_id)
        if not election:
            return False
        
        election.status = ElectionStatus.CLOSED.value
        await db.commit()
        return True
    
    @staticmethod
    async def add_position(db: AsyncSession, election_id: UUID, position_id: UUID) -> bool:
        """Add a position to an election."""
        # Check if already exists
        result = await db.execute(
            select(election_positions).where(
                and_(
                    election_positions.c.election_id == election_id,
                    election_positions.c.position_id == position_id
                )
            )
        )
        if result.first():
            raise AlreadyExistsError(resource="ElectionPosition")
        
        stmt = election_positions.insert().values(
            election_id=election_id,
            position_id=position_id,
        )
        await db.execute(stmt)
        await db.commit()
        return True
    
    @staticmethod
    async def publish(db: AsyncSession, election_id: UUID) -> Optional[Election]:
        """Publish election (open for nominations)."""
        election = await ElectionCRUD.get_by_id(db, Election, election_id)
        if not election:
            raise NotFoundError(resource="Election", resource_id=str(election_id))
        
        if election.status != ElectionStatus.DRAFT.value:
            raise BusinessError(
                message="Election can only be published from draft status",
                code="INVALID_STATUS"
            )
        
        election.status = ElectionStatus.NOMINATIONS_OPEN.value
        await db.commit()
        await db.refresh(election)
        return election
    
    @staticmethod
    async def start_voting(db: AsyncSession, election_id: UUID) -> Optional[Election]:
        """Start voting phase."""
        election = await ElectionCRUD.get_by_id(db, Election, election_id)
        if not election:
            raise NotFoundError(resource="Election", resource_id=str(election_id))
        
        if election.status != ElectionStatus.NOMINATIONS_OPEN.value:
            raise BusinessError(
                message="Election must be in nominations_open status to start voting",
                code="INVALID_STATUS"
            )
        
        # Check if there are approved candidates
        candidates_count = await db.execute(
            select(func.count(ElectionCandidate.id))
            .where(ElectionCandidate.election_id == election_id)
        )
        if (candidates_count.scalar() or 0) == 0:
            raise BusinessError(
                message="Cannot start voting without candidates",
                code="NO_CANDIDATES"
            )
        
        election.status = ElectionStatus.VOTING_OPEN.value
        await db.commit()
        await db.refresh(election)
        return election
    
    @staticmethod
    async def end_voting(db: AsyncSession, election_id: UUID) -> Optional[Election]:
        """End voting phase."""
        election = await ElectionCRUD.get_by_id(db, Election, election_id)
        if not election:
            raise NotFoundError(resource="Election", resource_id=str(election_id))
        
        if election.status != ElectionStatus.VOTING_OPEN.value:
            raise BusinessError(
                message="Election must be in voting_open status to end voting",
                code="INVALID_STATUS"
            )
        
        election.status = ElectionStatus.CLOSED.value
        await db.commit()
        await db.refresh(election)
        return election


# =============================================================================
# Nomination CRUD
# =============================================================================

class NominationCRUD(CRUDBase):
    """CRUD operations for nominations."""
    
    @staticmethod
    async def create(
        db: AsyncSession,
        election_id: UUID,
        member_id: UUID,
        nomination_data: ElectionNominationCreate
    ) -> ElectionNomination:
        """Submit a nomination."""
        # Check if election is accepting nominations
        election = await ElectionCRUD.get_by_id(db, Election, election_id)
        if not election:
            raise NotFoundError(resource="Election", resource_id=str(election_id))
        
        if election.status != ElectionStatus.NOMINATIONS_OPEN.value:
            raise BusinessError(
                message="Nominations are not currently open",
                code="NOMINATIONS_CLOSED"
            )
        
        # Check if already nominated
        existing = await NominationCRUD.get_by_member_and_election(db, election_id, member_id)
        if existing:
            raise AlreadyExistsError(resource="Nomination")
        
        # Check if already a candidate
        existing_candidate = await db.execute(
            select(ElectionCandidate).where(
                and_(
                    ElectionCandidate.election_id == election_id,
                    ElectionCandidate.member_id == member_id
                )
            )
        )
        if existing_candidate.scalar_one_or_none():
            raise AlreadyExistsError(resource="ElectionCandidate")
        
        nomination = ElectionNomination(
            election_id=election_id,
            position_id=nomination_data.position_id,
            member_id=member_id,
            manifesto=nomination_data.manifesto,
            photo_url=nomination_data.photo_url,
            status=NominationStatus.PENDING.value,
        )
        
        db.add(nomination)
        await db.commit()
        await db.refresh(nomination)
        return nomination
    
    @staticmethod
    async def get_by_member_and_election(
        db: AsyncSession,
        election_id: UUID,
        member_id: UUID
    ) -> Optional[ElectionNomination]:
        """Get nomination by member and election."""
        result = await db.execute(
            select(ElectionNomination).where(
                and_(
                    ElectionNomination.election_id == election_id,
                    ElectionNomination.member_id == member_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_election(
        db: AsyncSession,
        election_id: UUID,
        status: str = None,
        position_id: UUID = None
    ) -> List[ElectionNomination]:
        """Get nominations for an election."""
        query = select(ElectionNomination).where(
            ElectionNomination.election_id == election_id
        )
        
        if status:
            query = query.where(ElectionNomination.status == status)
        if position_id:
            query = query.where(ElectionNomination.position_id == position_id)
        
        query = query.order_by(ElectionNomination.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def approve(
        db: AsyncSession,
        nomination_id: UUID,
        approved_by_id: UUID
    ) -> Optional[ElectionNomination]:
        """Approve a nomination and create candidate."""
        nomination = await NominationCRUD.get_by_id(db, ElectionNomination, nomination_id)
        if not nomination:
            raise NotFoundError(resource="Nomination", resource_id=str(nomination_id))
        
        if nomination.status != NominationStatus.PENDING.value:
            raise BusinessError(
                message="Nomination is not pending",
                code="INVALID_STATUS"
            )
        
        # Update nomination status
        nomination.status = NominationStatus.APPROVED.value
        nomination.approved_by_id = approved_by_id
        nomination.approved_at = datetime.now(timezone.utc)
        
        # Create candidate from nomination
        candidate = ElectionCandidate(
            election_id=nomination.election_id,
            position_id=nomination.position_id,
            member_id=nomination.member_id,
            manifesto=nomination.manifesto,
            photo_url=nomination.photo_url,
            approved_by_id=approved_by_id,
            approved_at=datetime.now(timezone.utc),
        )
        db.add(candidate)
        
        await db.commit()
        await db.refresh(nomination)
        return nomination
    
    @staticmethod
    async def reject(
        db: AsyncSession,
        nomination_id: UUID,
        rejection_reason: str
    ) -> Optional[ElectionNomination]:
        """Reject a nomination."""
        nomination = await NominationCRUD.get_by_id(db, ElectionNomination, nomination_id)
        if not nomination:
            raise NotFoundError(resource="Nomination", resource_id=str(nomination_id))
        
        if nomination.status != NominationStatus.PENDING.value:
            raise BusinessError(
                message="Nomination is not pending",
                code="INVALID_STATUS"
            )
        
        nomination.status = NominationStatus.REJECTED.value
        nomination.rejection_reason = rejection_reason
        
        await db.commit()
        await db.refresh(nomination)
        return nomination


# =============================================================================
# Candidate CRUD
# =============================================================================

class CandidateCRUD(CRUDBase):
    """CRUD operations for candidates."""
    
    @staticmethod
    async def get_by_election(
        db: AsyncSession,
        election_id: UUID,
        position_id: UUID = None
    ) -> List[ElectionCandidate]:
        """Get candidates for an election."""
        query = select(ElectionCandidate).where(
            ElectionCandidate.election_id == election_id
        )
        
        if position_id:
            query = query.where(ElectionCandidate.position_id == position_id)
        
        query = query.order_by(ElectionCandidate.votes_count.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_by_id(db: AsyncSession, candidate_id: UUID) -> Optional[ElectionCandidate]:
        """Get candidate by ID."""
        result = await db.execute(
            select(ElectionCandidate).where(ElectionCandidate.id == candidate_id)
        )
        return result.scalar_one_or_none()


# =============================================================================
# Voting Operations
# =============================================================================

class VotingCRUD:
    """Voting operations."""
    
    @staticmethod
    async def cast_vote(
        db: AsyncSession,
        election_id: UUID,
        candidate_id: UUID,
        member_id: UUID,
        rank: int = 1
    ) -> Tuple[Vote, ElectionVoter]:
        """Cast a vote."""
        # Check election status
        election = await ElectionCRUD.get_by_id(db, Election, election_id)
        if not election:
            raise NotFoundError(resource="Election", resource_id=str(election_id))
        
        if election.status != ElectionStatus.VOTING_OPEN.value:
            raise BusinessError(
                message="Voting is not currently open",
                code="VOTING_NOT_OPEN"
            )
        
        # Check if member has already voted
        existing_vote = await VotingCRUD.has_voted(db, election_id, member_id)
        if existing_vote:
            raise BusinessError(
                message="You have already voted in this election",
                code="ALREADY_VOTED"
            )
        
        # Verify candidate exists
        candidate = await CandidateCRUD.get_by_id(db, candidate_id)
        if not candidate:
            raise NotFoundError(resource="Candidate", resource_id=str(candidate_id))
        
        if candidate.election_id != election_id:
            raise ValidationError(message="Candidate does not belong to this election")
        
        # Generate vote hash for verification (maintains secrecy)
        salt = secrets.token_hex(16)
        vote_data = f"{election_id}:{member_id}:{candidate_id}:{datetime.now(timezone.utc).isoformat()}:{salt}"
        vote_hash = hashlib.sha256(vote_data.encode()).hexdigest()
        
        # Generate vote receipt number
        vote_receipt = f"VR{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{secrets.token_hex(4).upper()}"
        
        # Create vote
        vote = Vote(
            election_id=election_id,
            candidate_id=candidate_id,
            vote_hash=vote_hash,
            rank=rank,
        )
        db.add(vote)
        await db.flush()
        
        # Create vote proof
        vote_proof = VoteProof(
            election_id=election_id,
            vote_id=vote.id,
            proof_type="hash",
            proof_data={
                "hash": vote_hash,
                "salt": salt,
            },
            is_verified=True,
            verified_at=datetime.now(timezone.utc),
        )
        db.add(vote_proof)
        
        # Create voter registry entry
        voter = ElectionVoter(
            election_id=election_id,
            member_id=member_id,
            vote_receipt_number=vote_receipt,
        )
        db.add(voter)
        
        await db.commit()
        await db.refresh(vote)
        await db.refresh(voter)
        
        return vote, voter
    
    @staticmethod
    async def has_voted(db: AsyncSession, election_id: UUID, member_id: UUID) -> bool:
        """Check if member has voted in election."""
        result = await db.execute(
            select(ElectionVoter).where(
                and_(
                    ElectionVoter.election_id == election_id,
                    ElectionVoter.member_id == member_id
                )
            )
        )
        return result.scalar_one_or_none() is not None
    
    @staticmethod
    async def verify_vote(db: AsyncSession, vote_receipt_number: str) -> Optional[ElectionVoter]:
        """Verify a vote using receipt number."""
        result = await db.execute(
            select(ElectionVoter).where(
                ElectionVoter.vote_receipt_number == vote_receipt_number
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_vote_count(db: AsyncSession, election_id: UUID) -> int:
        """Get total vote count for election."""
        result = await db.execute(
            select(func.count(Vote.id)).where(Vote.election_id == election_id)
        )
        return result.scalar() or 0


# =============================================================================
# Result Calculation
# =============================================================================

class ResultCRUD:
    """Election result operations."""
    
    @staticmethod
    async def calculate_results(db: AsyncSession, election_id: UUID) -> Dict[str, Any]:
        """Calculate and store election results."""
        election = await ElectionCRUD.get_by_id(db, Election, election_id)
        if not election:
            raise NotFoundError(resource="Election", resource_id=str(election_id))
        
        if election.status != ElectionStatus.CLOSED.value:
            raise BusinessError(
                message="Results can only be calculated after voting is closed",
                code="VOTING_NOT_CLOSED"
            )
        
        # Delete existing results
        await db.execute(
            delete(ElectionResult).where(ElectionResult.election_id == election_id)
        )
        
        # Get all votes
        total_votes = await VotingCRUD.get_vote_count(db, election_id)
        
        # Get total eligible voters
        voters_count = await db.execute(
            select(func.count(ElectionVoter.id)).where(ElectionVoter.election_id == election_id)
        )
        total_voters = voters_count.scalar() or 0
        
        # Calculate results for each position
        positions = await ElectionPositionCRUD.get_by_election(db, election_id)
        
        for position in positions:
            candidates = await CandidateCRUD.get_by_election(db, election_id, position.id)
            
            # Count votes for each candidate
            vote_counts = {}
            for candidate in candidates:
                result = await db.execute(
                    select(func.count(Vote.id)).where(
                        and_(
                            Vote.candidate_id == candidate.id,
                            Vote.rank == 1  # First choice votes for FPTP
                        )
                    )
                )
                vote_counts[candidate.id] = result.scalar() or 0
            
            # Sort by votes
            sorted_candidates = sorted(
                vote_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Store results
            for rank, (candidate_id, votes) in enumerate(sorted_candidates, 1):
                percentage = round((votes / max(total_votes, 1)) * 100, 2)
                is_winner = rank <= position.seats_available
                
                result = ElectionResult(
                    election_id=election_id,
                    position_id=position.id,
                    candidate_id=candidate_id,
                    votes_received=votes,
                    percentage=percentage,
                    rank=rank,
                    is_winner=is_winner,
                )
                db.add(result)
                
                # Update candidate vote count
                candidate = next((c for c in candidates if c.id == candidate_id), None)
                if candidate:
                    candidate.votes_count = votes
        
        # Update election status
        election.status = ElectionStatus.RESULTS_DECLARED.value
        election.results_published_at = datetime.now(timezone.utc)
        
        await db.commit()
        
        # Return results
        return await ResultCRUD.get_results(db, election_id)
    
    @staticmethod
    async def get_results(db: AsyncSession, election_id: UUID) -> Dict[str, Any]:
        """Get election results."""
        election = await ElectionCRUD.get_by_id(db, Election, election_id)
        if not election:
            raise NotFoundError(resource="Election", resource_id=str(election_id))
        
        # Get voter count
        voters_count = await db.execute(
            select(func.count(ElectionVoter.id)).where(ElectionVoter.election_id == election_id)
        )
        total_voters = voters_count.scalar() or 0
        
        # Get vote count
        total_votes = await VotingCRUD.get_vote_count(db, election_id)
        
        turnout = round((total_votes / max(total_voters, 1)) * 100, 2)
        
        # Get positions with results
        positions = await ElectionPositionCRUD.get_by_election(db, election_id)
        results_data = []
        
        for position in positions:
            candidates = await CandidateCRUD.get_by_election(db, election_id, position.id)
            candidate_results = []
            
            for candidate in candidates:
                # Get result record
                result = await db.execute(
                    select(ElectionResult).where(
                        and_(
                            ElectionResult.election_id == election_id,
                            ElectionResult.position_id == position.id,
                            ElectionResult.candidate_id == candidate.id
                        )
                    )
                )
                result_data = result.scalar_one_or_none()
                
                candidate_results.append({
                    "candidate_id": candidate.id,
                    "member_id": candidate.member_id,
                    "member_name": None,
                    "votes_received": candidate.votes_count,
                    "percentage": float(result_data.percentage) if result_data else 0,
                    "rank": result_data.rank if result_data else 0,
                    "is_winner": result_data.is_winner if result_data else False,
                })
            
            candidate_results.sort(key=lambda x: x["rank"])
            
            results_data.append({
                "position_id": position.id,
                "position_name": position.name,
                "voting_method": position.voting_method,
                "seats_available": position.seats_available,
                "total_votes": total_votes,
                "candidates": candidate_results,
            })
        
        return {
            "election_id": election_id,
            "election_title": election.title,
            "status": election.status,
            "total_voters": total_voters,
            "total_votes_cast": total_votes,
            "turnout_percentage": turnout,
            "results_published_at": election.results_published_at,
            "positions": results_data,
            "calculated_at": datetime.now(timezone.utc),
        }
    
    @staticmethod
    async def get_by_position(
        db: AsyncSession,
        election_id: UUID,
        position_id: UUID
    ) -> List[ElectionResult]:
        """Get results for a specific position."""
        result = await db.execute(
            select(ElectionResult).where(
                and_(
                    ElectionResult.election_id == election_id,
                    ElectionResult.position_id == position_id
                )
            ).order_by(ElectionResult.rank.asc())
        )
        return list(result.scalars().all())


# =============================================================================
# Voter Registry CRUD
# =============================================================================

class VoterRegistryCRUD(CRUDBase):
    """Operations for voter registry."""
    
    @staticmethod
    async def get_by_election(
        db: AsyncSession,
        election_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ElectionVoter]:
        """Get all voters who voted in an election."""
        query = select(ElectionVoter).where(
            ElectionVoter.election_id == election_id
        ).order_by(ElectionVoter.voted_at.desc())
        
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def count_by_election(db: AsyncSession, election_id: UUID) -> int:
        """Count voters who voted in an election."""
        result = await db.execute(
            select(func.count(ElectionVoter.id)).where(
                ElectionVoter.election_id == election_id
            )
        )
        return result.scalar() or 0


# =============================================================================
# Election Statistics
# =============================================================================

class ElectionStatsCRUD:
    """Statistics operations for elections."""
    
    @staticmethod
    async def get_stats(db: AsyncSession) -> Dict[str, Any]:
        """Get overall election statistics."""
        now = datetime.now(timezone.utc)
        
        # Total elections
        total = await db.execute(select(func.count(Election.id)))
        total = total.scalar() or 0
        
        # By status
        status_counts = {}
        status_result = await db.execute(
            select(Election.status, func.count(Election.id))
            .group_by(Election.status)
        )
        for row in status_result:
            status_counts[row[0]] = row[1]
        
        # Upcoming elections
        upcoming = await db.execute(
            select(func.count(Election.id)).where(
                and_(
                    Election.voting_start > now,
                    Election.status != ElectionStatus.CLOSED.value
                )
            )
        )
        upcoming = upcoming.scalar() or 0
        
        # Active elections (voting open)
        active = await db.execute(
            select(func.count(Election.id)).where(
                Election.status == ElectionStatus.VOTING_OPEN.value
            )
        )
        active = active.scalar() or 0
        
        # Completed elections
        completed = status_counts.get(ElectionStatus.RESULTS_DECLARED.value, 0)
        
        # Elections this month
        first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month = await db.execute(
            select(func.count(Election.id)).where(
                Election.created_at >= first_of_month
            )
        )
        this_month = this_month.scalar() or 0
        
        return {
            "total_elections": total,
            "active_elections": active,
            "upcoming_elections": upcoming,
            "completed_elections": completed,
            "by_status": status_counts,
            "elections_this_month": this_month,
        }
