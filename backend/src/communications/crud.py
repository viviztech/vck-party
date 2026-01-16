"""
Communications CRUD Operations
CRUD operations for announcements, forums, posts, comments, and grievances.
"""

import math
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Type, TypeVar
from uuid import UUID, uuid4

from sqlalchemy import select, update, delete, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import (
    NotFoundError,
    AlreadyExistsError,
    AuthorizationError,
    ValidationError,
)
from src.core import redis
from src.communications.models import (
    Announcement,
    AnnouncementTarget,
    Forum,
    ForumPost,
    ForumComment,
    ForumReaction,
    ForumGrievance,
    GrievanceUpdate,
    GrievanceAttachment,
    CommunicationLog,
    AnnouncementScope,
    AnnouncementType,
    ForumVisibility,
    GrievanceStatus,
    GrievancePriority,
    CommunicationChannel,
    ReactionType,
)
from src.communications.schemas import (
    AnnouncementCreate,
    AnnouncementUpdate,
    ForumCreate,
    ForumUpdate,
    ForumPostCreate,
    ForumPostUpdate,
    ForumCommentCreate,
    ForumReactionCreate,
    GrievanceCreate,
    GrievanceUpdate as GrievanceUpdateSchema,
    GrievanceStatusUpdate,
    AnnouncementFilters,
    ForumFilters,
    ForumPostFilters,
    GrievanceFilters,
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
                    query = query.order_by(desc(order_field))
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
    
    @staticmethod
    async def delete(db: AsyncSession, model: Type[T], id: UUID) -> bool:
        """Delete a record by ID (hard delete)."""
        record = await CRUDBase.get_by_id(db, model, id)
        if record:
            await db.delete(record)
            await db.commit()
            return True
        return False


# =============================================================================
# Announcement CRUD
# =============================================================================

class AnnouncementCRUD(CRUDBase):
    """CRUD operations for announcements."""
    
    @staticmethod
    async def create(
        db: AsyncSession,
        announcement_data: AnnouncementCreate,
        created_by_id: UUID
    ) -> Announcement:
        """Create a new announcement."""
        announcement = Announcement(
            title=announcement_data.title,
            title_ta=announcement_data.title_ta,
            content=announcement_data.content,
            content_ta=announcement_data.content_ta,
            created_by_id=created_by_id,
            unit_id=announcement_data.unit_id,
            target_scope=announcement_data.target_scope,
            send_push=announcement_data.send_push,
            send_sms=announcement_data.send_sms,
            send_email=announcement_data.send_email,
            publish_at=announcement_data.publish_at or datetime.now(timezone.utc),
            expires_at=announcement_data.expires_at,
            image_url=announcement_data.image_url,
            attachment_urls=announcement_data.attachment_urls,
            is_pinned=announcement_data.is_pinned,
            announcement_type=announcement_data.announcement_type,
        )
        db.add(announcement)
        await db.flush()
        
        # Add targets if specified
        if announcement_data.target_units:
            for unit_id in announcement_data.target_units:
                target = AnnouncementTarget(
                    announcement_id=announcement.id,
                    unit_id=unit_id,
                    unit_type=announcement_data.target_scope,
                )
                db.add(target)
        
        await db.commit()
        await db.refresh(announcement)
        return announcement
    
    @staticmethod
    async def update(
        db: AsyncSession,
        announcement_id: UUID,
        announcement_data: AnnouncementUpdate
    ) -> Optional[Announcement]:
        """Update an announcement."""
        announcement = await AnnouncementCRUD.get_by_id(
            db, Announcement, announcement_id
        )
        if not announcement:
            return None
        
        # Prevent updates to sent announcements
        if announcement.is_sent:
            raise ValidationError(
                message="Cannot update a sent announcement",
                details={"announcement_id": str(announcement_id)}
            )
        
        update_data = announcement_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(announcement, field, value)
        
        await db.commit()
        await db.refresh(announcement)
        return announcement
    
    @staticmethod
    async def get_with_targets(
        db: AsyncSession,
        announcement_id: UUID
    ) -> Optional[Announcement]:
        """Get announcement with targets."""
        result = await db.execute(
            select(Announcement)
            .where(Announcement.id == announcement_id)
            .options(selectinload(Announcement.targets))
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_paginated(
        db: AsyncSession,
        filters: AnnouncementFilters,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Announcement], int]:
        """Get announcements with pagination and filters."""
        query = select(Announcement).options(
            selectinload(Announcement.targets)
        )
        
        # Apply filters
        if filters.unit_id:
            query = query.where(Announcement.unit_id == filters.unit_id)
        if filters.target_scope:
            query = query.where(Announcement.target_scope == filters.target_scope)
        if filters.announcement_type:
            query = query.where(
                Announcement.announcement_type == filters.announcement_type
            )
        if filters.is_pinned is not None:
            query = query.where(Announcement.is_pinned == filters.is_pinned)
        if filters.is_sent is not None:
            query = query.where(Announcement.is_sent == filters.is_sent)
        if filters.created_by_id:
            query = query.where(
                Announcement.created_by_id == filters.created_by_id
            )
        if filters.from_date:
            query = query.where(
                Announcement.created_at >= filters.from_date
            )
        if filters.to_date:
            query = query.where(
                Announcement.created_at <= filters.to_date
            )
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    Announcement.title.ilike(search_term),
                    Announcement.content.ilike(search_term)
                )
            )
        
        # Get total count
        count_query = select(func.count(Announcement.id)).select_from(
            query.subquery()
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit).order_by(
            desc(Announcement.is_pinned),
            desc(Announcement.publish_at)
        )
        
        result = await db.execute(query)
        announcements = list(result.scalars().all())
        
        return announcements, total
    
    @staticmethod
    async def send(
        db: AsyncSession,
        announcement_id: UUID
    ) -> Tuple[bool, str, int]:
        """Send an announcement to recipients."""
        announcement = await AnnouncementCRUD.get_with_targets(
            db, announcement_id
        )
        if not announcement:
            raise NotFoundError(resource="Announcement", resource_id=str(announcement_id))
        
        if announcement.is_sent:
            raise ValidationError(message="Announcement already sent")
        
        # TODO: Integrate with SMS, Email, Push notification services
        # For now, just log and return success
        
        # Update announcement status
        announcement.is_sent = True
        announcement.sent_at = datetime.now(timezone.utc)
        
        # Log communication
        log = CommunicationLog(
            announcement_id=announcement.id,
            channel=CommunicationChannel.IN_APP.value,
            status="sent",
            status_message="Announcement published",
            sent_at=datetime.now(timezone.utc),
        )
        db.add(log)
        
        await db.commit()
        
        # Invalidate cache
        await redis.cache_delete(f"announcement:{announcement_id}")
        
        return True, "Announcement sent successfully", 100  # Mock recipient count
    
    @staticmethod
    async def pin(db: AsyncSession, announcement_id: UUID) -> Optional[Announcement]:
        """Pin an announcement."""
        announcement = await AnnouncementCRUD.get_by_id(
            db, Announcement, announcement_id
        )
        if not announcement:
            raise NotFoundError(resource="Announcement", resource_id=str(announcement_id))
        
        announcement.is_pinned = True
        await db.commit()
        await db.refresh(announcement)
        return announcement
    
    @staticmethod
    async def unpin(db: AsyncSession, announcement_id: UUID) -> Optional[Announcement]:
        """Unpin an announcement."""
        announcement = await AnnouncementCRUD.get_by_id(
            db, Announcement, announcement_id
        )
        if not announcement:
            raise NotFoundError(resource="Announcement", resource_id=str(announcement_id))
        
        announcement.is_pinned = False
        await db.commit()
        await db.refresh(announcement)
        return announcement


