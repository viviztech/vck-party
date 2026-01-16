"""
Event CRUD Operations
CRUD operations for events, campaigns, and related entities.
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple, Type, TypeVar, Dict, Any
from uuid import UUID

from sqlalchemy import select, update, delete, and_, or_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import (
    NotFoundError,
    AlreadyExistsError,
    ValidationError,
    BusinessError,
)
from src.core import redis
from src.events.models import (
    Event,
    EventAttendance,
    EventTask,
    EventBudget,
    EventFeedback,
    Campaign,
    CampaignTask,
    EventType,
    EventStatus,
    AttendanceStatus,
    TaskStatus,
    CampaignStatus,
    event_participants,
)
from src.events.schemas import (
    EventCreate,
    EventUpdate,
    EventSearchFilters,
    EventTaskCreate,
    EventTaskUpdate,
    EventAttendanceCreate,
    EventFeedbackCreate,
    CampaignCreate,
    CampaignUpdate,
    CampaignTaskCreate,
    CampaignTaskUpdate,
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
    
    @staticmethod
    async def delete(db: AsyncSession, model: Type[T], id: UUID) -> bool:
        """Soft delete a record by ID."""
        record = await CRUDBase.get_by_id(db, model, id)
        if record:
            if hasattr(record, 'is_deleted'):
                record.is_deleted = True
                record.deleted_at = datetime.now(timezone.utc)
            else:
                await db.delete(record)
            await db.commit()
            return True
        return False


# =============================================================================
# Event CRUD
# =============================================================================

class EventCRUD(CRUDBase):
    """CRUD operations for events."""
    
    @staticmethod
    async def create(db: AsyncSession, event_data: EventCreate, created_by_id: UUID = None) -> Event:
        """Create a new event."""
        event = Event(
            title=event_data.title,
            title_ta=event_data.title_ta,
            description=event_data.description,
            description_ta=event_data.description_ta,
            type=event_data.type,
            unit_id=event_data.unit_id,
            created_by_id=created_by_id,
            start_time=event_data.start_time,
            end_time=event_data.end_time,
            venue_name=event_data.venue_name,
            venue_address=event_data.venue_address,
            geo_location=event_data.geo_location,
            geo_fence_radius=event_data.geo_fence_radius,
            max_attendees=event_data.max_attendees,
            registration_required=event_data.registration_required,
            registration_deadline=event_data.registration_deadline,
            banner_url=event_data.banner_url,
            media_urls=event_data.media_urls or [],
            status=event_data.status or EventStatus.DRAFT.value,
            metadata=event_data.metadata or {},
        )
        
        db.add(event)
        await db.commit()
        await db.refresh(event)
        
        # Cache the event
        await redis.cache_event(event.id, event)
        
        return event
    
    @staticmethod
    async def update(db: AsyncSession, event_id: UUID, event_data: EventUpdate) -> Optional[Event]:
        """Update an event."""
        event = await EventCRUD.get_by_id(db, Event, event_id)
        if not event:
            return None
        
        update_data = event_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(event, field, value)
        
        await db.commit()
        await db.refresh(event)
        
        # Update cache
        await redis.cache_event(event_id, event)
        
        return event
    
    @staticmethod
    async def get_detailed(db: AsyncSession, event_id: UUID) -> Optional[Event]:
        """Get event with all relationships loaded."""
        result = await db.execute(
            select(Event)
            .where(Event.id == event_id)
            .where(Event.is_deleted == False)
            .options(
                selectinload(Event.participants),
                selectinload(Event.attendance_records),
                selectinload(Event.tasks),
                selectinload(Event.budget),
                selectinload(Event.feedback),
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def search(
        db: AsyncSession,
        filters: EventSearchFilters,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Event], int]:
        """Search events with filters."""
        query = (
            select(Event)
            .where(Event.is_deleted == False)
        )
        
        # Text search
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    Event.title.ilike(search_term),
                    Event.description.ilike(search_term),
                )
            )
        
        # Type filter
        if filters.type:
            query = query.where(Event.type.in_(filters.type))
        
        # Status filter
        if filters.status:
            query = query.where(Event.status.in_(filters.status))
        
        # Unit filter
        if filters.unit_id:
            query = query.where(Event.unit_id == filters.unit_id)
        
        # Date range filters
        if filters.from_date:
            query = query.where(Event.start_time >= filters.from_date)
        if filters.to_date:
            query = query.where(Event.start_time <= filters.to_date)
        
        # Upcoming events
        if filters.upcoming:
            now = datetime.now(timezone.utc)
            query = query.where(Event.start_time > now)
            query = query.where(Event.status != EventStatus.CANCELLED.value)
        
        # Get total count
        count_query = select(func.count(Event.id)).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit).order_by(Event.start_time.asc())
        
        result = await db.execute(query)
        events = list(result.scalars().all())
        
        return events, total
    
    @staticmethod
    async def get_upcoming(
        db: AsyncSession,
        from_date: datetime = None,
        to_date: datetime = None,
        limit: int = 10
    ) -> List[Event]:
        """Get upcoming events."""
        now = datetime.now(timezone.utc)
        
        query = (
            select(Event)
            .where(Event.is_deleted == False)
            .where(Event.start_time > now)
            .where(Event.status != EventStatus.CANCELLED.value)
        )
        
        if from_date:
            query = query.where(Event.start_time >= from_date)
        if to_date:
            query = query.where(Event.start_time <= to_date)
        
        query = query.order_by(Event.start_time.asc()).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def soft_delete(db: AsyncSession, event_id: UUID) -> bool:
        """Soft delete an event."""
        event = await EventCRUD.get_by_id(db, Event, event_id)
        if not event:
            return False
        
        event.is_deleted = True
        event.deleted_at = datetime.now(timezone.utc)
        event.status = EventStatus.CANCELLED.value
        
        await db.commit()
        
        # Remove from cache
        await redis.delete_event_cache(event_id)
        
        return True
    
    @staticmethod
    async def add_participant(
        db: AsyncSession,
        event_id: UUID,
        member_id: UUID,
        is_organizer: bool = False,
        notes: str = None
    ) -> bool:
        """Add a participant to an event."""
        event = await EventCRUD.get_by_id(db, Event, event_id)
        if not event:
            raise NotFoundError(resource="Event", resource_id=str(event_id))
        
        # Check if already a participant
        result = await db.execute(
            select(event_participants).where(
                and_(
                    event_participants.c.event_id == event_id,
                    event_participants.c.member_id == member_id
                )
            )
        )
        existing = result.first()
        if existing:
            raise AlreadyExistsError(resource="EventParticipant", field="member_id")
        
        # Check capacity
        if event.max_attendees:
            current_count = await db.execute(
                select(func.count(event_participants.c.member_id))
                .where(event_participants.c.event_id == event_id)
            )
            count = current_count.scalar() or 0
            if count >= event.max_attendees:
                raise BusinessError(
                    message="Event has reached maximum capacity",
                    code="EVENT_FULL"
                )
        
        # Add participant
        stmt = event_participants.insert().values(
            event_id=event_id,
            member_id=member_id,
            is_organizer=is_organizer,
            notes=notes,
            status=AttendanceStatus.REGISTERED.value,
        )
        await db.execute(stmt)
        await db.commit()
        
        return True
    
    @staticmethod
    async def remove_participant(db: AsyncSession, event_id: UUID, member_id: UUID) -> bool:
        """Remove a participant from an event."""
        stmt = event_participants.delete().where(
            and_(
                event_participants.c.event_id == event_id,
                event_participants.c.member_id == member_id
            )
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def get_participants(
        db: AsyncSession,
        event_id: UUID,
        status: str = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get event participants."""
        query = (
            select(
                event_participants.c.member_id,
                event_participants.c.status,
                event_participants.c.registered_at,
                event_participants.c.is_organizer,
                event_participants.c.notes,
            )
            .where(event_participants.c.event_id == event_id)
        )
        
        if status:
            query = query.where(event_participants.c.status == status)
        
        query = query.offset(skip).limit(limit).order_by(event_participants.c.registered_at.desc())
        
        result = await db.execute(query)
        return [dict(row._mapping) for row in result]


