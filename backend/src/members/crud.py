"""
Member CRUD Operations
CRUD operations for members and related entities.
"""

from datetime import datetime, date, timezone
from typing import List, Optional, Tuple, Type, TypeVar, Dict, Any
from uuid import UUID
import csv
import io

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
from src.members.models import (
    Member,
    MemberProfile,
    MemberFamily,
    MemberDocument,
    MemberNote,
    MembershipHistory,
    MemberTagDefinition,
    MemberSkillDefinition,
    MembershipStatus,
    MembershipType,
)
from src.members.schemas import (
    MemberCreate,
    MemberUpdate,
    MemberSearchFilters,
    MemberProfileCreate,
    MemberProfileUpdate,
    MemberFamilyCreate,
    MemberFamilyUpdate,
    MemberDocumentCreate,
    MemberNoteCreate,
    MemberNoteUpdate,
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
# Member CRUD
# =============================================================================

class MemberCRUD(CRUDBase):
    """CRUD operations for members."""
    
    @staticmethod
    async def generate_membership_number(db: AsyncSession) -> str:
        """Generate a unique membership number."""
        year = datetime.now(timezone.utc).year
        prefix = f"VCK{year}"
        
        # Get the latest membership number for this year
        result = await db.execute(
            select(func.max(Member.id))
            .where(Member.membership_number.like(f"{prefix}%"))
        )
        max_id = result.scalar()
        
        if max_id:
            # Get the sequence number from existing members
            result = await db.execute(
                select(Member.membership_number)
                .where(Member.membership_number.like(f"{prefix}%"))
                .order_by(Member.membership_number.desc())
                .limit(1)
            )
            last_number = result.scalar_one_or_none()
            if last_number:
                seq = int(last_number.replace(prefix, "")) + 1
            else:
                seq = 1
        else:
            seq = 1
        
        return f"{prefix}{seq:06d}"
    
    @staticmethod
    async def get_by_phone(db: AsyncSession, phone: str) -> Optional[Member]:
        """Get member by phone number."""
        result = await db.execute(
            select(Member)
            .where(Member.phone == phone)
            .where(Member.is_deleted == False)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_membership_number(db: AsyncSession, membership_number: str) -> Optional[Member]:
        """Get member by membership number."""
        result = await db.execute(
            select(Member)
            .where(Member.membership_number == membership_number)
            .where(Member.is_deleted == False)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(db: AsyncSession, member_data: MemberCreate) -> Member:
        """Create a new member."""
        # Check for existing phone
        existing = await MemberCRUD.get_by_phone(db, member_data.phone)
        if existing:
            raise AlreadyExistsError(resource="Member", field="phone", value=member_data.phone)
        
        # Generate membership number
        membership_number = await MemberCRUD.generate_membership_number(db)
        
        member = Member(
            membership_number=membership_number,
            first_name=member_data.first_name,
            last_name=member_data.last_name,
            first_name_ta=member_data.first_name_ta,
            last_name_ta=member_data.last_name_ta,
            phone=member_data.phone,
            email=member_data.email,
            date_of_birth=member_data.date_of_birth,
            gender=member_data.gender,
            address_line1=member_data.address_line1,
            address_line2=member_data.address_line2,
            city=member_data.city,
            district=member_data.district,
            constituency=member_data.constituency,
            ward=member_data.ward,
            state=member_data.state or "Tamil Nadu",
            pincode=member_data.pincode,
            voter_id=member_data.voter_id,
            blood_group=member_data.blood_group,
            education=member_data.education,
            occupation=member_data.occupation,
            membership_type=member_data.membership_type or MembershipType.ORDINARY.value,
            status=MembershipStatus.PENDING.value,
        )
        
        db.add(member)
        await db.commit()
        await db.refresh(member)
        
        # Create initial history entry
        await MemberCRUD._create_history_entry(
            db,
            member.id,
            action="registration",
            action_description="New member registration",
            new_status=MembershipStatus.PENDING.value,
        )
        
        # Cache the member
        await redis.cache_member(member.id, member)
        
        return member
    
    @staticmethod
    async def update(db: AsyncSession, member_id: UUID, member_data: MemberUpdate) -> Optional[Member]:
        """Update a member."""
        member = await MemberCRUD.get_by_id(db, Member, member_id)
        if not member:
            return None
        
        update_data = member_data.model_dump(exclude_unset=True)
        
        # Check for phone uniqueness if being updated
        if "phone" in update_data and update_data["phone"]:
            existing = await MemberCRUD.get_by_phone(db, update_data["phone"])
            if existing and existing.id != member_id:
                raise AlreadyExistsError(resource="Member", field="phone", value=update_data["phone"])
        
        for field, value in update_data.items():
            setattr(member, field, value)
        
        await db.commit()
        await db.refresh(member)
        
        # Update cache
        await redis.cache_member(member_id, member)
        
        return member
    
    @staticmethod
    async def update_status(
        db: AsyncSession,
        member_id: UUID,
        new_status: str,
        reason: str = None,
        performed_by: UUID = None
    ) -> Optional[Member]:
        """Update member status with history."""
        member = await MemberCRUD.get_by_id(db, Member, member_id)
        if not member:
            return None
        
        previous_status = member.status
        
        member.status = new_status
        if new_status == MembershipStatus.ACTIVE.value:
            member.verified_at = datetime.now(timezone.utc)
            member.verified_by = performed_by
        
        await db.commit()
        await db.refresh(member)
        
        # Create history entry
        await MemberCRUD._create_history_entry(
            db,
            member_id,
            action="status_change",
            action_description=f"Status changed from {previous_status} to {new_status}",
            previous_status=previous_status,
            new_status=new_status,
            reason=reason,
            performed_by=performed_by,
        )
        
        # Update cache
        await redis.cache_member(member_id, member)
        
        return member
    
    @staticmethod
    async def _create_history_entry(
        db: AsyncSession,
        member_id: UUID,
        action: str,
        action_description: str = None,
        previous_status: str = None,
        new_status: str = None,
        reason: str = None,
        performed_by: UUID = None,
        metadata: Dict = None
    ) -> MembershipHistory:
        """Create a membership history entry."""
        history = MembershipHistory(
            member_id=member_id,
            action=action,
            action_description=action_description,
            previous_status=previous_status,
            new_status=new_status,
            reason=reason,
            performed_by=performed_by,
            metadata=metadata or {},
        )
        db.add(history)
        await db.commit()
        return history
    
    @staticmethod
    async def search(
        db: AsyncSession,
        filters: MemberSearchFilters,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Member], int]:
        """Search members with filters."""
        query = (
            select(Member)
            .where(Member.is_deleted == False)
            .options(selectinload(Member.tags))
        )
        
        # Text search
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    Member.first_name.ilike(search_term),
                    Member.last_name.ilike(search_term),
                    Member.phone.ilike(search_term),
                    Member.email.ilike(search_term),
                    Member.voter_id.ilike(search_term),
                    Member.membership_number.ilike(search_term),
                )
            )
        
        # Status filter
        if filters.status:
            query = query.where(Member.status.in_(filters.status))
        
        # Membership type filter
        if filters.membership_type:
            query = query.where(Member.membership_type.in_(filters.membership_type))
        
        # Location filters
        if filters.district:
            query = query.where(Member.district == filters.district)
        if filters.constituency:
            query = query.where(Member.constituency == filters.constituency)
        if filters.ward:
            query = query.where(Member.ward == filters.ward)
        
        # Gender filter
        if filters.gender:
            query = query.where(Member.gender == filters.gender)
        
        # Occupation filter
        if filters.occupation:
            query = query.where(Member.occupation == filters.occupation)
        
        # Education filter
        if filters.education:
            query = query.where(Member.education == filters.education)
        
        # Date range filters
        if filters.from_date:
            query = query.where(Member.joined_at >= filters.from_date)
        if filters.to_date:
            query = query.where(Member.joined_at <= filters.to_date)
        
        # Age filters
        if filters.min_age or filters.max_age:
            today = date.today()
            if filters.max_age:
                min_birth = today.replace(year=today.year - filters.max_age)
                query = query.where(Member.date_of_birth <= min_birth)
            if filters.min_age:
                max_birth = today.replace(year=today.year - filters.min_age + 1)
                query = query.where(Member.date_of_birth >= max_birth)
        
        # Get total count
        count_query = select(func.count(Member.id)).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit).order_by(Member.created_at.desc())
        
        result = await db.execute(query)
        members = list(result.scalars().all())
        
        return members, total
    
    @staticmethod
    async def get_detailed(
        db: AsyncSession,
        member_id: UUID
    ) -> Optional[Member]:
        """Get member with all relationships loaded."""
        result = await db.execute(
            select(Member)
            .where(Member.id == member_id)
            .where(Member.is_deleted == False)
            .options(
                selectinload(Member.tags),
                selectinload(Member.skills),
                selectinload(Member.profile),
                selectinload(Member.documents),
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def soft_delete(db: AsyncSession, member_id: UUID) -> bool:
        """Soft delete a member."""
        member = await MemberCRUD.get_by_id(db, Member, member_id)
        if not member:
            return False
        
        member.is_deleted = True
        member.deleted_at = datetime.now(timezone.utc)
        member.status = MembershipStatus.RESIGNED.value
        
        await db.commit()
        
        # Remove from cache
        await redis.delete_member_cache(member_id)
        
        # Create history entry
        await MemberCRUD._create_history_entry(
            db,
            member_id,
            action="deletion",
            action_description="Member record deleted",
            previous_status=member.status,
            new_status=MembershipStatus.RESIGNED.value,
        )
        
        return True


# =============================================================================
# Member Profile CRUD
# =============================================================================

class MemberProfileCRUD(CRUDBase):
    """CRUD operations for member profiles."""
    
    @staticmethod
    async def get_by_member_id(db: AsyncSession, member_id: UUID) -> Optional[MemberProfile]:
        """Get profile by member ID."""
        result = await db.execute(
            select(MemberProfile)
            .where(MemberProfile.member_id == member_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(
        db: AsyncSession,
        member_id: UUID,
        profile_data: MemberProfileCreate
    ) -> MemberProfile:
        """Create member profile."""
        profile = MemberProfile(
            member_id=member_id,
            **profile_data.model_dump()
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        return profile
    
    @staticmethod
    async def update(
        db: AsyncSession,
        member_id: UUID,
        profile_data: MemberProfileUpdate
    ) -> Optional[MemberProfile]:
        """Update member profile."""
        profile = await MemberProfileCRUD.get_by_member_id(db, member_id)
        if not profile:
            return None
        
        update_data = profile_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)
        
        await db.commit()
        await db.refresh(profile)
        return profile


# =============================================================================
# Member Family CRUD
# =============================================================================

class MemberFamilyCRUD(CRUDBase):
    """CRUD operations for member family relationships."""
    
    @staticmethod
    async def get_family_tree(
        db: AsyncSession,
        member_id: UUID
    ) -> List[MemberFamily]:
        """Get all family relationships for a member."""
        result = await db.execute(
            select(MemberFamily)
            .where(
                or_(
                    MemberFamily.member_id == member_id,
                    MemberFamily.related_member_id == member_id
                )
            )
            .where(MemberFamily.is_active == True)
            .options(
                selectinload(MemberFamily.member),
                selectinload(MemberFamily.related_member),
            )
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def add_relationship(
        db: AsyncSession,
        member_id: UUID,
        family_data: MemberFamilyCreate
    ) -> MemberFamily:
        """Add a family relationship."""
        # Check if relationship already exists
        existing = await db.execute(
            select(MemberFamily).where(
                or_(
                    and_(
                        MemberFamily.member_id == member_id,
                        MemberFamily.related_member_id == family_data.related_member_id
                    ),
                    and_(
                        MemberFamily.member_id == family_data.related_member_id,
                        MemberFamily.related_member_id == member_id
                    )
                )
            )
        )
        if existing.scalar_one_or_none():
            raise AlreadyExistsError(resource="FamilyRelationship", field="members", value=str(member_id))
        
        family = MemberFamily(
            member_id=member_id,
            related_member_id=family_data.related_member_id,
            relationship_type=family_data.relationship_type,
            notes=family_data.notes,
        )
        db.add(family)
        await db.commit()
        await db.refresh(family)
        return family
    
    @staticmethod
    async def update_relationship(
        db: AsyncSession,
        family_id: UUID,
        family_data: MemberFamilyUpdate
    ) -> Optional[MemberFamily]:
        """Update a family relationship."""
        family = await MemberFamilyCRUD.get_by_id(db, MemberFamily, family_id)
        if not family:
            return None
        
        update_data = family_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(family, field, value)
        
        await db.commit()
        await db.refresh(family)
        return family
    
    @staticmethod
    async def remove_relationship(db: AsyncSession, family_id: UUID) -> bool:
        """Remove (deactivate) a family relationship."""
        family = await MemberFamilyCRUD.get_by_id(db, MemberFamily, family_id)
        if not family:
            return False
        
        family.is_active = False
        await db.commit()
        return True


# =============================================================================
# Member Document CRUD
# =============================================================================

class MemberDocumentCRUD(CRUDBase):
    """CRUD operations for member documents."""
    
    @staticmethod
    async def get_by_member_id(db: AsyncSession, member_id: UUID) -> List[MemberDocument]:
        """Get all documents for a member."""
        result = await db.execute(
            select(MemberDocument)
            .where(MemberDocument.member_id == member_id)
            .where(MemberDocument.is_active == True)
            .order_by(MemberDocument.created_at.desc())
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_by_type(
        db: AsyncSession,
        member_id: UUID,
        document_type: str
    ) -> Optional[MemberDocument]:
        """Get a specific document type for a member."""
        result = await db.execute(
            select(MemberDocument)
            .where(MemberDocument.member_id == member_id)
            .where(MemberDocument.document_type == document_type)
            .where(MemberDocument.is_active == True)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(
        db: AsyncSession,
        member_id: UUID,
        document_data: MemberDocumentCreate
    ) -> MemberDocument:
        """Create a new document."""
        document = MemberDocument(
            member_id=member_id,
            **document_data.model_dump()
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)
        return document
    
    @staticmethod
    async def delete(db: AsyncSession, document_id: UUID) -> bool:
        """Soft delete a document."""
        document = await MemberDocumentCRUD.get_by_id(db, MemberDocument, document_id)
        if not document:
            return False
        
        document.is_active = False
        await db.commit()
        return True


# =============================================================================
# Member Note CRUD
# =============================================================================

class MemberNoteCRUD(CRUDBase):
    """CRUD operations for member notes."""
    
    @staticmethod
    async def get_by_member_id(
        db: AsyncSession,
        member_id: UUID,
        include_private: bool = True
    ) -> List[MemberNote]:
        """Get all notes for a member."""
        query = select(MemberNote).where(MemberNote.member_id == member_id)
        if not include_private:
            query = query.where(MemberNote.is_private == False)
        
        result = await db.execute(
            query.order_by(MemberNote.created_at.desc())
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def create(
        db: AsyncSession,
        member_id: UUID,
        author_id: UUID,
        note_data: MemberNoteCreate
    ) -> MemberNote:
        """Create a new note."""
        note = MemberNote(
            member_id=member_id,
            author_id=author_id,
            **note_data.model_dump()
        )
        db.add(note)
        await db.commit()
        await db.refresh(note)
        return note
    
    @staticmethod
    async def update(
        db: AsyncSession,
        note_id: UUID,
        note_data: MemberNoteUpdate
    ) -> Optional[MemberNote]:
        """Update a note."""
        note = await MemberNoteCRUD.get_by_id(db, MemberNote, note_id)
        if not note:
            return None
        
        update_data = note_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(note, field, value)
        
        await db.commit()
        await db.refresh(note)
        return note


# =============================================================================
# Member Tag CRUD
# =============================================================================

class MemberTagCRUD(CRUDBase):
    """CRUD operations for member tags."""
    
    @staticmethod
    async def get_all_definitions(db: AsyncSession) -> List[MemberTagDefinition]:
        """Get all tag definitions."""
        result = await db.execute(
            select(MemberTagDefinition)
            .where(MemberTagDefinition.is_active == True)
            .order_by(MemberTagDefinition.name)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def add_tags(
        db: AsyncSession,
        member_id: UUID,
        tag_ids: List[UUID]
    ) -> Member:
        """Add tags to a member."""
        member = await MemberCRUD.get_by_id(db, Member, member_id)
        if not member:
            raise NotFoundError(resource="Member", resource_id=str(member_id))
        
        tags = await db.execute(
            select(MemberTagDefinition)
            .where(MemberTagDefinition.id.in_(tag_ids))
        )
        member.tags.extend(list(tags.scalars().all()))
        
        await db.commit()
        await db.refresh(member)
        return member
    
    @staticmethod
    async def remove_tag(
        db: AsyncSession,
        member_id: UUID,
        tag_id: UUID
    ) -> bool:
        """Remove a tag from a member."""
        member = await MemberCRUD.get_by_id(db, Member, member_id)
        if not member:
            raise NotFoundError(resource="Member", resource_id=str(member_id))
        
        member.tags = [t for t in member.tags if t.id != tag_id]
        await db.commit()
        return True


# =============================================================================
# Member Statistics CRUD
# =============================================================================

class MemberStatsCRUD:
    """Statistics operations for members."""
    
    @staticmethod
    async def get_stats(db: AsyncSession) -> Dict[str, Any]:
        """Get overall member statistics."""
        # Basic counts
        total = await db.execute(
            select(func.count(Member.id)).where(Member.is_deleted == False)
        )
        total = total.scalar() or 0
        
        active = await db.execute(
            select(func.count(Member.id)).where(
                and_(
                    Member.is_deleted == False,
                    Member.status == MembershipStatus.ACTIVE.value
                )
            )
        )
        active = active.scalar() or 0
        
        pending = await db.execute(
            select(func.count(Member.id)).where(
                and_(
                    Member.is_deleted == False,
                    Member.status == MembershipStatus.PENDING.value
                )
            )
        )
        pending = pending.scalar() or 0
        
        suspended = await db.execute(
            select(func.count(Member.id)).where(
                and_(
                    Member.is_deleted == False,
                    Member.status == MembershipStatus.SUSPENDED.value
                )
            )
        )
        suspended = suspended.scalar() or 0
        
        expelled = await db.execute(
            select(func.count(Member.id)).where(
                and_(
                    Member.is_deleted == False,
                    Member.status == MembershipStatus.EXPELLED.value
                )
            )
        )
        expelled = expelled.scalar() or 0
        
        # By status
        status_counts = {}
        status_result = await db.execute(
            select(Member.status, func.count(Member.id))
            .where(Member.is_deleted == False)
            .group_by(Member.status)
        )
        for row in status_result:
            status_counts[row[0]] = row[1]
        
        # By membership type
        type_counts = {}
        type_result = await db.execute(
            select(Member.membership_type, func.count(Member.id))
            .where(Member.is_deleted == False)
            .group_by(Member.membership_type)
        )
        for row in type_result:
            type_counts[row[0]] = row[1]
        
        # By gender
        gender_counts = {}
        gender_result = await db.execute(
            select(Member.gender, func.count(Member.id))
            .where(Member.is_deleted == False)
            .where(Member.gender.isnot(None))
            .group_by(Member.gender)
        )
        for row in gender_result:
            gender_counts[row[0] or "not_specified"] = row[1]
        
        # By district
        district_counts = {}
        district_result = await db.execute(
            select(Member.district, func.count(Member.id))
            .where(Member.is_deleted == False)
            .where(Member.district.isnot(None))
            .group_by(Member.district)
        )
        for row in district_result:
            district_counts[row[0]] = row[1]
        
        # By occupation
        occupation_counts = {}
        occupation_result = await db.execute(
            select(Member.occupation, func.count(Member.id))
            .where(Member.is_deleted == False)
            .where(Member.occupation.isnot(None))
            .group_by(Member.occupation)
            .order_by(func.count(Member.id).desc())
            .limit(10)
        )
        for row in occupation_result:
            occupation_counts[row[0]] = row[1]
        
        # New members this month
        now = datetime.now(timezone.utc)
        first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_this_month = await db.execute(
            select(func.count(Member.id)).where(
                and_(
                    Member.is_deleted == False,
                    Member.created_at >= first_of_month
                )
            )
        )
        new_this_month = new_this_month.scalar() or 0
        
        # New members this year
        first_of_year = now.replace(month=1, day=1)
        new_this_year = await db.execute(
            select(func.count(Member.id)).where(
                and_(
                    Member.is_deleted == False,
                    Member.created_at >= first_of_year
                )
            )
        )
        new_this_year = new_this_year.scalar() or 0
        
        return {
            "total_members": total,
            "active_members": active,
            "pending_members": pending,
            "suspended_members": suspended,
            "expelled_members": expelled,
            "by_status": status_counts,
            "by_membership_type": type_counts,
            "by_gender": gender_counts,
            "by_district": district_counts,
            "by_occupation": occupation_counts,
            "new_this_month": new_this_month,
            "new_this_year": new_this_year,
            "growth_percentage_month": round((new_this_month / max(total - new_this_month, 1)) * 100, 2),
            "growth_percentage_year": round((new_this_year / max(total - new_this_year, 1)) * 100, 2),
        }
    
    @staticmethod
    async def export_members(
        db: AsyncSession,
        filters: MemberSearchFilters = None,
        fields: List[str] = None
    ) -> str:
        """Export members to CSV format."""
        if filters:
            members, _ = await MemberCRUD.search(db, filters, page=1, limit=100000)
        else:
            result = await db.execute(
                select(Member)
                .where(Member.is_deleted == False)
                .order_by(Member.created_at.desc())
            )
            members = list(result.scalars().all())
        
        # Default fields to export
        export_fields = fields or [
            "membership_number",
            "first_name",
            "last_name",
            "phone",
            "email",
            "status",
            "membership_type",
            "district",
            "constituency",
            "ward",
            "occupation",
            "joined_at",
        ]
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=export_fields)
        writer.writeheader()
        
        for member in members:
            row = {}
            for field in export_fields:
                value = getattr(member, field, None)
                if isinstance(value, datetime):
                    value = value.isoformat()
                row[field] = value
            writer.writerow(row)
        
        return output.getvalue()


# =============================================================================
# Bulk Import CRUD
# =============================================================================

class MemberBulkCRUD:
    """Bulk operations for members."""
    
    @staticmethod
    async def import_members(
        db: AsyncSession,
        members_data: List[dict],
        notify: bool = True
    ) -> Dict[str, Any]:
        """Import members from a list of data."""
        successful = 0
        failed = 0
        errors = []
        
        for idx, data in enumerate(members_data):
            try:
                member_create = MemberCreate(**data)
                await MemberCRUD.create(db, member_create)
                successful += 1
            except Exception as e:
                failed += 1
                errors.append({
                    "row": idx + 1,
                    "error": str(e),
                    "data": data,
                })
        
        return {
            "total": len(members_data),
            "successful": successful,
            "failed": failed,
            "errors": errors,
        }
