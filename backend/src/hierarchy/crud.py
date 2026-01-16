"""
Hierarchy CRUD Operations
CRUD operations for hierarchy entities and hierarchical queries.
"""

import json
import csv
import io
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Type, TypeVar, Dict, Any
from uuid import UUID
from math import radians, sin, cos, sqrt, atan2

from sqlalchemy import select, update, delete, and_, or_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from src.core.exceptions import (
    NotFoundError,
    AlreadyExistsError,
    ValidationError,
)
from src.core import redis
from src.hierarchy.models import (
    District,
    Constituency,
    Ward,
    Booth,
    ZipCodeMapping,
    ConstituencyType,
    HierarchyLevel,
)
from src.hierarchy.schemas import (
    DistrictCreate,
    DistrictUpdate,
    ConstituencyCreate,
    ConstituencyUpdate,
    WardCreate,
    WardUpdate,
    BoothCreate,
    BoothUpdate,
    HierarchySearchFilters,
)


# =============================================================================
# Cache Keys
# =============================================================================

HIERARCHY_CACHE_PREFIX = "hierarchy:"
DISTRICT_CACHE_PREFIX = f"{HIERARCHY_CACHE_PREFIX}district:"
CONSTITUENCY_CACHE_PREFIX = f"{HIERARCHY_CACHE_PREFIX}constituency:"
WARD_CACHE_PREFIX = f"{HIERARCHY_CACHE_PREFIX}ward:"
BOOTH_CACHE_PREFIX = f"{HIERARCHY_CACHE_PREFIX}booth:"
TREE_CACHE_KEY = f"{HIERARCHY_CACHE_PREFIX}tree"


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
        descending: bool = False,
        is_active: Optional[bool] = None
    ) -> List[T]:
        """Get all records with pagination."""
        query = select(model)
        
        if is_active is not None:
            query = query.where(model.is_active == is_active)
        
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
                if hasattr(record, 'is_active'):
                    record.is_active = False
            await db.commit()
            return True
        return False
    
    @staticmethod
    async def hard_delete(db: AsyncSession, model, id: UUID) -> bool:
        """Hard delete a record by ID."""
        record = await CRUDBase.get_by_id(db, model, id)
        if record:
            await db.delete(record)
            await db.commit()
            return True
        return False


# =============================================================================
# District CRUD
# =============================================================================

