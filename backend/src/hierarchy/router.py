"""
Hierarchy Router
API routes for hierarchy management (district → constituency → ward → booth).
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import NotFoundError, AlreadyExistsError, AuthorizationError
from src.core.deps import get_current_user_id

from src.hierarchy.models import District, Constituency, Ward, Booth

from src.hierarchy.schemas import (
    DistrictCreate,
    DistrictUpdate,
    DistrictResponse,
    DistrictDetailResponse,
    PaginatedDistrictResponse,
    ConstituencyCreate,
    ConstituencyUpdate,
    ConstituencyResponse,
    ConstituencyDetailResponse,
    PaginatedConstituencyResponse,
    WardCreate,
    WardUpdate,
    WardResponse,
    WardDetailResponse,
    PaginatedWardResponse,
    BoothCreate,
    BoothUpdate,
    BoothResponse,
    BoothDetailResponse,
    PaginatedBoothResponse,
    ZipCodeMappingCreate,
    ZipCodeMappingResponse,
    ZipCodeLookupResponse,
    HierarchyTreeResponse,
    SubTreeResponse,
    HierarchySearchFilters,
    GeoSearchResult,
    HierarchyStatsResponse,
    BulkImportRequest,
    BulkImportResult,
    ExportRequest,
    ApiResponse,
    ErrorResponse,
    HierarchyTreeNode,
)
from src.hierarchy.deps import (
    get_district_by_id,
    get_constituency_by_id,
    get_ward_by_id,
    get_booth_by_id,
    DBSession,
    CurrentUserId,
)
from src.hierarchy.crud import (
    DistrictCRUD,
    ConstituencyCRUD,
    WardCRUD,
    BoothCRUD,
    ZipCodeCRUD,
    HierarchyTreeCRUD,
    GeoSearchCRUD,
    HierarchyStatsCRUD,
    BulkHierarchyCRUD,
)


router = APIRouter(prefix="/hierarchy", tags=["Hierarchy"])


# =============================================================================
# District Endpoints
# =============================================================================

@router.get("/districts", response_model=PaginatedDistrictResponse)
async def list_districts(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str = Query(None, description="Search by name or code"),
    db: AsyncSession = Depends(get_db),
):
    """List all districts with pagination."""
    districts, total = await DistrictCRUD.search(db, search, page, limit)
    
    return PaginatedDistrictResponse(
        districts=[
            DistrictResponse(
                id=d.id,
                name=d.name,
                name_ta=d.name_ta,
                code=d.code,
                state=d.state,
                latitude=d.latitude,
                longitude=d.longitude,
                is_active=d.is_active,
                created_at=d.created_at,
                updated_at=d.updated_at,
                constituencies_count=len(d.constituencies) if hasattr(d, 'constituencies') else 0
            )
            for d in districts
        ],
        total=total,
        page=page,
        limit=limit,
        total_pages=(total + limit - 1) // limit if total > 0 else 1
    )


@router.post("/districts", response_model=DistrictResponse, status_code=status.HTTP_201_CREATED)
async def create_district(
    district_data: DistrictCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create a new district."""
    try:
        district = await DistrictCRUD.create(db, district_data)
        return DistrictResponse(
            id=district.id,
            name=district.name,
            name_ta=district.name_ta,
            code=district.code,
            state=district.state,
            latitude=district.latitude,
            longitude=district.longitude,
            is_active=district.is_active,
            created_at=district.created_at,
            updated_at=district.updated_at,
            constituencies_count=0
        )
    except AlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=e.to_dict())


