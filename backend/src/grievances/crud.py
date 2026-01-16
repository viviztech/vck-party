"""
Grievance CRUD Operations
CRUD operations for grievances, assignments, escalations, and SLA tracking.
"""

from datetime import datetime, date, timezone, timedelta
from typing import List, Optional, Tuple, Type, TypeVar, Dict, Any
from uuid import UUID
import uuid

from sqlalchemy import select, update, delete, and_, or_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from src.core.exceptions import (
    NotFoundError,
    AlreadyExistsError,
    ValidationError,
    BusinessError,
)
from src.core import redis
from src.grievances.models import (
    Grievance,
    GrievanceCategory,
    GrievanceAssignment,
    GrievanceEscalation,
    GrievanceSLA,
    GrievanceResolution,
    GrievanceStatus,
    GrievancePriority,
    GrievanceCategoryType,
    AssignmentType,
    EscalationLevel,
)
from src.grievances.schemas import (
    GrievanceCreate,
    GrievanceUpdate,
    GrievanceSearchFilters,
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
# Grievance Category CRUD
# =============================================================================

class GrievanceCategoryCRUD(CRUDBase):
    """CRUD operations for grievance categories."""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, category_id: UUID) -> Optional[GrievanceCategory]:
        """Get category by ID."""
        result = await db.execute(
            select(GrievanceCategory)
            .where(GrievanceCategory.id == category_id)
            .where(GrievanceCategory.is_active == True)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_type(db: AsyncSession, category_type: str) -> List[GrievanceCategory]:
        """Get all categories of a specific type."""
        result = await db.execute(
            select(GrievanceCategory)
            .where(GrievanceCategory.category_type == category_type)
            .where(GrievanceCategory.is_active == True)
            .order_by(GrievanceCategory.display_order, GrievanceCategory.name)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_all_active(db: AsyncSession) -> List[GrievanceCategory]:
        """Get all active categories."""
        result = await db.execute(
            select(GrievanceCategory)
            .where(GrievanceCategory.is_active == True)
            .order_by(GrievanceCategory.display_order, GrievanceCategory.name)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def create(db: AsyncSession, category_data: dict) -> GrievanceCategory:
        """Create a new category."""
        category = GrievanceCategory(**category_data)
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category
    
    @staticmethod
    async def update(
        db: AsyncSession,
        category_id: UUID,
        category_data: dict
    ) -> Optional[GrievanceCategory]:
        """Update a category."""
        category = await GrievanceCategoryCRUD.get_by_id(db, category_id)
        if not category:
            return None
        
        for field, value in category_data.items():
            setattr(category, field, value)
        
        await db.commit()
        await db.refresh(category)
        return category
    
    @staticmethod
    async def deactivate(db: AsyncSession, category_id: UUID) -> bool:
        """Deactivate a category."""
        category = await GrievanceCategoryCRUD.get_by_id(db, category_id)
        if not category:
            return False
        
        category.is_active = False
        await db.commit()
        return True


# =============================================================================
# Grievance CRUD
# =============================================================================

class GrievanceCRUD(CRUDBase):
    """CRUD operations for grievances."""
    
    @staticmethod
    async def generate_reference_number(db: AsyncSession) -> str:
        """Generate a unique reference number."""
        year = datetime.now(timezone.utc).year
        prefix = f"GRV{year}"
        
        # Get the latest reference number
        result = await db.execute(
            select(func.max(Grievance.id))
            .where(Grievance.reference_number.like(f"{prefix}%"))
        )
        max_id = result.scalar()
        
        if max_id:
            # Get the sequence number
            result = await db.execute(
                select(Grievance.reference_number)
                .where(Grievance.reference_number.like(f"{prefix}%"))
                .order_by(Grievance.reference_number.desc())
                .limit(1)
            )
            last_number = result.scalar_one_or_none()
            if last_number:
                # Extract sequence number
                seq_str = last_number.replace(prefix, "")
                try:
                    seq = int(seq_str) + 1
                except ValueError:
                    seq = 1
            else:
                seq = 1
        else:
            seq = 1
        
        return f"{prefix}{seq:06d}"
    
    @staticmethod
    async def get_by_id(db: AsyncSession, grievance_id: UUID) -> Optional[Grievance]:
        """Get grievance by ID with relationships."""
        result = await db.execute(
            select(Grievance)
            .where(Grievance.id == grievance_id)
            .where(Grievance.is_deleted == False)
            .options(
                selectinload(Grievance.category),
                selectinload(Grievance.assignments),
                selectinload(Grievance.sla),
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(
        db: AsyncSession,
        grievance_data: GrievanceCreate,
        submitted_by_id: UUID = None,
        submitted_by_name: str = None
    ) -> Grievance:
        """Create a new grievance."""
        # Generate reference number
        reference_number = await GrievanceCRUD.generate_reference_number(db)
        
        # Get category for SLA settings
        category = None
        if grievance_data.category_id:
            category = await GrievanceCategoryCRUD.get_by_id(db, grievance_data.category_id)
        
        # Determine priority
        priority = grievance_data.priority or (
            category.default_priority if category else GrievancePriority.MEDIUM.value
        )
        
        grievance = Grievance(
            reference_number=reference_number,
            submitted_by_id=submitted_by_id,
            submitted_by_name=submitted_by_name or "Anonymous",
            contact_phone=grievance_data.contact_phone,
            contact_email=grievance_data.contact_email,
            preferred_contact=grievance_data.preferred_contact,
            category_id=grievance_data.category_id,
            priority=priority,
            subject=grievance_data.subject,
            description=grievance_data.description,
            district=grievance_data.district,
            constituency=grievance_data.constituency,
            ward=grievance_data.ward,
            specific_location=grievance_data.specific_location,
            related_member_id=grievance_data.related_member_id,
            related_event_id=grievance_data.related_event_id,
            attachments=grievance_data.attachments or [],
            is_anonymous=grievance_data.is_anonymous or False,
            is_confidential=grievance_data.is_confidential or False,
            status=GrievanceStatus.SUBMITTED.value,
        )
        
        db.add(grievance)
        await db.commit()
        await db.refresh(grievance)
        
        # Create SLA record if category exists
        if category:
            await GrievanceSLACRUD.create_for_grievance(db, grievance, category)
        
        # Cache the grievance
        await redis.cache_grievance(grievance.id, grievance)
        
        return grievance
    
    @staticmethod
    async def update(
        db: AsyncSession,
        grievance_id: UUID,
        grievance_data: GrievanceUpdate
    ) -> Optional[Grievance]:
        """Update a grievance."""
        grievance = await GrievanceCRUD.get_by_id(db, grievance_id)
        if not grievance:
            return None
        
        update_data = grievance_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(grievance, field, value)
        
        await db.commit()
        await db.refresh(grievance)
        
        # Update cache
        await redis.cache_grievance(grievance_id, grievance)
        
        return grievance
    
    @staticmethod
    async def search(
        db: AsyncSession,
        filters: GrievanceSearchFilters,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Grievance], int]:
        """Search grievances with filters."""
        query = (
            select(Grievance)
            .where(Grievance.is_deleted == False)
            .options(selectinload(Grievance.category))
        )
        
        # Text search
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    Grievance.subject.ilike(search_term),
                    Grievance.description.ilike(search_term),
                    Grievance.reference_number.ilike(search_term),
                )
            )
        
        # Status filter
        if filters.status:
            query = query.where(Grievance.status.in_(filters.status))
        
        # Priority filter
        if filters.priority:
            query = query.where(Grievance.priority.in_(filters.priority))
        
        # Category filter
        if filters.category_id:
            query = query.where(Grievance.category_id == filters.category_id)
        
        # Category type filter
        if filters.category_type:
            query = query.join(GrievanceCategory).where(
                GrievanceCategory.category_type == filters.category_type
            )
        
        # Location filters
        if filters.district:
            query = query.where(Grievance.district == filters.district)
        if filters.constituency:
            query = query.where(Grievance.constituency == filters.constituency)
        
        # Submitter filter
        if filters.submitted_by_id:
            query = query.where(Grievance.submitted_by_id == filters.submitted_by_id)
        
        # Assignee filter
        if filters.assignee_id:
            query = query.where(Grievance.current_assignee_id == filters.assignee_id)
        
        # Anonymous/Confidential filters
        if filters.is_anonymous is not None:
            query = query.where(Grievance.is_anonymous == filters.is_anonymous)
        if filters.is_confidential is not None:
            query = query.where(Grievance.is_confidential == filters.is_confidential)
        
        # Date range filters
        if filters.from_date:
            query = query.where(Grievance.submitted_at >= filters.from_date)
        if filters.to_date:
            query = query.where(Grievance.submitted_at <= filters.to_date)
        
        # Overdue filter
        if filters.overdue:
            query = query.join(GrievanceSLA).where(
                and_(
                    GrievanceSLA.resolution_due_at < datetime.now(timezone.utc),
                    Grievance.status.notin_([
                        GrievanceStatus.CLOSED.value,
                        GrievanceStatus.RESOLVED.value,
                    ])
                )
            )
        
        # Get total count
        count_query = select(func.count(Grievance.id)).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit).order_by(Grievance.created_at.desc())
        
        result = await db.execute(query)
        grievances = list(result.scalars().all())
        
        return grievances, total
    
    @staticmethod
    async def get_by_submitter(
        db: AsyncSession,
        submitter_id: UUID,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Grievance], int]:
        """Get grievances submitted by a member."""
        query = (
            select(Grievance)
            .where(Grievance.submitted_by_id == submitter_id)
            .where(Grievance.is_deleted == False)
            .options(selectinload(Grievance.category))
        )
        
        count_query = select(func.count(Grievance.id)).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit).order_by(Grievance.created_at.desc())
        
        result = await db.execute(query)
        grievances = list(result.scalars().all())
        
        return grievances, total
    
    @staticmethod
    async def get_by_assignee(
        db: AsyncSession,
        assignee_id: UUID,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Grievance], int]:
        """Get grievances assigned to a handler."""
        query = (
            select(Grievance)
            .where(Grievance.current_assignee_id == assignee_id)
            .where(Grievance.is_deleted == False)
            .options(selectinload(Grievance.category))
        )
        
        count_query = select(func.count(Grievance.id)).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit).order_by(Grievance.created_at.desc())
        
        result = await db.execute(query)
        grievances = list(result.scalars().all())
        
        return grievances, total
    
    @staticmethod
    async def get_overdue(
        db: AsyncSession,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Grievance], int]:
        """Get overdue grievances."""
        query = (
            select(Grievance)
            .join(GrievanceSLA, Grievance.id == GrievanceSLA.grievance_id)
            .where(Grievance.is_deleted == False)
            .where(
                and_(
                    GrievanceSLA.resolution_due_at < datetime.now(timezone.utc),
                    Grievance.status.notin_([
                        GrievanceStatus.CLOSED.value,
                        GrievanceStatus.RESOLVED.value,
                    ])
                )
            )
            .options(selectinload(Grievance.category))
        )
        
        count_query = select(func.count(Grievance.id)).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit).order_by(GrievanceSLA.resolution_due_at.asc())
        
        result = await db.execute(query)
        grievances = list(result.scalars().all())
        
        return grievances, total
    
    @staticmethod
    async def soft_delete(db: AsyncSession, grievance_id: UUID) -> bool:
        """Soft delete a grievance."""
        grievance = await GrievanceCRUD.get_by_id(db, grievance_id)
        if not grievance:
            return False
        
        grievance.is_deleted = True
        grievance.deleted_at = datetime.now(timezone.utc)
        
        await db.commit()
        
        # Remove from cache
        await redis.delete_grievance_cache(grievance_id)
        
        return True


