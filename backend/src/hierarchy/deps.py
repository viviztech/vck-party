"""
Hierarchy Dependencies
Dependency injection functions for hierarchy module.
"""

from typing import Annotated
from uuid import UUID
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import NotFoundError
from src.core.deps import get_current_user_id

from src.hierarchy.models import District, Constituency, Ward, Booth


# Type aliases for dependencies
DBSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUserId = Annotated[str, Depends(get_current_user_id)]


async def get_district_by_id(
    district_id: UUID,
    db: DBSession,
) -> District:
    """Dependency to get a district by ID or raise 404."""
    district = await db.get(District, district_id)
    if not district:
        raise NotFoundError(resource="District", resource_id=str(district_id))
    return district


async def get_constituency_by_id(
    constituency_id: UUID,
    db: DBSession,
) -> Constituency:
    """Dependency to get a constituency by ID or raise 404."""
    constituency = await db.get(Constituency, constituency_id)
    if not constituency:
        raise NotFoundError(resource="Constituency", resource_id=str(constituency_id))
    return constituency


async def get_ward_by_id(
    ward_id: UUID,
    db: DBSession,
) -> Ward:
    """Dependency to get a ward by ID or raise 404."""
    ward = await db.get(Ward, ward_id)
    if not ward:
        raise NotFoundError(resource="Ward", resource_id=str(ward_id))
    return ward


async def get_booth_by_id(
    booth_id: UUID,
    db: DBSession,
) -> Booth:
    """Dependency to get a booth by ID or raise 404."""
    booth = await db.get(Booth, booth_id)
    if not booth:
        raise NotFoundError(resource="Booth", resource_id=str(booth_id))
    return booth
