"""
Auth Models
SQLAlchemy models for authentication and authorization.
"""

from datetime import datetime, timezone
from typing import List, TYPE_CHECKING
import uuid

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Table, Integer, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.core.database import Base
import enum


# =============================================================================
# Enums
# =============================================================================

class UserStatus(str, enum.Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


# =============================================================================
# Association Tables (Many-to-Many)
# =============================================================================

# User-Role association table
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("assigned_at", DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
    Column("assigned_by", ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
)

# Role-Permission association table
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


# =============================================================================
# Permission Model
# =============================================================================

class Permission(Base):
    """
    Permission model for resource-based access control.
    
    Permissions define specific actions that can be performed on resources.
    Examples: 'users:read', 'users:write', 'members:delete', 'events:create'
    """
    __tablename__ = "permissions"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    resource: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., 'users', 'members', 'events'
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., 'create', 'read', 'update', 'delete'
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions"
    )
    
    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, name={self.name})>"


# =============================================================================
# Role Model
# =============================================================================

class Role(Base):
    """
    Role model for role-based access control (RBAC).
    
    Roles group permissions that can be assigned to users.
    Examples: 'admin', 'member', 'volunteer', 'booth_agent'
    """
    __tablename__ = "roles"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )  # System roles cannot be deleted
    priority: Mapped[int] = mapped_column(Integer, default=0)  # Higher priority roles take precedence
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles"
    )
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles"
    )
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if role has a specific permission."""
        return any(p.name == permission_name for p in self.permissions)
    
    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name={self.name})>"


# =============================================================================
# User Model
# =============================================================================

class User(Base):
    """
    User model for authentication.
    
    This is the base user model for authentication purposes.
    Additional profile information is stored in the members table.
    """
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    phone: Mapped[str] = mapped_column(String(15), unique=True, index=True, nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=True)  # Nullable for social login users
    status: Mapped[str] = mapped_column(
        String(20),
        default=UserStatus.ACTIVE.value,
        nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_ip: Mapped[str] = mapped_column(String(45), nullable=True)  # IPv6 compatible
    login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        lazy="selectin"
    )
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # Additional profile relationship (optional)
    member_profile = relationship("Member", back_populates="user", uselist=False)
    
    def get_all_permissions(self) -> set:
        """Get all permissions from all user roles."""
        permissions = set()
        for role in self.roles:
            if role.is_active:
                for perm in role.permissions:
                    permissions.add(perm.name)
        return permissions
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if user has a specific permission through any of their roles."""
        return permission_name in self.get_all_permissions()
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return any(r.name == role_name for r in self.roles)
    
    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.has_role("admin")
    
    def is_locked(self) -> bool:
        """Check if user account is locked."""
        if self.locked_until:
            return self.locked_until > datetime.now(timezone.utc)
        return False
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, phone={self.phone})>"


# =============================================================================
# RefreshToken Model
# =============================================================================

class RefreshToken(Base):
    """
    Refresh token model for JWT token refresh.
    
    Stores refresh tokens with device information for tracking and revocation.
    """
    __tablename__ = "refresh_tokens"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    token_jti: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)  # JWT ID for revocation
    device_info: Mapped[str] = mapped_column(Text, nullable=True)  # JSON stored as text
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str] = mapped_column(String(500), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")
    
    def is_active(self) -> bool:
        """Check if refresh token is still active."""
        if self.revoked_at:
            return False
        if self.expires_at < datetime.now(timezone.utc):
            return False
        return True
    
    def revoke(self) -> None:
        """Revoke the refresh token."""
        self.revoked_at = datetime.now(timezone.utc)
    
    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, jti={self.token_jti})>"


# =============================================================================
# Import for relationships (avoid circular imports)
# =============================================================================

if TYPE_CHECKING:
    from src.members.models import Member
