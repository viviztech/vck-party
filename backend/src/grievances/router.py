"""
Grievance Router
API routes for grievance management.
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
)
from src.core.security import get_current_user
from src.auth.models import User

from src.grievances.schemas import (
    GrievanceCreate,
    GrievanceUpdate,
    GrievanceResponse,
    GrievanceDetailResponse,
    GrievanceListResponse,
    GrievanceSearchFilters,
    GrievanceCategoryCreate,
    GrievanceCategoryUpdate,
    GrievanceCategoryResponse,
    GrievanceCategoryListResponse,
    GrievanceAssignmentCreate,
    GrievanceAssignmentClaim,
    GrievanceAssignmentResponse,
    GrievanceAssignmentHistoryResponse,
    GrievanceEscalationCreate,
    GrievanceEscalationResponse,
    GrievanceSLAResponse,
    GrievanceSLAStatus,
    GrievanceResolutionCreate,
    GrievanceResolutionResponse,
    GrievanceStats,
    GrievanceStatsResponse,
    GrievanceDashboard,
    GrievanceDashboardResponse,
    GrievanceAcknowledge,
    GrievanceInvestigate,
    GrievanceResolve,
    GrievanceClose,
    GrievanceReopen,
    GrievanceReject,
    GrievanceSubmitFeedback,
)
from src.grievances.deps import (
    get_grievance_by_id,
    check_grievance_view_permission,
    check_grievance_handler_permission,
    check_grievance_assignment_permission,
    get_current_member_from_user,
    require_current_member,
    validate_assignee,
    getGrievancePaginationParams,
)
from src.grievances.crud import (
    GrievanceCRUD,
    GrievanceCategoryCRUD,
    GrievanceWorkflowCRUD,
    GrievanceAssignmentCRUD,
    GrievanceEscalationCRUD,
    GrievanceSLACRUD,
    GrievanceResolutionCRUD,
    GrievanceStatsCRUD,
)


router = APIRouter(prefix="/grievances", tags=["Grievances"])


# =============================================================================
# Health Check
# =============================================================================

@router.get("/health")
async def grievances_health_check():
    """Health check endpoint for grievances service."""
    return {"status": "healthy", "service": "grievances"}


# =============================================================================
# Grievance CRUD
# =============================================================================

@router.get("", response_model=GrievanceListResponse)
async def list_grievances(
    request: Request,
    search: Optional[str] = None,
    status_filter: Optional[List[str]] = Query(None),
    priority: Optional[List[str]] = Query(None),
    category_id: Optional[UUID] = None,
    district: Optional[str] = None,
    constituency: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List/search grievances with filters.
    
    Supports pagination and filtering by various criteria.
    """
    page, limit = getGrievancePaginationParams(page, limit)
    
    filters = GrievanceSearchFilters(
        search=search,
        status=status_filter,
        priority=priority,
        category_id=category_id,
        district=district,
        constituency=constituency,
    )
    
    # Check permissions - if not admin, only show own or assigned
    if not current_user.is_admin() and not current_user.has_permission("grievances:read"):
        filters.submitted_by_id = current_user.member_profile.id if current_user.member_profile else None
    
    grievances, total = await GrievanceCRUD.search(db, filters, page, limit)
    
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    
    return GrievanceListResponse(
        grievances=[GrievanceResponse.model_validate(g) for g in grievances],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.post("", response_model=GrievanceResponse, status_code=status.HTTP_201_CREATED)
async def create_grievance(
    grievance_data: GrievanceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a new grievance.
    
    Creates a new grievance with submitted status.
    """
    member = await get_current_member_from_user(current_user, db)
    member_name = f"{member.first_name} {member.last_name}" if member else "Anonymous"
    member_id = member.id if member else None
    
    try:
        grievance = await GrievanceCRUD.create(
            db,
            grievance_data,
            submitted_by_id=member_id,
            submitted_by_name=member_name,
        )
        return GrievanceResponse.model_validate(grievance)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{grievance_id}", response_model=GrievanceDetailResponse)
async def get_grievance(
    grievance_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get grievance by ID with full details.
    """
    grievance = await GrievanceCRUD.get_by_id(db, grievance_id)
    if not grievance or grievance.is_deleted:
        raise NotFoundError(resource="Grievance", resource_id=str(grievance_id))
    
    # Check view permission
    if not current_user.is_admin() and not current_user.has_permission("grievances:read"):
        if grievance.submitted_by_id != current_user.member_profile.id if current_user.member_profile else None:
            if grievance.current_assignee_id != current_user.member_profile.id if current_user.member_profile else None:
                raise AuthorizationError("You don't have permission to view this grievance")
    
    return GrievanceDetailResponse.model_validate(grievance)


@router.put("/{grievance_id}", response_model=GrievanceResponse)
async def update_grievance(
    grievance_id: UUID,
    grievance_data: GrievanceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a grievance.
    """
    # Check edit permission
    await check_grievance_handler_permission(request=Request(), grievance_id=grievance_id, current_user=current_user, db=db)
    
    try:
        grievance = await GrievanceCRUD.update(db, grievance_id, grievance_data)
        if not grievance:
            raise NotFoundError(resource="Grievance", resource_id=str(grievance_id))
        return GrievanceResponse.model_validate(grievance)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{grievance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_grievance(
    grievance_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a grievance (soft delete).
    """
    # Check delete permission
    await check_grievance_handler_permission(request=Request(), grievance_id=grievance_id, current_user=current_user, db=db)
    
    success = await GrievanceCRUD.soft_delete(db, grievance_id)
    if not success:
        raise NotFoundError(resource="Grievance", resource_id=str(grievance_id))


# =============================================================================
# Workflow Actions
# =============================================================================

@router.post("/{grievance_id}/acknowledge", response_model=GrievanceResponse)
async def acknowledge_grievance(
    grievance_id: UUID,
    action: GrievanceAcknowledge = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Acknowledge a submitted grievance.
    """
    await check_grievance_handler_permission(request=Request(), grievance_id=grievance_id, current_user=current_user, db=db)
    
    member = await get_current_member_from_user(current_user, db)
    member_name = f"{member.first_name} {member.last_name}" if member else "Unknown"
    
    grievance = await GrievanceWorkflowCRUD.acknowledge(
        db,
        grievance_id,
        acknowledged_by_id=member.id if member else None,
        acknowledged_by_name=member_name,
        notes=action.notes if action else None,
    )
    if not grievance:
        raise NotFoundError(resource="Grievance", resource_id=str(grievance_id))
    
    return GrievanceResponse.model_validate(grievance)


@router.post("/{grievance_id}/investigate", response_model=GrievanceResponse)
async def start_investigation(
    grievance_id: UUID,
    action: GrievanceInvestigate = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start investigation on a grievance.
    """
    await check_grievance_handler_permission(request=Request(), grievance_id=grievance_id, current_user=current_user, db=db)
    
    member = await get_current_member_from_user(current_user, db)
    member_name = f"{member.first_name} {member.last_name}" if member else "Unknown"
    
    grievance = await GrievanceWorkflowCRUD.start_investigation(
        db,
        grievance_id,
        investigated_by_id=member.id if member else None,
        investigated_by_name=member_name,
        notes=action.notes if action else None,
    )
    if not grievance:
        raise NotFoundError(resource="Grievance", resource_id=str(grievance_id))
    
    return GrievanceResponse.model_validate(grievance)


@router.post("/{grievance_id}/resolve", response_model=GrievanceResponse)
async def resolve_grievance(
    grievance_id: UUID,
    action: GrievanceResolve,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Resolve a grievance.
    """
    await check_grievance_handler_permission(request=Request(), grievance_id=grievance_id, current_user=current_user, db=db)
    
    member = await require_current_member(current_user, db)
    member_name = f"{member.first_name} {member.last_name}"
    
    grievance = await GrievanceWorkflowCRUD.resolve(
        db,
        grievance_id,
        resolved_by_id=member.id,
        resolved_by_name=member_name,
        resolution_summary=action.resolution_summary,
        resolution_template_id=action.resolution_template_id,
        action_taken=action.action_taken,
        notes=action.notes,
        follow_up_required=action.follow_up_required,
        follow_up_date=action.follow_up_date,
    )
    if not grievance:
        raise NotFoundError(resource="Grievance", resource_id=str(grievance_id))
    
    return GrievanceResponse.model_validate(grievance)


@router.post("/{grievance_id}/close", response_model=GrievanceResponse)
async def close_grievance(
    grievance_id: UUID,
    action: GrievanceClose = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Close a resolved grievance.
    """
    await check_grievance_handler_permission(request=Request(), grievance_id=grievance_id, current_user=current_user, db=db)
    
    member = await get_current_member_from_user(current_user, db)
    member_name = f"{member.first_name} {member.last_name}" if member else "Unknown"
    
    grievance = await GrievanceWorkflowCRUD.close(
        db,
        grievance_id,
        closed_by_id=member.id if member else None,
        closed_by_name=member_name,
        notes=action.notes if action else None,
    )
    if not grievance:
        raise NotFoundError(resource="Grievance", resource_id=str(grievance_id))
    
    return GrievanceResponse.model_validate(grievance)


@router.post("/{grievance_id}/reopen", response_model=GrievanceResponse)
async def reopen_grievance(
    grievance_id: UUID,
    action: GrievanceReopen,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Reopen a closed/resolved grievance.
    """
    await check_grievance_handler_permission(request=Request(), grievance_id=grievance_id, current_user=current_user, db=db)
    
    member = await get_current_member_from_user(current_user, db)
    member_name = f"{member.first_name} {member.last_name}" if member else "Unknown"
    
    grievance = await GrievanceWorkflowCRUD.reopen(
        db,
        grievance_id,
        reopened_by_id=member.id if member else None,
        reopened_by_name=member_name,
        reason=action.reason,
        notes=action.notes,
    )
    if not grievance:
        raise NotFoundError(resource="Grievance", resource_id=str(grievance_id))
    
    return GrievanceResponse.model_validate(grievance)


@router.post("/{grievance_id}/reject", response_model=GrievanceResponse)
async def reject_grievance(
    grievance_id: UUID,
    action: GrievanceReject,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Reject a grievance.
    """
    await check_grievance_handler_permission(request=Request(), grievance_id=grievance_id, current_user=current_user, db=db)
    
    member = await get_current_member_from_user(current_user, db)
    member_name = f"{member.first_name} {member.last_name}" if member else "Unknown"
    
    grievance = await GrievanceWorkflowCRUD.reject(
        db,
        grievance_id,
        rejected_by_id=member.id if member else None,
        rejected_by_name=member_name,
        reason=action.reason,
        notes=action.notes,
    )
    if not grievance:
        raise NotFoundError(resource="Grievance", resource_id=str(grievance_id))
    
    return GrievanceResponse.model_validate(grievance)


@router.post("/{grievance_id}/feedback", response_model=GrievanceResponse)
async def submit_feedback(
    grievance_id: UUID,
    feedback: GrievanceSubmitFeedback,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit feedback/rating for a resolved grievance.
    """
    grievance = await GrievanceCRUD.get_by_id(db, grievance_id)
    if not grievance or grievance.is_deleted:
        raise NotFoundError(resource="Grievance", resource_id=str(grievance_id))
    
    # Only the submitter can provide feedback
    member_profile = current_user.member_profile
    if member_profile is None or grievance.submitted_by_id != member_profile.id:
        raise AuthorizationError("Only the submitter can provide feedback")
    
    grievance.submitter_rating = feedback.rating
    
    # Get resolution and add feedback
    resolutions = await GrievanceResolutionCRUD.get_by_grievance_id(db, grievance_id)
    if resolutions:
        await GrievanceResolutionCRUD.add_feedback(
            db,
            resolutions[0].id,
            rating=feedback.rating,
            feedback=feedback.feedback,
        )
    
    await db.commit()
    await db.refresh(grievance)
    
    return GrievanceResponse.model_validate(grievance)


# =============================================================================
# Assignment Actions
# =============================================================================

@router.post("/{grievance_id}/assign", response_model=GrievanceResponse)
async def assign_grievance(
    grievance_id: UUID,
    assignment: GrievanceAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Assign a grievance to a handler.
    """
    await check_grievance_assignment_permission(request=Request(), grievance_id=grievance_id, current_user=current_user, db=db)
    
    # Validate assignee
    assignee = await validate_assignee(assignment.assignee_id, db)
    assignee_name = f"{assignee.first_name} {assignee.last_name}"
    
    member = await get_current_member_from_user(current_user, db)
    member_name = f"{member.first_name} {member.last_name}" if member else "Unknown"
    
    grievance = await GrievanceAssignmentCRUD.assign(
        db,
        grievance_id,
        assignee_id=assignment.assignee_id,
        assignee_name=assignee_name,
        assigned_by_id=member.id if member else None,
        assigned_by_name=member_name,
        assignment_type=assignment.assignment_type,
        reason=assignment.reason,
        notes=assignment.notes,
    )
    if not grievance:
        raise NotFoundError(resource="Grievance", resource_id=str(grievance_id))
    
    return GrievanceResponse.model_validate(grievance)


@router.post("/{grievance_id}/claim", response_model=GrievanceResponse)
async def claim_grievance(
    grievance_id: UUID,
    claim: GrievanceAssignmentClaim = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Claim a grievance for self.
    """
    member = await require_current_member(current_user, db)
    
    grievance = await GrievanceAssignmentCRUD.claim(
        db,
        grievance_id,
        claimer_id=member.id,
        claimer_name=f"{member.first_name} {member.last_name}",
        notes=claim.notes if claim else None,
    )
    if not grievance:
        raise NotFoundError(resource="Grievance", resource_id=str(grievance_id))
    
    return GrievanceResponse.model_validate(grievance)


@router.post("/{grievance_id}/unassign", response_model=GrievanceResponse)
async def unassign_grievance(
    grievance_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Unassign a grievance.
    """
    await check_grievance_assignment_permission(request=Request(), grievance_id=grievance_id, current_user=current_user, db=db)
    
    member = await get_current_member_from_user(current_user, db)
    member_name = f"{member.first_name} {member.last_name}" if member else "Unknown"
    
    grievance = await GrievanceAssignmentCRUD.unassign(
        db,
        grievance_id,
        unassigned_by_id=member.id if member else None,
        unassigned_by_name=member_name,
    )
    if not grievance:
        raise NotFoundError(resource="Grievance", resource_id=str(grievance_id))
    
    return GrievanceResponse.model_validate(grievance)


@router.get("/{grievance_id}/assignments", response_model=GrievanceAssignmentHistoryResponse)
async def get_assignment_history(
    grievance_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get assignment history for a grievance.
    """
    await check_grievance_view_permission(request=Request(), grievance_id=grievance_id, current_user=current_user, db=db)
    
    current_assignment, assignments = await GrievanceAssignmentCRUD.get_history(db, grievance_id)
    
    return GrievanceAssignmentHistoryResponse(
        grievance_id=grievance_id,
        current_assignment=GrievanceAssignmentResponse.model_validate(current_assignment) if current_assignment else None,
        history=[GrievanceAssignmentResponse.model_validate(a) for a in assignments],
    )


# =============================================================================
# Escalation Actions
# =============================================================================

@router.post("/{grievance_id}/escalate", response_model=GrievanceResponse)
async def escalate_grievance(
    grievance_id: UUID,
    escalation: GrievanceEscalationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Escalate a grievance to a higher level.
    """
    await check_grievance_handler_permission(request=Request(), grievance_id=grievance_id, current_user=current_user, db=db)
    
    # Validate escalate_to user
    escalate_to = await validate_assignee(escalation.escalated_to_id, db)
    escalate_to_name = f"{escalate_to.first_name} {escalate_to.last_name}"
    
    member = await get_current_member_from_user(current_user, db)
    member_name = f"{member.first_name} {member.last_name}" if member else "Unknown"
    
    grievance = await GrievanceEscalationCRUD.escalate(
        db,
        grievance_id,
        escalated_to_id=escalation.escalated_to_id,
        escalated_to_name=escalate_to_name,
        escalation_level=escalation.escalation_level,
        escalation_reason=escalation.escalation_reason,
        escalated_from_id=member.id if member else None,
        escalated_from_name=member_name,
        trigger_type=escalation.trigger_type,
        trigger_notes=escalation.trigger_notes,
    )
    if not grievance:
        raise NotFoundError(resource="Grievance", resource_id=str(grievance_id))
    
    return GrievanceResponse.model_validate(grievance)


@router.get("/{grievance_id}/escalations", response_model=List[GrievanceEscalationResponse])
async def get_escalation_history(
    grievance_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get escalation history for a grievance.
    """
    await check_grievance_view_permission(request=Request(), grievance_id=grievance_id, current_user=current_user, db=db)
    
    escalations = await GrievanceEscalationCRUD.get_history(db, grievance_id)
    return [GrievanceEscalationResponse.model_validate(e) for e in escalations]


# =============================================================================
# SLA Actions
# =============================================================================

@router.get("/{grievance_id}/sla", response_model=GrievanceSLAResponse)
async def get_sla_info(
    grievance_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get SLA information for a grievance.
    """
    await check_grievance_view_permission(request=Request(), grievance_id=grievance_id, current_user=current_user, db=db)
    
    grievance = await GrievanceCRUD.get_by_id(db, grievance_id)
    if not grievance:
        raise NotFoundError(resource="Grievance", resource_id=str(grievance_id))
    
    if not grievance.sla:
        raise NotFoundError(resource="SLA", resource_id=f"grievance:{grievance_id}")
    
    return GrievanceSLAResponse.model_validate(grievance.sla)


@router.get("/{grievance_id}/sla/status")
async def get_sla_status(
    grievance_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get SLA status (overdue/pending) for a grievance.
    """
    await check_grievance_view_permission(request=Request(), grievance_id=grievance_id, current_user=current_user, db=db)
    
    grievance = await GrievanceCRUD.get_by_id(db, grievance_id)
    if not grievance:
        raise NotFoundError(resource="Grievance", resource_id=str(grievance_id))
    
    if not grievance.sla:
        raise NotFoundError(resource="SLA", resource_id=f"grievance:{grievance_id}")
    
    now = datetime.now(timezone.utc)
    sla = grievance.sla
    
    # Calculate status
    is_overdue = now > sla.resolution_due_at and grievance.status not in ["closed", "resolved"]
    
    response_status = "met" if sla.responded_at and sla.response_sla_met else (
        "pending" if not sla.responded_at else "breached"
    )
    resolution_status = "met" if sla.resolved_at and sla.resolution_sla_met else (
        "pending" if not sla.resolved_at else "breached"
    )
    
    response_remaining = None
    if not sla.responded_at:
        remaining = (sla.response_due_at - now).total_seconds() / 3600
        response_remaining = max(0, remaining)
    
    resolution_remaining = None
    if not sla.resolved_at:
        remaining = (sla.resolution_due_at - now).total_seconds() / 3600
        resolution_remaining = max(0, remaining)
    
    return GrievanceSLAStatus(
        is_overdue=is_overdue,
        response_status=response_status,
        resolution_status=resolution_status,
        response_time_remaining_hours=response_remaining,
        resolution_time_remaining_hours=resolution_remaining,
    )


# =============================================================================
# Resolution Actions
# =============================================================================

@router.get("/{grievance_id}/resolutions", response_model=List[GrievanceResolutionResponse])
async def get_resolutions(
    grievance_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all resolutions for a grievance.
    """
    await check_grievance_view_permission(request=Request(), grievance_id=grievance_id, current_user=current_user, db=db)
    
    resolutions = await GrievanceResolutionCRUD.get_by_grievance_id(db, grievance_id)
    return [GrievanceResolutionResponse.model_validate(r) for r in resolutions]


@router.get("/resolutions/templates", response_model=List[GrievanceResolutionResponse])
async def get_resolution_templates(
    category_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get resolution templates.
    """
    if not current_user.is_admin() and not current_user.has_permission("grievances:write"):
        raise AuthorizationError("You don't have permission to view resolution templates")
    
    templates = await GrievanceResolutionCRUD.get_templates(db, category_id)
    return [GrievanceResolutionResponse.model_validate(t) for t in templates]


# =============================================================================
# Categories
# =============================================================================

@router.get("/categories", response_model=GrievanceCategoryListResponse)
async def list_categories(
    category_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all active grievance categories.
    """
    if category_type:
        categories = await GrievanceCategoryCRUD.get_by_type(db, category_type)
    else:
        categories = await GrievanceCategoryCRUD.get_all_active(db)
    
    return GrievanceCategoryListResponse(
        categories=[GrievanceCategoryResponse.model_validate(c) for c in categories],
        total=len(categories),
    )


@router.post("/categories", response_model=GrievanceCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: GrievanceCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new grievance category.
    """
    if not current_user.is_admin() and not current_user.has_permission("grievances:admin"):
        raise AuthorizationError("You don't have permission to create categories")
    
    category = await GrievanceCategoryCRUD.create(db, category_data.model_dump())
    return GrievanceCategoryResponse.model_validate(category)


@router.get("/categories/{category_id}", response_model=GrievanceCategoryResponse)
async def get_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a grievance category by ID.
    """
    category = await GrievanceCategoryCRUD.get_by_id(db, category_id)
    if not category:
        raise NotFoundError(resource="GrievanceCategory", resource_id=str(category_id))
    
    return GrievanceCategoryResponse.model_validate(category)


@router.put("/categories/{category_id}", response_model=GrievanceCategoryResponse)
async def update_category(
    category_id: UUID,
    category_data: GrievanceCategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a grievance category.
    """
    if not current_user.is_admin() and not current_user.has_permission("grievances:admin"):
        raise AuthorizationError("You don't have permission to update categories")
    
    category = await GrievanceCategoryCRUD.update(db, category_id, category_data.model_dump(exclude_unset=True))
    if not category:
        raise NotFoundError(resource="GrievanceCategory", resource_id=str(category_id))
    
    return GrievanceCategoryResponse.model_validate(category)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Deactivate a grievance category.
    """
    if not current_user.is_admin() and not current_user.has_permission("grievances:admin"):
        raise AuthorizationError("You don't have permission to deactivate categories")
    
    success = await GrievanceCategoryCRUD.deactivate(db, category_id)
    if not success:
        raise NotFoundError(resource="GrievanceCategory", resource_id=str(category_id))


# =============================================================================
# My Grievances
# =============================================================================

@router.get("/my", response_model=GrievanceListResponse)
async def get_my_grievances(
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get grievances submitted by the current user.
    """
    member = await get_current_member_from_user(current_user, db)
    if not member:
        raise AuthorizationError("You need to have a member profile to view your grievances")
    
    page, limit = getGrievancePaginationParams(page, limit)
    
    grievances, total = await GrievanceCRUD.get_by_submitter(db, member.id, page, limit)
    
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    
    return GrievanceListResponse(
        grievances=[GrievanceResponse.model_validate(g) for g in grievances],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.get("/assigned", response_model=GrievanceListResponse)
async def get_assigned_grievances(
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get grievances assigned to the current user.
    """
    member = await get_current_member_from_user(current_user, db)
    if not member:
        raise AuthorizationError("You need to have a member profile to view assigned grievances")
    
    page, limit = getGrievancePaginationParams(page, limit)
    
    grievances, total = await GrievanceCRUD.get_by_assignee(db, member.id, page, limit)
    
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    
    return GrievanceListResponse(
        grievances=[GrievanceResponse.model_validate(g) for g in grievances],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


# =============================================================================
# Overdue Grievances
# =============================================================================

@router.get("/overdue", response_model=GrievanceListResponse)
async def get_overdue_grievances(
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get overdue grievances.
    """
    if not current_user.is_admin() and not current_user.has_permission("grievances:read"):
        raise AuthorizationError("You don't have permission to view overdue grievances")
    
    page, limit = getGrievancePaginationParams(page, limit)
    
    grievances, total = await GrievanceCRUD.get_overdue(db, page, limit)
    
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    
    return GrievanceListResponse(
        grievances=[GrievanceResponse.model_validate(g) for g in grievances],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


# =============================================================================
# Statistics
# =============================================================================

@router.get("/stats", response_model=GrievanceStatsResponse)
async def get_grievance_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get grievance statistics.
    """
    if not current_user.is_admin() and not current_user.has_permission("grievances:read"):
        raise AuthorizationError("You don't have permission to view statistics")
    
    stats_data = await GrievanceStatsCRUD.get_stats(db)
    return GrievanceStatsResponse(
        stats=GrievanceStats(**stats_data),
        generated_at=datetime.now(timezone.utc),
    )


# =============================================================================
# Dashboard
# =============================================================================

@router.get("/dashboard", response_model=GrievanceDashboardResponse)
async def get_grievance_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get grievance dashboard data.
    """
    member = await get_current_member_from_user(current_user, db)
    member_id = member.id if member else None
    
    dashboard_data = await GrievanceStatsCRUD.get_dashboard(db, member_id)
    return GrievanceDashboardResponse(
        dashboard=GrievanceDashboard(**dashboard_data),
        generated_at=datetime.now(timezone.utc),
    )
