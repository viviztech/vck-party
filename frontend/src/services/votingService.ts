/**
 * Voting Service
 * API endpoints for election, nomination, and voting management operations
 */

import { api, ApiResponse, PaginationParams, ApiError } from './api';

// ============================================================================
// Types
// ============================================================================

// Election types
export type ElectionStatus = 
  | 'draft'
  | 'published'
  | 'nominations_open'
  | 'nominations_closed'
  | 'voting_open'
  | 'voting_closed'
  | 'results_calculated'
  | 'results_published'
  | 'cancelled';

export type VotingMethod = 
  | 'fptp'  // First Past The Post
  | 'ranked' // Ranked Choice
  | 'approval' // Approval Voting
  | 'preferential'; // Preferential Voting

export interface Election {
  id: string;
  title: string;
  description?: string;
  unit_id?: string;
  nominations_start?: string;
  nominations_end?: string;
  voting_start: string;
  voting_end: string;
  eligible_voter_criteria?: Record<string, unknown>;
  status: ElectionStatus;
  is_secret_voting: boolean;
  require_verified_voter_id: boolean;
  results_published_at?: string;
  created_by_id?: string;
  created_at: string;
  updated_at: string;
}

export interface ElectionDetail extends Election {
  positions_count: number;
  candidates_count: number;
  nominations_count: number;
  total_votes: number;
  unit_name?: string;
  created_by_name?: string;
}

export interface ElectionPosition {
  id: string;
  name: string;
  name_ta?: string;
  description?: string;
  voting_method: VotingMethod;
  seats_available: number;
  min_membership_months: number;
  max_candidates: number;
  created_at: string;
  candidates_count?: number;
}

// Nomination types
export type NominationStatus = 
  | 'pending'
  | 'approved'
  | 'rejected'
  | 'withdrawn';

export interface Nomination {
  id: string;
  election_id: string;
  position_id: string;
  member_id: string;
  manifesto?: string;
  photo_url?: string;
  status: NominationStatus;
  nominated_at: string;
  approved_by_id?: string;
  approved_at?: string;
  rejection_reason?: string;
  created_at: string;
  member_name?: string;
  member_photo_url?: string;
  position_name?: string;
}

// Candidate types
export interface Candidate {
  id: string;
  election_id: string;
  position_id: string;
  member_id: string;
  manifesto?: string;
  photo_url?: string;
  votes_count: number;
  nominated_at: string;
  approved_by_id?: string;
  approved_at?: string;
  member_name?: string;
  member_photo_url?: string;
  position_name?: string;
}

// Voting types
export interface VotingStatus {
  can_vote: boolean;
  has_voted: boolean;
  election_id: string;
  election_title: string;
  positions: Array<{
    position_id: string;
    position_name: string;
    has_voted: boolean;
    candidates: Array<{
      candidate_id: string;
      member_name: string;
      photo_url?: string;
    }>;
  }>;
}

export interface VoteCast {
  candidate_id: string;
  rank?: number;
}

export interface VoteReceipt {
  success: boolean;
  vote_receipt_number: string;
  message: string;
  voted_at: string;
}

export interface VoteVerification {
  is_valid: boolean;
  election_id: string;
  election_title: string;
  vote_receipt_number: string;
  voted_at?: string;
  message: string;
}

// Results types
export interface ElectionResultCandidate {
  candidate_id: string;
  member_id: string;
  member_name: string;
  member_photo_url?: string;
  votes_received: number;
  percentage: number;
  rank: number;
  is_winner: boolean;
}

export interface ElectionResultPosition {
  position_id: string;
  position_name: string;
  voting_method: VotingMethod;
  seats_available: number;
  total_votes: number;
  candidates: ElectionResultCandidate[];
}

export interface ElectionResults {
  election_id: string;
  election_title: string;
  status: ElectionStatus;
  total_voters: number;
  total_votes_cast: number;
  turnout_percentage: number;
  results_published_at?: string;
  positions: ElectionResultPosition[];
  calculated_at: string;
}

// Stats types
export interface ElectionStats {
  total_elections: number;
  active_elections: number;
  upcoming_elections: number;
  completed_elections: number;
  by_status: Record<ElectionStatus, number>;
  elections_this_month: number;
}

// Filter types
export interface ElectionFilters extends PaginationParams {
  search?: string;
  status?: ElectionStatus[];
  unit_id?: string;
  from_date?: string;
  to_date?: string;
  upcoming?: boolean;
}