# =============================================================================
# Event Attendance CRUD
# =============================================================================

class EventAttendanceCRUD(CRUDBase):
    """CRUD operations for event attendance."""
    
    @staticmethod
    async def create(
        db: AsyncSession,
        event_id: UUID,
        attendance_data: EventAttendanceCreate
    ) -> EventAttendance:
        """Create an attendance record."""
        # Check if record already exists
        existing = await EventAttendanceCRUD.get_by_event_and_member(
            db, event_id, attendance_data.member_id
        )
        if existing:
            raise AlreadyExistsError(resource="EventAttendance", field="member_id")
        
        attendance = EventAttendance(
            event_id=event_id,
            member_id=attendance_data.member_id,
            status=attendance_data.status or AttendanceStatus.REGISTERED.value,
        )
        
        db.add(attendance)
        await db.commit()
        await db.refresh(attendance)
        return attendance
    
    @staticmethod
    async def get_by_event_and_member(
        db: AsyncSession,
        event_id: UUID,
        member_id: UUID
    ) -> Optional[EventAttendance]:
        """Get attendance record by event and member."""
        result = await db.execute(
            select(EventAttendance).where(
                and_(
                    EventAttendance.event_id == event_id,
                    EventAttendance.member_id == member_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def check_in(
        db: AsyncSession,
        event_id: UUID,
        member_id: UUID,
        location: str = None
    ) -> Optional[EventAttendance]:
        """Check in a member to an event."""
        attendance = await EventAttendanceCRUD.get_by_event_and_member(db, event_id, member_id)
        if not attendance:
            raise NotFoundError(resource="EventAttendance")
        
        if attendance.check_in_time:
            raise BusinessError(message="Already checked in", code="ALREADY_CHECKED_IN")
        
        attendance.check_in_time = datetime.now(timezone.utc)
        attendance.check_in_location = location
        attendance.status = AttendanceStatus.ATTENDED.value
        
        await db.commit()
        await db.refresh(attendance)
        return attendance
    
    @staticmethod
    async def check_out(
        db: AsyncSession,
        event_id: UUID,
        member_id: UUID
    ) -> Optional[EventAttendance]:
        """Check out a member from an event."""
        attendance = await EventAttendanceCRUD.get_by_event_and_member(db, event_id, member_id)
        if not attendance:
            raise NotFoundError(resource="EventAttendance")
        
        if not attendance.check_in_time:
            raise BusinessError(message="Not checked in yet", code="NOT_CHECKED_IN")
        
        if attendance.check_out_time:
            raise BusinessError(message="Already checked out", code="ALREADY_CHECKED_OUT")
        
        attendance.check_out_time = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(attendance)
        return attendance
    
    @staticmethod
    async def get_by_event(
        db: AsyncSession,
        event_id: UUID,
        status: str = None
    ) -> List[EventAttendance]:
        """Get all attendance records for an event."""
        query = (
            select(EventAttendance)
            .where(EventAttendance.event_id == event_id)
        )
        
        if status:
            query = query.where(EventAttendance.status == status)
        
        query = query.order_by(EventAttendance.registered_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())


# =============================================================================
# Event Task CRUD
# =============================================================================

class EventTaskCRUD(CRUDBase):
    """CRUD operations for event tasks."""
    
    @staticmethod
    async def create(
        db: AsyncSession,
        event_id: UUID,
        task_data: EventTaskCreate
    ) -> EventTask:
        """Create an event task."""
        task = EventTask(
            event_id=event_id,
            title=task_data.title,
            description=task_data.description,
            assigned_to_id=task_data.assigned_to_id,
            unit_id=task_data.unit_id,
            due_date=task_data.due_date,
            priority=task_data.priority,
            metadata=task_data.metadata or {},
        )
        
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task
    
    @staticmethod
    async def update(
        db: AsyncSession,
        task_id: UUID,
        task_data: EventTaskUpdate
    ) -> Optional[EventTask]:
        """Update an event task."""
        task = await EventTaskCRUD.get_by_id(db, EventTask, task_id)
        if not task:
            return None
        
        update_data = task_data.model_dump(exclude_unset=True)
        
        # Handle status change
        if "status" in update_data and update_data["status"] == TaskStatus.COMPLETED.value:
            update_data["completed_at"] = datetime.now(timezone.utc)
        
        for field, value in update_data.items():
            setattr(task, field, value)
        
        await db.commit()
        await db.refresh(task)
        return task
    
    @staticmethod
    async def get_by_event(
        db: AsyncSession,
        event_id: UUID,
        status: str = None,
        assigned_to_id: UUID = None
    ) -> List[EventTask]:
        """Get tasks for an event."""
        query = (
            select(EventTask)
            .where(EventTask.event_id == event_id)
        )
        
        if status:
            query = query.where(EventTask.status == status)
        if assigned_to_id:
            query = query.where(EventTask.assigned_to_id == assigned_to_id)
        
        query = query.order_by(EventTask.priority.asc(), EventTask.due_date.asc())
        
        result = await db.execute(query)
        return list(result.scalars().all())


# =============================================================================
# Event Budget CRUD
# =============================================================================

class EventBudgetCRUD(CRUDBase):
    """CRUD operations for event budgets."""
    
    @staticmethod
    async def get_by_event(db: AsyncSession, event_id: UUID) -> Optional[EventBudget]:
        """Get budget for an event."""
        result = await db.execute(
            select(EventBudget).where(EventBudget.event_id == event_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(
        db: AsyncSession,
        event_id: UUID,
        budget_data: dict = None
    ) -> EventBudget:
        """Create an event budget."""
        # Check if already exists
        existing = await EventBudgetCRUD.get_by_event(db, event_id)
        if existing:
            raise AlreadyExistsError(resource="EventBudget", field="event_id")
        
        budget = EventBudget(
            event_id=event_id,
            estimated_cost=budget_data.get("estimated_cost", 0) if budget_data else 0,
            actual_cost=budget_data.get("actual_cost", 0) if budget_data else 0,
            currency=budget_data.get("currency", "INR") if budget_data else "INR",
            categories=budget_data.get("categories", {}) if budget_data else {},
            notes=budget_data.get("notes") if budget_data else None,
        )
        
        db.add(budget)
        await db.commit()
        await db.refresh(budget)
        return budget
    
    @staticmethod
    async def update(
        db: AsyncSession,
        event_id: UUID,
        budget_data: dict
    ) -> Optional[EventBudget]:
        """Update an event budget."""
        budget = await EventBudgetCRUD.get_by_event(db, event_id)
        if not budget:
            return None
        
        for field, value in budget_data.items():
            if value is not None:
                setattr(budget, field, value)
        
        await db.commit()
        await db.refresh(budget)
        return budget


# =============================================================================
# Event Feedback CRUD
# =============================================================================

class EventFeedbackCRUD(CRUDBase):
    """CRUD operations for event feedback."""
    
    @staticmethod
    async def create(
        db: AsyncSession,
        event_id: UUID,
        member_id: UUID,
        feedback_data: EventFeedbackCreate
    ) -> EventFeedback:
        """Create event feedback."""
        feedback = EventFeedback(
            event_id=event_id,
            member_id=member_id,
            rating=feedback_data.rating,
            feedback_type=feedback_data.feedback_type,
            comments=feedback_data.comments,
            would_recommend=feedback_data.would_recommend,
            highlights=feedback_data.highlights or [],
            improvements=feedback_data.improvements or [],
            is_anonymous=feedback_data.is_anonymous,
        )
        
        db.add(feedback)
        await db.commit()
        await db.refresh(feedback)
        return feedback
    
    @staticmethod
    async def get_by_event(
        db: AsyncSession,
        event_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[EventFeedback]:
        """Get feedback for an event."""
        query = (
            select(EventFeedback)
            .where(EventFeedback.event_id == event_id)
            .order_by(EventFeedback.created_at.desc())
        )
        
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_average_rating(db: AsyncSession, event_id: UUID) -> Optional[float]:
        """Get average rating for an event."""
        result = await db.execute(
            select(func.avg(EventFeedback.rating))
            .where(
                and_(
                    EventFeedback.event_id == event_id,
                    EventFeedback.rating.isnot(None)
                )
            )
        )
        avg = result.scalar()
        return float(avg) if avg else None


# =============================================================================
# Event Statistics CRUD
# =============================================================================

class EventStatsCRUD:
    """Statistics operations for events."""
    
    @staticmethod
    async def get_stats(db: AsyncSession, unit_id: UUID = None) -> Dict[str, Any]:
        """Get overall event statistics."""
        now = datetime.now(timezone.utc)
        
        # Base query
        base_query = select(Event).where(Event.is_deleted == False)
        if unit_id:
            base_query = base_query.where(Event.unit_id == unit_id)
        
        # Total events
        total = await db.execute(select(func.count(Event.id)).select_from(base_query.subquery()))
        total = total.scalar() or 0
        
        # By status
        status_counts = {}
        status_result = await db.execute(
            select(Event.status, func.count(Event.id))
            .where(Event.is_deleted == False)
            .group_by(Event.status)
        )
        for row in status_result:
            status_counts[row[0]] = row[1]
        
        # By type
        type_counts = {}
        type_result = await db.execute(
            select(Event.type, func.count(Event.id))
            .where(Event.is_deleted == False)
            .group_by(Event.type)
        )
        for row in type_result:
            type_counts[row[0]] = row[1]
        
        # Upcoming events
        upcoming = await db.execute(
            select(func.count(Event.id)).where(
                and_(
                    Event.is_deleted == False,
                    Event.start_time > now,
                    Event.status != EventStatus.CANCELLED.value
                )
            )
        )
        upcoming = upcoming.scalar() or 0
        
        # Events this month
        first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month = await db.execute(
            select(func.count(Event.id)).where(
                and_(
                    Event.is_deleted == False,
                    Event.created_at >= first_of_month
                )
            )
        )
        this_month = this_month.scalar() or 0
        
        # Events this week
        week_ago = now.replace(day=now.day - 7)
        this_week = await db.execute(
            select(func.count(Event.id)).where(
                and_(
                    Event.is_deleted == False,
                    Event.created_at >= week_ago
                )
            )
        )
        this_week = this_week.scalar() or 0
        
        # Attendance stats (from event_attendance table)
        from src.events.models import EventAttendance
        total_attendance = await db.execute(
            select(func.count(EventAttendance.id)).where(EventAttendance.status == AttendanceStatus.ATTENDED.value)
        )
        total_attendance = total_attendance.scalar() or 0
        
        total_registrations = await db.execute(
            select(func.count(EventAttendance.id))
        )
        total_registrations = total_registrations.scalar() or 0
        
        avg_attendance = round(total_attendance / max(total, 1), 2)
        
        return {
            "total_events": total,
            "upcoming_events": upcoming,
            "completed_events": status_counts.get(EventStatus.COMPLETED.value, 0),
            "ongoing_events": status_counts.get(EventStatus.ONGOING.value, 0),
            "by_type": type_counts,
            "by_status": status_counts,
            "total_participants": total_attendance,
            "avg_attendance": avg_attendance,
            "total_registrations": total_registrations,
            "events_this_month": this_month,
            "events_this_week": this_week,
        }
    
    @staticmethod
    async def get_event_analytics(db: AsyncSession, event_id: UUID) -> Dict[str, Any]:
        """Get analytics for a single event."""
        # Get counts
        registrations = await db.execute(
            select(func.count(EventAttendance.id)).where(EventAttendance.event_id == event_id)
        )
        registrations = registrations.scalar() or 0
        
        attended = await db.execute(
            select(func.count(EventAttendance.id)).where(
                and_(
                    EventAttendance.event_id == event_id,
                    EventAttendance.status == AttendanceStatus.ATTENDED.value
                )
            )
        )
        attended = attended.scalar() or 0
        
        no_shows = await db.execute(
            select(func.count(EventAttendance.id)).where(
                and_(
                    EventAttendance.event_id == event_id,
                    EventAttendance.status == AttendanceStatus.NO_SHOW.value
                )
            )
        )
        no_shows = no_shows.scalar() or 0
        
        attendance_rate = round((attended / max(registrations, 1)) * 100, 2)
        
        # Get average rating
        avg_rating = await EventFeedbackCRUD.get_average_rating(db, event_id)
        
        # Count feedback
        feedback_count = await db.execute(
            select(func.count(EventFeedback.id)).where(EventFeedback.event_id == event_id)
        )
        feedback_count = feedback_count.scalar() or 0
        
        return {
            "event_id": event_id,
            "registrations": registrations,
            "attended": attended,
            "no_shows": no_shows,
            "attendance_rate": attendance_rate,
            "avg_rating": avg_rating,
            "total_feedback": feedback_count,
            "by_unit": [],  # Can be enhanced with unit aggregation
            "check_in_timeline": [],  # Can be enhanced with timeline aggregation
        }


# =============================================================================
# Campaign CRUD
# =============================================================================

class CampaignCRUD(CRUDBase):
    """CRUD operations for campaigns."""
    
    @staticmethod
    async def create(db: AsyncSession, campaign_data: CampaignCreate, created_by_id: UUID = None) -> Campaign:
        """Create a new campaign."""
        campaign = Campaign(
            name=campaign_data.name,
            name_ta=campaign_data.name_ta,
            description=campaign_data.description,
            description_ta=campaign_data.description_ta,
            unit_id=campaign_data.unit_id,
            created_by_id=created_by_id,
            start_date=campaign_data.start_date,
            end_date=campaign_data.end_date,
            goals=campaign_data.goals or {},
            budget=campaign_data.budget,
            status=campaign_data.status or CampaignStatus.PLANNING.value,
        )
        
        db.add(campaign)
        await db.commit()
        await db.refresh(campaign)
        return campaign
    
    @staticmethod
    async def update(
        db: AsyncSession,
        campaign_id: UUID,
        campaign_data: CampaignUpdate
    ) -> Optional[Campaign]:
        """Update a campaign."""
        campaign = await CampaignCRUD.get_by_id(db, Campaign, campaign_id)
        if not campaign:
            return None
        
        update_data = campaign_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(campaign, field, value)
        
        await db.commit()
        await db.refresh(campaign)
        return campaign
    
    @staticmethod
    async def get_detailed(db: AsyncSession, campaign_id: UUID) -> Optional[Campaign]:
        """Get campaign with tasks."""
        result = await db.execute(
            select(Campaign)
            .where(Campaign.id == campaign_id)
            .options(selectinload(Campaign.tasks))
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def search(
        db: AsyncSession,
        status: str = None,
        unit_id: UUID = None,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Campaign], int]:
        """Search campaigns with filters."""
        query = select(Campaign)
        
        if status:
            query = query.where(Campaign.status == status)
        if unit_id:
            query = query.where(Campaign.unit_id == unit_id)
        
        # Get total count
        count_query = select(func.count(Campaign.id)).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit).order_by(Campaign.start_date.desc())
        
        result = await db.execute(query)
        campaigns = list(result.scalars().all())
        
        return campaigns, total
    
    @staticmethod
    async def get_progress(db: AsyncSession, campaign_id: UUID) -> Dict[str, Any]:
        """Get campaign progress."""
        campaign = await CampaignCRUD.get_detailed(db, campaign_id)
        if not campaign:
            raise NotFoundError(resource="Campaign", resource_id=str(campaign_id))
        
        total_tasks = len(campaign.tasks)
        completed_tasks = sum(1 for t in campaign.tasks if t.status == "completed")
        in_progress_tasks = sum(1 for t in campaign.tasks if t.status == "in_progress")
        
        # Calculate goal progress
        goals_progress = {}
        for goal_key, target in campaign.goals.items():
            if goal_key.endswith("_count") or goal_key in ["target_voters", "door_visits", "new_members"]:
                # These are numeric goals
                current = sum(
                    t.metrics.get(goal_key, 0) 
                    for t in campaign.tasks 
                    if t.status == "completed"
                )
                goals_progress[goal_key] = {
                    "target": target,
                    "achieved": current,
                    "percentage": round((current / max(target, 1)) * 100, 2)
                }
        
        return {
            "campaign_id": campaign_id,
            "tasks": {
                "total": total_tasks,
                "completed": completed_tasks,
                "in_progress": in_progress_tasks,
                "pending": total_tasks - completed_tasks - in_progress_tasks,
            },
            "goals": goals_progress,
        }


# =============================================================================
# Campaign Task CRUD
# =============================================================================

class CampaignTaskCRUD(CRUDBase):
    """CRUD operations for campaign tasks."""
    
    @staticmethod
    async def create(
        db: AsyncSession,
        campaign_id: UUID,
        task_data: CampaignTaskCreate
    ) -> CampaignTask:
        """Create a campaign task."""
        task = CampaignTask(
            campaign_id=campaign_id,
            title=task_data.title,
            description=task_data.description,
            assigned_to_id=task_data.assigned_to_id,
            unit_id=task_data.unit_id,
            due_date=task_data.due_date,
            priority=task_data.priority,
        )
        
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task
    
    @staticmethod
    async def update(
        db: AsyncSession,
        task_id: UUID,
        task_data: CampaignTaskUpdate
    ) -> Optional[CampaignTask]:
        """Update a campaign task."""
        task = await CampaignTaskCRUD.get_by_id(db, CampaignTask, task_id)
        if not task:
            return None
        
        update_data = task_data.model_dump(exclude_unset=True)
        
        # Handle status change
        if "status" in update_data and update_data["status"] == "completed":
            update_data["completed_at"] = datetime.now(timezone.utc)
        
        for field, value in update_data.items():
            setattr(task, field, value)
        
        await db.commit()
        await db.refresh(task)
        return task
    
    @staticmethod
    async def get_by_campaign(
        db: AsyncSession,
        campaign_id: UUID,
        status: str = None,
        assigned_to_id: UUID = None
    ) -> List[CampaignTask]:
        """Get tasks for a campaign."""
        query = (
            select(CampaignTask)
            .where(CampaignTask.campaign_id == campaign_id)
        )
        
        if status:
            query = query.where(CampaignTask.status == status)
        if assigned_to_id:
            query = query.where(CampaignTask.assigned_to_id == assigned_to_id)
        
        query = query.order_by(CampaignTask.priority.asc(), CampaignTask.due_date.asc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
