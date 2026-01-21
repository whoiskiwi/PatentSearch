"""
Redis Cache Layer

This module provides optional Redis caching for sessions and user data.
Caching improves performance by reducing database queries.

Cache types:
- Session cache: User authentication data (TTL: 1 hour)
- User cache: User profile data (TTL: 30 minutes)
- History cache: Search history list (TTL: 5 minutes)

The cache is optional - if Redis is not available or disabled,
all methods gracefully return without errors.

Usage:
    from .cache import cache

    # Cache session after login
    await cache.cache_session(session_id, user_data)

    # Get cached session (returns None if not cached)
    user_data = await cache.get_cached_session(session_id)

    # Invalidate on logout
    await cache.invalidate_session(session_id)
"""

import json
import logging
from typing import Optional, Any

from .config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Redis cache for sessions and frequently accessed data.

    This class wraps Redis operations with error handling.
    All methods return gracefully if Redis is unavailable.

    Attributes:
        client: Redis async client instance
        enabled: Whether caching is enabled and connected
    """

    def __init__(self):
        """Initialize cache with disabled state until connect() is called."""
        self.client = None
        self.enabled = settings.redis_enabled

    async def connect(self) -> None:
        """
        Connect to Redis server.

        Attempts to establish connection to Redis. If connection fails,
        caching is disabled but the application continues to work.
        """
        if not self.enabled:
            logger.info("Redis cache is disabled")
            return

        try:
            import redis.asyncio as redis
            self.client = redis.from_url(
                settings.get_redis_url(),
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection with ping
            await self.client.ping()
            logger.info("Redis cache connected")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Running without cache.")
            self.client = None
            self.enabled = False

    async def close(self) -> None:
        """Close Redis connection gracefully."""
        if self.client:
            await self.client.close()

    # ==================== Session Cache ====================

    async def cache_session(self, session_id: str, user_data: dict, ttl: int = 3600) -> bool:
        """
        Cache session data.

        Stores user data associated with a session for fast lookup.

        Args:
            session_id: Unique session identifier
            user_data: User information to cache
            ttl: Time-to-live in seconds (default: 1 hour)

        Returns:
            bool: True if cached successfully, False otherwise
        """
        if not self.client:
            return False
        try:
            key = f"session:{session_id}"
            await self.client.setex(key, ttl, json.dumps(user_data))
            return True
        except Exception as e:
            logger.error(f"Failed to cache session: {e}")
            return False

    async def get_cached_session(self, session_id: str) -> Optional[dict]:
        """
        Get cached session data.

        Args:
            session_id: Unique session identifier

        Returns:
            dict: Cached user data if found
            None: If not cached or error
        """
        if not self.client:
            return None
        try:
            key = f"session:{session_id}"
            data = await self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get cached session: {e}")
            return None

    async def invalidate_session(self, session_id: str) -> bool:
        """
        Remove session from cache (on logout).

        Args:
            session_id: Session to invalidate

        Returns:
            bool: True if removed, False otherwise
        """
        if not self.client:
            return False
        try:
            key = f"session:{session_id}"
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate session: {e}")
            return False

    async def invalidate_user_sessions(self, user_id: int) -> int:
        """
        Remove all sessions for a user from cache.

        Used when user logs out from all devices.

        Args:
            user_id: User whose sessions to invalidate

        Returns:
            int: Number of sessions invalidated
        """
        if not self.client:
            return 0
        try:
            pattern = f"session:*"
            count = 0
            # Scan all session keys and check user_id
            async for key in self.client.scan_iter(pattern):
                data = await self.client.get(key)
                if data:
                    session_data = json.loads(data)
                    if session_data.get("user_id") == user_id:
                        await self.client.delete(key)
                        count += 1
            return count
        except Exception as e:
            logger.error(f"Failed to invalidate user sessions: {e}")
            return 0

    # ==================== User Cache ====================

    async def cache_user(self, user_id: int, user_data: dict, ttl: int = 1800) -> bool:
        """
        Cache user profile data.

        Args:
            user_id: User's database ID
            user_data: User profile to cache
            ttl: Time-to-live in seconds (default: 30 minutes)

        Returns:
            bool: True if cached successfully
        """
        if not self.client:
            return False
        try:
            key = f"user:{user_id}"
            await self.client.setex(key, ttl, json.dumps(user_data))
            return True
        except Exception as e:
            logger.error(f"Failed to cache user: {e}")
            return False

    async def get_cached_user(self, user_id: int) -> Optional[dict]:
        """
        Get cached user profile.

        Args:
            user_id: User's database ID

        Returns:
            dict: Cached user data if found
            None: If not cached
        """
        if not self.client:
            return None
        try:
            key = f"user:{user_id}"
            data = await self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get cached user: {e}")
            return None

    async def invalidate_user(self, user_id: int) -> bool:
        """
        Remove user from cache.

        Called when user data changes.

        Args:
            user_id: User to invalidate

        Returns:
            bool: True if removed
        """
        if not self.client:
            return False
        try:
            key = f"user:{user_id}"
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate user: {e}")
            return False

    # ==================== Search History Cache ====================

    async def cache_history_list(self, user_id: int, history: list, ttl: int = 300) -> bool:
        """
        Cache user's search history list.

        Args:
            user_id: User's database ID
            history: List of search history entries
            ttl: Time-to-live in seconds (default: 5 minutes)

        Returns:
            bool: True if cached successfully
        """
        if not self.client:
            return False
        try:
            key = f"history_list:{user_id}"
            await self.client.setex(key, ttl, json.dumps(history))
            return True
        except Exception as e:
            logger.error(f"Failed to cache history list: {e}")
            return False

    async def get_cached_history_list(self, user_id: int) -> Optional[list]:
        """
        Get cached search history list.

        Args:
            user_id: User's database ID

        Returns:
            list: Cached history if found
            None: If not cached
        """
        if not self.client:
            return None
        try:
            key = f"history_list:{user_id}"
            data = await self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get cached history list: {e}")
            return None

    async def invalidate_history_list(self, user_id: int) -> bool:
        """
        Remove history list from cache.

        Called when user adds/deletes search history.

        Args:
            user_id: User whose history cache to invalidate

        Returns:
            bool: True if removed
        """
        if not self.client:
            return False
        try:
            key = f"history_list:{user_id}"
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate history list: {e}")
            return False

    # ==================== Generic Cache Operations ====================

    async def get(self, key: str) -> Optional[Any]:
        """
        Get any value from cache by key.

        Args:
            key: Cache key

        Returns:
            Any: Cached value (JSON decoded)
            None: If not found
        """
        if not self.client:
            return None
        try:
            data = await self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Set any value in cache.

        Args:
            key: Cache key
            value: Value to cache (will be JSON encoded)
            ttl: Time-to-live in seconds

        Returns:
            bool: True if set successfully
        """
        if not self.client:
            return False
        try:
            await self.client.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key to delete

        Returns:
            bool: True if deleted
        """
        if not self.client:
            return False
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False


# Global cache instance - connect() called during app startup
cache = RedisCache()
