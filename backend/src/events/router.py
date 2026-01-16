"""
Event Router
API routes for event management.
"""

from datetime import datetime, timezone
from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import (
    NotFoundError,
    AlreadyExistsError,
    ValidationError,
    AuthorizationError,
    BusinessError,
)
from src.core.security import get_current_user
from src.auth.models import User

from src.events.schemas import (
    EventCreate,
    EventUpdate,
    EventResponse,
    EventDetailResponse,
    EventListResponse,
    EventSearchFilters,
    EventTypeResponse,
    EventParticipantCreate,
    EventParticipantResponse,
    EventParticipantUpdate,
    EventAttendanceCreate,
    EventAttendanceResponse,
    CheckInRequest,
    CheckInResponse,
    EventTaskCreate,
    EventTaskUpdate,
    EventTaskResponse,
    EventBudgetCreate,
    EventBudgetUpdate,
    EventBudgetResponse,
    EventFeedbackCreate,
    EventFeedbackResponse,
    EventStats,
    EventStatsResponse,
    EventAnalyticsResponse,
    UpcomingEventsResponse,
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignTaskCreate,
    CampaignTaskUpdate,
    CampaignTaskResponse,
    ApiResponse,
)
from src.events.deps import (
    get_event_by_id,
    get_event_task_by_id,
    check_event_view_permission,
    check_event_edit_permission,
    check_event_delete_permission,
    check_task_edit_permission,
)
from src.events.crud import (
    EventCRUD,
    EventAttendanceCRUD,
    EventTaskCRUD,
    EventBudgetCRUD,
    EventFeedbackCRUD,
    EventStatsCRUD,
    CampaignCRUD,
    CampaignTaskCRUD,
)
from src.events.models import (
    Event,
    EventTask,
    EventType,
    EventStatus,
    AttendanceStatus,
    TaskStatus,
)


router = APIRouter(prefix="/events", tags=["Events"])


# =============================================================================
# Health Check
# =============================================================================

@router.get("/health")
async def events_health_check():
    """Health check endpoint for events service."""
    return {"status": "healthy", "service": "events"}


# =============================================================================
# Event Types
# =============================================================================

@router.get("/types", response_model=List[EventTypeResponse])
async def list_event_types():
    """List all available event types."""
    return [
        EventTypeResponse(value=t.value, label=t.value.replace("_", " ").title())
        for t in EventType
    ]


# =============================================================================
# Events CRUD
# =============================================================================

