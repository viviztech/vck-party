/**
 * Members Service
 * API endpoints for member management operations
 */

import { api, ApiResponse, PaginationParams, ApiError } from './api';

// ============================================================================
// Types
// ============================================================================

// Member types
export interface Member {
  id: string;
  membership_number: string;
  first_name: string;
  last_name?: string;
  first_name_ta?: string;
  last_name_ta?: string;
  phone: string;
  email?: string;
  date_of_birth?: string;
  gender?: string;
  photo_url?: string;
  alternate_phone?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  district?: string;
  constituency?: string;
  ward?: string;
  state?: string;
  pincode?: string;
  voter_id?: string;
  blood_group?: string;
  education?: string;
  occupation?: string;
  organization?: string;
  status: string;
  membership_type: string;
  joined_at: string;
  verified_at?: string;
  created_at: string;
  updated_at: string;
  tags?: string[];
  user_id?: string;
}

export interface MemberCreate {
  first_name: string;
  last_name?: string;
  first_name_ta?: string;
  last_name_ta?: string;
  phone: string;
  email?: string;
  date_of_birth?: string;
  gender?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  district?: string;
  constituency?: string;
  ward?: string;
  state?: string;
  pincode?: string;
  voter_id?: string;
  blood_group?: string;
  education?: string;
  occupation?: string;
  membership_type?: string;
}

export interface MemberUpdate {
  first_name?: string;
  last_name?: string;
  first_name_ta?: string;
  last_name_ta?: string;
  photo_url?: string;
  date_of_birth?: string;
  gender?: string;
  email?: string;
  alternate_phone?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  district?: string;
  constituency?: string;
  ward?: string;
  state?: string;
  pincode?: string;
  voter_id?: string;
  blood_group?: string;
  education?: string;
  occupation?: string;
  organization?: string;
  status?: string;
  membership_type?: string;
}

// Member profile types
export interface MemberProfile {
  id: string;
  member_id: string;
  mother_tongue?: string;
  religion?: string;
  caste_category?: string;
  nationality?: string;
  facebook_url?: string;
  twitter_url?: string;
  instagram_url?: string;
  linkedin_url?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  emergency_contact_relationship?: string;
  communication_preference?: string;
  language_preference?: string;
  interested_areas?: string[];
  previous_party_affiliation?: string;
  joined_from_which_party?: string;
  political_influence_level?: string;
  volunteer_availability?: string;
  preferred_roles?: string[];
  max_travel_distance_km?: number;
  hobbies_interests?: string[];
  achievements_recognitions?: string;
  photo_consent?: boolean;
  data_sharing_consent?: boolean;
  terms_accepted_at?: string;
  privacy_policy_accepted_at?: string;
  created_at: string;
  updated_at: string;
}

export interface MemberProfileUpdate {
  mother_tongue?: string;
  religion?: string;
  caste_category?: string;
  nationality?: string;
  facebook_url?: string;
  twitter_url?: string;
  instagram_url?: string;
  linkedin_url?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  emergency_contact_relationship?: string;
  communication_preference?: string;
  language_preference?: string;
  interested_areas?: string[];
  previous_party_affiliation?: string;
  joined_from_which_party?: string;
  political_influence_level?: string;
  volunteer_availability?: string;
  preferred_roles?: string[];
  max_travel_distance_km?: number;
  hobbies_interests?: string[];
  achievements_recognitions?: string;
  photo_consent?: boolean;
  data_sharing_consent?: boolean;
}

// Family types
export interface MemberFamily {
  id: string;
  member_id: string;
  related_member_id: string;
  relationship_type: string;
  related_member: Member;
  notes?: string;
  is_active: boolean;
  created_at: string;
}

export interface MemberFamilyCreate {
  related_member_id: string;
  relationship_type: string;
  notes?: string;
}

// Document types
export interface MemberDocument {
  id: string;
  member_id: string;
  document_type: string;
  file_name: string;
  file_url?: string;
  mime_type?: string;
  file_size?: number;
  is_verified: boolean;
  verified_at?: string;
  verified_by?: string;
  verification_notes?: string;
  created_at: string;
}

export interface MemberDocumentCreate {
  document_type: string;
  file_name: string;
  file_path: string;
  file_url?: string;
  mime_type?: string;
  file_size?: number;
}

// Tag types
export interface MemberTag {
  id: string;
  name: string;
  description?: string;
  color: string;
  created_at: string;
}

export interface MemberTagAdd {
  tag_ids: string[];
}

