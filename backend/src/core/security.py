"""
Security Utilities
JWT token handling, password hashing, and security helpers.
"""

import secrets
import re
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# =============================================================================
# Password Hashing
# =============================================================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


# =============================================================================
# JWT Token Management
# =============================================================================

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def create_refresh_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
        "jti": secrets.token_urlsafe(32)  # Unique token ID for revocation
    })

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def verify_access_token(token: str) -> Optional[dict]:
    """Verify an access token and return its payload."""
    payload = decode_token(token)
    if payload and payload.get("type") == "access":
        return payload
    return None


def verify_refresh_token(token: str) -> Optional[dict]:
    """Verify a refresh token and return its payload."""
    payload = decode_token(token)
    if payload and payload.get("type") == "refresh":
        return payload
    return None


# =============================================================================
# OTP Generation
# =============================================================================

def generate_otp(length: int = None) -> str:
    """Generate a numeric OTP of specified length."""
    if length is None:
        length = settings.OTP_LENGTH

    # Generate a secure random number
    otp = ""
    for _ in range(length):
        otp += str(secrets.randbelow(10))

    return otp


def hash_otp(otp: str) -> str:
    """Hash an OTP for storage."""
    return pwd_context.hash(otp)


def verify_otp(plain_otp: str, hashed_otp: str) -> bool:
    """Verify an OTP against its hash."""
    return pwd_context.verify(plain_otp, hashed_otp)


# =============================================================================
# Token Utilities
# =============================================================================

def generate_token(length: int = 32) -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(length)


def generate_vote_hash(election_id: str, voter_id: str, candidate_id: str) -> str:
    """Generate a hash for anonymous vote verification."""
    data = f"{election_id}:{voter_id}:{candidate_id}:{secrets.token_urlsafe(16)}"
    return hashlib.sha256(data.encode()).hexdigest()


# =============================================================================
# Data Masking
# =============================================================================

def mask_phone(phone: str) -> str:
    """Mask a phone number for display (e.g., +91****3210)."""
    if not phone or len(phone) < 4:
        return "****"
    return phone[:3] + "*" * (len(phone) - 7) + phone[-4:]


def mask_email(email: str) -> str:
    """Mask an email for display (e.g., k***@example.com)."""
    if not email or "@" not in email:
        return "****"
    local, domain = email.split("@")
    if len(local) <= 2:
        masked_local = local[0] + "***"
    else:
        masked_local = local[0] + "***" + local[-1]
    return f"{masked_local}@{domain}"


def mask_aadhar(aadhar: str) -> str:
    """Mask Aadhar number for display (e.g., XXXX XXXX 1234)."""
    if not aadhar or len(aadhar) < 4:
        return "XXXX XXXX XXXX"
    clean = aadhar.replace(" ", "")
    return f"XXXX XXXX {clean[-4:]}"


# =============================================================================
# Input Sanitization
# =============================================================================

def sanitize_phone(phone: str) -> str:
    """Sanitize and normalize phone number."""
    # Remove all non-digit characters except +
    cleaned = re.sub(r"[^\d+]", "", phone)

    # Add country code if missing
    if cleaned.startswith("0"):
        cleaned = "+91" + cleaned[1:]
    elif not cleaned.startswith("+"):
        cleaned = "+91" + cleaned

    return cleaned


def sanitize_string(text: str) -> str:
    """Sanitize a string by removing potentially harmful characters."""
    if not text:
        return ""
    # Remove null bytes and control characters
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text.strip())


# =============================================================================
# Auth Dependencies (for backwards compatibility)
# =============================================================================

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Dependency to get current user from JWT token.
    
    Note: This is a placeholder. The actual implementation is in src.auth.deps.
    For full authentication, use get_current_user from src.auth.deps
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    return {"id": user_id, "token": token}


async def get_optional_user(token: str = Depends(oauth2_scheme)):
    """Dependency to optionally get current user (returns None if not authenticated)."""
    try:
        return await get_current_user(token)
    except HTTPException:
        return None