@router.get("", response_model=EventListResponse)
async def list_events(
    request: Request,
    search: Optional[str] = None,
    type_filter: Optional[List[str]] = Query(None),
    status_filter: Optional[List[str]] = Query(None),
    unit_id: Optional[UUID] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    upcoming: Optional[bool] = None,
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List/search events with filters.
    
    Supports pagination and filtering by various criteria.
    """
    page = max(page, 1)
    limit = min(max(limit, 1), 100)
    
    filters = EventSearchFilters(
        search=search,
        type=type_filter,
        status=status_filter,
        unit_id=unit_id,
        from_date=from_date,
        to_date=to_date,
        upcoming=upcoming,
    )
    
    events, total = await EventCRUD.search(db, filters, page, limit)
    
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    
    return EventListResponse(
        events=[EventResponse.model_validate(e) for e in events],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.get("/upcoming", response_model=UpcomingEventsResponse)
async def get_upcoming_events(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get upcoming events.
    
    Returns events that are scheduled in the future.
    """
    now = datetime.now(timezone.utc)
    events = await EventCRUD.get_upcoming(db, from_date=now, limit=limit)
    
    return UpcomingEventsResponse(
        events=[EventResponse.model_validate(e) for e in events],
        total=len(events),
        from_date=now,
    )


@router.get("/stats", response_model=EventStatsResponse)
async def get_event_stats(
    unit_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get event statistics.
    
    Returns aggregated statistics about events.
    """
    stats_data = await EventStatsCRUD.get_stats(db, unit_id)
    return EventStatsResponse(
        stats=EventStats(**stats_data),
        generated_at=datetime.now(timezone.utc),
    )


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new event.
    
    The authenticated user will be set as the creator.
    """
    # Get member ID from current user
    member_id = None
    if hasattr(current_user, 'member_profile') and current_user.member_profile:
        member_id = current_user.member_profile.id
    
    try:
        event = await EventCRUD.create(db, event_data, created_by_id=member_id)
        return EventResponse.model_validate(event)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{event_id}", response_model=EventDetailResponse)
async def get_event(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get event by ID with full details.
    """
    event = await EventCRUD.get_detailed(db, event_id)
    if not event:
        raise NotFoundError(resource="Event", resource_id=str(event_id))
    
    # Build detail response
    response = EventDetailResponse.model_validate(event)
    response.participants_count = len(event.participants)
    response.attendance_count = len(event.attendance_records)
    response.tasks_count = len(event.tasks)
    response.feedback_count = len(event.feedback)
    
    return response


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: UUID,
    event_data: EventUpdate,
    event: Event = Depends(check_event_edit_permission),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an event.
    
    Requires edit permission on the event.
    """
    updated = await EventCRUD.update(db, event_id, event_data)
    if not updated:
        raise NotFoundError(resource="Event", resource_id=str(event_id))
    return EventResponse.model_validate(updated)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: UUID,
    event: Event = Depends(check_event_delete_permission),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete (soft-delete) an event.
    
    Requires delete permission on the event.
    """
    success = await EventCRUD.soft_delete(db, event_id)
    if not success:
        raise NotFoundError(resource="Event", resource_id=str(event_id))


# =============================================================================
# Event Participants
# =============================================================================

@router.get("/{event_id}/participants", response_model=List[EventParticipantResponse])
async def get_event_participants(
    event_id: UUID,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get participants for an event.
    """
    participants = await EventCRUD.get_participants(
        db, event_id, status=status_filter, skip=skip, limit=limit
    )
    
    # Get member info for each participant
    from src.members.models import Member
    result = []
    for p in participants:
        member = await MemberCRUD.get_by_id(db, Member, p["member_id"])
        participant_data = EventParticipantResponse(
            id=p["member_id"],  # Using member_id as id for response
            event_id=event_id,
            member_id=p["member_id"],
            status=p["status"],
            registered_at=p["registered_at"],
            is_organizer=p["is_organizer"],
            notes=p["notes"],
            member_name=member.get_full_name() if member else None,
            member_phone=member.phone if member else None,
        )
        result.append(participant_data)
    
    return result


@router.post("/{event_id}/participants", response_model=EventParticipantResponse, status_code=status.HTTP_201_CREATED)
async def add_event_participant(
    event_id: UUID,
    participant_data: EventParticipantCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a participant to an event.
    """
    try:
        await EventCRUD.add_participant(
            db,
            event_id,
            participant_data.member_id,
            is_organizer=participant_data.is_organizer,
            notes=participant_data.notes,
        )
        
        return EventParticipantResponse(
            id=participant_data.member_id,
            event_id=event_id,
            member_id=participant_data.member_id,
            status=AttendanceStatus.REGISTERED.value,
            registered_at=datetime.now(timezone.utc),
            is_organizer=participant_data.is_organizer or False,
            notes=participant_data.notes,
        )
    except AlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=e.to_dict())
    except BusinessError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


@router.delete("/{event_id}/participants/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_event_participant(
    event_id: UUID,
    member_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove a participant from an event.
    """
    success = await EventCRUD.remove_participant(db, event_id, member_id)
    if not success:
        raise NotFoundError(resource="EventParticipant")


# =============================================================================
# Event Tasks
# =============================================================================

@router.get("/{event_id}/tasks", response_model=List[EventTaskResponse])
async def get_event_tasks(
    event_id: UUID,
    status_filter: Optional[str] = None,
    assigned_to_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get tasks for an event.
    """
    tasks = await EventTaskCRUD.get_by_event(
        db, event_id, status=status_filter, assigned_to_id=assigned_to_id
    )
    
    return [EventTaskResponse.model_validate(t) for t in tasks]


@router.post("/{event_id}/tasks", response_model=EventTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_event_task(
    event_id: UUID,
    task_data: EventTaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a task for an event.
    """
    task = await EventTaskCRUD.create(db, event_id, task_data)
    return EventTaskResponse.model_validate(task)


@router.put("/{event_id}/tasks/{task_id}", response_model=EventTaskResponse)
async def update_event_task(
    event_id: UUID,
    task_id: UUID,
    task_data: EventTaskUpdate,
    task: EventTask = Depends(check_task_edit_permission),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an event task.
    """
    updated = await EventTaskCRUD.update(db, task_id, task_data)
    if not updated:
        raise NotFoundError(resource="EventTask", resource_id=str(task_id))
    return EventTaskResponse.model_validate(updated)


@router.delete("/{event_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event_task(
    event_id: UUID,
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an event task.
    """
    from src.events.crud import EventTaskCRUD
    success = await EventTaskCRUD.delete(db, EventTask, task_id)
    if not success:
        raise NotFoundError(resource="EventTask", resource_id=str(task_id))


# =============================================================================
# Event Attendance
# =============================================================================

@router.get("/{event_id}/attendance", response_model=List[EventAttendanceResponse])
async def get_event_attendance(
    event_id: UUID,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get attendance records for an event.
    """
    records = await EventAttendanceCRUD.get_by_event(db, event_id, status=status_filter)
    
    # Get member info
    from src.members.models import Member
    from src.members.crud import MemberCRUD
    
    result = []
    for r in records:
        member = await MemberCRUD.get_by_id(db, Member, r.member_id)
        record = EventAttendanceResponse.model_validate(r)
        record.member_name = member.get_full_name() if member else None
        result.append(record)
    
    return result


@router.post("/{event_id}/attendance/checkin", response_model=CheckInResponse)
async def check_in_to_event(
    event_id: UUID,
    checkin_data: CheckInRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Check in to an event.
    
    The current user will be checked in to the event.
    """
    # Get member ID from current user
    if not hasattr(current_user, 'member_profile') or not current_user.member_profile:
        raise AuthorizationError("User is not a member")
    
    member_id = current_user.member_profile.id
    
    try:
        attendance = await EventAttendanceCRUD.check_in(
            db, event_id, member_id, location=checkin_data.location
        )
        
        return CheckInResponse(
            success=True,
            status=attendance.status,
            check_in_time=attendance.check_in_time,
            message="Checked in successfully",
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())
    except BusinessError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


@router.post("/{event_id}/attendance/checkout", response_model=CheckInResponse)
async def check_out_of_event(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Check out from an event.
    
    The current user will be checked out from the event.
    """
    # Get member ID from current user
    if not hasattr(current_user, 'member_profile') or not current_user.member_profile:
        raise AuthorizationError("User is not a member")
    
    member_id = current_user.member_profile.id
    
    try:
        attendance = await EventAttendanceCRUD.check_out(db, event_id, member_id)
        
        return CheckInResponse(
            success=True,
            status=attendance.status,
            check_in_time=attendance.check_in_time,
            message="Checked out successfully",
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())
    except BusinessError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


# =============================================================================
# Event Feedback
# =============================================================================

@router.get("/{event_id}/feedback", response_model=List[EventFeedbackResponse])
async def get_event_feedback(
    event_id: UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get feedback for an event.
    """
    feedback_list = await EventFeedbackCRUD.get_by_event(db, event_id, skip=skip, limit=limit)
    
    # Get member info for non-anonymous feedback
    from src.members.models import Member
    from src.members.crud import MemberCRUD
    
    result = []
    for f in feedback_list:
        fb = EventFeedbackResponse.model_validate(f)
        if not f.is_anonymous:
            member = await MemberCRUD.get_by_id(db, Member, f.member_id)
            fb.member_name = member.get_full_name() if member else None
        result.append(fb)
    
    return result


@router.post("/{event_id}/feedback", response_model=EventFeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_event_feedback(
    event_id: UUID,
    feedback_data: EventFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit feedback for an event.
    """
    # Get member ID from current user
    if not hasattr(current_user, 'member_profile') or not current_user.member_profile:
        raise AuthorizationError("User is not a member")
    
    member_id = current_user.member_profile.id
    
    feedback = await EventFeedbackCRUD.create(db, event_id, member_id, feedback_data)
    return EventFeedbackResponse.model_validate(feedback)


# =============================================================================
# Event Analytics
# =============================================================================

@router.get("/{event_id}/analytics", response_model=EventAnalyticsResponse)
async def get_event_analytics(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get analytics for an event.
    """
    analytics = await EventStatsCRUD.get_event_analytics(db, event_id)
    return EventAnalyticsResponse(**analytics)


# =============================================================================
# Event Budget
# =============================================================================

@router.get("/{event_id}/budget", response_model=EventBudgetResponse)
async def get_event_budget(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get budget for an event.
    """
    budget = await EventBudgetCRUD.get_by_event(db, event_id)
    if not budget:
        raise NotFoundError(resource="EventBudget", resource_id=str(event_id))
    return EventBudgetResponse.model_validate(budget)


@router.post("/{event_id}/budget", response_model=EventBudgetResponse, status_code=status.HTTP_201_CREATED)
async def create_event_budget(
    event_id: UUID,
    budget_data: EventBudgetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create budget for an event.
    """
    try:
        budget = await EventBudgetCRUD.create(db, event_id, budget_data.model_dump())
        return EventBudgetResponse.model_validate(budget)
    except AlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=e.to_dict())


@router.put("/{event_id}/budget", response_model=EventBudgetResponse)
async def update_event_budget(
    event_id: UUID,
    budget_data: EventBudgetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update budget for an event.
    """
    updated = await EventBudgetCRUD.update(db, event_id, budget_data.model_dump(exclude_unset=True))
    if not updated:
        raise NotFoundError(resource="EventBudget", resource_id=str(event_id))
    return EventBudgetResponse.model_validate(updated)


# =============================================================================
# Campaigns
# =============================================================================

@router.get("/campaigns", response_model=List[CampaignResponse])
async def list_campaigns(
    status_filter: Optional[str] = None,
    unit_id: Optional[UUID] = None,
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List campaigns with filters.
    """
    page = max(page, 1)
    limit = min(max(limit, 1), 100)
    
    campaigns, total = await CampaignCRUD.search(db, status=status_filter, unit_id=unit_id, page=page, limit=limit)
    
    # Add task counts
    result = []
    for c in campaigns:
        campaign = CampaignResponse.model_validate(c)
        campaign.tasks_count = len(c.tasks)
        campaign.completed_tasks = sum(1 for t in c.tasks if t.status == "completed")
        campaign.progress_percentage = round((campaign.completed_tasks / max(campaign.tasks_count, 1)) * 100, 2)
        result.append(campaign)
    
    return result


@router.post("/campaigns", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_data: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new campaign.
    """
    member_id = None
    if hasattr(current_user, 'member_profile') and current_user.member_profile:
        member_id = current_user.member_profile.id
    
    campaign = await CampaignCRUD.create(db, campaign_data, created_by_id=member_id)
    return CampaignResponse.model_validate(campaign)


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get campaign by ID with details.
    """
    campaign = await CampaignCRUD.get_detailed(db, campaign_id)
    if not campaign:
        raise NotFoundError(resource="Campaign", resource_id=str(campaign_id))
    
    response = CampaignResponse.model_validate(campaign)
    response.tasks_count = len(campaign.tasks)
    response.completed_tasks = sum(1 for t in campaign.tasks if t.status == "completed")
    response.progress_percentage = round((response.completed_tasks / max(response.tasks_count, 1)) * 100, 2)
    
    return response


@router.get("/campaigns/{campaign_id}/progress")
async def get_campaign_progress(
    campaign_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get campaign progress with goals and tasks.
    """
    progress = await CampaignCRUD.get_progress(db, campaign_id)
    return progress


@router.put("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    campaign_data: CampaignUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a campaign.
    """
    updated = await CampaignCRUD.update(db, campaign_id, campaign_data)
    if not updated:
        raise NotFoundError(resource="Campaign", resource_id=str(campaign_id))
    return CampaignResponse.model_validate(updated)


# =============================================================================
# Campaign Tasks
# =============================================================================

@router.get("/campaigns/{campaign_id}/tasks", response_model=List[CampaignTaskResponse])
async def get_campaign_tasks(
    campaign_id: UUID,
    status_filter: Optional[str] = None,
    assigned_to_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get tasks for a campaign.
    """
    tasks = await CampaignTaskCRUD.get_by_campaign(
        db, campaign_id, status=status_filter, assigned_to_id=assigned_to_id
    )
    return [CampaignTaskResponse.model_validate(t) for t in tasks]


@router.post("/campaigns/{campaign_id}/tasks", response_model=CampaignTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign_task(
    campaign_id: UUID,
    task_data: CampaignTaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a task for a campaign.
    """
    task = await CampaignTaskCRUD.create(db, campaign_id, task_data)
    return CampaignTaskResponse.model_validate(task)


@router.put("/campaigns/{campaign_id}/tasks/{task_id}", response_model=CampaignTaskResponse)
async def update_campaign_task(
    campaign_id: UUID,
    task_id: UUID,
    task_data: CampaignTaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a campaign task.
    """
    updated = await CampaignTaskCRUD.update(db, task_id, task_data)
    if not updated:
        raise NotFoundError(resource="CampaignTask", resource_id=str(task_id))
    return CampaignTaskResponse.model_validate(updated)


@router.delete("/campaigns/{campaign_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign_task(
    campaign_id: UUID,
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a campaign task.
    """
    success = await CampaignTaskCRUD.delete(db, CampaignTask, task_id)
    if not success:
        raise NotFoundError(resource="CampaignTask", resource_id=str(task_id))
