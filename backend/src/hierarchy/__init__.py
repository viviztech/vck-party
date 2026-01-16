"""
Hierarchy Module
Organizational hierarchy management for the VCK platform.
Manages the political party structure: District → Constituency → Ward → Booth.
"""

from src.hierarchy.models import (
    District,
    Constituency,
    Ward,
    Booth,
    ZipCodeMapping,
    OrganizationUnit,
    HierarchyLevel,
    ConstituencyType,
    hierarchy_relations,
)
from src.hierarchy.schemas import (
    DistrictCreate,
    DistrictUpdate,
    DistrictResponse,
    DistrictDetailResponse,
    ConstituencyCreate,
    ConstituencyUpdate,
    ConstituencyResponse,
    ConstituencyDetailResponse,
    WardCreate,
    WardUpdate,
    WardResponse,
    WardDetailResponse,
    BoothCreate,
    BoothUpdate,
    BoothResponse,
    BoothDetailResponse,
    ZipCodeMappingCreate,
    ZipCodeMappingResponse,
    ZipCodeLookupResponse,
    HierarchyTreeNode,
    HierarchyTreeResponse,
    SubTreeResponse,
    HierarchySearchFilters,
    GeoSearchResult,
    HierarchyStats,
    HierarchyStatsResponse,
    BulkImportRequest,
    BulkImportResult,
    ExportRequest,
    ApiResponse,
    ErrorResponse,
    PaginatedDistrictResponse,
    PaginatedConstituencyResponse,
    PaginatedWardResponse,
    PaginatedBoothResponse,
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
    CRUDBase,
)
from src.hierarchy.router import router as hierarchy_router

__all__ = [
    # Models
    "District",
    "Constituency",
    "Ward",
    "Booth",
    "ZipCodeMapping",
    "OrganizationUnit",
    "HierarchyLevel",
    "ConstituencyType",
    "hierarchy_relations",
    
    # Schemas - District
    "DistrictCreate",
    "DistrictUpdate",
    "DistrictResponse",
    "DistrictDetailResponse",
    
    # Schemas - Constituency
    "ConstituencyCreate",
    "ConstituencyUpdate",
    "ConstituencyResponse",
    "ConstituencyDetailResponse",
    
    # Schemas - Ward
    "WardCreate",
    "WardUpdate",
    "WardResponse",
    "WardDetailResponse",
    
    # Schemas - Booth
    "BoothCreate",
    "BoothUpdate",
    "BoothResponse",
    "BoothDetailResponse",
    
    # Schemas - ZipCode
    "ZipCodeMappingCreate",
    "ZipCodeMappingResponse",
    "ZipCodeLookupResponse",
    
    # Schemas - Tree
    "HierarchyTreeNode",
    "HierarchyTreeResponse",
    "SubTreeResponse",
    
    # Schemas - Search & Filters
    "HierarchySearchFilters",
    "GeoSearchResult",
    
    # Schemas - Stats
    "HierarchyStats",
    "HierarchyStatsResponse",
    
    # Schemas - Bulk Operations
    "BulkImportRequest",
    "BulkImportResult",
    "ExportRequest",
    
    # Schemas - Response
    "ApiResponse",
    "ErrorResponse",
    
    # Schemas - Pagination
    "PaginatedDistrictResponse",
    "PaginatedConstituencyResponse",
    "PaginatedWardResponse",
    "PaginatedBoothResponse",
    
    # CRUD
    "CRUDBase",
    "DistrictCRUD",
    "ConstituencyCRUD",
    "WardCRUD",
    "BoothCRUD",
    "ZipCodeCRUD",
    "HierarchyTreeCRUD",
    "GeoSearchCRUD",
    "HierarchyStatsCRUD",
    "BulkHierarchyCRUD",
    
    # Router
    "hierarchy_router",
]
