/**
 * Communications Service
 * API endpoints for announcements, forums, and communications operations
 */

import { api, ApiResponse, PaginationParams, ApiError } from './api';

// ============================================================================
// Types
// ============================================================================

// Announcement types
export interface Announcement {
  id: string;
  title: string;
  content: string;
  category: AnnouncementCategory;
  priority: AnnouncementPriority;
  is_pinned: boolean;
  is_active: boolean;
  published_at?: string;
  expires_at?: string;
  author_id: string;
  author_name?: string;
  target_audience?: string[];
  target_districts?: string[];
  target_constituencies?: string[];
  attachments?: Attachment[];
  views_count: number;
  created_at: string;
  updated_at: string;
}

export type AnnouncementCategory = 
  | 'general'
  | 'event'
  | 'campaign'
  | 'policy'
  | 'alert'
  | 'update';

export type AnnouncementPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface AnnouncementCreate {
  title: string;
  content: string;
  category: AnnouncementCategory;
  priority: AnnouncementPriority;
  is_pinned?: boolean;
  published_at?: string;
  expires_at?: string;
  target_audience?: string[];
  target_districts?: string[];
  target_constituencies?: string[];
}

export interface AnnouncementUpdate {
  title?: string;
  content?: string;
  category?: AnnouncementCategory;
  priority?: AnnouncementPriority;
  is_pinned?: boolean;
  is_active?: boolean;
  published_at?: string;
  expires_at?: string;
  target_audience?: string[];
  target_districts?: string[];
  target_constituencies?: string[];
}

// Forum types
export interface Forum {
  id: string;
  title: string;
  description: string;
  slug: string;
  category: ForumCategory;
  is_moderated: boolean;
  requires_approval: boolean;
  is_active: boolean;
  created_by: string;
  created_by_name?: string;
  moderators?: ForumModerator[];
  thread_count: number;
  post_count: number;
  last_activity_at?: string;
  created_at: string;
  updated_at: string;
}

export type ForumCategory = 
  | 'general'
  | 'discussion'
  | 'feedback'
  | 'suggestion'
  | 'announcement'
  | 'support';

export interface ForumCreate {
  title: string;
  description: string;
  category: ForumCategory;
  is_moderated?: boolean;
  requires_approval?: boolean;
  moderators?: string[];
}

export interface ForumUpdate {
  title?: string;
  description?: string;
  category?: ForumCategory;
  is_moderated?: boolean;
  requires_approval?: boolean;
  moderators?: string[];
}

export interface ForumModerator {
  user_id: string;
  user_name?: string;
  role: 'moderator' | 'admin';
  added_at: string;
}

// Forum Post types
export interface ForumPost {
  id: string;
  forum_id: string;
  title?: string;
  content: string;
  author_id: string;
  author_name?: string;
  author_avatar?: string;
  is_approved: boolean;
  is_pinned: boolean;
  is_locked: boolean;
  is_anonymous: boolean;
  parent_id?: string;
  replies_count: number;
  likes_count: number;
  views_count: number;
  tags?: string[];
  created_at: string;
  updated_at: string;
  replies?: ForumPost[];
}

export interface ForumPostCreate {
  title?: string;
  content: string;
  is_anonymous?: boolean;
  parent_id?: string;
  tags?: string[];
}

export interface ForumPostUpdate {
  title?: string;
  content?: string;
  tags?: string[];
}

// Comment types
export interface Comment {
  id: string;
  post_id: string;
  content: string;
  author_id: string;
  author_name?: string;
  author_avatar?: string;
  parent_id?: string;
  replies_count: number;
  likes_count: number;
  is_approved: boolean;
  created_at: string;
  updated_at: string;
  replies?: Comment[];
}

export interface CommentCreate {
  content: string;
  parent_id?: string;
}

export interface CommentUpdate {
  content: string;
}

// Attachment types
export interface Attachment {
  id: string;
  file_name: string;
  file_url: string;
  file_type: string;
  file_size: number;
  uploaded_by: string;
  uploaded_at: string;
}

// Filter types
export interface AnnouncementFilters extends PaginationParams {
  search?: string;
  category?: AnnouncementCategory[];
  priority?: AnnouncementPriority[];
  is_pinned?: boolean;
  is_active?: boolean;
  from_date?: string;
  to_date?: string;
  target_audience?: string[];
}

export interface ForumFilters extends PaginationParams {
  search?: string;
  category?: ForumCategory[];
  is_moderated?: boolean;
  is_active?: boolean;
}

