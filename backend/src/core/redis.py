"""
Redis Connection and Utilities
Manages Redis connection for caching, sessions, and rate limiting.
"""

from typing import Any, Optional
import json

import redis.asyncio as redis

from src.core.config import settings


class RedisClient:
    """Redis client manager."""

    _client: redis.Redis = None

    @classmethod
    async def connect(cls):
        """Initialize Redis connection."""
        cls._client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        # Test connection
        await cls._client.ping()
        print("Connected to Redis")

    @classmethod
    async def disconnect(cls):
        """Close Redis connection."""
        if cls._client:
            await cls._client.close()
            print("Disconnected from Redis")

    @classmethod
    def get_client(cls) -> redis.Redis:
        """Get Redis client instance."""
        if cls._client is None:
            raise RuntimeError("Redis not connected. Call RedisClient.connect() first.")
        return cls._client


# =============================================================================
# Caching Utilities
# =============================================================================

async def cache_get(key: str) -> Optional[Any]:
    """Get a value from cache."""
    client = RedisClient.get_client()
    value = await client.get(key)
    if value:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return None


async def cache_set(
    key: str,
    value: Any,
    expire_seconds: int = 3600
) -> bool:
    """Set a value in cache with expiration."""
    client = RedisClient.get_client()
    if not isinstance(value, str):
        value = json.dumps(value)
    return await client.setex(key, expire_seconds, value)


async def cache_delete(key: str) -> bool:
    """Delete a key from cache."""
    client = RedisClient.get_client()
    return await client.delete(key) > 0


async def cache_exists(key: str) -> bool:
    """Check if a key exists in cache."""
    client = RedisClient.get_client()
    return await client.exists(key) > 0


# =============================================================================
# OTP Storage
# =============================================================================

OTP_PREFIX = "otp:"
OTP_ATTEMPTS_PREFIX = "otp_attempts:"
OTP_COOLDOWN_PREFIX = "otp_cooldown:"


async def store_otp(
    phone: str,
    otp_hash: str,
    expire_seconds: int = None
) -> bool:
    """Store OTP hash in Redis."""
    if expire_seconds is None:
        expire_seconds = settings.OTP_EXPIRE_MINUTES * 60

    client = RedisClient.get_client()
    key = f"{OTP_PREFIX}{phone}"
    return await client.setex(key, expire_seconds, otp_hash)


async def get_otp_hash(phone: str) -> Optional[str]:
    """Get stored OTP hash for a phone number."""
    client = RedisClient.get_client()
    key = f"{OTP_PREFIX}{phone}"
    return await client.get(key)


async def delete_otp(phone: str) -> bool:
    """Delete OTP after successful verification."""
    client = RedisClient.get_client()
    key = f"{OTP_PREFIX}{phone}"
    return await client.delete(key) > 0


async def increment_otp_attempts(phone: str) -> int:
    """Increment OTP verification attempts."""
    client = RedisClient.get_client()
    key = f"{OTP_ATTEMPTS_PREFIX}{phone}"
    attempts = await client.incr(key)
    # Set expiry on first attempt
    if attempts == 1:
        await client.expire(key, settings.OTP_EXPIRE_MINUTES * 60)
    return attempts


async def get_otp_attempts(phone: str) -> int:
    """Get current OTP verification attempts."""
    client = RedisClient.get_client()
    key = f"{OTP_ATTEMPTS_PREFIX}{phone}"
    attempts = await client.get(key)
    return int(attempts) if attempts else 0


async def reset_otp_attempts(phone: str) -> bool:
    """Reset OTP attempts after successful verification."""
    client = RedisClient.get_client()
    key = f"{OTP_ATTEMPTS_PREFIX}{phone}"
    return await client.delete(key) > 0


async def set_otp_cooldown(phone: str) -> bool:
    """Set cooldown for OTP resend."""
    client = RedisClient.get_client()
    key = f"{OTP_COOLDOWN_PREFIX}{phone}"
    return await client.setex(key, settings.OTP_RESEND_COOLDOWN_SECONDS, "1")


async def check_otp_cooldown(phone: str) -> int:
    """Check remaining cooldown time for OTP resend. Returns 0 if no cooldown."""
    client = RedisClient.get_client()
    key = f"{OTP_COOLDOWN_PREFIX}{phone}"
    ttl = await client.ttl(key)
    return max(0, ttl)


# =============================================================================
# Session Management
# =============================================================================

SESSION_PREFIX = "session:"
REFRESH_TOKEN_PREFIX = "refresh:"