# =============================================================================
# Grievance Workflow CRUD
# =============================================================================

class GrievanceWorkflowCRUD:
    """Workflow operations for grievances."""
    
    @staticmethod
    async def acknowledge(
        db: AsyncSession,
        grievance_id: UUID,
        acknowledged_by_id: UUID = None,
        acknowledged_by_name: str = None,
        notes: str = None
    ) -> Optional[Grievance]:
        """Acknowledge a grievance."""
        grievance = await GrievanceCRUD.get_by_id(db, grievance_id)
        if not grievance:
            return None
        
        if grievance.status != GrievanceStatus.SUBMITTED.value:
            raise BusinessError(
                message="Can only acknowledge submitted grievances",
                code="INVALID_STATUS"
            )
        
        grievance.status = GrievanceStatus.ACKNOWLEDGED.value
        grievance.acknowledged_at = datetime.now(timezone.utc)
        
        if notes:
            existing_notes = grievance.internal_notes or ""
            grievance.internal_notes = f"{existing_notes}\n[Acknowledged by {acknowledged_by_name}]: {notes}".strip()
        
        await db.commit()
        await db.refresh(grievance)
        
        # Update cache
        await redis.cache_grievance(grievance_id, grievance)
        
        return grievance
    
    @staticmethod
    async def start_investigation(
        db: AsyncSession,
        grievance_id: UUID,
        investigated_by_id: UUID = None,
        investigated_by_name: str = None,
        notes: str = None
    ) -> Optional[Grievance]:
        """Start investigation on a grievance."""
        grievance = await GrievanceCRUD.get_by_id(db, grievance_id)
        if not grievance:
            return None
        
        valid_statuses = [
            GrievanceStatus.SUBMITTED.value,
            GrievanceStatus.ACKNOWLEDGED.value,
        ]
        if grievance.status not in valid_statuses:
            raise BusinessError(
                message=f"Cannot start investigation from status: {grievance.status}",
                code="INVALID_STATUS"
            )
        
        grievance.status = GrievanceStatus.UNDER_INVESTIGATION.value
        grievance.investigation_started_at = datetime.now(timezone.utc)
        
        if notes:
            existing_notes = grievance.internal_notes or ""
            grievance.internal_notes = f"{existing_notes}\n[Investigation started by {investigated_by_name}]: {notes}".strip()
        
        await db.commit()
        await db.refresh(grievance)
        
        # Update cache
        await redis.cache_grievance(grievance_id, grievance)
        
        return grievance
    
    @staticmethod
    async def resolve(
        db: AsyncSession,
        grievance_id: UUID,
        resolved_by_id: UUID,
        resolved_by_name: str,
        resolution_summary: str,
        resolution_template_id: UUID = None,
        action_taken: str = None,
        notes: str = None,
        follow_up_required: bool = False,
        follow_up_date: datetime = None
    ) -> Optional[Grievance]:
        """Resolve a grievance."""
        grievance = await GrievanceCRUD.get_by_id(db, grievance_id)
        if not grievance:
            return None
        
        valid_statuses = [
            GrievanceStatus.ACKNOWLEDGED.value,
            GrievanceStatus.UNDER_INVESTIGATION.value,
            GrievanceStatus.PENDING_ACTION.value,
            GrievanceStatus.REOPENED.value,
        ]
        if grievance.status not in valid_statuses:
            raise BusinessError(
                message=f"Cannot resolve from status: {grievance.status}",
                code="INVALID_STATUS"
            )
        
        # Create resolution record
        resolution = GrievanceResolution(
            grievance_id=grievance_id,
            title=f"Resolution: {grievance.subject[:100]}",
            description=resolution_summary,
            resolution_type="resolution",
            resolved_by_id=resolved_by_id,
            resolved_by_name=resolved_by_name,
            action_taken=action_taken,
            follow_up_required=follow_up_required,
            follow_up_date=follow_up_date,
            handler_notes=notes,
        )
        db.add(resolution)
        
        # Update grievance
        grievance.status = GrievanceStatus.RESOLVED.value
        grievance.resolved_at = datetime.now(timezone.utc)
        grievance.resolution_summary = resolution_summary
        grievance.resolution_template_id = resolution_template_id
        
        if notes:
            existing_notes = grievance.internal_notes or ""
            grievance.internal_notes = f"{existing_notes}\n[Resolved by {resolved_by_name}]: {notes}".strip()
        
        # Update SLA
        if grievance.sla:
            grievance.sla.resolved_at = datetime.now(timezone.utc)
            # Calculate SLA met
            now = datetime.now(timezone.utc)
            grievance.sla.resolution_sla_met = now <= grievance.sla.resolution_due_at
        
        await db.commit()
        await db.refresh(grievance)
        
        # Update cache
        await redis.cache_grievance(grievance_id, grievance)
        
        return grievance
    
    @staticmethod
    async def close(
        db: AsyncSession,
        grievance_id: UUID,
        closed_by_id: UUID = None,
        closed_by_name: str = None,
        notes: str = None
    ) -> Optional[Grievance]:
        """Close a grievance."""
        grievance = await GrievanceCRUD.get_by_id(db, grievance_id)
        if not grievance:
            return None
        
        if grievance.status != GrievanceStatus.RESOLVED.value:
            raise BusinessError(
                message="Can only close resolved grievances",
                code="INVALID_STATUS"
            )
        
        grievance.status = GrievanceStatus.CLOSED.value
        grievance.closed_at = datetime.now(timezone.utc)
        
        if notes:
            existing_notes = grievance.internal_notes or ""
            grievance.internal_notes = f"{existing_notes}\n[Closed by {closed_by_name}]: {notes}".strip()
        
        await db.commit()
        await db.refresh(grievance)
        
        # Update cache
        await redis.cache_grievance(grievance_id, grievance)
        
        return grievance
    
    @staticmethod
    async def reopen(
        db: AsyncSession,
        grievance_id: UUID,
        reopened_by_id: UUID = None,
        reopened_by_name: str = None,
        reason: str = None,
        notes: str = None
    ) -> Optional[Grievance]:
        """Reopen a closed grievance."""
        grievance = await GrievanceCRUD.get_by_id(db, grievance_id)
        if not grievance:
            return None
        
        if grievance.status not in [GrievanceStatus.RESOLVED.value, GrievanceStatus.CLOSED.value]:
            raise BusinessError(
                message="Can only reopen resolved or closed grievances",
                code="INVALID_STATUS"
            )
        
        grievance.status = GrievanceStatus.REOPENED.value
        
        if notes or reason:
            existing_notes = grievance.internal_notes or ""
            note_text = f"[Reopened by {reopened_by_name}]"
            if reason:
                note_text += f" Reason: {reason}"
            if notes:
                note_text += f" Notes: {notes}"
            grievance.internal_notes = f"{existing_notes}\n{note_text}".strip()
        
        await db.commit()
        await db.refresh(grievance)
        
        # Update cache
        await redis.cache_grievance(grievance_id, grievance)
        
        return grievance
    
    @staticmethod
    async def reject(
        db: AsyncSession,
        grievance_id: UUID,
        rejected_by_id: UUID = None,
        rejected_by_name: str = None,
        reason: str = None,
        notes: str = None
    ) -> Optional[Grievance]:
        """Reject a grievance."""
        grievance = await GrievanceCRUD.get_by_id(db, grievance_id)
        if not grievance:
            return None
        
        valid_statuses = [
            GrievanceStatus.SUBMITTED.value,
            GrievanceStatus.ACKNOWLEDGED.value,
        ]
        if grievance.status not in valid_statuses:
            raise BusinessError(
                message=f"Cannot reject from status: {grievance.status}",
                code="INVALID_STATUS"
            )
        
        grievance.status = GrievanceStatus.REJECTED.value
        
        note_text = f"[Rejected by {reopened_by_name}]"
        if reason:
            note_text += f" Reason: {reason}"
        if notes:
            note_text += f" Notes: {notes}"
        
        existing_notes = grievance.internal_notes or ""
        grievance.internal_notes = f"{existing_notes}\n{note_text}".strip()
        
        await db.commit()
        await db.refresh(grievance)
        
        # Update cache
        await redis.cache_grievance(grievance_id, grievance)
        
        return grievance


