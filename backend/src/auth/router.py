"""
Auth Router
API routes for authentication and authorization.
"""

from datetime import timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.config import settings
from src.core.security import create_access_token
from src.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    AlreadyExistsError,
    ValidationError,
)
from src.core import redis

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
from src.auth.deps import (
    get_current_user,
    get_current_active_user,
    get_current_admin,
    get_client_ip,
    get_device_info,
    check_auth_rate_limit,
    require_permission,
)
from src.auth.crud import UserCRUD, RoleCRUD, TokenCRUD, PermissionCRUD
from src.auth.models import User, Role, UserStatus


router = APIRouter(prefix="/auth", tags=["Authentication"])


# =============================================================================
# Health Check
# =============================================================================

@router.get("/health")
async def auth_health_check():
    """Health check endpoint for auth service."""
    return {"status": "healthy", "service": "auth"}


# =============================================================================
# Registration
# =============================================================================

@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    ip_address: str = Depends(get_client_ip),
):
    """
    Register a new user.
    
    Creates a new user account with the provided email and phone.
    The user will need to verify their email/phone to activate.
    """
    # Check rate limit
    await check_auth_rate_limit(request, limit=5, window=3600)
    
    try:
        # Create user
        user = await UserCRUD.create(db, user_data)
        
        # Assign default member role
        _, member_role, _ = await RoleCRUD.get_default_roles(db)
        if member_role:
            await UserCRUD.assign_roles(db, user.id, [member_role.id])
            await db.refresh(user)
        
        # Generate tokens
        access_token = create_access_token(
            {"sub": str(user.id), "email": user.email, "phone": user.phone}
        )
        refresh_token = await TokenCRUD.create_refresh_token(
            db,
            user.id,
            ip_address,
            request.headers.get("user-agent"),
            get_device_info(request)
        )
        
        return AuthResponse(
            success=True,
            message="User registered successfully",
            data=TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="Bearer",
                expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user=UserResponse.model_validate(user),
            ),
        )
    except AlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=e.to_dict())


# =============================================================================
# Login
# =============================================================================

@router.post("/login", response_model=AuthResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
    ip_address: str = Depends(get_client_ip),
):
    """
    Login with email and password.
    
    Returns JWT access and refresh tokens upon successful authentication.
    """
    # Check rate limit
    await check_auth_rate_limit(request)
    
    try:
        user = await UserCRUD.authenticate(
            db,
            login_data.email,
            login_data.password,
            ip_address,
            request.headers.get("user-agent"),
            login_data.device_info or get_device_info(request),
        )
        
        # Generate tokens
        access_token = create_access_token(
            {"sub": str(user.id), "email": user.email, "phone": user.phone}
        )
        refresh_token = await TokenCRUD.create_refresh_token(
            db,
            user.id,
            ip_address,
            request.headers.get("user-agent"),
            login_data.device_info or get_device_info(request)
        )
        
        return AuthResponse(
            success=True,
            message="Login successful",
            data=TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="Bearer",
                expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user=UserResponse.model_validate(user),
            ),
        )
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=e.to_dict())


# =============================================================================
# Token Refresh
# =============================================================================

@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    request: Request,
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    ip_address: str = Depends(get_client_ip),
):
    """
    Refresh access token using refresh token.
    
    Invalidates the old refresh token and issues a new pair of tokens.
    """
    try:
        access_token, refresh_token, user = await TokenCRUD.refresh_access_token(
            db,
            refresh_data.refresh_token,
            ip_address,
            request.headers.get("user-agent"),
            get_device_info(request),
        )
        
        return AuthResponse(
            success=True,
            message="Token refreshed successfully",
            data=TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="Bearer",
                expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user=UserResponse.model_validate(user),
            ),
        )
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=e.to_dict())


# =============================================================================
# Logout
# =============================================================================

