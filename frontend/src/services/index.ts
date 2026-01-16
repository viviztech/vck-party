/**
 * Services Index
 * Export all API services from a single entry point
 */

// Base API configuration
export { api, ApiClient } from './api';
export type { ApiError, ApiResponse, ErrorResponse } from './api';
export type {
  PaginatedResponse,
  PaginationParams,
  AuthTokens,
  User,
  Role,
  Permission,
} from './api';

// Authentication Service
export { authService } from './authService';
export type {
  LoginRequest,
  PhoneLoginRequest,
  RegisterRequest,
  UserUpdateRequest,
  PasswordChangeRequest,
  PasswordResetRequest,
  PasswordResetConfirmRequest,
  OTPRequest,
  OTPVerifyRequest,
  AuthResponse,
} from './authService';

// Members Service
export { membersService } from './membersService';
export type {
  Member,
  MemberCreate,
  MemberUpdate,
  MemberProfile,
  MemberProfileUpdate,
  MemberFamily,
  MemberFamilyCreate,
  MemberDocument,
  MemberDocumentCreate,
  MemberTag,
  MemberTagAdd,
  MemberNote,
  MemberNoteCreate,
  MemberNoteUpdate,
  MemberHistory,
  MemberStats,
  MemberFilters,
  MemberListResponse,
  MemberStatsResponse,
  MemberBulkImportResult,
  MemberExportResponse,
} from './membersService';

// Hierarchy Service
export { hierarchyService } from './hierarchyService';
export type {
  HierarchyNode,
  HierarchyTreeNode,
  HierarchyFilters,
  District,
  DistrictCreate,
  DistrictUpdate,
  DistrictDetail,
  Constituency,
  ConstituencyCreate,
  ConstituencyUpdate,
  ConstituencyDetail,
  Ward,
  WardCreate,
  WardUpdate,
  WardDetail,
  Booth,
  BoothCreate,
  BoothUpdate,
  BoothDetail,
  ZipCodeMapping,
  PincodeLookup,
  HierarchyStats,
  HierarchyStatsResponse,
  GeoSearchResult,
  GeoLocation,
  HierarchyTreeResponse,
  SubTreeResponse,
  PaginatedDistrictResponse,
  PaginatedConstituencyResponse,
  PaginatedWardResponse,
  PaginatedBoothResponse,
} from './hierarchyService';

// Events Service
export { eventsService } from './eventsService';
export type {
  Event,
  EventCreate,
  EventUpdate,
  EventType,
  EventStatus,
  Campaign,
  CampaignCreate,
  CampaignUpdate,
  CampaignType,
  CampaignStatus,
  EventAttendance,
  AttendanceCreate,
  AttendanceUpdate,
  AttendanceStatus,
  EventTask,
  TaskCreate,
  TaskUpdate,
  TaskStatus,
  TaskPriority,
  EventStats,
  CampaignStats,
  EventFilters,
  CampaignFilters,
  EventListResponse,
  CampaignListResponse,
  AttendanceListResponse,
  TaskListResponse,
  EventStatsResponse,
  CampaignStatsResponse,
} from './eventsService';

// Voting Service
export { votingService } from './votingService';
export type {
  Election,
  ElectionDetail,
  ElectionStatus,
  ElectionPosition,
  Nomination,
  NominationStatus,
  Candidate,
  VotingStatus,
  VoteCast,
  VoteReceipt,
  VoteVerification,
  ElectionResults,
  ElectionResultCandidate,
  ElectionResultPosition,
  ElectionStats,
  ElectionFilters,
  NominationFilters,
  ElectionListResponse,
  ElectionCandidatesResponse,
  NominationListResponse,
  ElectionStatsResponse,
  VotingMethod,
} from './votingService';

// Communications Service
export { communicationsService } from './communicationsService';
export type {
  Announcement,
  AnnouncementCreate,
  AnnouncementUpdate,
  AnnouncementCategory,
  AnnouncementPriority,
  AnnouncementFilters,
  AnnouncementListResponse,
  Forum,
  ForumCreate,
  ForumUpdate,
  ForumCategory,
  ForumModerator,
  ForumFilters,
  ForumListResponse,
  ForumDetailResponse,
  ForumPost,
  ForumPostCreate,
  ForumPostUpdate,
  PostFilters,
  PostListResponse,
  PostDetailResponse,
  Comment,
  CommentCreate,
  CommentUpdate,
  CommentFilters,
  CommentListResponse,
  CommunicationsStats,
} from './communicationsService';