# =============================================================================
# Grievance Assignment CRUD
# =============================================================================

class GrievanceAssignmentCRUD(CRUDBase):
    """CRUD operations for grievance assignments."""
    
    @staticmethod
    async def assign(
        db: AsyncSession,
        grievance_id: UUID,
        assignee_id: UUID,
        assignee_name: str,
        assigned_by_id: UUID = None,
        assigned_by_name: str = None,
        assignment_type: str = AssignmentType.DIRECT.value,
        reason: str = None,
        notes: str = None
    ) -> Optional[Grievance]:
        """Assign a grievance to a handler."""
        grievance = await GrievanceCRUD.get_by_id(db, grievance_id)
        if not grievance:
            return None
        
        # Get previous assignee
        previous_assignee_id = grievance.current_assignee_id
        previous_assignee_name = grievance.current_assignee_name
        
        # Update previous assignment to not current
        if previous_assignee_id:
            await db.execute(
                update(GrievanceAssignment)
                .where(
                    and_(
                        GrievanceAssignment.grievance_id == grievance_id,
                        GrievanceAssignment.assignee_id == previous_assignee_id,
                        GrievanceAssignment.is_current == True
                    )
                )
                .values(
                    is_current=False,
                    unassigned_at=datetime.now(timezone.utc)
                )
            )
        
        # Create new assignment record
        assignment = GrievanceAssignment(
            grievance_id=grievance_id,
            assignee_id=assignee_id,
            assignee_name=assignee_name,
            assignment_type=assignment_type,
            assigned_by_id=assigned_by_id,
            assigned_by_name=assigned_by_name,
            previous_assignee_id=previous_assignee_id,
            previous_assignee_name=previous_assignee_name,
            reason=reason,
            notes=notes,
            is_current=True,
        )
        db.add(assignment)
        
        # Update grievance
        grievance.current_assignee_id = assignee_id
        grievance.current_assignee_name = assignee_name
        
        await db.commit()
        await db.refresh(grievance)
        
        # Update cache
        await redis.cache_grievance(grievance_id, grievance)
        
        return grievance
    
    @staticmethod
    async def claim(
        db: AsyncSession,
        grievance_id: UUID,
        claimer_id: UUID,
        claimer_name: str,
        notes: str = None
    ) -> Optional[Grievance]:
        """Claim a grievance for self."""
        grievance = await GrievanceCRUD.get_by_id(db, grievance_id)
        if not grievance:
            return None
        
        if grievance.current_assignee_id:
            raise BusinessError(
                message="Grievance is already assigned",
                code="ALREADY_ASSIGNED"
            )
        
        return await GrievanceAssignmentCRUD.assign(
            db=db,
            grievance_id=grievance_id,
            assignee_id=claimer_id,
            assignee_name=claimer_name,
            assigned_by_id=claimer_id,
            assigned_by_name=claimer_name,
            assignment_type=AssignmentType.CLAIMED.value,
            notes=notes
        )
    
    @staticmethod
    async def get_history(
        db: AsyncSession,
        grievance_id: UUID
    ) -> Tuple[Optional[GrievanceAssignment], List[GrievanceAssignment]]:
        """Get assignment history for a grievance."""
        result = await db.execute(
            select(GrievanceAssignment)
            .where(GrievanceAssignment.grievance_id == grievance_id)
            .order_by(GrievanceAssignment.assigned_at.desc())
        )
        assignments = list(result.scalars().all())
        
        current = None
        if assignments:
            current = next((a for a in assignments if a.is_current), None)
            if not current:
                current = assignments[0]
        
        return current, assignments
    
    @staticmethod
    async def unassign(
        db: AsyncSession,
        grievance_id: UUID,
        unassigned_by_id: UUID = None,
        unassigned_by_name: str = None,
        reason: str = None
    ) -> Optional[Grievance]:
        """Unassign a grievance."""
        grievance = await GrievanceCRUD.get_by_id(db, grievance_id)
        if not grievance:
            return None
        
        if not grievance.current_assignee_id:
            return grievance
        
        # Update current assignment
        await db.execute(
            update(GrievanceAssignment)
            .where(
                and_(
                    GrievanceAssignment.grievance_id == grievance_id,
                    GrievanceAssignment.is_current == True
                )
            )
            .values(
                is_current=False,
                unassigned_at=datetime.now(timezone.utc)
            )
        )
        
        # Update grievance
        grievance.current_assignee_id = None
        grievance.current_assignee_name = None
        
        await db.commit()
        await db.refresh(grievance)
        
        # Update cache
        await redis.cache_grievance(grievance_id, grievance)
        
        return grievance