export interface NominationFilters extends PaginationParams {
  election_id?: string;
  position_id?: string;
  status?: NominationStatus[];
}

// Response types
export interface ElectionListResponse {
  elections: Election[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface ElectionDetailResponse extends ElectionDetail {}

export interface ElectionCandidatesResponse {
  candidates: Candidate[];
  total: number;
  position_id?: string;
}

export interface NominationListResponse {
  nominations: Nomination[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface ElectionStatsResponse {
  stats: ElectionStats;
  generated_at: string;
}

// ============================================================================
// Election CRUD Operations
// ============================================================================

export const votingService = {
  // =========================================================================
  // Election CRUD Operations
  // =========================================================================

  /**
   * Get list of elections with filters and pagination
   */
  async getElections(params?: ElectionFilters): Promise<ElectionListResponse> {
    return api.get('/elections', params);
  },

  /**
   * Get a single election by ID
   */
  async getElection(id: string): Promise<ElectionDetail> {
    const response = await api.get<ApiResponse<ElectionDetailResponse>>(`/elections/${id}`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Election not found',
      status: 404,
    });
  },

  /**
   * Create a new election
   */
  async createElection(data: Partial<Election>): Promise<Election> {
    const response = await api.post<ApiResponse<Election>>('/elections', data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to create election',
      status: 400,
    });
  },

  /**
   * Update an election
   */
  async updateElection(id: string, data: Partial<Election>): Promise<Election> {
    const response = await api.patch<ApiResponse<Election>>(`/elections/${id}`, data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to update election',
      status: 400,
    });
  },

  /**
   * Delete an election
   */
  async deleteElection(id: string): Promise<void> {
    const response = await api.delete<ApiResponse<void>>(`/elections/${id}`);
    
    if (!response.success) {
      throw new ApiError({
        message: response.message || 'Failed to delete election',
        status: 400,
      });
    }
  },

  /**
   * Publish an election (open for nominations)
   */
  async publishElection(id: string): Promise<Election> {
    return this.updateElection(id, { status: 'published' });
  },

  /**
   * Open nominations
   */
  async openNominations(id: string): Promise<Election> {
    return this.updateElection(id, { status: 'nominations_open' });
  },

  /**
   * Close nominations
   */
  async closeNominations(id: string): Promise<Election> {
    return this.updateElection(id, { status: 'nominations_closed' });
  },

  /**
   * Start voting
   */
  async startVoting(id: string): Promise<Election> {
    return this.updateElection(id, { status: 'voting_open' });
  },

  /**
   * End voting
   */
  async endVoting(id: string): Promise<Election> {
    return this.updateElection(id, { status: 'voting_closed' });
  },

  /**
   * Publish results
   */
  async publishResults(id: string): Promise<Election> {
    return this.updateElection(id, { status: 'results_published' });
  },

  // =========================================================================
  // Election Position Operations
  // =========================================================================

  /**
   * Get election positions
   */
  async getElectionPositions(electionId: string): Promise<ElectionPosition[]> {
    return api.get(`/elections/${electionId}/positions`);
  },

  /**
   * Create election position
   */
  async createElectionPosition(electionId: string, data: Partial<ElectionPosition>): Promise<ElectionPosition> {
    const response = await api.post<ApiResponse<ElectionPosition>>(`/elections/${electionId}/positions`, data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to create position',
      status: 400,
    });
  },