# =============================================================================
# Forum CRUD
# =============================================================================

class ForumCRUD(CRUDBase):
    """CRUD operations for forums."""
    
    @staticmethod
    async def create(
        db: AsyncSession,
        forum_data: ForumCreate,
        created_by_id: UUID
    ) -> Forum:
        """Create a new forum."""
        forum = Forum(
            name=forum_data.name,
            name_ta=forum_data.name_ta,
            description=forum_data.description,
            description_ta=forum_data.description_ta,
            unit_id=forum_data.unit_id,
            created_by_id=created_by_id,
            visibility=forum_data.visibility,
            is_moderated=forum_data.is_moderated,
            allow_anonymous=forum_data.allow_anonymous,
            category=forum_data.category,
            tags=forum_data.tags,
            cover_image_url=forum_data.cover_image_url,
            icon_url=forum_data.icon_url,
        )
        db.add(forum)
        await db.commit()
        await db.refresh(forum)
        return forum
    
    @staticmethod
    async def update(
        db: AsyncSession,
        forum_id: UUID,
        forum_data: ForumUpdate
    ) -> Optional[Forum]:
        """Update a forum."""
        forum = await ForumCRUD.get_by_id(db, Forum, forum_id)
        if not forum:
            return None
        
        update_data = forum_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(forum, field, value)
        
        await db.commit()
        await db.refresh(forum)
        return forum
    
    @staticmethod
    async def get_with_posts(
        db: AsyncSession,
        forum_id: UUID
    ) -> Optional[Forum]:
        """Get forum with posts."""
        result = await db.execute(
            select(Forum)
            .where(Forum.id == forum_id)
            .options(
                selectinload(Forum.posts).options(
                    selectinload(ForumPost.author),
                    selectinload(ForumPost.reactions),
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_paginated(
        db: AsyncSession,
        filters: ForumFilters,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Forum], int]:
        """Get forums with pagination and filters."""
        query = select(Forum)
        
        # Apply filters
        if filters.unit_id:
            query = query.where(Forum.unit_id == filters.unit_id)
        if filters.visibility:
            query = query.where(Forum.visibility == filters.visibility)
        if filters.category:
            query = query.where(Forum.category == filters.category)
        if filters.is_locked is not None:
            query = query.where(Forum.is_locked == filters.is_locked)
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    Forum.name.ilike(search_term),
                    Forum.description.ilike(search_term)
                )
            )
        
        # Exclude deleted forums
        query = query.where(Forum.is_deleted == False)
        
        # Get total count
        count_query = select(func.count(Forum.id)).select_from(
            query.subquery()
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit).order_by(
            desc(Forum.is_pinned),
            desc(Forum.posts_count),
            Forum.name.asc()
        )
        
        result = await db.execute(query)
        forums = list(result.scalars().all())
        
        return forums, total
    
    @staticmethod
    async def lock(
        db: AsyncSession,
        forum_id: UUID,
        moderator_id: UUID
    ) -> Optional[Forum]:
        """Lock a forum."""
        forum = await ForumCRUD.get_by_id(db, Forum, forum_id)
        if not forum:
            raise NotFoundError(resource="Forum", resource_id=str(forum_id))
        
        forum.is_locked = True
        forum.locked_at = datetime.now(timezone.utc)
        forum.locked_by_id = moderator_id
        
        await db.commit()
        await db.refresh(forum)
        return forum
    
    @staticmethod
    async def unlock(db: AsyncSession, forum_id: UUID) -> Optional[Forum]:
        """Unlock a forum."""
        forum = await ForumCRUD.get_by_id(db, Forum, forum_id)
        if not forum:
            raise NotFoundError(resource="Forum", resource_id=str(forum_id))
        
        forum.is_locked = False
        forum.locked_at = None
        forum.locked_by_id = None
        
        await db.commit()
        await db.refresh(forum)
        return forum
    
    @staticmethod
    async def soft_delete(db: AsyncSession, forum_id: UUID) -> bool:
        """Soft delete a forum."""
        forum = await ForumCRUD.get_by_id(db, Forum, forum_id)
        if not forum:
            return False
        
        forum.is_deleted = True
        forum.deleted_at = datetime.now(timezone.utc)
        
        await db.commit()
        return True
    
    @staticmethod
    async def increment_posts_count(db: AsyncSession, forum_id: UUID, count: int = 1):
        """Increment forum posts count."""
        await db.execute(
            update(Forum)
            .where(Forum.id == forum_id)
            .values(posts_count=Forum.posts_count + count)
        )
        await db.commit()


