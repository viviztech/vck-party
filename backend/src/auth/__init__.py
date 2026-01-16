"""
Auth Module
Authentication and authorization for the VCK platform.
"""

from src.auth.models import User, Role, Permission, RefreshToken, UserStatus
from src.auth.schemas import (
    TokenResponse,
    TokenPayload,
    LoginRequest,
    RefreshTokenRequest,
    LogoutRequest,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    PermissionCreate,
    PermissionResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordChange,
    UserRoleAssign,
    ApiResponse,
    AuthResponse,
    OTPRequest,
    OTPVerify,
    OTPResponse,
)
from src.auth.crud import UserCRUD, RoleCRUD, PermissionCRUD, TokenCRUD
from src.auth.router import router as auth_router

__all__ = [
    # Models
    "User",
    "Role",
    "Permission",
    "RefreshToken",
    "UserStatus",
    # Schemas
    "TokenResponse",
    "TokenPayload",
    "LoginRequest",
    "RefreshTokenRequest",
    "LogoutRequest",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserListResponse",
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
    "PermissionCreate",
    "PermissionResponse",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "PasswordChange",
    "UserRoleAssign",
    "ApiResponse",
    "AuthResponse",
    "OTPRequest",
    "OTPVerify",
    "OTPResponse",
    # CRUD
    "UserCRUD",
    "RoleCRUD",
    "PermissionCRUD",
    "TokenCRUD",
    # Router
    "auth_router",
]