// Note types
export interface MemberNote {
  id: string;
  member_id: string;
  author_id?: string;
  author_name?: string;
  title?: string;
  content: string;
  category?: string;
  is_private: boolean;
  created_at: string;
  updated_at: string;
}

export interface MemberNoteCreate {
  title?: string;
  content: string;
  category?: string;
  is_private?: boolean;
}

export interface MemberNoteUpdate {
  title?: string;
  content?: string;
  category?: string;
}

// History types
export interface MemberHistory {
  id: string;
  member_id: string;
  action: string;
  action_description?: string;
  previous_status?: string;
  new_status?: string;
  performed_by?: string;
  performed_by_name?: string;
  reason?: string;
  created_at: string;
}

// Stats types
export interface MemberStats {
  total_members: number;
  active_members: number;
  pending_members: number;
  suspended_members: number;
  expelled_members: number;
  by_status: Record<string, number>;
  by_membership_type: Record<string, number>;
  by_gender: Record<string, number>;
  by_district: Record<string, number>;
  by_occupation: Record<string, number>;
  new_this_month: number;
  new_this_year: number;
  growth_percentage_month: number;
  growth_percentage_year: number;
}

// Filter types
export interface MemberFilters extends PaginationParams {
  search?: string;
  status?: string[];
  membership_type?: string[];
  district?: string;
  constituency?: string;
  ward?: string;
  tags?: string[];
  gender?: string;
  occupation?: string;
  education?: string;
  from_date?: string;
  to_date?: string;
  min_age?: number;
  max_age?: number;
}

// Response types
export interface MemberListResponse {
  members: Member[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface MemberStatsResponse {
  stats: MemberStats;
  generated_at: string;
}

export interface MemberBulkImportResult {
  total: number;
  successful: number;
  failed: number;
  errors: Array<{ row?: number; message: string; data?: Record<string, unknown> }>;
}

export interface MemberExportResponse {
  file_url: string;
  file_name: string;
  total_records: number;
  generated_at: string;
}

// ============================================================================
// Members Service
// ============================================================================

export const membersService = {
  // =========================================================================
  // Member CRUD Operations
  // =========================================================================

  /**
   * Get list of members with filters and pagination
   */
  async getMembers(params?: MemberFilters): Promise<MemberListResponse> {
    return api.get('/members', params);
  },

  /**
   * Get a single member by ID
   */
  async getMember(id: string): Promise<Member> {
    const response = await api.get<ApiResponse<Member>>(`/members/${id}`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Member not found',
      status: 404,
    });
  },

  /**
   * Create a new member
   */
  async createMember(data: MemberCreate): Promise<Member> {
    const response = await api.post<ApiResponse<Member>>('/members', data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to create member',
      status: 400,
    });
  },

