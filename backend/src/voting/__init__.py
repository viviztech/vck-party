"""
Voting Module
eVoting system for internal party elections.
"""

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
from src.voting.schemas import *
from src.voting.router import router as voting_router

__all__ = [
    # Models
    "Election",
    "ElectionPosition",
    "ElectionCandidate",
    "ElectionNomination",
    "Vote",
    "VoteProof",
    "ElectionVoter",
    "ElectionResult",
    "ElectionStatus",
    "VotingMethod",
    "NominationStatus",
    # CRUD
    "ElectionCRUD",
    "ElectionPositionCRUD",
    "NominationCRUD",
    "CandidateCRUD",
    "VotingCRUD",
    "ResultCRUD",
    "VoterRegistryCRUD",
    "ElectionStatsCRUD",
    # Router
    "voting_router",
]
