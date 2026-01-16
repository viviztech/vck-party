/**
 * Events Service
 * API endpoints for event, campaign, and activity management operations
 */

import { api, ApiResponse, PaginationParams, ApiError } from './api';

// ============================================================================
// Types
// ============================================================================

// Event types
export interface Event {
  id: string;
  title: string;
  title_ta?: string;
  description?: string;
  description_ta?: string;
  event_type: EventType;
  status: EventStatus;
  start_date: string;
  end_date: string;
  start_time?: string;
  end_time?: string;
  venue?: string;
  venue_address?: string;
  district?: string;
  constituency?: string;
  ward?: string;
  expected_attendees?: number;
  actual_attendees?: number;
  registration_required: boolean;
  registration_deadline?: string;
  max_registrations?: number;
  image_url?: string;
  banner_url?: string;
  is_recurring: boolean;
  recurring_pattern?: string;
  parent_event_id?: string;
  campaign_id?: string;
  organizer_name?: string;
  organizer_phone?: string;
  organizer_email?: string;
  tags?: string[];
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export type EventType = 
  | 'meeting'
  | 'rally'
  | 'campaign'
  | 'conference'
  | 'workshop'
  | 'training'
  | 'volunteer'
  | 'fundraiser'
  | 'awareness'
  | 'visit'
  | 'inauguration'
  | 'other';

export type EventStatus = 
  | 'draft'
  | 'published'
  | 'cancelled'
  | 'completed'
  | 'postponed'
  | 'in_progress';

export interface EventCreate {
  title: string;
  title_ta?: string;
  description?: string;
  description_ta?: string;
  event_type: EventType;
  start_date: string;
  end_date: string;
  start_time?: string;
  end_time?: string;
  venue?: string;
  venue_address?: string;
  district?: string;
  constituency?: string;
  ward?: string;
  expected_attendees?: number;
  registration_required?: boolean;
  registration_deadline?: string;
  max_registrations?: number;
  image_url?: string;
  banner_url?: string;
  is_recurring?: boolean;
  recurring_pattern?: string;
  parent_event_id?: string;
  campaign_id?: string;
  organizer_name?: string;
  organizer_phone?: string;
  organizer_email?: string;
  tags?: string[];
}

export interface EventUpdate {
  title?: string;
  title_ta?: string;
  description?: string;
  description_ta?: string;
  event_type?: EventType;
  status?: EventStatus;
  start_date?: string;
  end_date?: string;
  start_time?: string;
  end_time?: string;
  venue?: string;
  venue_address?: string;
  district?: string;
  constituency?: string;
  ward?: string;
  expected_attendees?: number;
  actual_attendees?: number;
  registration_required?: boolean;
  registration_deadline?: string;
  max_registrations?: number;
  image_url?: string;
  banner_url?: string;
  is_recurring?: boolean;
  recurring_pattern?: string;
  organizer_name?: string;
  organizer_phone?: string;
  organizer_email?: string;
  tags?: string[];
}

// Campaign types
export interface Campaign {
  id: string;
  name: string;
  name_ta?: string;
  description?: string;
  description_ta?: string;
  campaign_type: CampaignType;
  status: CampaignStatus;
  start_date: string;
  end_date: string;
  budget?: number;
  target_constituency?: string;
  target_ward?: string;
  goals?: string[];
  key_messages?: string[];
  image_url?: string;
  color_code?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
  events_count?: number;
  total_attendees?: number;
}

export type CampaignType = 
  | 'election'
  | 'awareness'
  | 'membership'
  | 'fundraising'
  | 'outreach'
  | 'voter_education'
  | 'mobilization'
  | 'other';

export type CampaignStatus = 
  | 'planning'
  | 'active'
  | 'paused'
  | 'completed'
  | 'cancelled';

export interface CampaignCreate {
  name: string;
  name_ta?: string;
  description?: string;
  description_ta?: string;
  campaign_type: CampaignType;
  start_date: string;
  end_date: string;
  budget?: number;
  target_constituency?: string;
  target_ward?: string;
  goals?: string[];
  key_messages?: string[];
  image_url?: string;
  color_code?: string;
}

export interface CampaignUpdate {
  name?: string;
  name_ta?: string;
  description?: string;
  description_ta?: string;
  campaign_type?: CampaignType;
  status?: CampaignStatus;
  start_date?: string;
  end_date?: string;
  budget?: number;
  target_constituency?: string;
  target_ward?: string;
  goals?: string[];
  key_messages?: string[];
  image_url?: string;
  color_code?: string;
}

// Attendance types
export interface EventAttendance {
  id: string;
  event_id: string;
  member_id?: string;
  non_member_name?: string;
  non_member_phone?: string;
  status: AttendanceStatus;
  registered_at?: string;
  checked_in_at?: string;
  checked_out_at?: string;
  notes?: string;
  member?: {
    id: string;
    first_name: string;
    last_name?: string;
    phone: string;
    photo_url?: string;
  };
}

export type AttendanceStatus = 
  | 'registered'
  | 'confirmed'
  | 'checked_in'
  | 'checked_out'
  | 'no_show'
  | 'cancelled';

export interface AttendanceCreate {
  member_id?: string;
  non_member_name?: string;
  non_member_phone?: string;
  status?: AttendanceStatus;
  notes?: string;
}

export interface AttendanceUpdate {
  status?: AttendanceStatus;
  checked_in_at?: string;
  checked_out_at?: string;
  notes?: string;
}

// Task types
export interface EventTask {
  id: string;
  event_id: string;
  title: string;
  description?: string;
  assigned_to?: string;
  assigned_to_name?: string;
  due_date?: string;
  status: TaskStatus;
  priority: TaskPriority;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'cancelled';
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface TaskCreate {
  title: string;
  description?: string;
  assigned_to?: string;
  due_date?: string;
  priority?: TaskPriority;
}

export interface TaskUpdate {
  title?: string;
  description?: string;
  assigned_to?: string;
  due_date?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  completed_at?: string;
}

// Stats types
export interface EventStats {
  total_events: number;
  upcoming_events: number;
  completed_events: number;
  active_campaigns: number;
  total_attendance: number;
  avg_attendance: number;
  by_type: Record<EventType, number>;
  by_status: Record<EventStatus, number>;
  by_month: Array<{ month: string; count: number; attendance: number }>;
}

export interface CampaignStats {
  total_campaigns: number;
  active_campaigns: number;
  completed_campaigns: number;
  total_budget: number;
  total_events: number;
  total_attendance: number;
  by_type: Record<CampaignType, number>;
}

// Filter types
export interface EventFilters extends PaginationParams {
  search?: string;
  event_type?: EventType[];
  status?: EventStatus[];
  campaign_id?: string;
  district?: string;
  constituency?: string;
  ward?: string;
  from_date?: string;
  to_date?: string;
  organizer?: string;
  tags?: string[];
}

export interface CampaignFilters extends PaginationParams {
  search?: string;
  campaign_type?: CampaignType[];
  status?: CampaignStatus[];
  from_date?: string;
  to_date?: string;
}

// Response types
export interface EventListResponse {
  events: Event[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface CampaignListResponse {
  campaigns: Campaign[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface AttendanceListResponse {
  attendance: EventAttendance[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface TaskListResponse {
  tasks: EventTask[];
  total: number;
}

export interface EventStatsResponse {
  stats: EventStats;
  generated_at: string;
}

export interface CampaignStatsResponse {
  stats: CampaignStats;
  generated_at: string;
}

// ============================================================================
// Events Service
// ============================================================================

export const eventsService = {
  // =========================================================================
  // Event CRUD Operations
  // =========================================================================

  /**
   * Get list of events with filters and pagination
   */
  async getEvents(params?: EventFilters): Promise<EventListResponse> {
    return api.get('/events', params);
  },

  /**
   * Get a single event by ID
   */
  async getEvent(id: string): Promise<Event> {
    const response = await api.get<ApiResponse<Event>>(`/events/${id}`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Event not found',
      status: 404,
    });
  },

  /**
   * Create a new event
   */
  async createEvent(data: EventCreate): Promise<Event> {
    const response = await api.post<ApiResponse<Event>>('/events', data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to create event',
      status: 400,
    });
  },

  /**
   * Update an event
   */
  async updateEvent(id: string, data: EventUpdate): Promise<Event> {
    const response = await api.patch<ApiResponse<Event>>(`/events/${id}`, data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to update event',
      status: 400,
    });
  },

  /**
   * Delete an event
   */
  async deleteEvent(id: string): Promise<void> {
    const response = await api.delete<ApiResponse<void>>(`/events/${id}`);
    
    if (!response.success) {
      throw new ApiError({
        message: response.message || 'Failed to delete event',
        status: 400,
      });
    }
  },

  /**
   * Publish an event
   */
  async publishEvent(id: string): Promise<Event> {
    return this.updateEvent(id, { status: 'published' });
  },

  /**
   * Cancel an event
   */
  async cancelEvent(id: string): Promise<Event> {
    return this.updateEvent(id, { status: 'cancelled' });
  },

  // =========================================================================
  // Campaign CRUD Operations
  // =========================================================================

  /**
   * Get list of campaigns with filters and pagination
   */
  async getCampaigns(params?: CampaignFilters): Promise<CampaignListResponse> {
    return api.get('/campaigns', params);
  },

  /**
   * Get a single campaign by ID
   */
  async getCampaign(id: string): Promise<Campaign> {
    const response = await api.get<ApiResponse<Campaign>>(`/campaigns/${id}`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Campaign not found',
      status: 404,
    });
  },

  /**
   * Create a new campaign
   */
  async createCampaign(data: CampaignCreate): Promise<Campaign> {
    const response = await api.post<ApiResponse<Campaign>>('/campaigns', data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to create campaign',
      status: 400,
    });
  },

  /**
   * Update a campaign
   */
  async updateCampaign(id: string, data: CampaignUpdate): Promise<Campaign> {
    const response = await api.patch<ApiResponse<Campaign>>(`/campaigns/${id}`, data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to update campaign',
      status: 400,
    });
  },

