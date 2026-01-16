"""
Auth CRUD Operations
CRUD operations for authentication and authorization.
"""

import json
import math
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Type, Generic, TypeVar
from uuid import UUID

from sqlalchemy import select, update, delete, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import (
    NotFoundError,
    AlreadyExistsError,
    InvalidCredentialsError,
    AuthenticationError,
)
from src.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from src.core import redis
from src.auth.models import User, Role, Permission, RefreshToken
from src.auth.schemas import UserCreate, UserUpdate, RoleCreate, RoleUpdate


# =============================================================================
# Base CRUD Class
# =============================================================================

T = TypeVar('T')

class CRUDBase:
    """Base CRUD class with common operations."""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, model: Type[T], id: UUID) -> Optional[T]:
        """Get a record by ID."""
        result = await db.execute(
            select(model).where(model.id == id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all(
        db: AsyncSession,
        model: Type[T],
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        descending: bool = False
    ) -> List[T]:
        """Get all records with pagination."""
        query = select(model)
        
        if order_by:
            order_field = getattr(model, order_by, None)
            if order_field:
                if descending:
                    query = query.order_by(order_field.desc())
                else:
                    query = query.order_by(order_field.asc())
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def count(db: AsyncSession, model: Type[T]) -> int:
        """Count all records."""
        result = await db.execute(select(func.count(model.id)))
        return result.scalar_one() or 0
    
    @staticmethod
    async def delete(db: AsyncSession, model: Type[T], id: UUID) -> bool:
        """Delete a record by ID."""
        record = await CRUDBase.get_by_id(db, model, id)
        if record:
            await db.delete(record)
            await db.commit()
            return True
        return False


# =============================================================================
# Permission CRUD
# =============================================================================

class PermissionCRUD(CRUDBase):
    """CRUD operations for permissions."""
    
    @staticmethod
    async def get_by_name(db: AsyncSession, name: str) -> Optional[Permission]:
        """Get permission by name."""
        result = await db.execute(
            select(Permission).where(Permission.name == name)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_resource(db: AsyncSession, resource: str) -> List[Permission]:
        """Get all permissions for a resource."""
        result = await db.execute(
            select(Permission).where(Permission.resource == resource)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def create(db: AsyncSession, permission_data: dict) -> Permission:
        """Create a new permission."""
        permission = Permission(**permission_data)
        db.add(permission)
        await db.commit()
        await db.refresh(permission)
        return permission
    
    @staticmethod
    async def get_or_create_default(db: AsyncSession) -> List[Permission]:
        """Create default permissions if they don't exist."""
        default_permissions = [
            {"name": "users:read", "description": "View users", "resource": "users", "action": "read"},
            {"name": "users:write", "description": "Create/Update users", "resource": "users", "action": "write"},
            {"name": "users:delete", "description": "Delete users", "resource": "users", "action": "delete"},
            {"name": "members:read", "description": "View members", "resource": "members", "action": "read"},
            {"name": "members:write", "description": "Create/Update members", "resource": "members", "action": "write"},
            {"name": "members:delete", "description": "Delete members", "resource": "members", "action": "delete"},
            {"name": "events:read", "description": "View events", "resource": "events", "action": "read"},
            {"name": "events:create", "description": "Create events", "resource": "events", "action": "create"},
            {"name": "events:write", "description": "Update events", "resource": "events", "action": "write"},
            {"name": "events:delete", "description": "Delete events", "resource": "events", "action": "delete"},
            {"name": "admin:all", "description": "Full admin access", "resource": "admin", "action": "all"},
        ]
        
        created = []
        for perm_data in default_permissions:
            existing = await PermissionCRUD.get_by_name(db, perm_data["name"])
            if not existing:
                permission = await PermissionCRUD.create(db, perm_data)
                created.append(permission)
        
        return created


# =============================================================================
# Role CRUD
# =============================================================================

class RoleCRUD(CRUDBase):
    """CRUD operations for roles."""
    
    @staticmethod
    async def get_by_name(db: AsyncSession, name: str) -> Optional[Role]:
        """Get role by name."""
        result = await db.execute(
            select(Role)
            .where(Role.name == name)
            .options(selectinload(Role.permissions))
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_with_permissions(db: AsyncSession, role_id: UUID) -> Optional[Role]:
        """Get role with all permissions."""
        result = await db.execute(
            select(Role)
            .where(Role.id == role_id)
            .options(selectinload(Role.permissions))
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(db: AsyncSession, role_data: RoleCreate) -> Role:
        """Create a new role with permissions."""
        role = Role(
            name=role_data.name,
            description=role_data.description,
        )
        db.add(role)
        
        # Add permissions if provided
        if role_data.permission_ids:
            permissions = await db.execute(
                select(Permission).where(Permission.id.in_(role_data.permission_ids))
            )
            role.permissions = list(permissions.scalars().all())
        
        await db.commit()
        await db.refresh(role)
        return role
    
    @staticmethod
    async def update(db: AsyncSession, role_id: UUID, role_data: RoleUpdate) -> Optional[Role]:
        """Update a role."""
        role = await RoleCRUD.get_by_id(db, Role, role_id)
        if not role:
            return None
        
        update_data = role_data.model_dump(exclude_unset=True)
        
        # Handle permissions update
        if "permission_ids" in update_data:
            permission_ids = update_data.pop("permission_ids")
            permissions = await db.execute(
                select(Permission).where(Permission.id.in_(permission_ids))
            )
            role.permissions = list(permissions.scalars().all())
        
        for field, value in update_data.items():
            setattr(role, field, value)
        
        await db.commit()
        await db.refresh(role)
        return role
    
    @staticmethod
    async def get_default_roles(db: AsyncSession) -> Tuple[Optional[Role], Optional[Role], Optional[Role]]:
        """Get or create default admin and member roles."""
        admin_role = await RoleCRUD.get_by_name(db, "admin")
        member_role = await RoleCRUD.get_by_name(db, "member")
        volunteer_role = await RoleCRUD.get_by_name(db, "volunteer")
        
        if not admin_role:
            admin_role = Role(
                name="admin",
                description="Administrator with full access",
                priority=100,
                is_system=True,
            )
            db.add(admin_role)
        
        if not member_role:
            member_role = Role(
                name="member",
                description="Regular member",
                priority=10,
                is_system=True,
            )
            db.add(member_role)
        
        if not volunteer_role:
            volunteer_role = Role(
                name="volunteer",
                description="Volunteer with limited access",
                priority=20,
                is_system=True,
            )
            db.add(volunteer_role)
        
        await db.commit()
        
        # Refresh to get IDs
        if admin_role.id is None:
            await db.refresh(admin_role)
        if member_role.id is None:
            await db.refresh(member_role)
        if volunteer_role.id is None:
            await db.refresh(volunteer_role)
        
        return admin_role, member_role, volunteer_role


# =============================================================================
# User CRUD
# =============================================================================

class UserCRUD(CRUDBase):
    """CRUD operations for users."""
    
    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email."""
        result = await db.execute(
            select(User)
            .where(User.email == email)
            .options(selectinload(User.roles))
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_phone(db: AsyncSession, phone: str) -> Optional[User]:
        """Get user by phone number."""
        result = await db.execute(
            select(User)
            .where(User.phone == phone)
            .options(selectinload(User.roles))
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_phone_or_email(db: AsyncSession, identifier: str) -> Optional[User]:
        """Get user by phone or email."""
        result = await db.execute(
            select(User)
            .where((User.phone == identifier) | (User.email == identifier))
            .options(selectinload(User.roles))
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(db: AsyncSession, user_data: UserCreate) -> User:
        """Create a new user."""
        # Check for existing user
        existing = await UserCRUD.get_by_phone_or_email(db, user_data.phone)
        if existing:
            raise AlreadyExistsError(resource="User", field="phone", value=user_data.phone)
        
        if user_data.email:
            existing_email = await UserCRUD.get_by_email(db, user_data.email)
            if existing_email:
                raise AlreadyExistsError(resource="User", field="email", value=user_data.email)
        
        user = User(
            email=user_data.email,
            phone=user_data.phone,
            password_hash=hash_password(user_data.password),
            is_active=user_data.is_active,
            status="active",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def update(db: AsyncSession, user_id: UUID, user_data: UserUpdate) -> Optional[User]:
        """Update a user."""
        user = await UserCRUD.get_by_id(db, User, user_id)
        if not user:
            return None
        
        update_data = user_data.model_dump(exclude_unset=True)
        
        # Check for uniqueness conflicts
        if "email" in update_data and update_data["email"]:
            existing = await UserCRUD.get_by_email(db, update_data["email"])
            if existing and existing.id != user_id:
                raise AlreadyExistsError(resource="User", field="email", value=update_data["email"])
        
        if "phone" in update_data and update_data["phone"]:
            existing = await UserCRUD.get_by_phone(db, update_data["phone"])
            if existing and existing.id != user_id:
                raise AlreadyExistsError(resource="User", field="phone", value=update_data["phone"])
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def authenticate(
        db: AsyncSession,
        email: str,
        password: str,
        ip_address: str = None,
        user_agent: str = None,
        device_info: dict = None
    ) -> User:
        """Authenticate a user with email and password."""
        user = await UserCRUD.get_by_email(db, email)
        
        if not user:
            raise InvalidCredentialsError("Invalid email or password")
        
        if not user.is_active:
            raise AuthenticationError("Account is disabled")
        
        if user.is_locked():
            raise AuthenticationError("Account is temporarily locked")
        
        if user.password_hash and verify_password(password, user.password_hash):
            # Update login stats
            user.login_attempts = 0
            user.last_login_at = datetime.now(timezone.utc)
            user.last_login_ip = ip_address
            
            # Create refresh token
            await TokenCRUD.create_refresh_token(
                db,
                user.id,
                ip_address,
                user_agent,
                device_info
            )
            
            await db.commit()
            return user
        
        # Increment failed login attempts
        user.login_attempts += 1
        
        # Lock account after 5 failed attempts
        if user.login_attempts >= 5:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
        
        await db.commit()
        raise InvalidCredentialsError("Invalid email or password")
    
    @staticmethod
    async def update_password(db: AsyncSession, user_id: UUID, new_password: str) -> User:
        """Update user password."""
        user = await UserCRUD.get_by_id(db, User, user_id)
        if not user:
            raise NotFoundError(resource="User", resource_id=str(user_id))
        
        user.password_hash = hash_password(new_password)
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def assign_roles(db: AsyncSession, user_id: UUID, role_ids: List[UUID]) -> User:
        """Assign roles to a user."""
        user = await UserCRUD.get_by_id(db, User, user_id)
        if not user:
            raise NotFoundError(resource="User", resource_id=str(user_id))
        
        roles = await db.execute(
            select(Role).where(Role.id.in_(role_ids))
        )
        user.roles = list(roles.scalars().all())
        
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def remove_roles(db: AsyncSession, user_id: UUID, role_ids: List[UUID]) -> User:
        """Remove roles from a user."""
        user = await UserCRUD.get_by_id(db, User, user_id)
        if not user:
            raise NotFoundError(resource="User", resource_id=str(user_id))
        
        user.roles = [r for r in user.roles if r.id not in role_ids]
        
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def get_users_paginated(
        db: AsyncSession,
        page: int = 1,
        limit: int = 20,
        search: str = None,
        role: str = None,
        status: str = None
    ) -> Tuple[List[User], int]:
        """Get users with pagination and filters."""
        query = select(User).options(selectinload(User.roles))
        
        # Apply filters
        if search:
            query = query.where(
                (User.email.ilike(f"%{search}%")) |
                (User.phone.ilike(f"%{search}%"))
            )
        
        if status:
            query = query.where(User.status == status)
        
        if role:
            query = query.where(User.roles.any(Role.name == role))
        
        # Get total count
        count_query = select(func.count(User.id)).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
        
        result = await db.execute(query)
        users = list(result.scalars().all())
        
        return users, total


# =============================================================================
# Token CRUD
# =============================================================================

class TokenCRUD(CRUDBase):
    """CRUD operations for refresh tokens."""
    
    @staticmethod
    async def create_refresh_token(
        db: AsyncSession,
        user_id: UUID,
        ip_address: str = None,
        user_agent: str = None,
        device_info: dict = None
    ) -> str:
        """Create a new refresh token for a user."""
        user = await UserCRUD.get_by_id(db, User, user_id)
        if not user:
            raise NotFoundError(resource="User", resource_id=str(user_id))
        
        # Generate token
        token_data = {"sub": str(user_id), "type": "refresh"}
        token = create_refresh_token(token_data)
        
        # Get JTI from token (we need to decode it)
        from jose import jwt
        payload = jwt.decode(
            token,
            "your-secret-key-change-in-production",  # This should match the actual secret
            algorithms=["HS256"]
        )
        token_jti = payload.get("jti")
        
        # Calculate expiry
        from datetime import timedelta
        from src.core.config import settings
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        
        # Store in Redis for quick revocation
        await redis.store_refresh_token(
            str(user_id),
            token_jti,
            device_info,
            settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )
        
        # Create database record
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=hash_password(token),  # Store hash for verification
            token_jti=token_jti,
            device_info=json.dumps(device_info) if device_info else None,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
        )
        db.add(refresh_token)
        await db.commit()
        
        return token
    
    @staticmethod
    async def verify_refresh_token(db: AsyncSession, token: str) -> Optional[User]:
        """Verify a refresh token and return the user."""
        from jose import jwt, JWTError
        from src.core.config import settings
        
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
        except JWTError:
            return None
        
        if payload.get("type") != "refresh":
            return None
        
        token_jti = payload.get("jti")
        user_id = payload.get("sub")
        
        if not token_jti or not user_id:
            return None
        
        # Check if token is revoked in Redis
        is_active = await redis.verify_refresh_token_active(token_jti)
        if not is_active:
            return None
        
        # Get user
        user = await UserCRUD.get_by_id(db, User, UUID(user_id))
        if not user or not user.is_active:
            return None
        
        return user
    
    @staticmethod
    async def revoke_refresh_token(db: AsyncSession, token: str) -> bool:
        """Revoke a refresh token."""
        from jose import jwt, JWTError
        from src.core.config import settings
        
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
        except JWTError:
            return False
        
        token_jti = payload.get("jti")
        if not token_jti:
            return False
        
        # Revoke in Redis
        await redis.revoke_refresh_token(token_jti)
        
        # Revoke in database
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token_jti == token_jti)
        )
        rt = result.scalar_one_or_none()
        if rt:
            rt.revoke()
            await db.commit()
        
        return True
    
    @staticmethod
    async def revoke_all_user_tokens(db: AsyncSession, user_id: UUID) -> int:
        """Revoke all refresh tokens for a user."""
        # Revoke in Redis
        count = await redis.revoke_all_user_tokens(str(user_id))
        
        # Revoke in database
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await db.commit()
        
        return count
    
    @staticmethod
    async def refresh_access_token(
        db: AsyncSession,
        refresh_token: str,
        ip_address: str = None,
        user_agent: str = None,
        device_info: dict = None
    ) -> Tuple[str, str, User]:
        """Refresh access token using refresh token."""
        user = await TokenCRUD.verify_refresh_token(db, refresh_token)
        
        if not user:
            raise AuthenticationError("Invalid or expired refresh token")
        
        # Create new tokens
        from src.core.config import settings
        access_token = create_access_token(
            {"sub": str(user.id), "email": user.email, "phone": user.phone}
        )
        
        # Create new refresh token (rotate token)
        new_refresh_token = await TokenCRUD.create_refresh_token(
            db,
            user.id,
            ip_address,
            user_agent,
            device_info
        )
        
        # Revoke old refresh token
        await TokenCRUD.revoke_refresh_token(db, refresh_token)
        
        return access_token, new_refresh_token, user


# Import timedelta for password update
from datetime import timedelta
