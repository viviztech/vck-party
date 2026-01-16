# API Routers
# This module organizes all API routers for the VCK platform.

from src.auth.router import router as auth_router
from src.members.router import router as members_router
from src.hierarchy.router import router as hierarchy_router
from src.events.router import router as events_router
from src.communications.router import router as communications_router
from src.voting.router import router as voting_router
from src.grievances.router import router as grievances_router
from src.donations.router import router as donations_router

__all__ = [
    "auth_router",
    "members_router",
    "hierarchy_router",
    "events_router",
    "communications_router",
    "voting_router",
    "grievances_router",
    "donations_router",
]