export interface PostFilters extends PaginationParams {
  search?: string;
  forum_id?: string;
  author_id?: string;
  is_approved?: boolean;
  is_pinned?: boolean;
  sort_by?: 'recent' | 'popular' | 'unanswered';
}

export interface CommentFilters extends PaginationParams {
  post_id: string;
  parent_id?: string;
}

// Response types
export interface AnnouncementListResponse {
  announcements: Announcement[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface ForumListResponse {
  forums: Forum[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface ForumDetailResponse {
  forum: Forum;
  recent_posts: ForumPost[];
}

export interface PostListResponse {
  posts: ForumPost[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface PostDetailResponse {
  post: ForumPost;
  comments: Comment[];
}

export interface CommentListResponse {
  comments: Comment[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

// Stats types
export interface CommunicationsStats {
  total_announcements: number;
  active_announcements: number;
  total_forums: number;
  active_forums: number;
  total_posts: number;
  total_comments: number;
  announcements_this_month: number;
  posts_this_week: number;
  top_forums: Array<{ forum: Forum; post_count: number }>;
}

// ============================================================================
// Communications Service
// ============================================================================

export const communicationsService = {
  // =========================================================================
  // Announcement Operations
  // =========================================================================

  /**
   * Get list of announcements with filters and pagination
   */
  async getAnnouncements(params?: AnnouncementFilters): Promise<AnnouncementListResponse> {
    return api.get('/communications/announcements', params);
  },

  /**
   * Get a single announcement by ID
   */
  async getAnnouncement(id: string): Promise<Announcement> {
    const response = await api.get<ApiResponse<Announcement>>(`/communications/announcements/${id}`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Announcement not found',
      status: 404,
    });
  },

  /**
   * Create a new announcement
   */
  async createAnnouncement(data: AnnouncementCreate): Promise<Announcement> {
    const response = await api.post<ApiResponse<Announcement>>('/communications/announcements', data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to create announcement',
      status: 400,
    });
  },

  /**
   * Update an announcement
   */
  async updateAnnouncement(id: string, data: AnnouncementUpdate): Promise<Announcement> {
    const response = await api.patch<ApiResponse<Announcement>>(`/communications/announcements/${id}`, data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to update announcement',
      status: 400,
    });
  },

  /**
   * Delete an announcement
   */
  async deleteAnnouncement(id: string): Promise<void> {
    const response = await api.delete<ApiResponse<void>>(`/communications/announcements/${id}`);
    
    if (!response.success) {
      throw new ApiError({
        message: response.message || 'Failed to delete announcement',
        status: 400,
      });
    }
  },

  /**
   * Publish an announcement
   */
  async publishAnnouncement(id: string): Promise<Announcement> {
    const response = await api.post<ApiResponse<Announcement>>(`/communications/announcements/${id}/publish`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to publish announcement',
      status: 400,
    });
  },

  // =========================================================================
  // Forum Operations
  // =========================================================================

  /**
   * Get list of forums with filters and pagination
   */
  async getForums(params?: ForumFilters): Promise<ForumListResponse> {
    return api.get('/communications/forums', params);
  },

  /**
   * Get a single forum by ID or slug
   */
  async getForum(idOrSlug: string): Promise<ForumDetailResponse> {
    const response = await api.get<ApiResponse<ForumDetailResponse>>(`/communications/forums/${idOrSlug}`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Forum not found',
      status: 404,
    });
  },

  /**
   * Create a new forum
   */
  async createForum(data: ForumCreate): Promise<Forum> {
    const response = await api.post<ApiResponse<Forum>>('/communications/forums', data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to create forum',
      status: 400,
    });
  },

  /**
   * Update a forum
   */
  async updateForum(id: string, data: ForumUpdate): Promise<Forum> {
    const response = await api.patch<ApiResponse<Forum>>(`/communications/forums/${id}`, data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to update forum',
      status: 400,
    });
  },

  /**
   * Delete a forum
   */
  async deleteForum(id: string): Promise<void> {
    const response = await api.delete<ApiResponse<void>>(`/communications/forums/${id}`);
    
    if (!response.success) {
      throw new ApiError({
        message: response.message || 'Failed to delete forum',
        status: 400,
      });
    }
  },

  /**
   * Add moderator to forum
   */
  async addForumModerator(forumId: string, userId: string): Promise<ForumModerator> {
    const response = await api.post<ApiResponse<ForumModerator>>(
      `/communications/forums/${forumId}/moderators`,
      { user_id: userId }
    );
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to add moderator',
      status: 400,
    });
  },

  /**
   * Remove moderator from forum
   */
  async removeForumModerator(forumId: string, userId: string): Promise<void> {
    await api.delete(`/communications/forums/${forumId}/moderators/${userId}`);
  },

  // =========================================================================
  // Forum Post Operations
  // =========================================================================

  /**
   * Get posts with filters and pagination
   */
  async getPosts(params?: PostFilters): Promise<PostListResponse> {
    return api.get('/communications/posts', params);
  },

  /**
   * Get a single post by ID
   */
  async getPost(id: string): Promise<PostDetailResponse> {
    const response = await api.get<ApiResponse<PostDetailResponse>>(`/communications/posts/${id}`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Post not found',
      status: 404,
    });
  },

  /**
   * Create a new post in a forum
   */
  async createPost(forumId: string, data: ForumPostCreate): Promise<ForumPost> {
    const response = await api.post<ApiResponse<ForumPost>>(
      `/communications/forums/${forumId}/posts`,
      data
    );
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to create post',
      status: 400,
    });
  },

  /**
   * Update a post
   */
  async updatePost(id: string, data: ForumPostUpdate): Promise<ForumPost> {
    const response = await api.patch<ApiResponse<ForumPost>>(`/communications/posts/${id}`, data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to update post',
      status: 400,
    });
  },

  /**
   * Delete a post
   */
  async deletePost(id: string): Promise<void> {
    const response = await api.delete<ApiResponse<void>>(`/communications/posts/${id}`);
    
    if (!response.success) {
      throw new ApiError({
        message: response.message || 'Failed to delete post',
        status: 400,
      });
    }
  },

  /**
   * Approve a post
   */
  async approvePost(id: string): Promise<ForumPost> {
    const response = await api.post<ApiResponse<ForumPost>>(`/communications/posts/${id}/approve`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to approve post',
      status: 400,
    });
  },

  /**
   * Pin/unpin a post
   */
  async togglePinPost(id: string): Promise<ForumPost> {
    const response = await api.post<ApiResponse<ForumPost>>(`/communications/posts/${id}/pin`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to pin/unpin post',
      status: 400,
    });
  },

  /**
   * Lock/unlock a post
   */
  async toggleLockPost(id: string): Promise<ForumPost> {
    const response = await api.post<ApiResponse<ForumPost>>(`/communications/posts/${id}/lock`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to lock/unlock post',
      status: 400,
    });
  },

  /**
   * Like a post
   */
  async likePost(id: string): Promise<ForumPost> {
    const response = await api.post<ApiResponse<ForumPost>>(`/communications/posts/${id}/like`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to like post',
      status: 400,
    });
  },

  // =========================================================================
  // Comment Operations
  // =========================================================================

  /**
   * Get comments for a post
   */
  async getComments(params: CommentFilters): Promise<CommentListResponse> {
    return api.get('/communications/comments', params);
  },

  /**
   * Create a new comment on a post
   */
  async createComment(postId: string, data: CommentCreate): Promise<Comment> {
    const response = await api.post<ApiResponse<Comment>>(
      `/communications/posts/${postId}/comments`,
      data
    );
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to create comment',
      status: 400,
    });
  },

  /**
   * Update a comment
   */
  async updateComment(id: string, data: CommentUpdate): Promise<Comment> {
    const response = await api.patch<ApiResponse<Comment>>(`/communications/comments/${id}`, data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to update comment',
      status: 400,
    });
  },

  /**
   * Delete a comment
   */
  async deleteComment(id: string): Promise<void> {
    const response = await api.delete<ApiResponse<void>>(`/communications/comments/${id}`);
    
    if (!response.success) {
      throw new ApiError({
        message: response.message || 'Failed to delete comment',
        status: 400,
      });
    }
  },

  /**
   * Like a comment
   */
  async likeComment(id: string): Promise<Comment> {
    const response = await api.post<ApiResponse<Comment>>(`/communications/comments/${id}/like`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to like comment',
      status: 400,
    });
  },

  // =========================================================================
  // Statistics
  // =========================================================================

  /**
   * Get communications statistics
   */
  async getStats(): Promise<CommunicationsStats> {
    const response = await api.get<ApiResponse<{ stats: CommunicationsStats }>>(
      '/communications/stats'
    );
    
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
   * Search announcements
   */
  async searchAnnouncements(query: string, limit?: number): Promise<Announcement[]> {
    return api.get('/communications/announcements/search', { q: query, limit });
  },

  /**
   * Search forum posts
   */
  async searchPosts(query: string, forumId?: string, limit?: number): Promise<ForumPost[]> {
    return api.get('/communications/posts/search', { q: query, forum_id: forumId, limit });
  },
};

export default communicationsService;
