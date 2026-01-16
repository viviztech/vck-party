"""
Communications Router
API routes for announcements, forums, posts, comments, and grievances.
"""

from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import (
    NotFoundError,
    AuthorizationError,
    ValidationError,
)
from src.core.security import get_current_user, get_optional_user
from src.auth.models import User
from src.members.models import Member
from src.members.crud import MemberCRUD

from src.communications.models import (
    Forum,
    Announcement,
    ForumPost,
    ForumComment,
    ForumGrievance,
)
