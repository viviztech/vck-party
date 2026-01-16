"""
Voting API Routes
API routes for elections, nominations, voting, and results.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import (
    NotFoundError,
    AuthorizationError,
    BusinessError,
)
from src.auth.deps import get_current_user
from src.voting.models import (
    Election,
    ElectionStatus,
    ElectionPosition,
    ElectionCandidate,
    ElectionNomination,
)
from src.voting.crud import (
    ElectionCRUD,
    ElectionPositionCRUD,
    NominationCRUD,
    CandidateCRUD,
    VotingCRUD,
    ResultCRUD,
    VoterRegistryCRUD,
    ElectionStatsCRUD,
)
from src.voting.schemas import (
    ElectionCreate,
    ElectionUpdate,
    ElectionResponse,
    ElectionDetailResponse,
    ElectionListResponse,
    ElectionSearchFilters,
    ElectionPositionCreate,
    ElectionPositionResponse,
    ElectionNominationCreate,
    ElectionNominationResponse,
    ElectionNominationApprove,
    ElectionCandidateResponse,
    VoteCastRequest,
    VoteReceiptResponse,
    VoteVerificationRequest,
    VoteVerificationResponse,
    ElectionResultsResponse,
    CalculateResultsRequest,
    ElectionVoterResponse,
    ElectionVotersListResponse,
    ElectionStatsResponse,
    ElectionWorkflowResponse,
    ApiResponse,
)
from src.voting.deps import (
    get_election_by_id,
    check_election_admin_permission,
    check_can_vote,
    check_can_nominate,
    check_has_not_voted,
    check_can_view_results,
)


router = APIRouter(prefix="/voting", tags=["Voting"])


# =============================================================================
# Election Routes
# =============================================================================

@router.post("/elections", response_model=ElectionResponse, status_code=status.HTTP_201_CREATED)
async def create_election(
    election_data: ElectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new election."""
    election = await ElectionCRUD.create(
        db, election_data, created_by_id=getattr(current_user, 'member_id', None)
    )
    return election


