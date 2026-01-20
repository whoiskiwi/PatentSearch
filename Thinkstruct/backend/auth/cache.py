"""Redis cache layer for sessions and hot data."""

import json
import logging
from typing import Optional, Any

from .config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache for sessions and frequently accessed data."""

    def __init__(self):
        self.client = None
        self.enabled = settings.redis_enabled

    async def connect(self) -> None:
        """Connect to Redis."""
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
            # Test connection
            await self.client.ping()
            logger.info("Redis cache connected")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Running without cache.")
            self.client = None
            self.enabled = False

    async def close(self) -> None:
        """Close Redis connection."""
        if self.client:
            await self.client.close()

    # ==================== Session Cache ====================

    async def cache_session(self, session_id: str, user_data: dict, ttl: int = 3600) -> bool:
        """Cache session data. TTL in seconds (default 1 hour)."""
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
        """Get cached session data."""
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
        """Remove session from cache."""
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
        """Remove all sessions for a user from cache."""
        if not self.client:
            return 0
        try:
            pattern = f"session:*"
            count = 0
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
        """Cache user data. TTL in seconds (default 30 minutes)."""
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
        """Get cached user data."""
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
        """Remove user from cache."""
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
        """Cache user's history list. TTL in seconds (default 5 minutes)."""
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
        """Get cached history list."""
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
        """Remove history list from cache."""
        if not self.client:
            return False
        try:
            key = f"history_list:{user_id}"
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate history list: {e}")
            return False

    # ==================== Generic Cache ====================

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.client:
            return None
        try:
            data = await self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL."""
        if not self.client:
            return False
        try:
            await self.client.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self.client:
            return False
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False


# Global cache instance
cache = RedisCache()
