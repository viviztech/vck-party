"""
Hierarchy Schemas
Pydantic schemas for hierarchy-related API requests and responses.
"""

from datetime import datetime
from typing import List, Optional, Any, Dict
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict

from src.hierarchy.models import HierarchyLevel, ConstituencyType


# =============================================================================
# Base Schemas
# =============================================================================

class HierarchyBase(BaseModel):
    """Base hierarchy schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    name_ta: Optional[str] = Field(None, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)


# =============================================================================
# District Schemas
# =============================================================================

class DistrictBase(HierarchyBase):
    """Base district schema."""
    state: Optional[str] = Field(default="Tamil Nadu", max_length=100)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class DistrictCreate(DistrictBase):
    """Schema for creating a district."""
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Chennai",
                "name_ta": "சென்னை",
                "code": "CHN",
                "state": "Tamil Nadu",
                "latitude": 13.0827,
                "longitude": 80.2707
            }
        }
    }


class DistrictUpdate(BaseModel):
    """Schema for updating a district."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    name_ta: Optional[str] = Field(None, max_length=255)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class DistrictResponse(DistrictBase):
    """Schema for district response."""
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    constituencies_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class DistrictDetailResponse(DistrictResponse):
    """Detailed district response with constituencies."""
    constituencies: List["ConstituencyResponse"] = []
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Constituency Schemas
# =============================================================================

class ConstituencyBase(HierarchyBase):
    """Base constituency schema."""
    constituency_type: Optional[str] = Field(default=ConstituencyType.ASSEMBLY.value)
    electorate_count: Optional[int] = Field(default=0, ge=0)
    polling_stations_count: Optional[int] = Field(default=0, ge=0)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ConstituencyCreate(BaseModel):
    """Schema for creating a constituency."""
    district_id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    name_ta: Optional[str] = Field(None, max_length=100)
    code: str = Field(..., min_length=1, max_length=50)
    constituency_type: Optional[str] = Field(default=ConstituencyType.ASSEMBLY.value)
    electorate_count: Optional[int] = Field(default=0, ge=0)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "district_id": "uuid",
                "name": "Chennai North",
                "name_ta": "சென்னை வடக்கு",
                "code": "CHN.NORTH",
                "constituency_type": "assembly",
                "electorate_count": 250000
            }
        }
    }


class ConstituencyUpdate(BaseModel):
    """Schema for updating a constituency."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    name_ta: Optional[str] = Field(None, max_length=100)
    constituency_type: Optional[str] = None
    electorate_count: Optional[int] = Field(None, ge=0)
    polling_stations_count: Optional[int] = Field(None, ge=0)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class ConstituencyResponse(ConstituencyBase):
    """Schema for constituency response."""
    id: UUID
    district_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    wards_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class ConstituencyDetailResponse(ConstituencyResponse):
    """Detailed constituency response with wards."""
    district: Optional[DistrictResponse] = None
    wards: List["WardResponse"] = []
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Ward Schemas
# =============================================================================

class WardBase(HierarchyBase):
    """Base ward schema."""
    ward_number: Optional[int] = Field(None, ge=1)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class WardCreate(BaseModel):
    """Schema for creating a ward."""
    constituency_id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    name_ta: Optional[str] = Field(None, max_length=100)
    code: str = Field(..., min_length=1, max_length=50)
    ward_number: Optional[int] = Field(None, ge=1)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "constituency_id": "uuid",
                "name": "Ward 1",
                "name_ta": "வார்டு 1",
                "code": "CHN.NORTH.001",
                "ward_number": 1
            }
        }
    }


class WardUpdate(BaseModel):
    """Schema for updating a ward."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    name_ta: Optional[str] = Field(None, max_length=100)
    ward_number: Optional[int] = Field(None, ge=1)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class WardResponse(WardBase):
    """Schema for ward response."""
    id: UUID
    constituency_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    booths_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class WardDetailResponse(WardResponse):
    """Detailed ward response with booths."""
    constituency: Optional[ConstituencyResponse] = None
    booths: List["BoothResponse"] = []
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Booth Schemas
# =============================================================================

class BoothBase(BaseModel):
    """Base booth schema."""
    booth_number: Optional[int] = Field(None, ge=1)
    polling_location_name: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    male_voters: Optional[int] = Field(default=0, ge=0)
    female_voters: Optional[int] = Field(default=0, ge=0)
    other_voters: Optional[int] = Field(default=0, ge=0)


class BoothCreate(BoothBase):
    """Schema for creating a booth."""
    ward_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    name_ta: Optional[str] = Field(None, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    booth_number: Optional[int] = Field(None, ge=1)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "ward_id": "uuid",
                "name": "Government Higher Secondary School",
                "name_ta": "அரசு மேல்நிலைப் பள்ளி",
                "code": "CHN.NORTH.001.101",
                "booth_number": 101,
                "address": "Main Road, Chennai",
                "male_voters": 450,
                "female_voters": 480
            }
        }
    }


