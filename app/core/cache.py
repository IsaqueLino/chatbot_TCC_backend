"""
Cache manager (Singleton Pattern).

This module provides caching functionality with support for in-memory and Redis.
Follows Singleton pattern to ensure single cache instance.

Architecture:
- Part of Infrastructure Layer
- Provides caching abstraction
- Used by Application Layer for caching
"""

import json
import time
from functools import lru_cache
from typing import Any

from app.core.config import get_settings


# Logger will be initialized after config
def _get_logger():
    from app.core.logger import get_logger

    return get_logger(__name__)


try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class CacheManager:
    """Cache manager (Singleton).

    Manages caching with support for:
    - In-memory cache (default)
    - Redis cache (if configured)

    Follows Singleton pattern to ensure single cache instance.
    """

    def __init__(self) -> None:
        """Initialize cache manager."""
        logger = _get_logger()
        settings = get_settings()
        self.enabled = settings.CACHE_ENABLED
        self.default_ttl = settings.CACHE_TTL_SECONDS

        # In-memory cache (fallback)
        self._memory_cache: dict[str, tuple[Any, float]] = {}

        # Redis client (if configured)
        self._redis_client: redis.Redis[str] | None = None

        if settings.REDIS_URL and REDIS_AVAILABLE:
            try:
                self._redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                )
                # Test connection
                self._redis_client.ping()
                logger.info("Redis cache initialized", extra={"redis_url": settings.REDIS_URL})
            except Exception as e:
                logger.warning("Failed to connect to Redis, using in-memory cache", extra={"error": str(e)})
                self._redis_client = None
        else:
            if not REDIS_AVAILABLE:
                logger.warning("Redis package not installed, using in-memory cache only")
            else:
                logger.info("Using in-memory cache (Redis not configured)")

    def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self.enabled:
            return None

        logger = _get_logger()

        # Try Redis first
        if self._redis_client:
            try:
                value = self._redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.warning("Redis get failed, falling back to memory", extra={"error": str(e)})

        # Fallback to memory cache
        if key in self._memory_cache:
            value, expiry = self._memory_cache[key]
            if time.time() < expiry:
                return value
            else:
                del self._memory_cache[key]

        return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        logger = _get_logger()
        ttl = ttl or self.default_ttl

        # Try Redis first
        if self._redis_client:
            try:
                self._redis_client.setex(
                    key,
                    ttl,
                    json.dumps(value, default=str),
                )
                return True
            except Exception as e:
                logger.warning("Redis set failed, falling back to memory", extra={"error": str(e)})

        # Fallback to memory cache
        expiry = time.time() + ttl
        self._memory_cache[key] = (value, expiry)

        # Clean expired entries (simple cleanup)
        if len(self._memory_cache) > 1000:
            current_time = time.time()
            self._memory_cache = {
                k: v for k, v in self._memory_cache.items() if v[1] > current_time
            }

        return True

    def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        logger = _get_logger()

        # Try Redis first
        if self._redis_client:
            try:
                self._redis_client.delete(key)
                return True
            except Exception as e:
                logger.warning("Redis delete failed", extra={"error": str(e)})

        # Fallback to memory cache
        self._memory_cache.pop(key, None)
        return True

    def clear(self) -> bool:
        """Clear all cache.

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        logger = _get_logger()

        # Clear Redis
        if self._redis_client:
            try:
                self._redis_client.flushdb()
                return True
            except Exception as e:
                logger.warning("Redis clear failed", extra={"error": str(e)})

        # Clear memory cache
        self._memory_cache.clear()
        return True

    def close(self) -> None:
        """Close cache connections."""
        if self._redis_client:
            try:
                self._redis_client.close()
                logger = _get_logger()
                logger.info("Redis cache connection closed")
            except Exception:
                pass


@lru_cache
def get_cache_manager() -> CacheManager:
    """Get cache manager instance (Singleton).

    Uses @lru_cache to ensure single instance of CacheManager.
    This follows Singleton pattern for caching.

    Returns:
        CacheManager instance (singleton)
    """
    return CacheManager()


# Export singleton instance and convenience functions
cache_manager = get_cache_manager()


def get_cache() -> CacheManager:
    """Get cache manager (convenience function).

    Returns:
        CacheManager instance
    """
    return cache_manager