@router.get("/districts/{district_id}", response_model=DistrictDetailResponse)
async def get_district(
    district: District = Depends(get_district_by_id),
    db: AsyncSession = Depends(get_db),
):
    """Get district details with constituencies."""
    constituencies = await ConstituencyCRUD.get_by_district(db, district.id)
    
    return DistrictDetailResponse(
        id=district.id,
        name=district.name,
        name_ta=district.name_ta,
        code=district.code,
        state=district.state,
        latitude=district.latitude,
        longitude=district.longitude,
        is_active=district.is_active,
        created_at=district.created_at,
        updated_at=district.updated_at,
        constituencies_count=len(constituencies),
        constituencies=[
            ConstituencyResponse(
                id=c.id,
                district_id=c.district_id,
                name=c.name,
                name_ta=c.name_ta,
                code=c.code,
                constituency_type=c.constituency_type,
                electorate_count=c.electorate_count,
                polling_stations_count=c.polling_stations_count,
                latitude=c.latitude,
                longitude=c.longitude,
                is_active=c.is_active,
                created_at=c.created_at,
                updated_at=c.updated_at,
                wards_count=0
            )
            for c in constituencies
        ]
    )


@router.put("/districts/{district_id}", response_model=DistrictResponse)
async def update_district(
    district_id: UUID,
    district_data: DistrictUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update a district."""
    district = await DistrictCRUD.update(db, district_id, district_data)
    if not district:
        raise NotFoundError(resource="District", resource_id=str(district_id))
    
    return DistrictResponse(
        id=district.id,
        name=district.name,
        name_ta=district.name_ta,
        code=district.code,
        state=district.state,
        latitude=district.latitude,
        longitude=district.longitude,
        is_active=district.is_active,
        created_at=district.created_at,
        updated_at=district.updated_at,
        constituencies_count=0
    )


@router.delete("/districts/{district_id}", response_model=ApiResponse)
async def delete_district(
    district_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Delete a district (soft delete)."""
    deleted = await DistrictCRUD.delete(db, District, district_id)
    if not deleted:
        raise NotFoundError(resource="District", resource_id=str(district_id))
    
    return ApiResponse(
        success=True,
        message="District deleted successfully",
    )


# =============================================================================
# Constituency Endpoints
# =============================================================================

@router.get("/constituencies", response_model=PaginatedConstituencyResponse)
async def list_constituencies(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    district_id: UUID = Query(None, description="Filter by district"),
    constituency_type: str = Query(None, description="Filter by type"),
    search: str = Query(None, description="Search by name or code"),
    db: AsyncSession = Depends(get_db),
):
    """List all constituencies with pagination."""
    filters = HierarchySearchFilters(
        search=search,
        district_id=district_id,
        constituency_type=constituency_type
    )
    constituencies, total = await ConstituencyCRUD.search(db, filters, page, limit)
    
    return PaginatedConstituencyResponse(
        constituencies=[
            ConstituencyResponse(
                id=c.id,
                district_id=c.district_id,
                name=c.name,
                name_ta=c.name_ta,
                code=c.code,
                constituency_type=c.constituency_type,
                electorate_count=c.electorate_count,
                polling_stations_count=c.polling_stations_count,
                latitude=c.latitude,
                longitude=c.longitude,
                is_active=c.is_active,
                created_at=c.created_at,
                updated_at=c.updated_at,
                wards_count=len(c.wards) if hasattr(c, 'wards') else 0
            )
            for c in constituencies
        ],
        total=total,
        page=page,
        limit=limit,
        total_pages=(total + limit - 1) // limit if total > 0 else 1
    )


@router.post("/constituencies", response_model=ConstituencyResponse, status_code=status.HTTP_201_CREATED)
async def create_constituency(
    constituency_data: ConstituencyCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create a new constituency."""
    try:
        constituency = await ConstituencyCRUD.create(db, constituency_data)
        return ConstituencyResponse(
            id=constituency.id,
            district_id=constituency.district_id,
            name=constituency.name,
            name_ta=constituency.name_ta,
            code=constituency.code,
            constituency_type=constituency.constituency_type,
            electorate_count=constituency.electorate_count,
            polling_stations_count=constituency.polling_stations_count,
            latitude=constituency.latitude,
            longitude=constituency.longitude,
            is_active=constituency.is_active,
            created_at=constituency.created_at,
            updated_at=constituency.updated_at,
            wards_count=0
        )
    except (AlreadyExistsError, NotFoundError) as e:
        raise HTTPException(status_code=409 if isinstance(e, AlreadyExistsError) else 404, detail=e.to_dict())


@router.get("/constituencies/{constituency_id}", response_model=ConstituencyDetailResponse)
async def get_constituency(
    constituency: Constituency = Depends(get_constituency_by_id),
    db: AsyncSession = Depends(get_db),
):
    """Get constituency details with wards."""
    district = await DistrictCRUD.get_by_id(db, District, constituency.district_id)
    wards = await WardCRUD.get_by_constituency(db, constituency.id)
    
    return ConstituencyDetailResponse(
        id=constituency.id,
        district_id=constituency.district_id,
        name=constituency.name,
        name_ta=constituency.name_ta,
        code=constituency.code,
        constituency_type=constituency.constituency_type,
        electorate_count=constituency.electorate_count,
        polling_stations_count=constituency.polling_stations_count,
        latitude=constituency.latitude,
        longitude=constituency.longitude,
        is_active=constituency.is_active,
        created_at=constituency.created_at,
        updated_at=constituency.updated_at,
        wards_count=len(wards),
        district=DistrictResponse(
            id=district.id,
            name=district.name,
            name_ta=district.name_ta,
            code=district.code,
            state=district.state,
            latitude=district.latitude,
            longitude=district.longitude,
            is_active=district.is_active,
            created_at=district.created_at,
            updated_at=district.updated_at,
            constituencies_count=0
        ) if district else None,
        wards=[
            WardResponse(
                id=w.id,
                constituency_id=w.constituency_id,
                name=w.name,
                name_ta=w.name_ta,
                code=w.code,
                ward_number=w.ward_number,
                latitude=w.latitude,
                longitude=w.longitude,
                is_active=w.is_active,
                created_at=w.created_at,
                updated_at=w.updated_at,
                booths_count=0
            )
            for w in wards
        ]
    )


@router.put("/constituencies/{constituency_id}", response_model=ConstituencyResponse)
async def update_constituency(
    constituency_id: UUID,
    constituency_data: ConstituencyUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update a constituency."""
    constituency = await ConstituencyCRUD.update(db, constituency_id, constituency_data)
    if not constituency:
        raise NotFoundError(resource="Constituency", resource_id=str(constituency_id))
    
    return ConstituencyResponse(
        id=constituency.id,
        district_id=constituency.district_id,
        name=constituency.name,
        name_ta=constituency.name_ta,
        code=constituency.code,
        constituency_type=constituency.constituency_type,
        electorate_count=constituency.electorate_count,
        polling_stations_count=constituency.polling_stations_count,
        latitude=constituency.latitude,
        longitude=constituency.longitude,
        is_active=constituency.is_active,
        created_at=constituency.created_at,
        updated_at=constituency.updated_at,
        wards_count=0
    )


@router.delete("/constituencies/{constituency_id}", response_model=ApiResponse)
async def delete_constituency(
    constituency_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Delete a constituency (soft delete)."""
    deleted = await ConstituencyCRUD.delete(db, Constituency, constituency_id)
    if not deleted:
        raise NotFoundError(resource="Constituency", resource_id=str(constituency_id))
    
    return ApiResponse(
        success=True,
        message="Constituency deleted successfully",
    )


# =============================================================================
# Ward Endpoints
# =============================================================================

@router.get("/wards", response_model=PaginatedWardResponse)
async def list_wards(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    constituency_id: UUID = Query(None, description="Filter by constituency"),
    search: str = Query(None, description="Search by name or code"),
    db: AsyncSession = Depends(get_db),
):
    """List all wards with pagination."""
    filters = HierarchySearchFilters(
        search=search,
        constituency_id=constituency_id
    )
    wards, total = await WardCRUD.search(db, filters, page, limit)
    
    return PaginatedWardResponse(
        wards=[
            WardResponse(
                id=w.id,
                constituency_id=w.constituency_id,
                name=w.name,
                name_ta=w.name_ta,
                code=w.code,
                ward_number=w.ward_number,
                latitude=w.latitude,
                longitude=w.longitude,
                is_active=w.is_active,
                created_at=w.created_at,
                updated_at=w.updated_at,
                booths_count=len(w.booths) if hasattr(w, 'booths') else 0
            )
            for w in wards
        ],
        total=total,
        page=page,
        limit=limit,
        total_pages=(total + limit - 1) // limit if total > 0 else 1
    )


@router.post("/wards", response_model=WardResponse, status_code=status.HTTP_201_CREATED)
async def create_ward(
    ward_data: WardCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create a new ward."""
    try:
        ward = await WardCRUD.create(db, ward_data)
        return WardResponse(
            id=ward.id,
            constituency_id=ward.constituency_id,
            name=ward.name,
            name_ta=ward.name_ta,
            code=ward.code,
            ward_number=ward.ward_number,
            latitude=ward.latitude,
            longitude=ward.longitude,
            is_active=ward.is_active,
            created_at=ward.created_at,
            updated_at=ward.updated_at,
            booths_count=0
        )
    except (AlreadyExistsError, NotFoundError) as e:
        raise HTTPException(status_code=409 if isinstance(e, AlreadyExistsError) else 404, detail=e.to_dict())


@router.get("/wards/{ward_id}", response_model=WardDetailResponse)
async def get_ward(
    ward: Ward = Depends(get_ward_by_id),
    db: AsyncSession = Depends(get_db),
):
    """Get ward details with booths."""
    constituency = await ConstituencyCRUD.get_by_id(db, Constituency, ward.constituency_id)
    booths = await BoothCRUD.get_by_ward(db, ward.id)
    
    return WardDetailResponse(
        id=ward.id,
        constituency_id=ward.constituency_id,
        name=ward.name,
        name_ta=ward.name_ta,
        code=ward.code,
        ward_number=ward.ward_number,
        latitude=ward.latitude,
        longitude=ward.longitude,
        is_active=ward.is_active,
        created_at=ward.created_at,
        updated_at=ward.updated_at,
        booths_count=len(booths),
        constituency=ConstituencyResponse(
            id=constituency.id,
            district_id=constituency.district_id,
            name=constituency.name,
            name_ta=constituency.name_ta,
            code=constituency.code,
            constituency_type=constituency.constituency_type,
            electorate_count=constituency.electorate_count,
            polling_stations_count=constituency.polling_stations_count,
            latitude=constituency.latitude,
            longitude=constituency.longitude,
            is_active=constituency.is_active,
            created_at=constituency.created_at,
            updated_at=constituency.updated_at,
            wards_count=0
        ) if constituency else None,
        booths=[
            BoothResponse(
                id=b.id,
                ward_id=b.ward_id,
                name=b.name,
                name_ta=b.name_ta,
                code=b.code,
                booth_number=b.booth_number,
                polling_location_name=b.polling_location_name,
                address=b.address,
                latitude=b.latitude,
                longitude=b.longitude,
                male_voters=b.male_voters,
                female_voters=b.female_voters,
                other_voters=b.other_voters,
                total_voters=b.total_voters,
                is_active=b.is_active,
                created_at=b.created_at,
                updated_at=b.updated_at
            )
            for b in booths
        ]
    )


@router.put("/wards/{ward_id}", response_model=WardResponse)
async def update_ward(
    ward_id: UUID,
    ward_data: WardUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update a ward."""
    ward = await WardCRUD.update(db, ward_id, ward_data)
    if not ward:
        raise NotFoundError(resource="Ward", resource_id=str(ward_id))
    
    return WardResponse(
        id=ward.id,
        constituency_id=ward.constituency_id,
        name=ward.name,
        name_ta=ward.name_ta,
        code=ward.code,
        ward_number=ward.ward_number,
        latitude=ward.latitude,
        longitude=ward.longitude,
        is_active=ward.is_active,
        created_at=ward.created_at,
        updated_at=ward.updated_at,
        booths_count=0
    )


@router.delete("/wards/{ward_id}", response_model=ApiResponse)
async def delete_ward(
    ward_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Delete a ward (soft delete)."""
    deleted = await WardCRUD.delete(db, Ward, ward_id)
    if not deleted:
        raise NotFoundError(resource="Ward", resource_id=str(ward_id))
    
    return ApiResponse(
        success=True,
        message="Ward deleted successfully",
    )


# =============================================================================
# Booth Endpoints
# =============================================================================

@router.get("/booths", response_model=PaginatedBoothResponse)
async def list_booths(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    ward_id: UUID = Query(None, description="Filter by ward"),
    search: str = Query(None, description="Search by name or code"),
    db: AsyncSession = Depends(get_db),
):
    """List all booths with pagination."""
    filters = HierarchySearchFilters(
        search=search,
        ward_id=ward_id
    )
    booths, total = await BoothCRUD.search(db, filters, page, limit)
    
    return PaginatedBoothResponse(
        booths=[
            BoothResponse(
                id=b.id,
                ward_id=b.ward_id,
                name=b.name,
                name_ta=b.name_ta,
                code=b.code,
                booth_number=b.booth_number,
                polling_location_name=b.polling_location_name,
                address=b.address,
                latitude=b.latitude,
                longitude=b.longitude,
                male_voters=b.male_voters,
                female_voters=b.female_voters,
                other_voters=b.other_voters,
                total_voters=b.total_voters,
                is_active=b.is_active,
                created_at=b.created_at,
                updated_at=b.updated_at
            )
            for b in booths
        ],
        total=total,
        page=page,
        limit=limit,
        total_pages=(total + limit - 1) // limit if total > 0 else 1
    )


@router.post("/booths", response_model=BoothResponse, status_code=status.HTTP_201_CREATED)
async def create_booth(
    booth_data: BoothCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create a new booth."""
    try:
        booth = await BoothCRUD.create(db, booth_data)
        return BoothResponse(
            id=booth.id,
            ward_id=booth.ward_id,
            name=booth.name,
            name_ta=booth.name_ta,
            code=booth.code,
            booth_number=booth.booth_number,
            polling_location_name=booth.polling_location_name,
            address=booth.address,
            latitude=booth.latitude,
            longitude=booth.longitude,
            male_voters=booth.male_voters,
            female_voters=booth.female_voters,
            other_voters=booth.other_voters,
            total_voters=booth.total_voters,
            is_active=booth.is_active,
            created_at=booth.created_at,
            updated_at=booth.updated_at
        )
    except (AlreadyExistsError, NotFoundError) as e:
        raise HTTPException(status_code=409 if isinstance(e, AlreadyExistsError) else 404, detail=e.to_dict())


@router.get("/booths/{booth_id}", response_model=BoothDetailResponse)
async def get_booth(
    booth: Booth = Depends(get_booth_by_id),
    db: AsyncSession = Depends(get_db),
):
    """Get booth details with ward."""
    ward = await WardCRUD.get_by_id(db, Ward, booth.ward_id)
    
    return BoothDetailResponse(
        id=booth.id,
        ward_id=booth.ward_id,
        name=booth.name,
        name_ta=booth.name_ta,
        code=booth.code,
        booth_number=booth.booth_number,
        polling_location_name=booth.polling_location_name,
        address=booth.address,
        latitude=booth.latitude,
        longitude=booth.longitude,
        male_voters=booth.male_voters,
        female_voters=booth.female_voters,
        other_voters=booth.other_voters,
        total_voters=booth.total_voters,
        is_active=booth.is_active,
        created_at=booth.created_at,
        updated_at=booth.updated_at,
        ward=WardResponse(
            id=ward.id,
            constituency_id=ward.constituency_id,
            name=ward.name,
            name_ta=ward.name_ta,
            code=ward.code,
            ward_number=ward.ward_number,
            latitude=ward.latitude,
            longitude=ward.longitude,
            is_active=ward.is_active,
            created_at=ward.created_at,
            updated_at=ward.updated_at,
            booths_count=0
        ) if ward else None
    )


@router.put("/booths/{booth_id}", response_model=BoothResponse)
async def update_booth(
    booth_id: UUID,
    booth_data: BoothUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update a booth."""
    booth = await BoothCRUD.update(db, booth_id, booth_data)
    if not booth:
        raise NotFoundError(resource="Booth", resource_id=str(booth_id))
    
    return BoothResponse(
        id=booth.id,
        ward_id=booth.ward_id,
        name=booth.name,
        name_ta=booth.name_ta,
        code=booth.code,
        booth_number=booth.booth_number,
        polling_location_name=booth.polling_location_name,
        address=booth.address,
        latitude=booth.latitude,
        longitude=booth.longitude,
        male_voters=booth.male_voters,
        female_voters=booth.female_voters,
        other_voters=booth.other_voters,
        total_voters=booth.total_voters,
        is_active=booth.is_active,
        created_at=booth.created_at,
        updated_at=booth.updated_at
    )


@router.delete("/booths/{booth_id}", response_model=ApiResponse)
async def delete_booth(
    booth_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Delete a booth (soft delete)."""
    deleted = await BoothCRUD.delete(db, Booth, booth_id)
    if not deleted:
        raise NotFoundError(resource="Booth", resource_id=str(booth_id))
    
    return ApiResponse(
        success=True,
        message="Booth deleted successfully",
    )


# =============================================================================
# Tree & Search Endpoints
# =============================================================================

@router.get("/tree", response_model=HierarchyTreeResponse)
async def get_full_tree(db: AsyncSession = Depends(get_db)):
    """Get the full hierarchy tree."""
    tree_data = await HierarchyTreeCRUD.get_full_tree(db)
    return HierarchyTreeResponse(
        districts=tree_data["districts"],
        generated_at=tree_data["generated_at"]
    )


@router.get("/tree/{level}/{node_id}", response_model=SubTreeResponse)
async def get_subtree(
    level: str,
    node_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get subtree starting from a specific node."""
    subtree_data = await HierarchyTreeCRUD.get_subtree(db, level, node_id)
    return SubTreeResponse(
        node=subtree_data["node"],
        ancestors=subtree_data["ancestors"],
        descendants_count=subtree_data["descendants_count"]
    )


@router.get("/search", response_model=list[GeoSearchResult])
async def search_hierarchy(
    search: str = Query(None, description="Search by name or code"),
    lat: float = Query(None, description="Latitude for geo search"),
    lng: float = Query(None, description="Longitude for geo search"),
    radius_km: float = Query(10, ge=0, le=100, description="Search radius in km"),
    level: str = Query("all", description="Filter by level: district, constituency, ward, booth, all"),
    db: AsyncSession = Depends(get_db),
):
    """Search hierarchy by name/code or geographic location."""
    if lat and lng:
        results = await GeoSearchCRUD.search_nearby(db, lat, lng, radius_km, level)
        return results
    else:
        # Text search
        results = []
        if level in ["district", "all"]:
            districts, _ = await DistrictCRUD.search(db, search, 1, 50)
            for d in districts:
                results.append({
                    "id": d.id,
                    "name": d.name,
                    "code": d.code,
                    "level": "district",
                    "distance_km": 0,
                    "latitude": d.latitude,
                    "longitude": d.longitude
                })
        if level in ["constituency", "all"]:
            filters = HierarchySearchFilters(search=search)
            constituencies, _ = await ConstituencyCRUD.search(db, filters, 1, 50)
            for c in constituencies:
                results.append({
                    "id": c.id,
                    "name": c.name,
                    "code": c.code,
                    "level": "constituency",
                    "distance_km": 0,
                    "latitude": c.latitude,
                    "longitude": c.longitude
                })
        return results


@router.get("/lookup", response_model=ZipCodeLookupResponse)
async def lookup_by_pincode(
    pincode: str = Query(..., min_length=5, max_length=10, description="Pincode to lookup"),
    db: AsyncSession = Depends(get_db),
):
    """Lookup hierarchy by pincode."""
    mapping = await ZipCodeCRUD.get_by_pincode(db, pincode)
    
    if not mapping:
        return ZipCodeLookupResponse(
            pincode=pincode,
            district=None,
            constituency=None,
            ward=None,
            booth=None
        )
    
    district = await DistrictCRUD.get_by_id(db, District, mapping.district_id)
    constituency = None
    ward = None
    booth = None
    
    if mapping.constituency_id:
        constituency = await ConstituencyCRUD.get_by_id(db, Constituency, mapping.constituency_id)
    if mapping.ward_id:
        ward = await WardCRUD.get_by_id(db, Ward, mapping.ward_id)
    if mapping.booth_id:
        booth = await BoothCRUD.get_by_id(db, Booth, mapping.booth_id)
    
    return ZipCodeLookupResponse(
        pincode=pincode,
        district=DistrictResponse(
            id=district.id,
            name=district.name,
            name_ta=district.name_ta,
            code=district.code,
            state=district.state,
            latitude=district.latitude,
            longitude=district.longitude,
            is_active=district.is_active,
            created_at=district.created_at,
            updated_at=district.updated_at,
            constituencies_count=0
        ) if district else None,
        constituency=ConstituencyResponse(
            id=constituency.id,
            district_id=constituency.district_id,
            name=constituency.name,
            name_ta=constituency.name_ta,
            code=constituency.code,
            constituency_type=constituency.constituency_type,
            electorate_count=constituency.electorate_count,
            polling_stations_count=constituency.polling_stations_count,
            latitude=constituency.latitude,
            longitude=constituency.longitude,
            is_active=constituency.is_active,
            created_at=constituency.created_at,
            updated_at=constituency.updated_at,
            wards_count=0
        ) if constituency else None,
        ward=WardResponse(
            id=ward.id,
            constituency_id=ward.constituency_id,
            name=ward.name,
            name_ta=ward.name_ta,
            code=ward.code,
            ward_number=ward.ward_number,
            latitude=ward.latitude,
            longitude=ward.longitude,
            is_active=ward.is_active,
            created_at=ward.created_at,
            updated_at=ward.updated_at,
            booths_count=0
        ) if ward else None,
        booth=BoothResponse(
            id=booth.id,
            ward_id=booth.ward_id,
            name=booth.name,
            name_ta=booth.name_ta,
            code=booth.code,
            booth_number=booth.booth_number,
            polling_location_name=booth.polling_location_name,
            address=booth.address,
            latitude=booth.latitude,
            longitude=booth.longitude,
            male_voters=booth.male_voters,
            female_voters=booth.female_voters,
            other_voters=booth.other_voters,
            total_voters=booth.total_voters,
            is_active=booth.is_active,
            created_at=booth.created_at,
            updated_at=booth.updated_at
        ) if booth else None,
        area_name=mapping.area_name,
        city=mapping.city
    )


@router.get("/stats", response_model=HierarchyStatsResponse)
async def get_hierarchy_stats(db: AsyncSession = Depends(get_db)):
    """Get hierarchy statistics."""
    stats = await HierarchyStatsCRUD.get_stats(db)
    return HierarchyStatsResponse(
        stats=stats,
        generated_at=datetime.now(timezone.utc).isoformat()
    )


# =============================================================================
# Bulk Operations
# =============================================================================

@router.post("/bulk/import", response_model=BulkImportResult)
async def bulk_import_hierarchy(
    import_data: BulkImportRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Bulk import hierarchy data."""
    items = [{"type": item.type, "data": item.data} for item in import_data.items]
    result = await BulkHierarchyCRUD.import_hierarchy(db, items)
    return BulkImportResult(**result)


@router.get("/export")
async def export_hierarchy(
    level: str = Query("district", description="Export level: district, constituency, ward, booth"),
    format: str = Query("json", description="Export format: json, csv"),
    db: AsyncSession = Depends(get_db),
):
    """Export hierarchy data."""
    if format == "csv":
        from fastapi.responses import Response
        content = await HierarchyStatsCRUD.export_hierarchy(db, level, "csv")
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=hierarchy_{level}.csv"}
        )
    else:
        content = await HierarchyStatsCRUD.export_hierarchy(db, level, "json")
        return {"data": content}


# Import datetime for stats
from datetime import datetime, timezone