# =============================================================================
# Forum Post CRUD
# =============================================================================

class ForumPostCRUD(CRUDBase):
    """CRUD operations for forum posts."""
    
    @staticmethod
    async def create(
        db: AsyncSession,
        post_data: ForumPostCreate,
        author_id: UUID
    ) -> ForumPost:
        """Create a new forum post."""
        post = ForumPost(
            forum_id=post_data.forum_id,
            title=post_data.title,
            content=post_data.content,
            content_ta=post_data.content_ta,
            author_id=author_id,
            is_anonymous=post_data.is_anonymous,
            parent_id=post_data.parent_id,
            image_urls=post_data.image_urls,
            attachment_urls=post_data.attachment_urls,
        )
        db.add(post)
        await db.flush()
        
        # Update forum posts count
        await ForumCRUD.increment_posts_count(db, post_data.forum_id)
        
        await db.commit()
        await db.refresh(post)
        return post
    
    @staticmethod
    async def update(
        db: AsyncSession,
        post_id: UUID,
        post_data: ForumPostUpdate,
        user_id: UUID
    ) -> Optional[ForumPost]:
        """Update a forum post."""
        post = await ForumPostCRUD.get_by_id(db, ForumPost, post_id)
        if not post:
            return None
        
        # Check ownership
        if post.author_id != user_id:
            raise AuthorizationError("You can only edit your own posts")
        
        # Check if not hidden/deleted
        if post.is_hidden or post.is_deleted:
            raise AuthorizationError("Cannot edit a hidden or deleted post")
        
        update_data = post_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(post, field, value)
        
        await db.commit()
        await db.refresh(post)
        return post
    
    @staticmethod
    async def get_with_details(
        db: AsyncSession,
        post_id: UUID
    ) -> Optional[ForumPost]:
        """Get post with author, reactions, and comments."""
        result = await db.execute(
            select(ForumPost)
            .where(ForumPost.id == post_id)
            .options(
                selectinload(ForumPost.author),
                selectinload(ForumPost.reactions),
                selectinload(ForumPost.comments).options(
                    selectinload(ForumComment.author),
                    selectinload(ForumComment.reactions),
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_paginated(
        db: AsyncSession,
        filters: ForumPostFilters,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[ForumPost], int]:
        """Get forum posts with pagination and filters."""
        query = select(ForumPost).options(
            selectinload(ForumPost.author)
        )
        
        # Apply filters
        if filters.forum_id:
            query = query.where(ForumPost.forum_id == filters.forum_id)
        if filters.author_id:
            query = query.where(ForumPost.author_id == filters.author_id)
        if filters.is_pinned is not None:
            query = query.where(ForumPost.is_pinned == filters.is_pinned)
        if filters.is_hidden is not None:
            query = query.where(ForumPost.is_hidden == filters.is_hidden)
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    ForumPost.title.ilike(search_term),
                    ForumPost.content.ilike(search_term)
                )
            )
        
        # Exclude hidden and deleted
        query = query.where(
            and_(
                ForumPost.is_hidden == False,
                ForumPost.is_deleted == False
            )
        )
        
        # Get total count
        count_query = select(func.count(ForumPost.id)).select_from(
            query.subquery()
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit).order_by(
            desc(ForumPost.is_pinned),
            desc(ForumPost.created_at)
        )
        
        result = await db.execute(query)
        posts = list(result.scalars().all())
        
        return posts, total
    
    @staticmethod
    async def increment_views(db: AsyncSession, post_id: UUID):
        """Increment post views count."""
        await db.execute(
            update(ForumPost)
            .where(ForumPost.id == post_id)
            .values(views_count=ForumPost.views_count + 1)
        )
        await db.commit()
    
    @staticmethod
    async def pin(db: AsyncSession, post_id: UUID) -> Optional[ForumPost]:
        """Pin a post."""
        post = await ForumPostCRUD.get_by_id(db, ForumPost, post_id)
        if not post:
            raise NotFoundError(resource="ForumPost", resource_id=str(post_id))
        
        post.is_pinned = True
        await db.commit()
        await db.refresh(post)
        return post
    
    @staticmethod
    async def unpin(db: AsyncSession, post_id: UUID) -> Optional[ForumPost]:
        """Unpin a post."""
        post = await ForumPostCRUD.get_by_id(db, ForumPost, post_id)
        if not post:
            raise NotFoundError(resource="ForumPost", resource_id=str(post_id))
        
        post.is_pinned = False
        await db.commit()
        await db.refresh(post)
        return post
    
    @staticmethod
    async def hide(
        db: AsyncSession,
        post_id: UUID,
        moderator_id: UUID,
        reason: str = None
    ) -> Optional[ForumPost]:
        """Hide a post (moderation)."""
        post = await ForumPostCRUD.get_by_id(db, ForumPost, post_id)
        if not post:
            raise NotFoundError(resource="ForumPost", resource_id=str(post_id))
        
        post.is_hidden = True
        post.hidden_at = datetime.now(timezone.utc)
        post.hidden_by_id = moderator_id
        post.hidden_reason = reason
        
        await db.commit()
        await db.refresh(post)
        return post
    
    @staticmethod
    async def unhide(db: AsyncSession, post_id: UUID) -> Optional[ForumPost]:
        """Unhide a post."""
        post = await ForumPostCRUD.get_by_id(db, ForumPost, post_id)
        if not post:
            raise NotFoundError(resource="ForumPost", resource_id=str(post_id))
        
        post.is_hidden = False
        post.hidden_at = None
        post.hidden_by_id = None
        post.hidden_reason = None
        
        await db.commit()
        await db.refresh(post)
        return post
    
    @staticmethod
    async def soft_delete(
        db: AsyncSession,
        post_id: UUID,
        user_id: UUID
    ) -> bool:
        """Soft delete a post."""
        post = await ForumPostCRUD.get_by_id(db, ForumPost, post_id)
        if not post:
            return False
        
        # Check ownership or moderator
        if post.author_id != user_id:
            raise AuthorizationError("You can only delete your own posts")
        
        post.is_deleted = True
        post.deleted_at = datetime.now(timezone.utc)
        post.deleted_by_id = user_id
        
        # Decrement forum posts count
        await ForumCRUD.increment_posts_count(db, post.forum_id, -1)
        
        await db.commit()
        return True


# =============================================================================
# Forum Comment CRUD
# =============================================================================

class ForumCommentCRUD(CRUDBase):
    """CRUD operations for forum comments."""
    
    @staticmethod
    async def create(
        db: AsyncSession,
        comment_data: ForumCommentCreate,
        author_id: UUID
    ) -> ForumComment:
        """Create a new comment."""
        comment = ForumComment(
            post_id=comment_data.post_id,
            parent_id=comment_data.parent_id,
            content=comment_data.content,
            author_id=author_id,
            is_anonymous=comment_data.is_anonymous,
            image_url=comment_data.image_url,
        )
        db.add(comment)
        await db.flush()
        
        # Update post comments count
        await db.execute(
            update(ForumPost)
            .where(ForumPost.id == comment_data.post_id)
            .values(comments_count=ForumPost.comments_count + 1)
        )
        
        await db.commit()
        await db.refresh(comment)
        return comment
    
    @staticmethod
    async def update(
        db: AsyncSession,
        comment_id: UUID,
        content: str,
        user_id: UUID
    ) -> Optional[ForumComment]:
        """Update a comment."""
        comment = await ForumCommentCRUD.get_by_id(db, ForumComment, comment_id)
        if not comment:
            return None
        
        if comment.author_id != user_id:
            raise AuthorizationError("You can only edit your own comments")
        
        if comment.is_deleted:
            raise AuthorizationError("Cannot edit a deleted comment")
        
        comment.content = content
        await db.commit()
        await db.refresh(comment)
        return comment
    
    @staticmethod
    async def get_paginated(
        db: AsyncSession,
        post_id: UUID,
        page: int = 1,
        limit: int = 50
    ) -> Tuple[List[ForumComment], int]:
        """Get comments for a post with pagination."""
        query = select(ForumComment).options(
            selectinload(ForumComment.author)
        ).where(
            and_(
                ForumComment.post_id == post_id,
                ForumComment.parent_id == None,  # Top-level comments only
                ForumComment.is_deleted == False
            )
        )
        
        # Get total count
        count_query = select(func.count(ForumComment.id)).select_from(
            query.subquery()
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit).order_by(
            ForumComment.created_at.asc()
        )
        
        result = await db.execute(query)
        comments = list(result.scalars().all())
        
        return comments, total
    
    @staticmethod
    async def get_replies(
        db: AsyncSession,
        parent_id: UUID
    ) -> List[ForumComment]:
        """Get replies to a comment."""
        result = await db.execute(
            select(ForumComment)
            .options(selectinload(ForumComment.author))
            .where(
                and_(
                    ForumComment.parent_id == parent_id,
                    ForumComment.is_deleted == False
                )
            )
            .order_by(ForumComment.created_at.asc())
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def soft_delete(
        db: AsyncSession,
        comment_id: UUID,
        user_id: UUID
    ) -> bool:
        """Soft delete a comment."""
        comment = await ForumCommentCRUD.get_by_id(db, ForumComment, comment_id)
        if not comment:
            return False
        
        if comment.author_id != user_id:
            raise AuthorizationError("You can only delete your own comments")
        
        comment.is_deleted = True
        comment.deleted_at = datetime.now(timezone.utc)
        
        # Update post comments count
        await db.execute(
            update(ForumPost)
            .where(ForumPost.id == comment.post_id)
            .values(comments_count=ForumPost.comments_count - 1)
        )
        
        await db.commit()
        return True


# =============================================================================
# Forum Reaction CRUD
# =============================================================================

class ForumReactionCRUD(CRUDBase):
    """CRUD operations for forum reactions."""
    
    @staticmethod
    async def add_reaction(
        db: AsyncSession,
        reaction_data: ForumReactionCreate,
        member_id: UUID
    ) -> ForumReaction:
        """Add or update a reaction."""
        # Check for existing reaction
        if reaction_data.post_id:
            result = await db.execute(
                select(ForumReaction)
                .where(
                    and_(
                        ForumReaction.post_id == reaction_data.post_id,
                        ForumReaction.member_id == member_id
                    )
                )
            )
        else:
            result = await db.execute(
                select(ForumReaction)
                .where(
                    and_(
                        ForumReaction.comment_id == reaction_data.comment_id,
                        ForumReaction.member_id == member_id
                    )
                )
            )
        
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing reaction
            existing.reaction_type = reaction_data.reaction_type
            await db.commit()
            await db.refresh(existing)
            return existing
        
        # Create new reaction
        reaction = ForumReaction(
            post_id=reaction_data.post_id,
            comment_id=reaction_data.comment_id,
            member_id=member_id,
            reaction_type=reaction_data.reaction_type,
        )
        db.add(reaction)
        await db.commit()
        await db.refresh(reaction)
        return reaction
    
    @staticmethod
    async def remove_reaction(
        db: AsyncSession,
        post_id: UUID = None,
        comment_id: UUID = None,
        member_id: UUID = None
    ) -> bool:
        """Remove a reaction."""
        if post_id:
            result = await db.execute(
                select(ForumReaction)
                .where(
                    and_(
                        ForumReaction.post_id == post_id,
                        ForumReaction.member_id == member_id
                    )
                )
            )
        else:
            result = await db.execute(
                select(ForumReaction)
                .where(
                    and_(
                        ForumReaction.comment_id == comment_id,
                        ForumReaction.member_id == member_id
                    )
                )
            )
        
        reaction = result.scalar_one_or_none()
        if reaction:
            await db.delete(reaction)
            await db.commit()
            return True
        return False
    
    @staticmethod
    async def get_reactions_count(
        db: AsyncSession,
        post_id: UUID = None,
        comment_id: UUID = None
    ) -> dict:
        """Get reaction counts for a post or comment."""
        if post_id:
            result = await db.execute(
                select(
                    ForumReaction.reaction_type,
                    func.count(ForumReaction.id)
                )
                .where(ForumReaction.post_id == post_id)
                .group_by(ForumReaction.reaction_type)
            )
        else:
            result = await db.execute(
                select(
                    ForumReaction.reaction_type,
                    func.count(ForumReaction.id)
                )
                .where(ForumReaction.comment_id == comment_id)
                .group_by(ForumReaction.reaction_type)
            )
        
        counts = {row[0]: row[1] for row in result.all()}
        return counts


# =============================================================================
# ForumGrievance CRUD
# =============================================================================

class ForumGrievanceCRUD(CRUDBase):
    """CRUD operations for grievances."""
    
    @staticmethod
    async def generate_ticket_number(db: AsyncSession) -> str:
        """Generate a unique ticket number."""
        import random
        import string
        
        while True:
            # Format: GRV2024000001
            number = ''.join(random.choices(string.digits, k=7))
            ticket_number = f"GRV{number}"
            
            # Check if exists
            result = await db.execute(
                select(ForumGrievance.id)
                .where(ForumGrievance.ticket_number == ticket_number)
            )
            if not result.scalar_one_or_none():
                return ticket_number
    
    @staticmethod
    async def create(
        db: AsyncSession,
        grievance_data: GrievanceCreate,
        member_id: UUID
    ) -> ForumGrievance:
        """Create a new grievance."""
        ticket_number = await ForumGrievanceCRUD.generate_ticket_number(db)
        
        grievance = ForumGrievance(
            ticket_number=ticket_number,
            member_id=member_id,
            unit_id=grievance_data.unit_id,
            category=grievance_data.category,
            subject=grievance_data.subject,
            description=grievance_data.description,
            priority=grievance_data.priority,
            attachments=grievance_data.attachments,
            status=GrievanceStatus.SUBMITTED.value,
        )
        db.add(grievance)
        await db.flush()
        
        # Create initial status update
        update_entry = GrievanceUpdate(
            grievance_id=grievance.id,
            status_to=GrievanceStatus.SUBMITTED.value,
            notes="ForumGrievance submitted",
        )
        db.add(update_entry)
        
        await db.commit()
        await db.refresh(grievance)
        return grievance
    
    @staticmethod
    async def update(
        db: AsyncSession,
        grievance_id: UUID,
        grievance_data: GrievanceUpdateSchema
    ) -> Optional[ForumGrievance]:
        """Update a grievance (not status)."""
        grievance = await ForumGrievanceCRUD.get_by_id(db, ForumGrievance, grievance_id)
        if not grievance:
            return None
        
        # Only allow updates if not resolved/closed
        if grievance.status in [
            GrievanceStatus.RESOLVED.value,
            GrievanceStatus.CLOSED.value,
            GrievanceStatus.REJECTED.value
        ]:
            raise ValidationError(
                message="Cannot update a resolved, closed, or rejected grievance"
            )
        
        update_data = grievance_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(grievance, field, value)
        
        await db.commit()
        await db.refresh(grievance)
        return grievance
    
    @staticmethod
    async def update_status(
        db: AsyncSession,
        grievance_id: UUID,
        status_update: GrievanceStatusUpdate,
        updated_by_id: UUID
    ) -> Optional[ForumGrievance]:
        """Update grievance status."""
        grievance = await ForumGrievanceCRUD.get_by_id(db, ForumGrievance, grievance_id)
        if not grievance:
            raise NotFoundError(resource="ForumGrievance", resource_id=str(grievance_id))
        
        old_status = grievance.status
        
        # Validate status transition
        valid_transitions = {
            GrievanceStatus.SUBMITTED.value: [
                GrievanceStatus.ACKNOWLEDGED.value,
                GrievanceStatus.REJECTED.value
            ],
            GrievanceStatus.ACKNOWLEDGED.value: [
                GrievanceStatus.IN_PROGRESS.value,
                GrievanceStatus.RESOLVED.value,
                GrievanceStatus.REJECTED.value
            ],
            GrievanceStatus.IN_PROGRESS.value: [
                GrievanceStatus.RESOLVED.value,
                GrievanceStatus.CLOSED.value,
                GrievanceStatus.SUBMITTED.value  # Reopen
            ],
            GrievanceStatus.RESOLVED.value: [
                GrievanceStatus.CLOSED.value,
                GrievanceStatus.SUBMITTED.value  # Reopen
            ],
            GrievanceStatus.CLOSED.value: [],
            GrievanceStatus.REJECTED.value: [],
        }
        
        if status_update.status not in valid_transitions.get(old_status, []):
            raise ValidationError(
                message=f"Cannot transition from {old_status} to {status_update.status}",
                details={
                    "from_status": old_status,
                    "to_status": status_update.status,
                    "valid_transitions": valid_transitions.get(old_status, [])
                }
            )
        
        # Update status
        grievance.status = status_update.status
        
        # Handle resolution
        if status_update.status == GrievanceStatus.RESOLVED.value:
            grievance.resolved_at = datetime.now(timezone.utc)
            grievance.resolution_summary = status_update.resolution_summary
            grievance.rating = status_update.rating
        
        # Handle feedback
        if status_update.notes and grievance.member_id:
            grievance.member_feedback = status_update.notes
        
        # Create status update record
        update_entry = GrievanceUpdate(
            grievance_id=grievance.id,
            status_from=old_status,
            status_to=status_update.status,
            notes=status_update.notes,
            internal_notes=status_update.internal_notes,
            updated_by_id=updated_by_id,
        )
        db.add(update_entry)
        
        await db.commit()
        await db.refresh(grievance)
        return grievance
    
    @staticmethod
    async def assign(
        db: AsyncSession,
        grievance_id: UUID,
        assigned_to_id: UUID,
        assigned_by_id: UUID
    ) -> Optional[ForumGrievance]:
        """Assign a grievance to a handler."""
        grievance = await ForumGrievanceCRUD.get_by_id(db, ForumGrievance, grievance_id)
        if not grievance:
            raise NotFoundError(resource="ForumGrievance", resource_id=str(grievance_id))
        
        grievance.assigned_to_id = assigned_to_id
        
        # Create update record
        update_entry = GrievanceUpdate(
            grievance_id=grievance.id,
            status_from=grievance.status,
            status_to=grievance.status,
            notes=f"Assigned to handler",
            internal_notes=f"Assigned by {assigned_by_id}",
            updated_by_id=assigned_by_id,
        )
        db.add(update_entry)
        
        await db.commit()
        await db.refresh(grievance)
        return grievance
    
    @staticmethod
    async def get_with_details(
        db: AsyncSession,
        grievance_id: UUID
    ) -> Optional[ForumGrievance]:
        """Get grievance with updates and attachments."""
        result = await db.execute(
            select(ForumGrievance)
            .where(ForumGrievance.id == grievance_id)
            .options(
                selectinload(ForumGrievance.updates),
                selectinload(ForumGrievance.attachments_rel)
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_paginated(
        db: AsyncSession,
        filters: GrievanceFilters,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[ForumGrievance], int]:
        """Get grievances with pagination and filters."""
        query = select(ForumGrievance)
        
        # Apply filters
        if filters.member_id:
            query = query.where(ForumGrievance.member_id == filters.member_id)
        if filters.unit_id:
            query = query.where(ForumGrievance.unit_id == filters.unit_id)
        if filters.status:
            query = query.where(ForumGrievance.status == filters.status)
        if filters.priority:
            query = query.where(ForumGrievance.priority == filters.priority)
        if filters.category:
            query = query.where(ForumGrievance.category == filters.category)
        if filters.assigned_to_id:
            query = query.where(
                ForumGrievance.assigned_to_id == filters.assigned_to_id
            )
        if filters.from_date:
            query = query.where(
                ForumGrievance.created_at >= filters.from_date
            )
        if filters.to_date:
            query = query.where(
                ForumGrievance.created_at <= filters.to_date
            )
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    ForumGrievance.ticket_number.ilike(search_term),
                    ForumGrievance.subject.ilike(search_term),
                    ForumGrievance.description.ilike(search_term)
                )
            )
        
        # Get total count
        count_query = select(func.count(ForumGrievance.id)).select_from(
            query.subquery()
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit).order_by(
            desc(ForumGrievance.created_at)
        )
        
        result = await db.execute(query)
        grievances = list(result.scalars().all())
        
        return grievances, total
    
    @staticmethod
    async def get_my_grievances(
        db: AsyncSession,
        member_id: UUID,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[ForumGrievance], int]:
        """Get grievances submitted by a member."""
        return await ForumGrievanceCRUD.get_paginated(
            db,
            GrievanceFilters(member_id=member_id),
            page,
            limit
        )
    
    @staticmethod
    async def get_assigned_grievances(
        db: AsyncSession,
        handler_id: UUID,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[ForumGrievance], int]:
        """Get grievances assigned to a handler."""
        return await ForumGrievanceCRUD.get_paginated(
            db,
            GrievanceFilters(assigned_to_id=handler_id),
            page,
            limit
        )
    
    @staticmethod
    async def get_statistics(db: AsyncSession) -> dict:
        """Get grievance statistics."""
        # Total by status
        status_result = await db.execute(
            select(
                ForumGrievance.status,
                func.count(ForumGrievance.id)
            )
            .group_by(ForumGrievance.status)
        )
        by_status = {row[0]: row[1] for row in status_result.all()}
        
        # Total by priority
        priority_result = await db.execute(
            select(
                ForumGrievance.priority,
                func.count(ForumGrievance.id)
            )
            .group_by(ForumGrievance.priority)
        )
        by_priority = {row[0]: row[1] for row in priority_result.all()}
        
        # Total by category
        category_result = await db.execute(
            select(
                ForumGrievance.category,
                func.count(ForumGrievance.id)
            )
            .group_by(ForumGrievance.category)
        )
        by_category = {row[0]: row[1] for row in category_result.all()}
        
        return {
            "total": sum(by_status.values()),
            "by_status": by_status,
            "by_priority": by_priority,
            "by_category": by_category,
            "pending": by_status.get(GrievanceStatus.SUBMITTED.value, 0) +
                       by_status.get(GrievanceStatus.ACKNOWLEDGED.value, 0) +
                       by_status.get(GrievanceStatus.IN_PROGRESS.value, 0),
            "resolved": by_status.get(GrievanceStatus.RESOLVED.value, 0),
        }


# =============================================================================
# Communication Log CRUD
# =============================================================================

class CommunicationLogCRUD(CRUDBase):
    """CRUD operations for communication logs."""
    
    @staticmethod
    async def log_communication(
        db: AsyncSession,
        announcement_id: UUID,
        channel: str,
        recipient_id: UUID = None,
        recipient_phone: str = None,
        recipient_email: str = None,
        subject: str = None,
        content_preview: str = None,
        status: str = "sent",
        status_message: str = None,
        external_id: str = None
    ) -> CommunicationLog:
        """Log a communication."""
        log = CommunicationLog(
            announcement_id=announcement_id,
            channel=channel,
            recipient_id=recipient_id,
            recipient_phone=recipient_phone,
            recipient_email=recipient_email,
            subject=subject,
            content_preview=content_preview,
            status=status,
            status_message=status_message,
            external_id=external_id,
            sent_at=datetime.now(timezone.utc),
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log
    
    @staticmethod
    async def get_logs_for_announcement(
        db: AsyncSession,
        announcement_id: UUID,
        channel: str = None,
        page: int = 1,
        limit: int = 100
    ) -> Tuple[List[CommunicationLog], int]:
        """Get communication logs for an announcement."""
        query = select(CommunicationLog).where(
            CommunicationLog.announcement_id == announcement_id
        )
        
        if channel:
            query = query.where(CommunicationLog.channel == channel)
        
        # Get total count
        count_query = select(func.count(CommunicationLog.id)).select_from(
            query.subquery()
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit).order_by(
            desc(CommunicationLog.created_at)
        )
        
        result = await db.execute(query)
        logs = list(result.scalars().all())
        
        return logs, total


# =============================================================================
# Communication Statistics
# =============================================================================

class CommunicationStatsCRUD:
    """Statistics for communications module."""
    
    @staticmethod
    async def get_announcement_stats(db: AsyncSession) -> dict:
        """Get announcement statistics."""
        total = await db.execute(
            select(func.count(Announcement.id))
        )
        total = total.scalar() or 0
        
        sent = await db.execute(
            select(func.count(Announcement.id))
            .where(Announcement.is_sent == True)
        )
        sent = sent.scalar() or 0
        
        # By type
        type_result = await db.execute(
            select(
                Announcement.announcement_type,
                func.count(Announcement.id)
            )
            .group_by(Announcement.announcement_type)
        )
        by_type = {row[0]: row[1] for row in type_result.all()}
        
        # By scope
        scope_result = await db.execute(
            select(
                Announcement.target_scope,
                func.count(Announcement.id)
            )
            .group_by(Announcement.target_scope)
        )
        by_scope = {row[0]: row[1] for row in scope_result.all()}
        
        return {
            "total": total,
            "sent": sent,
            "scheduled": total - sent,
            "by_type": by_type,
            "by_scope": by_scope,
        }
    
    @staticmethod
    async def get_forum_stats(db: AsyncSession) -> dict:
        """Get forum statistics."""
        total_forums = await db.execute(
            select(func.count(Forum.id)).where(Forum.is_deleted == False)
        )
        total_forums = total_forums.scalar() or 0
        
        total_posts = await db.execute(
            select(func.count(ForumPost.id))
            .where(
                and_(
                    ForumPost.is_deleted == False,
                    ForumPost.is_hidden == False
                )
            )
        )
        total_posts = total_posts.scalar() or 0
        
        total_comments = await db.execute(
            select(func.count(ForumComment.id))
            .where(ForumComment.is_deleted == False)
        )
        total_comments = total_comments.scalar() or 0
        
        return {
            "total_forums": total_forums,
            "total_posts": total_posts,
            "total_comments": total_comments,
        }
    
    @staticmethod
    async def get_communication_stats(db: AsyncSession) -> dict:
        """Get comprehensive communication statistics."""
        announcement_stats = await CommunicationStatsCRUD.get_announcement_stats(db)
        forum_stats = await CommunicationStatsCRUD.get_forum_stats(db)
        grievance_stats = await ForumGrievanceCRUD.get_statistics(db)
        
        # Channel stats
        channel_result = await db.execute(
            select(
                CommunicationLog.channel,
                func.count(CommunicationLog.id)
            )
            .group_by(CommunicationLog.channel)
        )
        channel_stats = {row[0]: row[1] for row in channel_result.all()}
        
        return {
            "announcements": announcement_stats,
            "forums": forum_stats,
            "grievances": grievance_stats,
            "channel_stats": channel_stats,
        }