class BoothUpdate(BaseModel):
    """Schema for updating a booth."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    name_ta: Optional[str] = Field(None, max_length=255)
    booth_number: Optional[int] = Field(None, ge=1)
    polling_location_name: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    male_voters: Optional[int] = Field(None, ge=0)
    female_voters: Optional[int] = Field(None, ge=0)
    other_voters: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class BoothResponse(BoothBase):
    """Schema for booth response."""
    id: UUID
    ward_id: UUID
    code: str
    total_voters: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class BoothDetailResponse(BoothResponse):
    """Detailed booth response with ward."""
    ward: Optional[WardResponse] = None
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# ZipCode Mapping Schemas
# =============================================================================

class ZipCodeMappingCreate(BaseModel):
    """Schema for creating zipcode mapping."""
    pincode: str = Field(..., min_length=5, max_length=10)
    district_id: UUID
    constituency_id: Optional[UUID] = None
    ward_id: Optional[UUID] = None
    booth_id: Optional[UUID] = None
    area_name: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)


class ZipCodeMappingResponse(BaseModel):
    """Schema for zipcode mapping response."""
    id: UUID
    pincode: str
    district_id: UUID
    constituency_id: Optional[UUID] = None
    ward_id: Optional[UUID] = None
    booth_id: Optional[UUID] = None
    area_name: Optional[str] = None
    city: Optional[str] = None
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


class ZipCodeLookupResponse(BaseModel):
    """Schema for pincode lookup response."""
    pincode: str
    district: Optional[DistrictResponse] = None
    constituency: Optional[ConstituencyResponse] = None
    ward: Optional[WardResponse] = None
    booth: Optional[BoothResponse] = None
    area_name: Optional[str] = None
    city: Optional[str] = None


# =============================================================================
# Hierarchy Tree Schemas
# =============================================================================

class HierarchyTreeNode(BaseModel):
    """Schema for hierarchy tree node."""
    id: UUID
    name: str
    name_ta: Optional[str] = None
    code: str
    level: str
    children: List["HierarchyTreeNode"] = []
    
    model_config = ConfigDict(from_attributes=True)


class HierarchyTreeResponse(BaseModel):
    """Schema for full hierarchy tree response."""
    districts: List[HierarchyTreeNode] = []
    generated_at: datetime


class SubTreeResponse(BaseModel):
    """Schema for subtree response."""
    node: HierarchyTreeNode
    ancestors: List[HierarchyTreeNode] = []
    descendants_count: int


# =============================================================================
# Search & Filter Schemas
# =============================================================================

class HierarchySearchFilters(BaseModel):
    """Filters for hierarchy search."""
    search: Optional[str] = None  # Search by name or code
    district_id: Optional[UUID] = None
    constituency_id: Optional[UUID] = None
    ward_id: Optional[UUID] = None
    constituency_type: Optional[str] = None
    is_active: Optional[bool] = None
    lat: Optional[float] = None  # Latitude for geo search
    lng: Optional[float] = None  # Longitude for geo search
    radius_km: Optional[float] = Field(None, ge=0, le=100)  # Search radius


class GeoSearchResult(BaseModel):
    """Schema for geographic search result."""
    id: UUID
    name: str
    code: str
    level: str
    distance_km: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None


# =============================================================================
# Statistics Schemas
# =============================================================================

class HierarchyStats(BaseModel):
    """Schema for hierarchy statistics."""
    total_districts: int
    total_constituencies: int
    total_wards: int
    total_booths: int
    total_voters: int
    
    by_constituency_type: Dict[str, int]
    by_district: List[Dict[str, Any]]


class HierarchyStatsResponse(BaseModel):
    """Schema for hierarchy statistics response."""
    stats: HierarchyStats
    generated_at: datetime


# =============================================================================
# Bulk Operations Schemas
# =============================================================================

class BulkImportItem(BaseModel):
    """Schema for bulk import item."""
    type: str  # district, constituency, ward, booth
    data: Dict[str, Any]


class BulkImportRequest(BaseModel):
    """Schema for bulk import request."""
    items: List[BulkImportItem]


class BulkImportResult(BaseModel):
    """Schema for bulk import result."""
    total: int
    successful: int
    failed: int
    errors: List[Dict[str, Any]] = []


class ExportRequest(BaseModel):
    """Schema for export request."""
    level: str = "district"  # district, constituency, ward, booth
    format: str = "json"  # json, csv
    include_inactive: bool = False


# =============================================================================
# Pagination Schemas
# =============================================================================

class PaginatedDistrictResponse(BaseModel):
    """Paginated district list response."""
    districts: List[DistrictResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class PaginatedConstituencyResponse(BaseModel):
    """Paginated constituency list response."""
    constituencies: List[ConstituencyResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class PaginatedWardResponse(BaseModel):
    """Paginated ward list response."""
    wards: List[WardResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class PaginatedBoothResponse(BaseModel):
    """Paginated booth list response."""
    booths: List[BoothResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# =============================================================================
# API Response Schemas
# =============================================================================

class ApiResponse(BaseModel):
    """Generic API response."""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Error API response."""
    success: bool = False
    error: dict


# =============================================================================
# Update forward references
# =============================================================================

DistrictResponse.model_rebuild()
DistrictDetailResponse.model_rebuild()
ConstituencyResponse.model_rebuild()
ConstituencyDetailResponse.model_rebuild()
WardResponse.model_rebuild()
WardDetailResponse.model_rebuild()
BoothResponse.model_rebuild()
BoothDetailResponse.model_rebuild()
HierarchyTreeNode.model_rebuild()