async def store_refresh_token(
    user_id: str,
    token_jti: str,
    device_info: dict = None,
    expire_days: int = None
) -> bool:
    """Store refresh token info in Redis."""
    if expire_days is None:
        expire_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS

    client = RedisClient.get_client()
    key = f"{REFRESH_TOKEN_PREFIX}{token_jti}"
    data = {
        "user_id": user_id,
        "device_info": device_info or {},
        "created_at": str(datetime.now(timezone.utc).isoformat())
    }
    return await client.setex(key, expire_days * 86400, json.dumps(data))


async def verify_refresh_token_active(token_jti: str) -> bool:
    """Check if a refresh token is still active (not revoked)."""
    client = RedisClient.get_client()
    key = f"{REFRESH_TOKEN_PREFIX}{token_jti}"
    return await client.exists(key) > 0


async def revoke_refresh_token(token_jti: str) -> bool:
    """Revoke a refresh token."""
    client = RedisClient.get_client()
    key = f"{REFRESH_TOKEN_PREFIX}{token_jti}"
    return await client.delete(key) > 0


async def revoke_all_user_tokens(user_id: str) -> int:
    """Revoke all refresh tokens for a user."""
    client = RedisClient.get_client()
    pattern = f"{REFRESH_TOKEN_PREFIX}*"
    count = 0

    async for key in client.scan_iter(match=pattern):
        data = await client.get(key)
        if data:
            try:
                token_data = json.loads(data)
                if token_data.get("user_id") == user_id:
                    await client.delete(key)
                    count += 1
            except json.JSONDecodeError:
                pass

    return count


# =============================================================================
# Rate Limiting
# =============================================================================

RATE_LIMIT_PREFIX = "rate:"


async def check_rate_limit(
    key: str,
    limit: int,
    window_seconds: int = 60
) -> tuple[bool, int]:
    """
    Check rate limit for a key.
    Returns (is_allowed, remaining_requests).
    """
    client = RedisClient.get_client()
    redis_key = f"{RATE_LIMIT_PREFIX}{key}"

    current = await client.get(redis_key)
    if current is None:
        await client.setex(redis_key, window_seconds, 1)
        return True, limit - 1

    current = int(current)
    if current >= limit:
        return False, 0

    await client.incr(redis_key)
    return True, limit - current - 1


# Import datetime for token storage
from datetime import datetime, timezone


# =============================================================================
# Event Caching
# =============================================================================

EVENT_PREFIX = "event:"
EVENT_CACHE_TTL = 3600  # 1 hour


async def cache_event(event_id: str, event_data: Any) -> bool:
    """Cache an event with its data."""
    client = RedisClient.get_client()
    key = f"{EVENT_PREFIX}{event_id}"
    return await cache_set(key, event_data, EVENT_CACHE_TTL)


async def get_event(event_id: str) -> Optional[Any]:
    """Get a cached event by ID."""
    key = f"{EVENT_PREFIX}{event_id}"
    return await cache_get(key)


async def delete_event_cache(event_id: str) -> bool:
    """Delete an event from cache."""
    key = f"{EVENT_PREFIX}{event_id}"
    return await cache_delete(key)


async def cache_member(member_id: str, member_data: Any) -> bool:
    """Cache a member with their data."""
    key = f"member:{member_id}"
    return await cache_set(key, member_data, EVENT_CACHE_TTL)


async def get_member(member_id: str) -> Optional[Any]:
    """Get a cached member by ID."""
    key = f"member:{member_id}"
    return await cache_get(key)


async def delete_member_cache(member_id: str) -> bool:
    """Delete a member from cache."""
    key = f"member:{member_id}"
    return await cache_delete(key)


# =============================================================================
# Grievance Caching
# =============================================================================

GRIEVANCE_PREFIX = "grievance:"
GRIEVANCE_CACHE_TTL = 3600  # 1 hour


async def cache_grievance(grievance_id: str, grievance_data: Any) -> bool:
    """Cache a grievance with its data."""
    key = f"{GRIEVANCE_PREFIX}{grievance_id}"
    return await cache_set(key, grievance_data, GRIEVANCE_CACHE_TTL)


async def get_grievance(grievance_id: str) -> Optional[Any]:
    """Get a cached grievance by ID."""
    key = f"{GRIEVANCE_PREFIX}{grievance_id}"
    return await cache_get(key)


async def delete_grievance_cache(grievance_id: str) -> bool:
    """Delete a grievance from cache."""
    key = f"{GRIEVANCE_PREFIX}{grievance_id}"
    return await cache_delete(key)