  /**
   * Update a member
   */
  async updateMember(id: string, data: MemberUpdate): Promise<Member> {
    const response = await api.patch<ApiResponse<Member>>(`/members/${id}`, data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to update member',
      status: 400,
    });
  },

  /**
   * Delete a member
   */
  async deleteMember(id: string): Promise<void> {
    const response = await api.delete<ApiResponse<void>>(`/members/${id}`);
    
    if (!response.success) {
      throw new ApiError({
        message: response.message || 'Failed to delete member',
        status: 400,
      });
    }
  },

  // =========================================================================
  // Member Profile Operations
  // =========================================================================

  /**
   * Get member profile
   */
  async getMemberProfile(id: string): Promise<MemberProfile> {
    const response = await api.get<ApiResponse<MemberProfile>>(`/members/${id}/profile`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Profile not found',
      status: 404,
    });
  },

  /**
   * Update member profile
   */
  async updateMemberProfile(id: string, data: MemberProfileUpdate): Promise<MemberProfile> {
    const response = await api.patch<ApiResponse<MemberProfile>>(`/members/${id}/profile`, data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to update profile',
      status: 400,
    });
  },

  // =========================================================================
  // Family Operations
  // =========================================================================

  /**
   * Get member family relationships
   */
  async getMemberFamily(id: string): Promise<MemberFamily[]> {
    const response = await api.get<ApiResponse<MemberFamily[]>>(`/members/${id}/family`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    return [];
  },

  /**
   * Add family relationship
   */
  async addMemberFamily(id: string, data: MemberFamilyCreate): Promise<MemberFamily> {
    const response = await api.post<ApiResponse<MemberFamily>>(`/members/${id}/family`, data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to add family member',
      status: 400,
    });
  },

  // =========================================================================
  // Document Operations
  // =========================================================================

  /**
   * Get member documents
   */
  async getMemberDocuments(id: string): Promise<MemberDocument[]> {
    const response = await api.get<ApiResponse<MemberDocument[]>>(`/members/${id}/documents`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    return [];
  },

  /**
   * Upload document for member
   */
  async uploadDocument(
    id: string,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<MemberDocument> {
    const response = await api.uploadFile<ApiResponse<MemberDocument>>(
      `/members/${id}/documents`,
      file,
      onProgress
    );
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to upload document',
      status: 400,
    });
  },

  /**
   * Delete member document
   */
  async deleteMemberDocument(memberId: string, documentId: string): Promise<void> {
    await api.delete(`/members/${memberId}/documents/${documentId}`);
  },

  // =========================================================================
  // Tag Operations
  // =========================================================================

  /**
   * Get member tags
   */
  async getMemberTags(id: string): Promise<MemberTag[]> {
    const response = await api.get<ApiResponse<MemberTag[]>>(`/members/${id}/tags`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    return [];
  },

  /**
   * Add tag to member
   */
  async addMemberTag(id: string, data: MemberTagAdd): Promise<MemberTag[]> {
    const response = await api.post<ApiResponse<MemberTag[]>>(`/members/${id}/tags`, data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to add tag',
      status: 400,
    });
  },

  /**
   * Remove tag from member
   */
  async removeMemberTag(memberId: string, tagId: string): Promise<void> {
    await api.delete(`/members/${memberId}/tags/${tagId}`);
  },

  // =========================================================================
  // Note Operations
  // =========================================================================

  /**
   * Get member notes
   */
  async getMemberNotes(id: string): Promise<MemberNote[]> {
    const response = await api.get<ApiResponse<MemberNote[]>>(`/members/${id}/notes`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    return [];
  },

  /**
   * Add note to member
   */
  async addMemberNote(id: string, data: MemberNoteCreate): Promise<MemberNote> {
    const response = await api.post<ApiResponse<MemberNote>>(`/members/${id}/notes`, data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to add note',
      status: 400,
    });
  },

  /**
   * Update member note
   */
  async updateMemberNote(
    memberId: string,
    noteId: string,
    data: MemberNoteUpdate
  ): Promise<MemberNote> {
    const response = await api.patch<ApiResponse<MemberNote>>(
      `/members/${memberId}/notes/${noteId}`,
      data
    );
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to update note',
      status: 400,
    });
  },

  /**
   * Delete member note
   */
  async deleteMemberNote(memberId: string, noteId: string): Promise<void> {
    await api.delete(`/members/${memberId}/notes/${noteId}`);
  },

  // =========================================================================
  // History Operations
  // =========================================================================

  /**
   * Get member history
   */
  async getMemberHistory(id: string): Promise<MemberHistory[]> {
    const response = await api.get<ApiResponse<MemberHistory[]>>(`/members/${id}/history`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    return [];
  },

  // =========================================================================
  // Bulk Operations
  // =========================================================================

  /**
   * Bulk import members from file
   */
  async bulkImportMembers(
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<MemberBulkImportResult> {
    const response = await api.uploadFile<MemberBulkImportResult>(
      '/members/bulk-import',
      file,
      onProgress
    );
    
    return response;
  },

  /**
   * Export members
   */
  async exportMembers(
    params?: MemberFilters
  ): Promise<MemberExportResponse> {
    return api.get('/members/export', params);
  },

  // =========================================================================
  // Statistics
  // =========================================================================

  /**
   * Get member statistics
   */
  async getMemberStats(): Promise<MemberStats> {
    const response = await api.get<ApiResponse<MemberStatsResponse>>('/members/stats');
    
    if (response.success && response.data) {
      return response.data.stats;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to get stats',
      status: 400,
    });
  },

  // =========================================================================
  // Search
  // =========================================================================

  /**
   * Search members
   */
  async searchMembers(query: string, limit?: number): Promise<Member[]> {
    return api.get('/members/search', { q: query, limit });
  },

  /**
   * Lookup member by voter ID
   */
  async getByVoterId(voterId: string): Promise<Member> {
    const response = await api.get<ApiResponse<Member>>(`/members/voter-id/${voterId}`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Member not found',
      status: 404,
    });
  },

  /**
   * Lookup member by phone
   */
  async getByPhone(phone: string): Promise<Member> {
    const response = await api.get<ApiResponse<Member>>(`/members/phone/${phone}`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Member not found',
      status: 404,
    });
  },
};

export default membersService;