  /**
   * Update election position
   */
  async updateElectionPosition(electionId: string, positionId: string, data: Partial<ElectionPosition>): Promise<ElectionPosition> {
    const response = await api.patch<ApiResponse<ElectionPosition>>(
      `/elections/${electionId}/positions/${positionId}`,
      data
    );
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to update position',
      status: 400,
    });
  },

  /**
   * Delete election position
   */
  async deleteElectionPosition(electionId: string, positionId: string): Promise<void> {
    await api.delete(`/elections/${electionId}/positions/${positionId}`);
  },

  // =========================================================================
  // Nomination Operations
  // =========================================================================

  /**
   * Get nominations for an election
   */
  async getNominations(electionId: string, params?: NominationFilters): Promise<NominationListResponse> {
    return api.get(`/elections/${electionId}/nominations`, params);
  },

  /**
   * Get my nominations
   */
  async getMyNominations(params?: PaginationParams): Promise<NominationListResponse> {
    return api.get('/elections/nominations/my', params);
  },

  /**
   * Submit a nomination
   */
  async submitNomination(electionId: string, data: { position_id: string; manifesto?: string; photo_url?: string }): Promise<Nomination> {
    const response = await api.post<ApiResponse<Nomination>>(`/elections/${electionId}/nominations`, data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to submit nomination',
      status: 400,
    });
  },

  /**
   * Update a nomination
   */
  async updateNomination(electionId: string, nominationId: string, data: Partial<Nomination>): Promise<Nomination> {
    const response = await api.patch<ApiResponse<Nomination>>(
      `/elections/${electionId}/nominations/${nominationId}`,
      data
    );
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to update nomination',
      status: 400,
    });
  },

  /**
   * Withdraw a nomination
   */
  async withdrawNomination(electionId: string, nominationId: string): Promise<Nomination> {
    return this.updateNomination(electionId, nominationId, { status: 'withdrawn' });
  },

  /**
   * Approve/reject a nomination (admin only)
   */
  async processNomination(electionId: string, nominationId: string, data: { approved: boolean; rejection_reason?: string }): Promise<Nomination> {
    const response = await api.post<ApiResponse<Nomination>>(
      `/elections/${electionId}/nominations/${nominationId}/process`,
      data
    );
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to process nomination',
      status: 400,
    });
  },

  // =========================================================================
  // Candidate Operations
  // =========================================================================

  /**
   * Get candidates for an election
   */
  async getCandidates(electionId: string, positionId?: string): Promise<ElectionCandidatesResponse> {
    const params = positionId ? { position_id: positionId } : {};
    return api.get(`/elections/${electionId}/candidates`, params);
  },

  // =========================================================================
  // Voting Operations
  // =========================================================================

  /**
   * Get voting status for current user
   */
  async getVotingStatus(electionId: string): Promise<VotingStatus> {
    const response = await api.get<ApiResponse<VotingStatus>>(`/elections/${electionId}/voting-status`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to get voting status',
      status: 400,
    });
  },

  /**
   * Cast a vote
   */
  async castVote(electionId: string, votes: VoteCast[]): Promise<VoteReceipt> {
    const response = await api.post<ApiResponse<VoteReceipt>>(`/elections/${electionId}/vote`, { votes });
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to cast vote',
      status: 400,
    });
  },

  /**
   * Verify a vote
   */
  async verifyVote(voteReceiptNumber: string): Promise<VoteVerification> {
    const response = await api.post<ApiResponse<VoteVerification>>('/elections/verify-vote', { vote_receipt_number: voteReceiptNumber });
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to verify vote',
      status: 400,
    });
  },

  /**
   * Check if current user has voted
   */
  async hasUserVoted(electionId: string): Promise<{ has_voted: boolean; vote_receipt_number?: string }> {
    const response = await api.get<ApiResponse<{ has_voted: boolean; vote_receipt_number?: string }>>(`/elections/${electionId}/has-voted`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    return { has_voted: false };
  },

  // =========================================================================
  // Results Operations
  // =========================================================================

  /**
   * Get election results
   */
  async getElectionResults(electionId: string): Promise<ElectionResults> {
    const response = await api.get<ApiResponse<ElectionResults>>(`/elections/${electionId}/results`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Results not available',
      status: 400,
    });
  },

  /**
   * Calculate results (admin only)
   */
  async calculateResults(electionId: string): Promise<ElectionResults> {
    const response = await api.post<ApiResponse<ElectionResults>>(`/elections/${electionId}/calculate-results`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to calculate results',
      status: 400,
    });
  },

  // =========================================================================
  // Statistics
  // =========================================================================

  /**
   * Get election statistics
   */
  async getElectionStats(): Promise<ElectionStats> {
    const response = await api.get<ApiResponse<ElectionStatsResponse>>('/elections/stats');
    
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
   * Search elections
   */
  async searchElections(query: string, limit?: number): Promise<Election[]> {
    return api.get('/elections/search', { q: query, limit });
  },

  /**
   * Get voters list (admin only)
   */
  async getVotersList(electionId: string): Promise<{ voters: Array<{ id: string; member_id: string; member_name?: string; voted_at: string }>; total: number }> {
    return api.get(`/elections/${electionId}/voters`);
  },
};

export default votingService;