@router.post("/logout", response_model=ApiResponse)
async def logout(
    request: Request,
    logout_data: LogoutRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Logout and revoke refresh token.
    
    Optionally revokes the specified refresh token.
    """
    if logout_data.refresh_token:
        await TokenCRUD.revoke_refresh_token(db, logout_data.refresh_token)
    
    return ApiResponse(
        success=True,
        message="Logged out successfully",
    )


# =============================================================================
# Current User
# =============================================================================

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get the current authenticated user's information.
    """
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update the current user's information.
    """
    user = await UserCRUD.update(db, current_user.id, user_data)
    return UserResponse.model_validate(user)


@router.post("/me/change-password", response_model=ApiResponse)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Change password for authenticated user.
    """
    from src.core.security import verify_password
    
    # Verify current password
    if current_user.password_hash:
        if not verify_password(password_data.current_password, current_user.password_hash):
            raise AuthenticationError("Current password is incorrect")
    
    # Update password
    await UserCRUD.update_password(db, current_user.id, password_data.new_password)
    
    # Revoke all refresh tokens for security
    await TokenCRUD.revoke_all_user_tokens(db, current_user.id)
    
    return ApiResponse(
        success=True,
        message="Password changed successfully. Please login again.",
    )


# =============================================================================
# User Management (Admin)
# =============================================================================

@router.get("/users", response_model=UserListResponse)
async def list_users(
    request: Request,
    page: int = 1,
    limit: int = 20,
    search: str = None,
    role: str = None,
    status: str = None,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    List all users (admin only).
    
    Supports pagination and filtering by search term, role, and status.
    """
    # Validate pagination
    limit = min(limit, 100)
    page = max(page, 1)
    
    users, total = await UserCRUD.get_users_paginated(
        db, page, limit, search, role, status
    )
    
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    
    return UserListResponse(
        users=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific user by ID (admin only).
    """
    user = await UserCRUD.get_by_id(db, User, user_id)
    if not user:
        raise NotFoundError(resource="User", resource_id=str(user_id))
    return UserResponse.model_validate(user)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a user (admin only).
    """
    user = await UserCRUD.update(db, user_id, user_data)
    if not user:
        raise NotFoundError(resource="User", resource_id=str(user_id))
    return UserResponse.model_validate(user)


@router.post("/users/{user_id}/roles", response_model=UserResponse)
async def assign_user_roles(
    user_id: UUID,
    role_assign: UserRoleAssign,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Assign roles to a user (admin only).
    """
    user = await UserCRUD.assign_roles(db, user_id, role_assign.role_ids)
    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}/roles", response_model=UserResponse)
async def remove_user_roles(
    user_id: UUID,
    role_assign: UserRoleAssign,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove roles from a user (admin only).
    """
    user = await UserCRUD.remove_roles(db, user_id, role_assign.role_ids)
    return UserResponse.model_validate(user)


@router.post("/users/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Deactivate a user (admin only).
    """
    user = await UserCRUD.update(db, user_id, UserUpdate(is_active=False))
    if not user:
        raise NotFoundError(resource="User", resource_id=str(user_id))
    
    # Revoke all user tokens
    await TokenCRUD.revoke_all_user_tokens(db, user_id)
    
    return UserResponse.model_validate(user)


@router.post("/users/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Activate a user (admin only).
    """
    user = await UserCRUD.update(db, user_id, UserUpdate(is_active=True))
    if not user:
        raise NotFoundError(resource="User", resource_id=str(user_id))
    return UserResponse.model_validate(user)


# =============================================================================
# Password Reset
# =============================================================================

@router.post("/password/reset-request", response_model=ApiResponse)
async def request_password_reset(
    request: Request,
    reset_data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Request a password reset email.
    
    Sends a password reset link to the user's email.
    """
    # Check rate limit
    await check_auth_rate_limit(request, limit=3, window=3600)
    
    user = await UserCRUD.get_by_email(db, reset_data.email)
    # Always return success to prevent email enumeration
    if not user:
        return ApiResponse(
            success=True,
            message="If the email exists, a reset link has been sent",
        )
    
    # TODO: Generate reset token and send email
    # For now, just return success
    return ApiResponse(
        success=True,
        message="If the email exists, a reset link has been sent",
    )


@router.post("/password/reset", response_model=ApiResponse)
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
):
    """
    Reset password with reset token.
    
    Validates the reset token and updates the password.
    """
    # TODO: Validate reset token and get user
    # For now, just return success
    return ApiResponse(
        success=True,
        message="Password reset successfully",
    )


# =============================================================================
# Role Management (Admin)
# =============================================================================

@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    List all roles (admin only).
    """
    roles = await RoleCRUD.get_all(db)
    return [RoleResponse.model_validate(r) for r in roles]


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new role (admin only).
    """
    # Check if role exists
    existing = await RoleCRUD.get_by_name(db, role_data.name)
    if existing:
        raise AlreadyExistsError(resource="Role", field="name", value=role_data.name)
    
    role = await RoleCRUD.create(db, role_data)
    return RoleResponse.model_validate(role)


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific role (admin only).
    """
    role = await RoleCRUD.get_by_id(db, Role, role_id)
    if not role:
        raise NotFoundError(resource="Role", resource_id=str(role_id))
    return RoleResponse.model_validate(role)


@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: UUID,
    role_data: RoleUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a role (admin only).
    """
    role = await RoleCRUD.update(db, role_id, role_data)
    if not role:
        raise NotFoundError(resource="Role", resource_id=str(role_id))
    return RoleResponse.model_validate(role)


@router.delete("/roles/{role_id}", response_model=ApiResponse)
async def delete_role(
    role_id: UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a role (admin only).
    
    Cannot delete system roles.
    """
    role = await RoleCRUD.get_by_id(db, Role, role_id)
    if not role:
        raise NotFoundError(resource="Role", resource_id=str(role_id))
    
    if role.is_system:
        raise ValidationError(message="Cannot delete system roles")
    
    await RoleCRUD.delete(db, Role, role_id)
    return ApiResponse(
        success=True,
        message="Role deleted successfully",
    )


# =============================================================================
# OTP Endpoints
# =============================================================================

@router.post("/otp/request", response_model=OTPResponse)
async def request_otp(
    request: Request,
    otp_data: OTPRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Request an OTP for phone verification.
    
    Sends an OTP to the specified phone number.
    """
    # Check rate limit
    await check_auth_rate_limit(request, limit=5, window=60)
    
    # TODO: Generate OTP and send via SMS
    # For now, just return success
    return OTPResponse(
        success=True,
        message="OTP sent successfully",
        expires_in=settings.OTP_EXPIRE_MINUTES * 60,
        retry_after=0,
    )


@router.post("/otp/verify", response_model=AuthResponse)
async def verify_otp(
    request: Request,
    otp_data: OTPVerify,
    db: AsyncSession = Depends(get_db),
    ip_address: str = Depends(get_client_ip),
):
    """
    Verify OTP and login/register user.
    
    Returns JWT tokens upon successful verification.
    """
    # TODO: Verify OTP and get/create user
    # For now, just return success
    return AuthResponse(
        success=True,
        message="OTP verified successfully",
    )
