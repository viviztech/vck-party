/**
 * Hierarchy Service
 * API endpoints for managing organizational hierarchy (districts, constituencies, wards, booths)
 */

import { api, ApiResponse, PaginationParams, ApiError } from './api';

// ============================================================================
// Types
// ============================================================================

// Common types
export interface HierarchyNode {
  id: string;
  name: string;
  name_ta?: string;
  code: string;
  level: string;
  latitude?: number;
  longitude?: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface HierarchyTreeNode {
  id: string;
  name: string;
  name_ta?: string;
  code: string;
  level: string;
  children: HierarchyTreeNode[];
}

export interface GeoLocation {
  latitude: number;
  longitude: number;
}

export interface HierarchyFilters extends PaginationParams {
  search?: string;
  district_id?: string;
  constituency_id?: string;
  ward_id?: string;
  constituency_type?: string;
  is_active?: boolean;
  lat?: number;
  lng?: number;
  radius_km?: number;
}

// District types
export interface District {
  id: string;
  name: string;
  name_ta?: string;
  code: string;
  state: string;
  latitude?: number;
  longitude?: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  constituencies_count: number;
}

export interface DistrictCreate {
  name: string;
  name_ta?: string;
  code: string;
  state?: string;
  latitude?: number;
  longitude?: number;
}

export interface DistrictUpdate {
  name?: string;
  name_ta?: string;
  latitude?: number;
  longitude?: number;
  is_active?: boolean;
  metadata?: Record<string, unknown>;
}

export interface DistrictDetail extends District {
  constituencies: Constituency[];
}

// Constituency types
export interface Constituency {
  id: string;
  district_id: string;
  name: string;
  name_ta?: string;
  code: string;
  constituency_type: string;
  electorate_count?: number;
  polling_stations_count?: number;
  latitude?: number;
  longitude?: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  wards_count: number;
}

export interface ConstituencyCreate {
  district_id: string;
  name: string;
  name_ta?: string;
  code: string;
  constituency_type?: string;
  electorate_count?: number;
  latitude?: number;
  longitude?: number;
}

export interface ConstituencyUpdate {
  name?: string;
  name_ta?: string;
  constituency_type?: string;
  electorate_count?: number;
  polling_stations_count?: number;
  latitude?: number;
  longitude?: number;
  is_active?: boolean;
  metadata?: Record<string, unknown>;
}

export interface ConstituencyDetail extends Constituency {
  district: District;
  wards: Ward[];
}

// Ward types
export interface Ward {
  id: string;
  constituency_id: string;
  name: string;
  name_ta?: string;
  code: string;
  ward_number?: number;
  latitude?: number;
  longitude?: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  booths_count: number;
}

export interface WardCreate {
  constituency_id: string;
  name: string;
  name_ta?: string;
  code: string;
  ward_number?: number;
  latitude?: number;
  longitude?: number;
}

export interface WardUpdate {
  name?: string;
  name_ta?: string;
  ward_number?: number;
  latitude?: number;
  longitude?: number;
  is_active?: boolean;
  metadata?: Record<string, unknown>;
}

export interface WardDetail extends Ward {
  constituency: Constituency;
  booths: Booth[];
}

// Booth types
export interface Booth {
  id: string;
  ward_id: string;
  name: string;
  name_ta?: string;
  code: string;
  booth_number?: number;
  polling_location_name?: string;
  address?: string;
  latitude?: number;
  longitude?: number;
  male_voters?: number;
  female_voters?: number;
  other_voters?: number;
  total_voters: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface BoothCreate {
  ward_id: string;
  name: string;
  name_ta?: string;
  code: string;
  booth_number?: number;
  polling_location_name?: string;
  address?: string;
  male_voters?: number;
  female_voters?: number;
  other_voters?: number;
}

export interface BoothUpdate {
  name?: string;
  name_ta?: string;
  booth_number?: number;
  polling_location_name?: string;
  address?: string;
  latitude?: number;
  longitude?: number;
  male_voters?: number;
  female_voters?: number;
  other_voters?: number;
  is_active?: boolean;
  metadata?: Record<string, unknown>;
}

export interface BoothDetail extends Booth {
  ward: Ward;
}

// Pincode types
export interface ZipCodeMapping {
  id: string;
  pincode: string;
  district_id: string;
  constituency_id?: string;
  ward_id?: string;
  booth_id?: string;
  area_name?: string;
  city?: string;
  is_active: boolean;
}

export interface PincodeLookup {
  pincode: string;
  district?: District;
  constituency?: Constituency;
  ward?: Ward;
  booth?: Booth;
  area_name?: string;
  city?: string;
}

// Statistics types
export interface HierarchyStats {
  total_districts: number;
  total_constituencies: number;
  total_wards: number;
  total_booths: number;
  total_voters: number;
  by_constituency_type: Record<string, number>;
  by_district: Array<{ name: string; count: number }>;
}

export interface HierarchyStatsResponse {
  stats: HierarchyStats;
  generated_at: string;
}

// Geo search types
export interface GeoSearchResult {
  id: string;
  name: string;
  code: string;
  level: string;
  distance_km: number;
  latitude?: number;
  longitude?: number;
}

// Response types
export interface PaginatedDistrictResponse {
  districts: District[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface PaginatedConstituencyResponse {
  constituencies: Constituency[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface PaginatedWardResponse {
  wards: Ward[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface PaginatedBoothResponse {
  booths: Booth[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface HierarchyTreeResponse {
  districts: HierarchyTreeNode[];
  generated_at: string;
}

export interface SubTreeResponse {
  node: HierarchyTreeNode;
  ancestors: HierarchyTreeNode[];
  descendants_count: number;
}

// ============================================================================
// Hierarchy Service
// ============================================================================

export const hierarchyService = {
  // =========================================================================
  // District Operations
  // =========================================================================

  /**
   * Get list of districts
   */
  async getDistricts(params?: HierarchyFilters): Promise<PaginatedDistrictResponse> {
    return api.get('/hierarchy/districts', params);
  },

  /**
   * Get a single district by ID
   */
  async getDistrict(id: string): Promise<District> {
    const response = await api.get<ApiResponse<District>>(`/hierarchy/districts/${id}`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'District not found',
      status: 404,
    });
  },

  /**
   * Get district with full details including constituencies
   */
  async getDistrictDetail(id: string): Promise<DistrictDetail> {
    const response = await api.get<ApiResponse<DistrictDetail>>(`/hierarchy/districts/${id}/detail`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'District not found',
      status: 404,
    });
  },

  /**
   * Create a new district
   */
  async createDistrict(data: DistrictCreate): Promise<District> {
    const response = await api.post<ApiResponse<District>>('/hierarchy/districts', data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to create district',
      status: 400,
    });
  },

  /**
   * Update a district
   */
  async updateDistrict(id: string, data: DistrictUpdate): Promise<District> {
    const response = await api.patch<ApiResponse<District>>(`/hierarchy/districts/${id}`, data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to update district',
      status: 400,
    });
  },

  /**
   * Delete a district
   */
  async deleteDistrict(id: string): Promise<void> {
    const response = await api.delete<ApiResponse<void>>(`/hierarchy/districts/${id}`);
    
    if (!response.success) {
      throw new ApiError({
        message: response.message || 'Failed to delete district',
        status: 400,
      });
    }
  },

  // =========================================================================
  // Constituency Operations
  // =========================================================================

  /**
   * Get list of constituencies
   */
  async getConstituencies(params?: HierarchyFilters): Promise<PaginatedConstituencyResponse> {
    return api.get('/hierarchy/constituencies', params);
  },

  /**
   * Get a single constituency by ID
   */
  async getConstituency(id: string): Promise<Constituency> {
    const response = await api.get<ApiResponse<Constituency>>(`/hierarchy/constituencies/${id}`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Constituency not found',
      status: 404,
    });
  },

  /**
   * Get constituency with full details including wards
   */
  async getConstituencyDetail(id: string): Promise<ConstituencyDetail> {
    const response = await api.get<ApiResponse<ConstituencyDetail>>(
      `/hierarchy/constituencies/${id}/detail`
    );
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Constituency not found',
      status: 404,
    });
  },

  /**
   * Create a new constituency
   */
  async createConstituency(data: ConstituencyCreate): Promise<Constituency> {
    const response = await api.post<ApiResponse<Constituency>>('/hierarchy/constituencies', data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to create constituency',
      status: 400,
    });
  },

