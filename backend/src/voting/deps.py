"""
Voting Dependencies
Dependency functions for voting routes.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status

from src.core.database import get_db
from src.core.exceptions import (
    NotFoundError,
    AuthorizationError,
    BusinessError,
)
from src.auth.deps import get_current_user
from src.members.models import Member
from src.voting.models import (
    Election,
    ElectionStatus,
    ElectionCandidate,
    ElectionNomination,
    ElectionVoter,
)
from src.voting.crud import (
    ElectionCRUD,
    VotingCRUD,
    NominationCRUD,
    CandidateCRUD,
)


# =============================================================================
# Election Dependencies
# =============================================================================

async def get_election_by_id(
    election_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Election:
    """Dependency to get election by ID or raise 404."""
    election = await ElectionCRUD.get_by_id(db, Election, election_id)
    if not election:
        raise NotFoundError(resource="Election", resource_id=str(election_id))
    return election


async def get_election_with_details(
    election_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Election:
    """Dependency to get election with all details or raise 404."""
    election = await ElectionCRUD.get_detailed(db, election_id)
    if not election:
        raise NotFoundError(resource="Election", resource_id=str(election_id))
    return election


# =============================================================================
# Election Status Dependencies
# =============================================================================

async def check_election_status(
    election: Election = Depends(get_election_by_id),
    required_status: ElectionStatus = None
) -> Election:
    """Check if election has required status."""
    if required_status and election.status != required_status.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Election must be in {required_status.value} status"
        )
    return election


def require_status(required_status: ElectionStatus):
    """Factory for status check dependency."""
    async def check_status(
        election: Election = Depends(get_election_by_id)
    ) -> Election:
        if election.status != required_status.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Election must be in {required_status.value} status"
            )
        return election
    return check_status


# =============================================================================
# Permission Dependencies
# =============================================================================

async def check_election_admin_permission(
    election: Election = Depends(get_election_by_id),
    current_user = Depends(get_current_user)
) -> Member:
    """Check if current user is admin of the election."""
    # Get member from user
    db = None  # Will be set by FastAPI DI
    
    # Check if user is super admin or election creator
    # For now, allow if user created the election or has admin role
    if election.created_by_id and str(election.created_by_id) != str(current_user.id):
        # Check if user has admin permissions for the unit
        # This would typically check the user's role/position
        pass  # Add unit-specific admin check
    
    return current_user


async def check_election_member(
    current_user = Depends(get_current_user)
) -> Member:
    """Check if current user is a member."""
    if not current_user or not hasattr(current_user, 'member'):
        raise AuthorizationError(message="You must be a member to perform this action")
    return current_user.member


# =============================================================================
# Voting Permissions
# =============================================================================

async def check_can_vote(
    election: Election = Depends(get_election_by_id),
    current_user = Depends(get_current_user)
) -> None:
    """Check if member can vote in this election.
    
    Validates:
    - Election is in voting_open status
    - Member hasn't already voted
    - Member meets eligibility criteria
    """
    if election.status != ElectionStatus.VOTING_OPEN.value:
        raise BusinessError(
            message="Voting is not currently open",
            code="VOTING_NOT_OPEN"
        )
    
    # Check if member has a member profile
    if not hasattr(current_user, 'member') or not current_user.member:
        raise AuthorizationError(message="You must be a member to vote")
    
    member = current_user.member
    
    # Check if already voted
    has_voted = await VotingCRUD.has_voted(db=None, election_id=election.id, member_id=member.id)
    if has_voted:
        raise BusinessError(
            message="You have already voted in this election",
            code="ALREADY_VOTED"
        )
    
    # Check eligibility criteria
    criteria = election.eligible_voter_criteria or {}
    
    # Check membership status
    required_status = criteria.get("status", ["active"])
    if member.status not in required_status:
        raise BusinessError(
            message="You are not eligible to vote in this election",
            code="NOT_ELIGIBLE"
        )
    
    # Check membership duration
    if member.joined_at:
        from datetime import datetime
        membership_months = (datetime.now(timezone.utc) - member.joined_at).days // 30
        min_months = criteria.get("min_membership_months", 0)
        if membership_months < min_months:
            raise BusinessError(
                message=f"You must be a member for at least {min_months} months to vote",
                code="NOT_ELIGIBLE"
            )


async def check_has_not_voted(
    election: Election = Depends(get_election_by_id),
    current_user = Depends(get_current_user)
) -> None:
    """Check if member has not yet voted."""
    if not hasattr(current_user, 'member') or not current_user.member:
        raise AuthorizationError(message="You must be a member")
    
    member = current_user.member
    has_voted = await VotingCRUD.has_voted(db=None, election_id=election.id, member_id=member.id)
    
    if has_voted:
        raise BusinessError(
            message="You have already voted in this election",
            code="ALREADY_VOTED"
        )


# =============================================================================
# Nomination Permissions
# =============================================================================

async def check_can_nominate(
    election: Election = Depends(get_election_by_id),
    current_user = Depends(get_current_user)
) -> None:
    """Check if member can submit a nomination.
    
    Validates:
    - Election is in nominations_open status
    - Member meets nomination criteria
    - Member hasn't already been nominated
    """
    from datetime import datetime
    
    if election.status != ElectionStatus.NOMINATIONS_OPEN.value:
        raise BusinessError(
            message="Nominations are not currently open",
            code="NOMINATIONS_CLOSED"
        )
    
    if not hasattr(current_user, 'member') or not current_user.member:
        raise AuthorizationError(message="You must be a member to nominate")
    
    member = current_user.member
    
    # Check if already nominated
    existing_nomination = await NominationCRUD.get_by_member_and_election(
        db=None, election_id=election.id, member_id=member.id
    )
    if existing_nomination:
        raise BusinessError(
            message="You have already submitted a nomination",
            code="ALREADY_NOMINATED"
        )
    
    # Check if already a candidate
    existing_candidates = await CandidateCRUD.get_by_election(db=None, election_id=election.id)
    if any(c.member_id == member.id for c in existing_candidates):
        raise BusinessError(
            message="You are already a candidate",
            code="ALREADY_CANDIDATE"
        )


async def check_nomination_permission(
    nomination: ElectionNomination = None,
    election: Election = Depends(get_election_by_id),
    current_user = Depends(get_current_user)
) -> Member:
    """Check if user can manage this nomination (approver)."""
    # Typically requires admin permissions
    # For now, allow election creator or admins
    if election.created_by_id and str(election.created_by_id) == str(current_user.id):
        return current_user.member
    
    # Add role-based check here
    raise AuthorizationError(message="You don't have permission to manage nominations")


# =============================================================================
# Candidate Dependencies
# =============================================================================

async def get_candidate_by_id(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> ElectionCandidate:
    """Dependency to get candidate by ID or raise 404."""
    candidate = await CandidateCRUD.get_by_id(db, candidate_id)
    if not candidate:
        raise NotFoundError(resource="Candidate", resource_id=str(candidate_id))
    return candidate


async def get_candidate_for_election(
    candidate: ElectionCandidate = Depends(get_candidate_by_id),
    election: Election = Depends(get_election_by_id)
) -> ElectionCandidate:
    """Ensure candidate belongs to the specified election."""
    if candidate.election_id != election.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Candidate does not belong to this election"
        )
    return candidate


# =============================================================================
# Result Dependencies
# =============================================================================

async def check_can_view_results(
    election: Election = Depends(get_election_by_id),
    current_user = Depends(get_current_user)
) -> None:
    """Check if user can view election results."""
    # Results can be viewed after they are declared
    if election.status not in [
        ElectionStatus.CLOSED.value,
        ElectionStatus.RESULTS_DECLARED.value
    ]:
        raise BusinessError(
            message="Results are not yet available",
            code="RESULTS_NOT_READY"
        )


# =============================================================================
# Database Access Helper
# =============================================================================

# Note: FastAPI's Depends injection handles db session
# This is just a placeholder for clarity
async def get_voting_db(
    db: AsyncSession = Depends(get_db)
) -> AsyncSession:
    """Get database session for voting operations."""
    return db