# =============================================================================
# Grievance Escalation CRUD
# =============================================================================

class GrievanceEscalationCRUD(CRUDBase):
    """CRUD operations for grievance escalations."""
    
    @staticmethod
    async def escalate(
        db: AsyncSession,
        grievance_id: UUID,
        escalated_to_id: UUID,
        escalated_to_name: str,
        escalation_level: str,
        escalation_reason: str = None,
        escalated_from_id: UUID = None,
        escalated_from_name: str = None,
        trigger_type: str = "manual",
        trigger_notes: str = None
    ) -> Optional[Grievance]:
        """Escalate a grievance."""
        grievance = await GrievanceCRUD.get_by_id(db, grievance_id)
        if not grievance:
            return None
        
        # Deactivate previous escalations
        await db.execute(
            update(GrievanceEscalation)
            .where(
                and_(
                    GrievanceEscalation.grievance_id == grievance_id,
                    GrievanceEscalation.is_active == True
                )
            )
            .values(is_active=False)
        )
        
        # Create new escalation
        escalation = GrievanceEscalation(
            grievance_id=grievance_id,
            escalation_level=escalation_level,
            escalation_reason=escalation_reason,
            escalated_from_id=escalated_from_id or grievance.current_assignee_id,
            escalated_from_name=escalated_from_name or grievance.current_assignee_name,
            escalated_to_id=escalated_to_id,
            escalated_to_name=escalated_to_name,
            trigger_type=trigger_type,
            trigger_notes=trigger_notes,
            is_active=True,
        )
        db.add(escalation)
        
        # Reassign to new handler
        await GrievanceAssignmentCRUD.assign(
            db=db,
            grievance_id=grievance_id,
            assignee_id=escalated_to_id,
            assignee_name=escalated_to_name,
            assigned_by_id=escalated_from_id or grievance.current_assignee_id,
            assigned_by_name=escalated_from_name or grievance.current_assignee_name,
            assignment_type=AssignmentType.ESCALATED.value,
            reason=f"Escalated: {escalation_reason}"
        )
        
        await db.commit()
        await db.refresh(grievance)
        
        # Update cache
        await redis.cache_grievance(grievance_id, grievance)
        
        return grievance
    
    @staticmethod
    async def get_active_escalation(
        db: AsyncSession,
        grievance_id: UUID
    ) -> Optional[GrievanceEscalation]:
        """Get active escalation for a grievance."""
        result = await db.execute(
            select(GrievanceEscalation)
            .where(
                and_(
                    GrievanceEscalation.grievance_id == grievance_id,
                    GrievanceEscalation.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_history(
        db: AsyncSession,
        grievance_id: UUID
    ) -> List[GrievanceEscalation]:
        """Get escalation history for a grievance."""
        result = await db.execute(
            select(GrievanceEscalation)
            .where(GrievanceEscalation.grievance_id == grievance_id)
            .order_by(GrievanceEscalation.escalated_at.desc())
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def check_and_auto_escalate(
        db: AsyncSession,
        grievance_id: UUID
    ) -> Optional[Grievance]:
        """Check SLA and auto-escalate if breached."""
        grievance = await GrievanceCRUD.get_by_id(db, grievance_id)
        if not grievance or not grievance.sla:
            return None
        
        # Check if response SLA is breached
        now = datetime.now(timezone.utc)
        if (
            grievance.status in [GrievanceStatus.SUBMITTED.value, GrievanceStatus.ACKNOWLEDGED.value]
            and now > grievance.sla.response_due_at
            and grievance.sla.response_breach_count == 0
        ):
            # First breach - increment count
            grievance.sla.response_breach_count += 1
            await db.commit()
            
            # Check if category allows auto-escalation
            if grievance.category and grievance.category.escalation_enabled:
                # Auto-escalate to next level
                # This would typically look up the escalation path
                pass
        
        return grievance


# =============================================================================
# Grievance SLA CRUD
# =============================================================================

class GrievanceSLACRUD(CRUDBase):
    """CRUD operations for grievance SLA."""
    
    @staticmethod
    async def create_for_grievance(
        db: AsyncSession,
        grievance: Grievance,
        category: GrievanceCategory
    ) -> GrievanceSLA:
        """Create SLA record for a grievance based on category."""
        now = datetime.now(timezone.utc)
        
        sla = GrievanceSLA(
            grievance_id=grievance.id,
            response_deadline_hours=category.response_sla_hours,
            resolution_deadline_hours=category.resolution_sla_hours,
            response_due_at=now + timedelta(hours=category.response_sla_hours),
            resolution_due_at=now + timedelta(hours=category.resolution_sla_hours),
        )
        db.add(sla)
        await db.commit()
        await db.refresh(sla)
        
        return sla
    
    @staticmethod
    async def get_by_grievance_id(
        db: AsyncSession,
        grievance_id: UUID
    ) -> Optional[GrievanceSLA]:
        """Get SLA for a grievance."""
        result = await db.execute(
            select(GrievanceSLA)
            .where(GrievanceSLA.grievance_id == grievance_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_deadline(
        db: AsyncSession,
        grievance_id: UUID,
        response_deadline_hours: int = None,
        resolution_deadline_hours: int = None
    ) -> Optional[GrievanceSLA]:
        """Update SLA deadlines."""
        sla = await GrievanceSLACRUD.get_by_grievance_id(db, grievance_id)
        if not sla:
            return None
        
        now = datetime.now(timezone.utc)
        
        if response_deadline_hours:
            sla.response_deadline_hours = response_deadline_hours
            sla.response_due_at = now + timedelta(hours=response_deadline_hours)
        
        if resolution_deadline_hours:
            sla.resolution_deadline_hours = resolution_deadline_hours
            sla.resolution_due_at = now + timedelta(hours=resolution_deadline_hours)
        
        await db.commit()
        await db.refresh(sla)
        
        return sla
    
    @staticmethod
    async def extend_deadline(
        db: AsyncSession,
        grievance_id: UUID,
        hours: int,
        reason: str = None
    ) -> Optional[GrievanceSLA]:
        """Extend SLA deadline."""
        sla = await GrievanceSLACRUD.get_by_grievance_id(db, grievance_id)
        if not sla:
            return None
        
        # Add extension to history
        extension = {
            "extended_at": datetime.now(timezone.utc).isoformat(),
            "hours_added": hours,
            "reason": reason,
        }
        extensions = list(sla.extensions or [])
        extensions.append(extension)
        sla.extensions = extensions
        
        # Extend deadlines
        sla.response_due_at = sla.response_due_at + timedelta(hours=hours)
        sla.resolution_due_at = sla.resolution_due_at + timedelta(hours=hours)
        
        await db.commit()
        await db.refresh(sla)
        
        return sla
    
    @staticmethod
    async def pause_sla(
        db: AsyncSession,
        grievance_id: UUID
    ) -> Optional[GrievanceSLA]:
        """Pause SLA tracking."""
        sla = await GrievanceSLACRUD.get_by_grievance_id(db, grievance_id)
        if not sla or sla.is_on_hold:
            return None
        
        sla.is_on_hold = True
        sla.hold_started_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(sla)
        
        return sla
    
    @staticmethod
    async def resume_sla(
        db: AsyncSession,
        grievance_id: UUID
    ) -> Optional[GrievanceSLA]:
        """Resume SLA tracking."""
        sla = await GrievanceSLACRUD.get_by_grievance_id(db, grievance_id)
        if not sla or not sla.is_on_hold:
            return None
        
        # Calculate hold duration
        hold_duration = datetime.now(timezone.utc) - sla.hold_started_at
        sla.total_hold_duration_hours += hold_duration.total_seconds() / 3600
        sla.is_on_hold = False
        sla.hold_started_at = None
        
        # Extend deadlines by hold duration
        sla.response_due_at = sla.response_due_at + hold_duration
        sla.resolution_due_at = sla.resolution_due_at + hold_duration
        
        await db.commit()
        await db.refresh(sla)
        
        return sla
    
    @staticmethod
    async def check_overdue(
        db: AsyncSession,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Grievance], int]:
        """Get overdue grievances."""
        query = (
            select(Grievance)
            join(GrievanceSLA, Grievance.id == GrievanceSLA.grievance_id)
            .where(Grievance.is_deleted == False)
            .where(
                and_(
                    GrievanceSLA.resolution_due_at < datetime.now(timezone.utc),
                    Grievance.status.notin_([
                        GrievanceStatus.CLOSED.value,
                        GrievanceStatus.RESOLVED.value,
                    ])
                )
            )
        )
        
        count_query = select(func.count(Grievance.id)).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit).order_by(GrievanceSLA.resolution_due_at.asc())
        
        result = await db.execute(query)
        grievances = list(result.scalars().all())
        
        return grievances, total


# =============================================================================
# Grievance Resolution CRUD
# =============================================================================

class GrievanceResolutionCRUD(CRUDBase):
    """CRUD operations for grievance resolutions."""
    
    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        resolution_id: UUID
    ) -> Optional[GrievanceResolution]:
        """Get resolution by ID."""
        result = await db.execute(
            select(GrievanceResolution)
            .where(GrievanceResolution.id == resolution_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_grievance_id(
        db: AsyncSession,
        grievance_id: UUID
    ) -> List[GrievanceResolution]:
        """Get all resolutions for a grievance."""
        result = await db.execute(
            select(GrievanceResolution)
            .where(GrievanceResolution.grievance_id == grievance_id)
            .order_by(GrievanceResolution.created_at.desc())
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_templates(
        db: AsyncSession,
        category_id: UUID = None
    ) -> List[GrievanceResolution]:
        """Get resolution templates."""
        query = select(GrievanceResolution).where(GrievanceResolution.is_template == True)
        
        if category_id:
            query = query.where(
                or_(
                    GrievanceResolution.applicable_category_id == category_id,
                    GrievanceResolution.applicable_category_id == None
                )
            )
        
        result = await db.execute(query.order_by(GrievanceResolution.title))
        return list(result.scalars().all())
    
    @staticmethod
    async def create(
        db: AsyncSession,
        grievance_id: UUID = None,
        resolved_by_id: UUID = None,
        resolved_by_name: str = None,
        resolution_data: dict = None
    ) -> GrievanceResolution:
        """Create a resolution."""
        resolution = GrievanceResolution(
            grievance_id=grievance_id,
            resolved_by_id=resolved_by_id,
            resolved_by_name=resolved_by_name,
            **resolution_data or {}
        )
        db.add(resolution)
        await db.commit()
        await db.refresh(resolution)
        return resolution
    
    @staticmethod
    async def update(
        db: AsyncSession,
        resolution_id: UUID,
        resolution_data: dict
    ) -> Optional[GrievanceResolution]:
        """Update a resolution."""
        resolution = await GrievanceResolutionCRUD.get_by_id(db, resolution_id)
        if not resolution:
            return None
        
        for field, value in resolution_data.items():
            setattr(resolution, field, value)
        
        await db.commit()
        await db.refresh(resolution)
        return resolution
    
    @staticmethod
    async def add_feedback(
        db: AsyncSession,
        resolution_id: UUID,
        rating: int,
        feedback: str = None
    ) -> Optional[GrievanceResolution]:
        """Add submitter feedback to a resolution."""
        resolution = await GrievanceResolutionCRUD.get_by_id(db, resolution_id)
        if not resolution:
            return None
        
        resolution.submitter_feedback = feedback
        
        # Update grievance rating
        if resolution.grievance_id:
            from src.grievances.models import Grievance
            await db.execute(
                update(Grievance)
                .where(Grievance.id == resolution.grievance_id)
                .values(submitter_rating=rating)
            )
        
        await db.commit()
        await db.refresh(resolution)
        
        return resolution


# =============================================================================
# Grievance Statistics CRUD
# =============================================================================

class GrievanceStatsCRUD:
    """Statistics operations for grievances."""
    
    @staticmethod
    async def get_stats(db: AsyncSession) -> Dict[str, Any]:
        """Get overall grievance statistics."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Basic counts
        total = await db.execute(
            select(func.count(Grievance.id)).where(Grievance.is_deleted == False)
        )
        total = total.scalar() or 0
        
        # By status
        status_counts = {}
        status_result = await db.execute(
            select(Grievance.status, func.count(Grievance.id))
            .where(Grievance.is_deleted == False)
            .group_by(Grievance.status)
        )
        for row in status_result:
            status_counts[row[0]] = row[1]
        
        # By priority
        priority_counts = {}
        priority_result = await db.execute(
            select(Grievance.priority, func.count(Grievance.id))
            .where(Grievance.is_deleted == False)
            .group_by(Grievance.priority)
        )
        for row in priority_result:
            priority_counts[row[0]] = row[1]
        
        # By category
        category_counts = {}
        category_result = await db.execute(
            select(GrievanceCategory.name, func.count(Grievance.id))
            .join(GrievanceCategory, Grievance.category_id == GrievanceCategory.id)
            .where(Grievance.is_deleted == False)
            .group_by(GrievanceCategory.name)
        )
        for row in category_result:
            category_counts[row[0]] = row[1]
        
        # By district
        district_counts = {}
        district_result = await db.execute(
            select(Grievance.district, func.count(Grievance.id))
            .where(Grievance.is_deleted == False)
            .where(Grievance.district.isnot(None))
            .group_by(Grievance.district)
        )
        for row in district_result:
            district_counts[row[0]] = row[1]
        
        # Overdue count
        overdue_count = await db.execute(
            select(func.count(Grievance.id))
            .join(GrievanceSLA, Grievance.id == GrievanceSLA.grievance_id)
            .where(Grievance.is_deleted == False)
            .where(
                and_(
                    GrievanceSLA.resolution_due_at < now,
                    Grievance.status.notin_([
                        GrievanceStatus.CLOSED.value,
                        GrievanceStatus.RESOLVED.value,
                    ])
                )
            )
        )
        overdue_count = overdue_count.scalar() or 0
        
        # SLA compliance
        response_compliant = await db.execute(
            select(func.count(GrievanceSLA.id))
            .join(Grievance, GrievanceSLA.grievance_id == Grievance.id)
            .where(
                and_(
                    Grievance.is_deleted == False,
                    GrievanceSLA.responded_at.isnot(None),
                    GrievanceSLA.response_sla_met == True
                )
            )
        )
        response_compliant = response_compliant.scalar() or 0
        
        resolution_compliant = await db.execute(
            select(func.count(GrievanceSLA.id))
            .join(Grievance, GrievanceSLA.grievance_id == Grievance.id)
            .where(
                and_(
                    Grievance.is_deleted == False,
                    GrievanceSLA.resolved_at.isnot(None),
                    GrievanceSLA.resolution_sla_met == True
                )
            )
        )
        resolution_compliant = resolution_compliant.scalar() or 0
        
        total_with_sla = await db.execute(
            select(func.count(GrievanceSLA.id))
            .join(Grievance, GrievanceSLA.grievance_id == Grievance.id)
            .where(Grievance.is_deleted == False)
        )
        total_with_sla = total_with_sla.scalar() or 1
        
        response_sla_compliance = round((response_compliant / total_with_sla) * 100, 2) if total_with_sla > 0 else 100.0
        resolution_sla_compliance = round((resolution_compliant / total_with_sla) * 100, 2) if total_with_sla > 0 else 100.0
        
        # Time-based metrics
        submitted_today = await db.execute(
            select(func.count(Grievance.id)).where(
                and_(
                    Grievance.is_deleted == False,
                    Grievance.submitted_at >= today_start
                )
            )
        )
        submitted_today = submitted_today.scalar() or 0
        
        submitted_this_week = await db.execute(
            select(func.count(Grievance.id)).where(
                and_(
                    Grievance.is_deleted == False,
                    Grievance.submitted_at >= week_start
                )
            )
        )
        submitted_this_week = submitted_this_week.scalar() or 0
        
        submitted_this_month = await db.execute(
            select(func.count(Grievance.id)).where(
                and_(
                    Grievance.is_deleted == False,
                    Grievance.submitted_at >= month_start
                )
            )
        )
        submitted_this_month = submitted_this_month.scalar() or 0
        
        resolved_today = await db.execute(
            select(func.count(Grievance.id)).where(
                and_(
                    Grievance.is_deleted == False,
                    Grievance.resolved_at >= today_start
                )
            )
        )
        resolved_today = resolved_today.scalar() or 0
        
        resolved_this_week = await db.execute(
            select(func.count(Grievance.id)).where(
                and_(
                    Grievance.is_deleted == False,
                    Grievance.resolved_at >= week_start
                )
            )
        )
        resolved_this_week = resolved_this_week.scalar() or 0
        
        resolved_this_month = await db.execute(
            select(func.count(Grievance.id)).where(
                and_(
                    Grievance.is_deleted == False,
                    Grievance.resolved_at >= month_start
                )
            )
        )
        resolved_this_month = resolved_this_month.scalar() or 0
        
        return {
            "total_grievances": total,
            "by_status": status_counts,
            "by_priority": priority_counts,
            "by_category": category_counts,
            "by_district": district_counts,
            "response_sla_compliance": response_sla_compliance,
            "resolution_sla_compliance": resolution_sla_compliance,
            "overdue_count": overdue_count,
            "submitted_today": submitted_today,
            "submitted_this_week": submitted_this_week,
            "submitted_this_month": submitted_this_month,
            "resolved_today": resolved_today,
            "resolved_this_week": resolved_this_week,
            "resolved_this_month": resolved_this_month,
            "avg_response_time_hours": 0.0,
            "avg_resolution_time_hours": 0.0,
        }
    
    @staticmethod
    async def get_dashboard(
        db: AsyncSession,
        member_id: UUID = None
    ) -> Dict[str, Any]:
        """Get dashboard data."""
        stats = await GrievanceStatsCRUD.get_stats(db)
        
        # Get my metrics if member_id provided
        my_assigned = 0
        my_pending = 0
        my_resolved_today = 0
        my_escalated = 0
        
        if member_id:
            my_assigned_result = await db.execute(
                select(func.count(Grievance.id)).where(
                    and_(
                        Grievance.is_deleted == False,
                        Grievance.current_assignee_id == member_id,
                        Grievance.status.notin_([
                            GrievanceStatus.CLOSED.value,
                            GrievanceStatus.RESOLVED.value,
                        ])
                    )
                )
            )
            my_assigned = my_assigned_result.scalar() or 0
            
            my_pending = my_assigned  # Same for now
            
            my_resolved_result = await db.execute(
                select(func.count(Grievance.id)).where(
                    and_(
                        Grievance.is_deleted == False,
                        Grievance.current_assignee_id == member_id,
                        Grievance.resolved_at >= datetime.now(timezone.utc).replace(
                            hour=0, minute=0, second=0, microsecond=0
                        )
                    )
                )
            )
            my_resolved_today = my_resolved_result.scalar() or 0
        
        # Recent grievances
        recent_result = await db.execute(
            select(Grievance)
            .where(Grievance.is_deleted == False)
            .order_by(Grievance.created_at.desc())
            .limit(5)
        )
        recently_submitted = list(recent_result.scalars().all())
        
        recent_resolved_result = await db.execute(
            select(Grievance)
            .where(
                and_(
                    Grievance.is_deleted == False,
                    Grievance.resolved_at.isnot(None)
                )
            )
            .order_by(Grievance.resolved_at.desc())
            .limit(5)
        )
        recently_resolved = list(recent_resolved_result.scalars().all())
        
        # Overdue grievances
        overdue, _ = await GrievanceCRUD.get_overdue(db, page=1, limit=5)
        
        # SLA alerts
        response_breached = await db.execute(
            select(func.count(GrievanceSLA.id))
            .join(Grievance, GrievanceSLA.grievance_id == Grievance.id)
            .where(
                and_(
                    Grievance.is_deleted == False,
                    GrievanceSLA.response_due_at < datetime.now(timezone.utc),
                    Grievance.status.in_([
                        GrievanceStatus.SUBMITTED.value,
                        GrievanceStatus.ACKNOWLEDGED.value,
                    ])
                )
            )
        )
        response_breached_today = response_breached.scalar() or 0
        
        resolution_breached = await db.execute(
            select(func.count(GrievanceSLA.id))
            .join(Grievance, GrievanceSLA.grievance_id == Grievance.id)
            .where(
                and_(
                    Grievance.is_deleted == False,
                    GrievanceSLA.resolution_due_at < datetime.now(timezone.utc),
                    Grievance.status.notin_([
                        GrievanceStatus.CLOSED.value,
                        GrievanceStatus.RESOLVED.value,
                    ])
                )
            )
        )
        resolution_breached_today = resolution_breached.scalar() or 0
        
        # Approaching deadline (within 24 hours)
        approaching = await db.execute(
            select(func.count(GrievanceSLA.id))
            .join(Grievance, GrievanceSLA.grievance_id == Grievance.id)
            .where(
                and_(
                    Grievance.is_deleted == False,
                    GrievanceSLA.resolution_due_at > datetime.now(timezone.utc),
                    GrievanceSLA.resolution_due_at < datetime.now(timezone.utc) + timedelta(hours=24),
                    Grievance.status.notin_([
                        GrievanceStatus.CLOSED.value,
                        GrievanceStatus.RESOLVED.value,
                    ])
                )
            )
        )
        approaching_deadline = approaching.scalar() or 0
        
        return {
            "total_open": stats["by_status"].get(GrievanceStatus.SUBMITTED.value, 0) + 
                         stats["by_status"].get(GrievanceStatus.ACKNOWLEDGED.value, 0) +
                         stats["by_status"].get(GrievanceStatus.UNDER_INVESTIGATION.value, 0),
            "total_pending": stats["by_status"].get(GrievanceStatus.PENDING_ACTION.value, 0),
            "total_resolved": stats["by_status"].get(GrievanceStatus.RESOLVED.value, 0),
            "total_closed": stats["by_status"].get(GrievanceStatus.CLOSED.value, 0),
            "critical_count": stats["by_priority"].get(GrievancePriority.CRITICAL.value, 0),
            "urgent_count": stats["by_priority"].get(GrievancePriority.URGENT.value, 0),
            "high_count": stats["by_priority"].get(GrievancePriority.HIGH.value, 0),
            "medium_count": stats["by_priority"].get(GrievancePriority.MEDIUM.value, 0),
            "low_count": stats["by_priority"].get(GrievancePriority.LOW.value, 0),
            "response_breached_today": response_breached_today,
            "resolution_breached_today": resolution_breached_today,
            "approaching_deadline": approaching_deadline,
            "assigned_to_me": my_assigned,
            "my_pending": my_pending,
            "my_resolved_today": my_resolved_today,
            "my_escalated": my_escalated,
            "recently_submitted": recently_submitted,
            "recently_resolved": recently_resolved,
            "overdue_grievances": overdue,
        }