@router.get("/elections", response_model=ElectionListResponse)
async def list_elections(
    search: Optional[str] = None,
    status_filter: Optional[List[str]] = Query(None),
    unit_id: Optional[UUID] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    upcoming: Optional[bool] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List elections with filters."""
    filters = ElectionSearchFilters(
        search=search,
        status=status_filter,
        unit_id=unit_id,
        from_date=from_date,
        to_date=to_date,
        upcoming=upcoming
    )
    elections, total = await ElectionCRUD.search(db, filters, page, limit)
    
    return ElectionListResponse(
        elections=[ElectionResponse.model_validate(e) for e in elections],
        total=total,
        page=page,
        limit=limit,
        total_pages=(total + limit - 1) // limit
    )


@router.get("/elections/{election_id}", response_model=ElectionDetailResponse)
async def get_election(
    election: Election = Depends(get_election_by_id),
    db: AsyncSession = Depends(get_db)
):
    """Get election details."""
    # Get counts
    positions_count = len(election.positions)
    candidates_count = await db.execute(
        __import__('sqlalchemy').select(__import__('sqlalchemy').func.count(ElectionCandidate.id))
        .where(ElectionCandidate.election_id == election.id)
    )
    nominations_count = await db.execute(
        __import__('sqlalchemy').select(__import__('sqlalchemy').func.count(ElectionNomination.id))
        .where(ElectionNomination.election_id == election.id)
    )
    total_votes = await VotingCRUD.get_vote_count(db, election.id)
    
    return ElectionDetailResponse(
        **ElectionResponse.model_validate(election).model_dump(),
        positions_count=positions_count,
        candidates_count=candidates_count.scalar() or 0,
        nominations_count=nominations_count.scalar() or 0,
        total_votes=total_votes,
    )


@router.put("/elections/{election_id}", response_model=ElectionResponse)
async def update_election(
    election_data: ElectionUpdate,
    election: Election = Depends(get_election_by_id),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update an election."""
    # Check permission
    await check_election_admin_permission(election, current_user)
    
    updated = await ElectionCRUD.update(db, election.id, election_data)
    return ElectionResponse.model_validate(updated)


@router.delete("/elections/{election_id}", response_model=ApiResponse)
async def delete_election(
    election: Election = Depends(get_election_by_id),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete (soft) an election."""
    await check_election_admin_permission(election, current_user)
    await ElectionCRUD.soft_delete(db, election.id)
    
    return ApiResponse(success=True, message="Election deleted successfully")


@router.post("/elections/{election_id}/publish", response_model=ElectionWorkflowResponse)
async def publish_election(
    election: Election = Depends(get_election_by_id),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Publish election (open for nominations)."""
    await check_election_admin_permission(election, current_user)
    updated = await ElectionCRUD.publish(db, election.id)
    
    return ElectionWorkflowResponse(
        success=True,
        message="Election published successfully. Nominations are now open.",
        election=ElectionResponse.model_validate(updated)
    )


@router.post("/elections/{election_id}/start", response_model=ElectionWorkflowResponse)
async def start_voting(
    election: Election = Depends(get_election_by_id),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Start voting phase."""
    await check_election_admin_permission(election, current_user)
    updated = await ElectionCRUD.start_voting(db, election.id)
    
    return ElectionWorkflowResponse(
        success=True,
        message="Voting has started.",
        election=ElectionResponse.model_validate(updated)
    )


@router.post("/elections/{election_id}/end", response_model=ElectionWorkflowResponse)
async def end_voting(
    election: Election = Depends(get_election_by_id),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """End voting phase."""
    await check_election_admin_permission(election, current_user)
    updated = await ElectionCRUD.end_voting(db, election.id)
    
    return ElectionWorkflowResponse(
        success=True,
        message="Voting has ended.",
        election=ElectionResponse.model_validate(updated)
    )


# =============================================================================
# Election Position Routes
# =============================================================================

@router.get("/elections/{election_id}/positions", response_model=List[ElectionPositionResponse])
async def get_election_positions(
    election: Election = Depends(get_election_by_id),
    db: AsyncSession = Depends(get_db)
):
    """Get positions for an election."""
    positions = await ElectionPositionCRUD.get_by_election(db, election.id)
    return [ElectionPositionResponse.model_validate(p) for p in positions]


@router.post("/elections/{election_id}/positions", response_model=ElectionPositionResponse)
async def create_election_position(
    position_data: ElectionPositionCreate,
    election: Election = Depends(get_election_by_id),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a position and add to election."""
    await check_election_admin_permission(election, current_user)
    
    # Create position
    position = await ElectionPositionCRUD.create(db, position_data)
    
    # Add to election
    await ElectionCRUD.add_position(db, election.id, position.id)
    
    return ElectionPositionResponse.model_validate(position)


# =============================================================================
# Nomination Routes
# =============================================================================

@router.get("/elections/{election_id}/nominations", response_model=List[ElectionNominationResponse])
async def get_nominations(
    election: Election = Depends(get_election_by_id),
    status_filter: Optional[str] = None,
    position_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get nominations for an election."""
    nominations = await NominationCRUD.get_by_election(db, election.id, status_filter, position_id)
    return [ElectionNominationResponse.model_validate(n) for n in nominations]


@router.post("/elections/{election_id}/nominate", response_model=ElectionNominationResponse)
async def submit_nomination(
    nomination_data: ElectionNominationCreate,
    election: Election = Depends(get_election_by_id),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Submit a nomination for an election."""
    await check_can_nominate(election, current_user)
    
    member_id = getattr(current_user, 'member_id', None)
    if not member_id:
        raise AuthorizationError(message="Member profile required")
    
    nomination = await NominationCRUD.create(db, election.id, member_id, nomination_data)
    return ElectionNominationResponse.model_validate(nomination)


@router.post("/elections/{election_id}/nominations/{nom_id}/approve", response_model=ElectionNominationResponse)
async def approve_nomination(
    approval: ElectionNominationApprove,
    election: Election = Depends(get_election_by_id),
    nom_id: UUID = None,  # Would be path parameter
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Approve a nomination."""
    await check_election_admin_permission(election, current_user)
    
    member_id = getattr(current_user, 'member_id', None)
    if not member_id:
        raise AuthorizationError(message="Member profile required")
    
    if approval.approved:
        nomination = await NominationCRUD.approve(db, nom_id, member_id)
    else:
        nomination = await NominationCRUD.reject(db, nom_id, approval.rejection_reason or "Rejected")
    
    return ElectionNominationResponse.model_validate(nomination)


@router.post("/elections/{election_id}/nominations/{nom_id}/reject", response_model=ElectionNominationResponse)
async def reject_nomination(
    rejection_reason: str,
    election: Election = Depends(get_election_by_id),
    nom_id: UUID = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Reject a nomination."""
    await check_election_admin_permission(election, current_user)
    
    nomination = await NominationCRUD.reject(db, nom_id, rejection_reason)
    return ElectionNominationResponse.model_validate(nomination)


# =============================================================================
# Candidate Routes
# =============================================================================

@router.get("/elections/{election_id}/candidates", response_model=List[ElectionCandidateResponse])
async def get_candidates(
    election: Election = Depends(get_election_by_id),
    position_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get candidates for an election."""
    candidates = await CandidateCRUD.get_by_election(db, election.id, position_id)
    return [ElectionCandidateResponse.model_validate(c) for c in candidates]


# =============================================================================
# Voting Routes
# =============================================================================

@router.get("/elections/{election_id}/cast", response_model=ApiResponse)
async def get_voting_page(
    election: Election = Depends(get_election_by_id),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get voting page data."""
    if election.status != ElectionStatus.VOTING_OPEN.value:
        raise BusinessError(message="Voting is not currently open", code="VOTING_NOT_OPEN")
    
    # Get candidates
    candidates = await CandidateCRUD.get_by_election(db, election.id)
    
    # Check if user has voted
    member_id = getattr(current_user, 'member_id', None)
    has_voted = False
    if member_id:
        has_voted = await VotingCRUD.has_voted(db, election.id, member_id)
    
    return ApiResponse(
        success=True,
        message="OK",
        data={
            "election": ElectionResponse.model_validate(election).model_dump(),
            "candidates": [ElectionCandidateResponse.model_validate(c).model_dump() for c in candidates],
            "has_voted": has_voted,
        }
    )


@router.post("/elections/{election_id}/cast", response_model=VoteReceiptResponse)
async def cast_vote(
    vote_data: VoteCastRequest,
    election: Election = Depends(get_election_by_id),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Cast a vote in an election."""
    # Verify member can vote
    await check_can_vote(election, current_user, db)
    await check_has_not_voted(election, current_user, db)
    
    member_id = getattr(current_user, 'member_id', None)
    if not member_id:
        raise AuthorizationError(message="Member profile required")
    
    vote, voter = await VotingCRUD.cast_vote(
        db, election.id, vote_data.candidate_id, member_id, vote_data.rank
    )
    
    return VoteReceiptResponse(
        success=True,
        vote_receipt_number=voter.vote_receipt_number,
        message="Your vote has been recorded successfully.",
        voted_at=voter.voted_at
    )


@router.get("/elections/{election_id}/verify", response_model=VoteVerificationResponse)
async def verify_vote(
    verification: VoteVerificationRequest,
    election: Election = Depends(get_election_by_id),
    db: AsyncSession = Depends(get_db)
):
    """Verify a vote using receipt number."""
    voter = await VotingCRUD.verify_vote(db, verification.vote_receipt_number)
    
    if not voter:
        return VoteVerificationResponse(
            is_valid=False,
            election_id=election.id,
            election_title=election.title,
            vote_receipt_number=verification.vote_receipt_number,
            message="Invalid vote receipt number"
        )
    
    return VoteVerificationResponse(
        is_valid=True,
        election_id=election.id,
        election_title=election.title,
        vote_receipt_number=voter.vote_receipt_number,
        voted_at=voter.voted_at,
        message="Vote verified successfully"
    )


# =============================================================================
# Results Routes
# =============================================================================

@router.get("/elections/{election_id}/results", response_model=ElectionResultsResponse)
async def get_election_results(
    election: Election = Depends(get_election_by_id),
    db: AsyncSession = Depends(get_db)
):
    """Get election results."""
    # Check if results are available
    if election.status not in [ElectionStatus.CLOSED.value, ElectionStatus.RESULTS_DECLARED.value]:
        # Allow viewing partial results for admin
        pass
    
    results = await ResultCRUD.get_results(db, election.id)
    
    return ElectionResultsResponse(**results)


@router.post("/elections/{election_id}/results/calculate", response_model=ElectionResultsResponse)
async def calculate_results(
    election: Election = Depends(get_election_by_id),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Calculate and publish election results."""
    await check_election_admin_permission(election, current_user)
    
    results = await ResultCRUD.calculate_results(db, election.id)
    return ElectionResultsResponse(**results)


# =============================================================================
# Voter Registry Routes
# =============================================================================

@router.get("/elections/{election_id}/voters", response_model=ElectionVotersListResponse)
async def get_voters(
    election: Election = Depends(get_election_by_id),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get list of voters who voted in an election."""
    voters = await VoterRegistryCRUD.get_by_election(db, election.id, skip, limit)
    total = await VoterRegistryCRUD.count_by_election(db, election.id)
    
    return ElectionVotersListResponse(
        voters=[ElectionVoterResponse.model_validate(v) for v in voters],
        total=total
    )


# =============================================================================
# Statistics Routes
# =============================================================================

@router.get("/elections/stats", response_model=ElectionStatsResponse)
async def get_election_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get overall election statistics."""
    stats = await ElectionStatsCRUD.get_stats(db)
    
    return ElectionStatsResponse(
        stats=stats,
        generated_at=datetime.now(timezone.utc)
    )