  /**
   * Update a constituency
   */
  async updateConstituency(id: string, data: ConstituencyUpdate): Promise<Constituency> {
    const response = await api.patch<ApiResponse<Constituency>>(
      `/hierarchy/constituencies/${id}`,
      data
    );
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to update constituency',
      status: 400,
    });
  },

  /**
   * Delete a constituency
   */
  async deleteConstituency(id: string): Promise<void> {
    const response = await api.delete<ApiResponse<void>>(`/hierarchy/constituencies/${id}`);
    
    if (!response.success) {
      throw new ApiError({
        message: response.message || 'Failed to delete constituency',
        status: 400,
      });
    }
  },

  // =========================================================================
  // Ward Operations
  // =========================================================================

  /**
   * Get list of wards
   */
  async getWards(params?: HierarchyFilters): Promise<PaginatedWardResponse> {
    return api.get('/hierarchy/wards', params);
  },

  /**
   * Get a single ward by ID
   */
  async getWard(id: string): Promise<Ward> {
    const response = await api.get<ApiResponse<Ward>>(`/hierarchy/wards/${id}`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Ward not found',
      status: 404,
    });
  },

  /**
   * Get ward with full details including booths
   */
  async getWardDetail(id: string): Promise<WardDetail> {
    const response = await api.get<ApiResponse<WardDetail>>(`/hierarchy/wards/${id}/detail`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Ward not found',
      status: 404,
    });
  },

  /**
   * Create a new ward
   */
  async createWard(data: WardCreate): Promise<Ward> {
    const response = await api.post<ApiResponse<Ward>>('/hierarchy/wards', data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to create ward',
      status: 400,
    });
  },

  /**
   * Update a ward
   */
  async updateWard(id: string, data: WardUpdate): Promise<Ward> {
    const response = await api.patch<ApiResponse<Ward>>(`/hierarchy/wards/${id}`, data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to update ward',
      status: 400,
    });
  },

  /**
   * Delete a ward
   */
  async deleteWard(id: string): Promise<void> {
    const response = await api.delete<ApiResponse<void>>(`/hierarchy/wards/${id}`);
    
    if (!response.success) {
      throw new ApiError({
        message: response.message || 'Failed to delete ward',
        status: 400,
      });
    }
  },

  // =========================================================================
  // Booth Operations
  // =========================================================================

  /**
   * Get list of booths
   */
  async getBooths(params?: HierarchyFilters): Promise<PaginatedBoothResponse> {
    return api.get('/hierarchy/booths', params);
  },

  /**
   * Get a single booth by ID
   */
  async getBooth(id: string): Promise<Booth> {
    const response = await api.get<ApiResponse<Booth>>(`/hierarchy/booths/${id}`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Booth not found',
      status: 404,
    });
  },

  /**
   * Get booth with full details
   */
  async getBoothDetail(id: string): Promise<BoothDetail> {
    const response = await api.get<ApiResponse<BoothDetail>>(`/hierarchy/booths/${id}/detail`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Booth not found',
      status: 404,
    });
  },

  /**
   * Create a new booth
   */
  async createBooth(data: BoothCreate): Promise<Booth> {
    const response = await api.post<ApiResponse<Booth>>('/hierarchy/booths', data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to create booth',
      status: 400,
    });
  },

  /**
   * Update a booth
   */
  async updateBooth(id: string, data: BoothUpdate): Promise<Booth> {
    const response = await api.patch<ApiResponse<Booth>>(`/hierarchy/booths/${id}`, data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to update booth',
      status: 400,
    });
  },

  /**
   * Delete a booth
   */
  async deleteBooth(id: string): Promise<void> {
    const response = await api.delete<ApiResponse<void>>(`/hierarchy/booths/${id}`);
    
    if (!response.success) {
      throw new ApiError({
        message: response.message || 'Failed to delete booth',
        status: 400,
      });
    }
  },

  // =========================================================================
  // Hierarchy Tree Operations
  // =========================================================================

  /**
   * Get full hierarchy tree
   */
  async getHierarchyTree(): Promise<HierarchyTreeResponse> {
    const response = await api.get<ApiResponse<HierarchyTreeResponse>>('/hierarchy/tree');
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to get hierarchy tree',
      status: 400,
    });
  },

  /**
   * Get subtree for a specific node
   */
  async getSubtree(level: string, id: string): Promise<SubTreeResponse> {
    const response = await api.get<ApiResponse<SubTreeResponse>>(
      `/hierarchy/subtree/${level}/${id}`
    );
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to get subtree',
      status: 400,
    });
  },

  // =========================================================================
  // Search Operations
  // =========================================================================

  /**
   * Search hierarchy
   */
  async searchHierarchy(query: string, limit?: number): Promise<HierarchyNode[]> {
    const response = await api.get<ApiResponse<HierarchyNode[]>>('/hierarchy/search', {
      q: query,
      limit,
    });
    
    if (response.success && response.data) {
      return response.data;
    }
    
    return [];
  },

  /**
   * Geo search - find hierarchy nodes near a location
   */
  async geoSearch(location: GeoLocation, radiusKm?: number): Promise<GeoSearchResult[]> {
    const response = await api.get<ApiResponse<GeoSearchResult[]>>('/hierarchy/geo-search', {
      lat: location.latitude,
      lng: location.longitude,
      radius_km: radiusKm,
    });
    
    if (response.success && response.data) {
      return response.data;
    }
    
    return [];
  },

  // =========================================================================
  // Pincode Operations
  // =========================================================================

  /**
   * Lookup hierarchy by pincode
   */
  async lookupByPincode(pincode: string): Promise<PincodeLookup> {
    const response = await api.get<ApiResponse<PincodeLookup>>(`/hierarchy/pincode/${pincode}`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Pincode not found',
      status: 404,
    });
  },

  // =========================================================================
  // Statistics
  // =========================================================================

  /**
   * Get hierarchy statistics
   */
  async getHierarchyStats(): Promise<HierarchyStats> {
    const response = await api.get<ApiResponse<HierarchyStatsResponse>>('/hierarchy/stats');
    
    if (response.success && response.data) {
      return response.data.stats;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to get hierarchy stats',
      status: 400,
    });
  },

  // =========================================================================
  // Bulk Operations
  // =========================================================================

  /**
   * Bulk import hierarchy data
   */
  async bulkImport(
    type: 'district' | 'constituency' | 'ward' | 'booth',
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<{ total: number; successful: number; failed: number; errors: unknown[] }> {
    const response = await api.uploadFile<{ total: number; successful: number; failed: number; errors: unknown[] }>(
      `/hierarchy/bulk-import/${type}`,
      file,
      onProgress
    );
    
    return response;
  },

  /**
   * Export hierarchy data
   */
  async exportHierarchy(
    level: 'district' | 'constituency' | 'ward' | 'booth',
    format: 'json' | 'csv' = 'json',
    includeInactive = false
  ): Promise<{ file_url: string; file_name: string }> {
    return api.get('/hierarchy/export', {
      level,
      format,
      include_inactive: includeInactive,
    });
  },
};

export default hierarchyService;
