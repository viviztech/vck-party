"""
Auth Schemas
Pydantic schemas for authentication and authorization.
"""

from datetime import datetime
from typing import List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict

from src.auth.models import UserStatus


# =============================================================================
# Token Schemas
# =============================================================================

class TokenResponse(BaseModel):
    """Token response after successful login."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int  # Seconds
    user: "UserResponse"


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: str  # User ID
    email: Optional[str] = None
    phone: Optional[str] = None
    jti: Optional[str] = None  # JWT ID
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None
    type: str = "access"


# =============================================================================
# Login Schemas
# =============================================================================

class LoginRequest(BaseModel):
    """Login request with email and password."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    device_info: Optional[dict] = None


class PhoneLoginRequest(BaseModel):
    """Phone login request."""
    phone: str = Field(..., min_length=10, max_length=15)
    device_info: Optional[dict] = None


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class LogoutRequest(BaseModel):
    """Logout request with optional refresh token to revoke."""
    refresh_token: Optional[str] = None


# =============================================================================
# User Schemas
# =============================================================================

class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False


class UserCreate(UserBase):
    """Schema for creating a new user."""
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=8)
    confirm_password: str
    
    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "phone": "+919876543210",
                "password": "securepassword123",
                "confirm_password": "securepassword123"
            }
        }
    }


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=10, max_length=15)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response."""
    id: UUID
    status: str
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    roles: List["RoleResponse"] = []
    
    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserResponse):
    """Schema for user with additional database fields."""
    password_hash: Optional[str] = None
    login_attempts: int = 0
    locked_until: Optional[datetime] = None


class UserListResponse(BaseModel):
    """Paginated user list response."""
    users: List[UserResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# =============================================================================
# Role Schemas
# =============================================================================

class RoleBase(BaseModel):
    """Base role schema."""
    name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None


class RoleCreate(RoleBase):
    """Schema for creating a new role."""
    permission_ids: List[UUID] = []


class RoleUpdate(BaseModel):
    """Schema for updating a role."""
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    permission_ids: Optional[List[UUID]] = None


class RoleResponse(RoleBase):
    """Role response schema."""
    id: UUID
    is_active: bool
    is_system: bool
    priority: int
    created_at: datetime
    updated_at: datetime
    permissions: List["PermissionResponse"] = []
    
    model_config = ConfigDict(from_attributes=True)


class RoleResponseMinimal(BaseModel):
    """Minimal role response for embedding."""
    id: UUID
    name: str
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Permission Schemas
# =============================================================================

class PermissionBase(BaseModel):
    """Base permission schema."""
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    resource: str = Field(..., min_length=2, max_length=50)
    action: str = Field(..., min_length=2, max_length=50)


class PermissionCreate(PermissionBase):
    """Schema for creating a permission."""
    pass


class PermissionResponse(PermissionBase):
    """Permission response schema."""
    id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Password Schemas
# =============================================================================

class PasswordResetRequest(BaseModel):
    """Password reset request."""
    email: EmailStr
    
    model_config = {
        "json_schema_extra": {
            "example": {"email": "user@example.com"}
        }
    }


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation with token."""
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_new_password: str
    
    @field_validator("confirm_new_password")
    @classmethod
    def passwords_match(cls, v: str, info):
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class PasswordChange(BaseModel):
    """Password change for authenticated users."""
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_new_password: str
    
    @field_validator("confirm_new_password")
    @classmethod
    def passwords_match(cls, v: str, info):
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


# =============================================================================
# User-Role Assignment Schemas
# =============================================================================

class UserRoleAssign(BaseModel):
    """Schema for assigning roles to a user."""
    role_ids: List[UUID]


class UserRoleResponse(BaseModel):
    """User role assignment response."""
    user_id: UUID
    role_id: UUID
    role: RoleResponseMinimal
    assigned_at: datetime


# =============================================================================
# OTP Schemas
# =============================================================================

class OTPRequest(BaseModel):
    """OTP request for phone verification."""
    phone: str = Field(..., min_length=10, max_length=15)
    purpose: str = Field(..., pattern="^(login|registration|reset)$")


class OTPVerify(BaseModel):
    """OTP verification request."""
    phone: str = Field(..., min_length=10, max_length=15)
    otp: str = Field(..., min_length=4, max_length=6)
    device_info: Optional[dict] = None


class OTPResponse(BaseModel):
    """OTP response."""
    success: bool
    message: str
    expires_in: int
    retry_after: Optional[int] = None


# =============================================================================
# Device Info Schema
# =============================================================================

class DeviceInfo(BaseModel):
    """Device information for tracking."""
    device_id: Optional[str] = None
    device_type: Optional[str] = None
    app_version: Optional[str] = None
    os_version: Optional[str] = None
    browser: Optional[str] = None


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
# Auth Response with Message
# =============================================================================

class AuthResponse(BaseModel):
    """Authentication response with message."""
    success: bool
    message: str
    data: Optional[TokenResponse] = None


# Update forward references
UserResponse.model_rebuild()
UserInDB.model_rebuild()
RoleResponse.model_rebuild()