  /**
   * Delete a campaign
   */
  async deleteCampaign(id: string): Promise<void> {
    const response = await api.delete<ApiResponse<void>>(`/campaigns/${id}`);
    
    if (!response.success) {
      throw new ApiError({
        message: response.message || 'Failed to delete campaign',
        status: 400,
      });
    }
  },

  /**
   * Get campaign events
   */
  async getCampaignEvents(campaignId: string): Promise<EventListResponse> {
    return api.get(`/campaigns/${campaignId}/events`);
  },

  // =========================================================================
  // Attendance Operations
  // =========================================================================

  /**
   * Get event attendance records
   */
  async getEventAttendance(eventId: string, params?: PaginationParams): Promise<AttendanceListResponse> {
    return api.get(`/events/${eventId}/attendance`, params);
  },

  /**
   * Add attendance record
   */
  async addAttendance(eventId: string, data: AttendanceCreate): Promise<EventAttendance> {
    const response = await api.post<ApiResponse<EventAttendance>>(`/events/${eventId}/attendance`, data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to add attendance',
      status: 400,
    });
  },

  /**
   * Update attendance record
   */
  async updateAttendance(eventId: string, attendanceId: string, data: AttendanceUpdate): Promise<EventAttendance> {
    const response = await api.patch<ApiResponse<EventAttendance>>(
      `/events/${eventId}/attendance/${attendanceId}`,
      data
    );
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to update attendance',
      status: 400,
    });
  },

  /**
   * Delete attendance record
   */
  async deleteAttendance(eventId: string, attendanceId: string): Promise<void> {
    await api.delete(`/events/${eventId}/attendance/${attendanceId}`);
  },

  /**
   * Check in attendee
   */
  async checkInAttendee(eventId: string, attendanceId: string): Promise<EventAttendance> {
    return this.updateAttendance(eventId, attendanceId, {
      status: 'checked_in',
      checked_in_at: new Date().toISOString(),
    });
  },

  /**
   * Check out attendee
   */
  async checkOutAttendee(eventId: string, attendanceId: string): Promise<EventAttendance> {
    return this.updateAttendance(eventId, attendanceId, {
      status: 'checked_out',
      checked_out_at: new Date().toISOString(),
    });
  },

  /**
   * Bulk check-in from member IDs
   */
  async bulkCheckIn(eventId: string, memberIds: string[]): Promise<{ checked_in: number; failed: number }> {
    const response = await api.post<ApiResponse<{ checked_in: number; failed: number }>>(
      `/events/${eventId}/attendance/bulk-check-in`,
      { member_ids: memberIds }
    );
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Bulk check-in failed',
      status: 400,
    });
  },

  // =========================================================================
  // Task Operations
  // =========================================================================

  /**
   * Get event tasks
   */
  async getEventTasks(eventId: string): Promise<TaskListResponse> {
    return api.get(`/events/${eventId}/tasks`);
  },

  /**
   * Create task for event
   */
  async createTask(eventId: string, data: TaskCreate): Promise<EventTask> {
    const response = await api.post<ApiResponse<EventTask>>(`/events/${eventId}/tasks`, data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to create task',
      status: 400,
    });
  },

  /**
   * Update task
   */
  async updateTask(eventId: string, taskId: string, data: TaskUpdate): Promise<EventTask> {
    const response = await api.patch<ApiResponse<EventTask>>(
      `/events/${eventId}/tasks/${taskId}`,
      data
    );
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to update task',
      status: 400,
    });
  },

  /**
   * Delete task
   */
  async deleteTask(eventId: string, taskId: string): Promise<void> {
    await api.delete(`/events/${eventId}/tasks/${taskId}`);
  },

  /**
   * Complete task
   */
  async completeTask(eventId: string, taskId: string): Promise<EventTask> {
    return this.updateTask(eventId, taskId, {
      status: 'completed',
      completed_at: new Date().toISOString(),
    });
  },

  // =========================================================================
  // Statistics
  // =========================================================================

  /**
   * Get event statistics
   */
  async getEventStats(): Promise<EventStats> {
    const response = await api.get<ApiResponse<EventStatsResponse>>('/events/stats');
    
    if (response.success && response.data) {
      return response.data.stats;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to get stats',
      status: 400,
    });
  },

  /**
   * Get campaign statistics
   */
  async getCampaignStats(): Promise<CampaignStats> {
    const response = await api.get<ApiResponse<CampaignStatsResponse>>('/campaigns/stats');
    
    if (response.success && response.data) {
      return response.data.stats;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to get campaign stats',
      status: 400,
    });
  },

  // =========================================================================
  // Calendar
  // =========================================================================

  /**
   * Get events for calendar view
   */
  async getCalendarEvents(fromDate: string, toDate: string, filters?: Partial<EventFilters>): Promise<Event[]> {
    const response = await api.get<ApiResponse<Event[]>>('/events/calendar', {
      from_date: fromDate,
      to_date: toDate,
      ...filters,
    });
    
    if (response.success && response.data) {
      return response.data;
    }
    
    return [];
  },

  // =========================================================================
  // Search
  // =========================================================================

  /**
   * Search events
   */
  async searchEvents(query: string, limit?: number): Promise<Event[]> {
    return api.get('/events/search', { q: query, limit });
  },

  /**
   * Search campaigns
   */
  async searchCampaigns(query: string, limit?: number): Promise<Campaign[]> {
    return api.get('/campaigns/search', { q: query, limit });
  },

  // =========================================================================
  // Registration
  // =========================================================================

  /**
   * Register for event
   */
  async registerForEvent(eventId: string, data: { member_id?: string; non_member_name?: string; non_member_phone?: string }): Promise<EventAttendance> {
    const response = await api.post<ApiResponse<EventAttendance>>(`/events/${eventId}/register`, data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to register for event',
      status: 400,
    });
  },

  /**
   * Cancel registration
   */
  async cancelRegistration(eventId: string, attendanceId: string): Promise<void> {
    await this.updateAttendance(eventId, attendanceId, { status: 'cancelled' });
  },
};

export default eventsService;