class DistrictCRUD(CRUDBase):
    """CRUD operations for districts."""
    
    @staticmethod
    async def get_by_code(db: AsyncSession, code: str) -> Optional[District]:
        """Get district by code."""
        result = await db.execute(
            select(District).where(District.code == code)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_name(db: AsyncSession, name: str) -> Optional[District]:
        """Get district by name."""
        result = await db.execute(
            select(District).where(District.name.ilike(f"%{name}%"))
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(db: AsyncSession, district_data: DistrictCreate) -> District:
        """Create a new district."""
        # Check for existing code
        existing = await DistrictCRUD.get_by_code(db, district_data.code)
        if existing:
            raise AlreadyExistsError(resource="District", field="code", value=district_data.code)
        
        district = District(
            name=district_data.name,
            name_ta=district_data.name_ta,
            code=district_data.code,
            state=district_data.state,
            latitude=district_data.latitude,
            longitude=district_data.longitude,
        )
        db.add(district)
        await db.commit()
        await db.refresh(district)
        
        # Cache the district
        await redis.cache_set(f"{DISTRICT_CACHE_PREFIX}{district.id}", district.__dict__)
        
        return district
    
    @staticmethod
    async def update(db: AsyncSession, district_id: UUID, district_data: DistrictUpdate) -> Optional[District]:
        """Update a district."""
        district = await DistrictCRUD.get_by_id(db, District, district_id)
        if not district:
            return None
        
        update_data = district_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(district, field, value)
        
        await db.commit()
        await db.refresh(district)
        
        # Update cache
        await redis.cache_set(f"{DISTRICT_CACHE_PREFIX}{district_id}", district.__dict__)
        await redis.cache_delete(f"{TREE_CACHE_KEY}")  # Invalidate tree cache
        
        return district
    
    @staticmethod
    async def get_with_counts(db: AsyncSession, skip: int = 0, limit: int = 100) -> Tuple[List[District], int]:
        """Get districts with constituency count."""
        # Get districts
        query = (
            select(District)
            .options(selectinload(District.constituencies))
            .order_by(District.name)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        districts = list(result.scalars().all())
        
        # Get total count
        total = await DistrictCRUD.count(db, District)
        
        return districts, total
    
    @staticmethod
    async def search(
        db: AsyncSession,
        search_term: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[District], int]:
        """Search districts."""
        query = select(District).where(District.is_active == True)
        
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.where(
                or_(
                    District.name.ilike(search_pattern),
                    District.code.ilike(search_pattern),
                    District.name_ta.ilike(search_pattern)
                )
            )
        
        # Get total count
        count_query = select(func.count(District.id)).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit).order_by(District.name)
        
        result = await db.execute(query)
        districts = list(result.scalars().all())
        
        return districts, total


# =============================================================================
# Constituency CRUD
# =============================================================================

class ConstituencyCRUD(CRUDBase):
    """CRUD operations for constituencies."""
    
    @staticmethod
    async def get_by_code(db: AsyncSession, code: str) -> Optional[Constituency]:
        """Get constituency by code."""
        result = await db.execute(
            select(Constituency).where(Constituency.code == code)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_district(db: AsyncSession, district_id: UUID) -> List[Constituency]:
        """Get all constituencies in a district."""
        result = await db.execute(
            select(Constituency)
            .where(Constituency.district_id == district_id)
            .where(Constituency.is_active == True)
            .order_by(Constituency.name)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def create(db: AsyncSession, constituency_data: ConstituencyCreate) -> Constituency:
        """Create a new constituency."""
        # Check for existing code
        existing = await ConstituencyCRUD.get_by_code(db, constituency_data.code)
        if existing:
            raise AlreadyExistsError(resource="Constituency", field="code", value=constituency_data.code)
        
        # Verify district exists
        district = await DistrictCRUD.get_by_id(db, District, constituency_data.district_id)
        if not district:
            raise NotFoundError(resource="District", resource_id=str(constituency_data.district_id))
        
        constituency = Constituency(
            district_id=constituency_data.district_id,
            name=constituency_data.name,
            name_ta=constituency_data.name_ta,
            code=constituency_data.code,
            constituency_type=constituency_data.constituency_type or ConstituencyType.ASSEMBLY.value,
            electorate_count=constituency_data.electorate_count or 0,
            latitude=constituency_data.latitude,
            longitude=constituency_data.longitude,
        )
        db.add(constituency)
        await db.commit()
        await db.refresh(constituency)
        
        return constituency
    
    @staticmethod
    async def update(
        db: AsyncSession,
        constituency_id: UUID,
        constituency_data: ConstituencyUpdate
    ) -> Optional[Constituency]:
        """Update a constituency."""
        constituency = await ConstituencyCRUD.get_by_id(db, Constituency, constituency_id)
        if not constituency:
            return None
        
        update_data = constituency_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(constituency, field, value)
        
        await db.commit()
        await db.refresh(constituency)
        
        return constituency
    
    @staticmethod
    async def search(
        db: AsyncSession,
        filters: HierarchySearchFilters,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Constituency], int]:
        """Search constituencies with filters."""
        query = select(Constituency).where(Constituency.is_active == True)
        
        if filters.search:
            search_pattern = f"%{filters.search}%"
            query = query.where(
                or_(
                    Constituency.name.ilike(search_pattern),
                    Constituency.code.ilike(search_pattern),
                )
            )
        
        if filters.district_id:
            query = query.where(Constituency.district_id == filters.district_id)
        
        if filters.constituency_type:
            query = query.where(Constituency.constituency_type == filters.constituency_type)
        
        # Get total count
        count_query = select(func.count(Constituency.id)).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit).order_by(Constituency.name)
        
        result = await db.execute(query)
        constituencies = list(result.scalars().all())
        
        return constituencies, total


# =============================================================================
# Ward CRUD
# =============================================================================

class WardCRUD(CRUDBase):
    """CRUD operations for wards."""
    
    @staticmethod
    async def get_by_code(db: AsyncSession, code: str) -> Optional[Ward]:
        """Get ward by code."""
        result = await db.execute(
            select(Ward).where(Ward.code == code)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_constituency(db: AsyncSession, constituency_id: UUID) -> List[Ward]:
        """Get all wards in a constituency."""
        result = await db.execute(
            select(Ward)
            .where(Ward.constituency_id == constituency_id)
            .where(Ward.is_active == True)
            .order_by(Ward.ward_number, Ward.name)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def create(db: AsyncSession, ward_data: WardCreate) -> Ward:
        """Create a new ward."""
        # Check for existing code
        existing = await WardCRUD.get_by_code(db, ward_data.code)
        if existing:
            raise AlreadyExistsError(resource="Ward", field="code", value=ward_data.code)
        
        # Verify constituency exists
        constituency = await ConstituencyCRUD.get_by_id(db, Constituency, ward_data.constituency_id)
        if not constituency:
            raise NotFoundError(resource="Constituency", resource_id=str(ward_data.constituency_id))
        
        ward = Ward(
            constituency_id=ward_data.constituency_id,
            name=ward_data.name,
            name_ta=ward_data.name_ta,
            code=ward_data.code,
            ward_number=ward_data.ward_number,
            latitude=ward_data.latitude,
            longitude=ward_data.longitude,
        )
        db.add(ward)
        await db.commit()
        await db.refresh(ward)
        
        return ward
    
    @staticmethod
    async def update(db: AsyncSession, ward_id: UUID, ward_data: WardUpdate) -> Optional[Ward]:
        """Update a ward."""
        ward = await WardCRUD.get_by_id(db, Ward, ward_id)
        if not ward:
            return None
        
        update_data = ward_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(ward, field, value)
        
        await db.commit()
        await db.refresh(ward)
        
        return ward
    
    @staticmethod
    async def search(
        db: AsyncSession,
        filters: HierarchySearchFilters,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Ward], int]:
        """Search wards with filters."""
        query = select(Ward).where(Ward.is_active == True)
        
        if filters.search:
            search_pattern = f"%{filters.search}%"
            query = query.where(
                or_(
                    Ward.name.ilike(search_pattern),
                    Ward.code.ilike(search_pattern),
                )
            )
        
        if filters.constituency_id:
            query = query.where(Ward.constituency_id == filters.constituency_id)
        
        # Get total count
        count_query = select(func.count(Ward.id)).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit).order_by(Ward.ward_number, Ward.name)
        
        result = await db.execute(query)
        wards = list(result.scalars().all())
        
        return wards, total


# =============================================================================
# Booth CRUD
# =============================================================================

class BoothCRUD(CRUDBase):
    """CRUD operations for booths."""
    
    @staticmethod
    async def get_by_code(db: AsyncSession, code: str) -> Optional[Booth]:
        """Get booth by code."""
        result = await db.execute(
            select(Booth).where(Booth.code == code)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_ward(db: AsyncSession, ward_id: UUID) -> List[Booth]:
        """Get all booths in a ward."""
        result = await db.execute(
            select(Booth)
            .where(Booth.ward_id == ward_id)
            .where(Booth.is_active == True)
            .order_by(Booth.booth_number, Booth.name)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def create(db: AsyncSession, booth_data: BoothCreate) -> Booth:
        """Create a new booth."""
        # Check for existing code
        existing = await BoothCRUD.get_by_code(db, booth_data.code)
        if existing:
            raise AlreadyExistsError(resource="Booth", field="code", value=booth_data.code)
        
        # Verify ward exists
        ward = await WardCRUD.get_by_id(db, Ward, booth_data.ward_id)
        if not ward:
            raise NotFoundError(resource="Ward", resource_id=str(booth_data.ward_id))
        
        booth = Booth(
            ward_id=booth_data.ward_id,
            name=booth_data.name,
            name_ta=booth_data.name_ta,
            code=booth_data.code,
            booth_number=booth_data.booth_number,
            polling_location_name=booth_data.polling_location_name,
            address=booth_data.address,
            latitude=booth_data.latitude,
            longitude=booth_data.longitude,
            male_voters=booth_data.male_voters or 0,
            female_voters=booth_data.female_voters or 0,
            other_voters=booth_data.other_voters or 0,
        )
        # Calculate total voters
        booth.total_voters = booth.male_voters + booth.female_voters + booth.other_voters
        
        db.add(booth)
        await db.commit()
        await db.refresh(booth)
        
        return booth
    
    @staticmethod
    async def update(db: AsyncSession, booth_id: UUID, booth_data: BoothUpdate) -> Optional[Booth]:
        """Update a booth."""
        booth = await BoothCRUD.get_by_id(db, Booth, booth_id)
        if not booth:
            return None
        
        update_data = booth_data.model_dump(exclude_unset=True)
        
        # Recalculate total voters if voter counts changed
        if any(field in update_data for field in ['male_voters', 'female_voters', 'other_voters']):
            male = update_data.get('male_voters', booth.male_voters)
            female = update_data.get('female_voters', booth.female_voters)
            other = update_data.get('other_voters', booth.other_voters)
            update_data['total_voters'] = male + female + other
        
        for field, value in update_data.items():
            setattr(booth, field, value)
        
        await db.commit()
        await db.refresh(booth)
        
        return booth
    
    @staticmethod
    async def search(
        db: AsyncSession,
        filters: HierarchySearchFilters,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Booth], int]:
        """Search booths with filters."""
        query = select(Booth).where(Booth.is_active == True)
        
        if filters.search:
            search_pattern = f"%{filters.search}%"
            query = query.where(
                or_(
                    Booth.name.ilike(search_pattern),
                    Booth.code.ilike(search_pattern),
                )
            )
        
        if filters.ward_id:
            query = query.where(Booth.ward_id == filters.ward_id)
        
        # Get total count
        count_query = select(func.count(Booth.id)).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit).order_by(Booth.booth_number, Booth.name)
        
        result = await db.execute(query)
        booths = list(result.scalars().all())
        
        return booths, total


# =============================================================================
# ZipCode Mapping CRUD
# =============================================================================

class ZipCodeCRUD(CRUDBase):
    """CRUD operations for zipcode mappings."""
    
    @staticmethod
    async def get_by_pincode(db: AsyncSession, pincode: str) -> Optional[ZipCodeMapping]:
        """Get zipcode mapping by pincode."""
        result = await db.execute(
            select(ZipCodeMapping)
            .where(ZipCodeMapping.pincode == pincode)
            .where(ZipCodeMapping.is_active == True)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(db: AsyncSession, mapping_data: dict) -> ZipCodeMapping:
        """Create a new zipcode mapping."""
        mapping = ZipCodeMapping(**mapping_data)
        db.add(mapping)
        await db.commit()
        await db.refresh(mapping)
        return mapping
    
    @staticmethod
    async def bulk_create(db: AsyncSession, mappings_data: List[dict]) -> List[ZipCodeMapping]:
        """Bulk create zipcode mappings."""
        mappings = []
        for data in mappings_data:
            mapping = ZipCodeMapping(**data)
            db.add(mapping)
            mappings.append(mapping)
        await db.commit()
        for mapping in mappings:
            await db.refresh(mapping)
        return mappings


# =============================================================================
# Hierarchy Tree Operations
# =============================================================================

class HierarchyTreeCRUD:
    """CRUD operations for hierarchy tree queries."""
    
    @staticmethod
    async def get_full_tree(db: AsyncSession) -> Dict[str, Any]:
        """Get the full hierarchy tree."""
        # Check cache first
        cached = await redis.cache_get(TREE_CACHE_KEY)
        if cached:
            return cached
        
        # Build tree from database
        result = await db.execute(
            select(District)
            .options(
                selectinload(District.constituencies)
                .selectinload(Constituency.wards)
                .selectinload(Ward.booths)
            )
            .where(District.is_active == True)
            .order_by(District.name)
        )
        districts = result.scalars().all()
        
        tree = []
        for district in districts:
            district_node = {
                "id": str(district.id),
                "name": district.name,
                "name_ta": district.name_ta,
                "code": district.code,
                "level": HierarchyLevel.DISTRICT.value,
                "children": []
            }
            
            for constituency in district.constituencies:
                constituency_node = {
                    "id": str(constituency.id),
                    "name": constituency.name,
                    "name_ta": constituency.name_ta,
                    "code": constituency.code,
                    "level": HierarchyLevel.CONSTITUENCY.value,
                    "children": []
                }
                
                for ward in constituency.wards:
                    ward_node = {
                        "id": str(ward.id),
                        "name": ward.name,
                        "name_ta": ward.name_ta,
                        "code": ward.code,
                        "level": HierarchyLevel.WARD.value,
                        "children": []
                    }
                    
                    for booth in ward.booths:
                        booth_node = {
                            "id": str(booth.id),
                            "name": booth.name,
                            "name_ta": booth.name_ta,
                            "code": booth.code,
                            "level": HierarchyLevel.BOOTH.value,
                            "children": []
                        }
                        ward_node["children"].append(booth_node)
                    
                    constituency_node["children"].append(ward_node)
                
                district_node["children"].append(constituency_node)
            
            tree.append(district_node)
        
        result_data = {
            "districts": tree,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Cache for 1 hour
        await redis.cache_set(TREE_CACHE_KEY, result_data, 3600)
        
        return result_data
    
    @staticmethod
    async def get_subtree(
        db: AsyncSession,
        level: str,
        node_id: UUID
    ) -> Dict[str, Any]:
        """Get subtree starting from a specific node."""
        node = None
        ancestors = []
        
        if level == HierarchyLevel.DISTRICT.value:
            result = await db.execute(
                select(District)
                .options(
                    selectinload(District.constituencies)
                    .selectinload(Constituency.wards)
                    .selectinload(Ward.booths)
                )
                .where(District.id == node_id)
            )
            node = result.scalar_one_or_none()
        
        elif level == HierarchyLevel.CONSTITUENCY.value:
            result = await db.execute(
                select(Constituency)
                .options(
                    selectinload(Constituency.wards)
                    .selectinload(Ward.booths)
                )
                .where(Constituency.id == node_id)
            )
            node = result.scalar_one_or_none()
            if node:
                # Get district ancestor
                district = await DistrictCRUD.get_by_id(db, District, node.district_id)
                if district:
                    ancestors = [{
                        "id": str(district.id),
                        "name": district.name,
                        "code": district.code,
                        "level": HierarchyLevel.DISTRICT.value
                    }]
        
        elif level == HierarchyLevel.WARD.value:
            result = await db.execute(
                select(Ward)
                .options(
                    selectinload(Ward.booths)
                )
                .where(Ward.id == node_id)
            )
            node = result.scalar_one_or_none()
            if node:
                # Get constituency and district ancestors
                constituency = await ConstituencyCRUD.get_by_id(db, Constituency, node.constituency_id)
                if constituency:
                    district = await DistrictCRUD.get_by_id(db, District, constituency.district_id)
                    if district:
                        ancestors = [
                            {
                                "id": str(district.id),
                                "name": district.name,
                                "code": district.code,
                                "level": HierarchyLevel.DISTRICT.value
                            },
                            {
                                "id": str(constituency.id),
                                "name": constituency.name,
                                "code": constituency.code,
                                "level": HierarchyLevel.CONSTITUENCY.value
                            }
                        ]
        
        if not node:
            raise NotFoundError(resource=level.capitalize(), resource_id=str(node_id))
        
        # Build subtree
        subtree_node = {
            "id": str(node.id),
            "name": node.name,
            "name_ta": getattr(node, 'name_ta', None),
            "code": node.code,
            "level": level,
            "children": []
        }
        
        # Count descendants
        descendants_count = 0
        
        if hasattr(node, 'constituencies'):  # District
            for constituency in node.constituencies:
                const_node = {
                    "id": str(constituency.id),
                    "name": constituency.name,
                    "code": constituency.code,
                    "level": HierarchyLevel.CONSTITUENCY.value,
                    "children": []
                }
                descendants_count += 1
                for ward in constituency.wards:
                    ward_node = {
                        "id": str(ward.id),
                        "name": ward.name,
                        "code": ward.code,
                        "level": HierarchyLevel.WARD.value,
                        "children": []
                    }
                    descendants_count += 1
                    for booth in ward.booths:
                        booth_node = {
                            "id": str(booth.id),
                            "name": booth.name,
                            "code": booth.code,
                            "level": HierarchyLevel.BOOTH.value,
                            "children": []
                        }
                        ward_node["children"].append(booth_node)
                    const_node["children"].append(ward_node)
                subtree_node["children"].append(const_node)
        
        elif hasattr(node, 'wards'):  # Constituency
            for ward in node.wards:
                ward_node = {
                    "id": str(ward.id),
                    "name": ward.name,
                    "code": ward.code,
                    "level": HierarchyLevel.WARD.value,
                    "children": []
                }
                descendants_count += 1
                for booth in ward.booths:
                    booth_node = {
                        "id": str(booth.id),
                        "name": booth.name,
                        "code": booth.code,
                        "level": HierarchyLevel.BOOTH.value,
                        "children": []
                    }
                    ward_node["children"].append(booth_node)
                subtree_node["children"].append(ward_node)
        
        elif hasattr(node, 'booths'):  # Ward
            for booth in node.booths:
                booth_node = {
                    "id": str(booth.id),
                    "name": booth.name,
                    "code": booth.code,
                    "level": HierarchyLevel.BOOTH.value,
                    "children": []
                }
                subtree_node["children"].append(booth_node)
            descendants_count = len(node.booths)
        
        return {
            "node": subtree_node,
            "ancestors": ancestors,
            "descendants_count": descendants_count
        }
    
    @staticmethod
    async def get_ancestors(db: AsyncSession, level: str, node_id: UUID) -> List[Dict[str, Any]]:
        """Get all ancestors of a node."""
        ancestors = []
        
        if level == HierarchyLevel.BOOTH.value:
            booth = await BoothCRUD.get_by_id(db, Booth, node_id)
            if booth:
                ward = await WardCRUD.get_by_id(db, Ward, booth.ward_id)
                if ward:
                    constituency = await ConstituencyCRUD.get_by_id(db, Constituency, ward.constituency_id)
                    if constituency:
                        district = await DistrictCRUD.get_by_id(db, District, constituency.district_id)
                        if district:
                            ancestors.append({
                                "id": str(district.id),
                                "name": district.name,
                                "code": district.code,
                                "level": HierarchyLevel.DISTRICT.value
                            })
                            ancestors.append({
                                "id": str(constituency.id),
                                "name": constituency.name,
                                "code": constituency.code,
                                "level": HierarchyLevel.CONSTITUENCY.value
                            })
                        ancestors.append({
                            "id": str(ward.id),
                            "name": ward.name,
                            "code": ward.code,
                            "level": HierarchyLevel.WARD.value
                        })
        
        elif level == HierarchyLevel.WARD.value:
            ward = await WardCRUD.get_by_id(db, Ward, node_id)
            if ward:
                constituency = await ConstituencyCRUD.get_by_id(db, Constituency, ward.constituency_id)
                if constituency:
                    district = await DistrictCRUD.get_by_id(db, District, constituency.district_id)
                    if district:
                        ancestors.append({
                            "id": str(district.id),
                            "name": district.name,
                            "code": district.code,
                            "level": HierarchyLevel.DISTRICT.value
                        })
                    ancestors.append({
                        "id": str(constituency.id),
                        "name": constituency.name,
                        "code": constituency.code,
                        "level": HierarchyLevel.CONSTITUENCY.value
                    })
        
        elif level == HierarchyLevel.CONSTITUENCY.value:
            constituency = await ConstituencyCRUD.get_by_id(db, Constituency, node_id)
            if constituency:
                district = await DistrictCRUD.get_by_id(db, District, constituency.district_id)
                if district:
                    ancestors.append({
                        "id": str(district.id),
                        "name": district.name,
                        "code": district.code,
                        "level": HierarchyLevel.DISTRICT.value
                    })
        
        return ancestors


# =============================================================================
# Geographic Search Operations
# =============================================================================

class GeoSearchCRUD:
    """Geographic search operations using coordinates."""
    
    @staticmethod
    def haversine_distance(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """Calculate distance between two points using Haversine formula."""
        R = 6371  # Earth's radius in kilometers
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    @staticmethod
    async def search_nearby(
        db: AsyncSession,
        lat: float,
        lng: float,
        radius_km: float = 10,
        level: str = "booth",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for hierarchy elements near a point."""
        results = []
        
        if level in ["district", "all"]:
            query = select(District).where(District.is_active == True)
            if lat and lng:
                # Simple bounding box filter for efficiency
                result = await db.execute(query)
                districts = result.scalars().all()
                for d in districts:
                    if d.latitude and d.longitude:
                        distance = GeoSearchCRUD.haversine_distance(lat, lng, d.latitude, d.longitude)
                        if distance <= radius_km:
                            results.append({
                                "id": d.id,
                                "name": d.name,
                                "code": d.code,
                                "level": HierarchyLevel.DISTRICT.value,
                                "distance_km": round(distance, 2),
                                "latitude": d.latitude,
                                "longitude": d.longitude
                            })
        
        if level in ["constituency", "all"]:
            query = select(Constituency).where(Constituency.is_active == True)
            if lat and lng:
                result = await db.execute(query)
                constituencies = result.scalars().all()
                for c in constituencies:
                    if c.latitude and c.longitude:
                        distance = GeoSearchCRUD.haversine_distance(lat, lng, c.latitude, c.longitude)
                        if distance <= radius_km:
                            results.append({
                                "id": c.id,
                                "name": c.name,
                                "code": c.code,
                                "level": HierarchyLevel.CONSTITUENCY.value,
                                "distance_km": round(distance, 2),
                                "latitude": c.latitude,
                                "longitude": c.longitude
                            })
        
        if level in ["ward", "all"]:
            query = select(Ward).where(Ward.is_active == True)
            if lat and lng:
                result = await db.execute(query)
                wards = result.scalars().all()
                for w in wards:
                    if w.latitude and w.longitude:
                        distance = GeoSearchCRUD.haversine_distance(lat, lng, w.latitude, w.longitude)
                        if distance <= radius_km:
                            results.append({
                                "id": w.id,
                                "name": w.name,
                                "code": w.code,
                                "level": HierarchyLevel.WARD.value,
                                "distance_km": round(distance, 2),
                                "latitude": w.latitude,
                                "longitude": w.longitude
                            })
        
        if level in ["booth", "all"]:
            query = select(Booth).where(Booth.is_active == True)
            if lat and lng:
                result = await db.execute(query)
                booths = result.scalars().all()
                for b in booths:
                    if b.latitude and b.longitude:
                        distance = GeoSearchCRUD.haversine_distance(lat, lng, b.latitude, b.longitude)
                        if distance <= radius_km:
                            results.append({
                                "id": b.id,
                                "name": b.name,
                                "code": b.code,
                                "level": HierarchyLevel.BOOTH.value,
                                "distance_km": round(distance, 2),
                                "latitude": b.latitude,
                                "longitude": b.longitude
                            })
        
        # Sort by distance and limit
        results.sort(key=lambda x: x["distance_km"])
        return results[:limit]


# =============================================================================
# Statistics Operations
# =============================================================================

class HierarchyStatsCRUD:
    """Statistics operations for hierarchy."""
    
    @staticmethod
    async def get_stats(db: AsyncSession) -> Dict[str, Any]:
        """Get hierarchy statistics."""
        # Count totals
        total_districts = await DistrictCRUD.count(db, District, is_active=True)
        total_constituencies = await ConstituencyCRUD.count(db, Constituency, is_active=True)
        total_wards = await WardCRUD.count(db, Ward, is_active=True)
        total_booths = await BoothCRUD.count(db, Booth, is_active=True)
        
        # Count total voters
        voters_result = await db.execute(
            select(func.sum(Booth.total_voters))
            .where(Booth.is_active == True)
        )
        total_voters = voters_result.scalar() or 0
        
        # By constituency type
        type_counts = {}
        type_result = await db.execute(
            select(Constituency.constituency_type, func.count(Constituency.id))
            .where(Constituency.is_active == True)
            .group_by(Constituency.constituency_type)
        )
        for row in type_result:
            type_counts[row[0]] = row[1]
        
        # By district
        district_counts = []
        district_result = await db.execute(
            select(
                District.id,
                District.name,
                func.count(Constituency.id)
            )
            .outerjoin(Constituency)
            .where(District.is_active == True)
            .group_by(District.id, District.name)
            .order_by(District.name)
        )
        for row in district_result:
            district_counts.append({
                "district_id": str(row[0]),
                "district_name": row[1],
                "constituencies_count": row[2]
            })
        
        return {
            "total_districts": total_districts,
            "total_constituencies": total_constituencies,
            "total_wards": total_wards,
            "total_booths": total_booths,
            "total_voters": total_voters,
            "by_constituency_type": type_counts,
            "by_district": district_counts
        }
    
    @staticmethod
    async def export_hierarchy(
        db: AsyncSession,
        level: str = "district",
        format: str = "json"
    ) -> Any:
        """Export hierarchy data."""
        if level == "district":
            result = await db.execute(
                select(District)
                .where(District.is_active == True)
                .order_by(District.name)
            )
            items = result.scalars().all()
        
        elif level == "constituency":
            result = await db.execute(
                select(Constituency)
                .options(joinedload(Constituency.district))
                .where(Constituency.is_active == True)
                .order_by(Constituency.name)
            )
            items = result.scalars().all()
        
        elif level == "ward":
            result = await db.execute(
                select(Ward)
                .options(joinedload(Ward.constituency))
                .where(Ward.is_active == True)
                .order_by(Ward.name)
            )
            items = result.scalars().all()
        
        elif level == "booth":
            result = await db.execute(
                select(Booth)
                .options(joinedload(Booth.ward))
                .where(Booth.is_active == True)
                .order_by(Booth.name)
            )
            items = result.scalars().all()
        
        else:
            raise ValidationError(message=f"Invalid export level: {level}")
        
        if format == "csv":
            output = io.StringIO()
            if items:
                field_names = [c.name for c in items[0].__table__.columns]
                writer = csv.DictWriter(output, fieldnames=field_names)
                writer.writeheader()
                
                for item in items:
                    row = {}
                    for field in field_names:
                        value = getattr(item, field, None)
                        if isinstance(value, datetime):
                            value = value.isoformat()
                        elif isinstance(value, UUID):
                            value = str(value)
                        row[field] = value
                    writer.writerow(row)
            
            return output.getvalue()
        
        else:  # json
            return json.dumps([
                {
                    "id": str(item.id),
                    "name": item.name,
                    "code": item.code,
                    "is_active": item.is_active,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "updated_at": item.updated_at.isoformat() if item.updated_at else None
                }
                for item in items
            ], indent=2)


# =============================================================================
# Bulk Operations
# =============================================================================

class BulkHierarchyCRUD:
    """Bulk operations for hierarchy."""
    
    @staticmethod
    async def import_hierarchy(
        db: AsyncSession,
        items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Import hierarchy items in bulk."""
        successful = 0
        failed = 0
        errors = []
        
        for idx, item in enumerate(items):
            try:
                item_type = item.get("type")
                data = item.get("data", {})
                
                if item_type == "district":
                    create_schema = DistrictCreate(**data)
                    await DistrictCRUD.create(db, create_schema)
                
                elif item_type == "constituency":
                    create_schema = ConstituencyCreate(**data)
                    await ConstituencyCRUD.create(db, create_schema)
                
                elif item_type == "ward":
                    create_schema = WardCreate(**data)
                    await WardCRUD.create(db, create_schema)
                
                elif item_type == "booth":
                    create_schema = BoothCreate(**data)
                    await BoothCRUD.create(db, create_schema)
                
                else:
                    raise ValidationError(message=f"Unknown item type: {item_type}")
                
                successful += 1
            
            except Exception as e:
                failed += 1
                errors.append({
                    "row": idx + 1,
                    "error": str(e),
                    "item": item
                })
        
        # Invalidate tree cache
        await redis.cache_delete(TREE_CACHE_KEY)
        
        return {
            "total": len(items),
            "successful": successful,
            "failed": failed,
            "errors": errors
        }
