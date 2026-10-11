import json
import logging
from typing import Optional, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisCacheService:
    def __init__(self):
        self._client = None
        self._available = False
        if settings.REDIS_ENABLED and settings.REDIS_URL:
            try:
                import redis
                self._client = redis.Redis.from_url(
                    settings.REDIS_URL, 
                    decode_responses=True,
                    socket_connect_timeout=2
                )
                # Quick test ping
                self._client.ping()
                self._available = True
                logger.info("Connected to Redis server successfully.")
            except Exception as e:
                logger.warning(f"Redis is unavailable, falling back to in-memory pass-through: {e}")
                self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    def get(self, key: str) -> Optional[Any]:
        if not self._available or not self._client:
            return None
        try:
            val = self._client.get(key)
            if val:
                return json.loads(val)
        except Exception as e:
            logger.warning(f"Error reading from Redis key {key}: {e}")
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        if not self._available or not self._client:
            return False
        try:
            ttl = ttl or settings.CACHE_DEFAULT_TTL
            serialized = json.dumps(value)
            self._client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.warning(f"Error setting Redis key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        if not self._available or not self._client:
            return False
        try:
            self._client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Error deleting Redis key {key}: {e}")
            return False

    def invalidate_prefix(self, prefix: str) -> int:
        """Invalidates all cache keys matching a prefix (e.g., when documents change)"""
        if not self._available or not self._client:
            return 0
        try:
            keys = self._client.keys(f"{prefix}*")
            if keys:
                return self._client.delete(*keys)
        except Exception as e:
            logger.warning(f"Error invalidating prefix {prefix}: {e}")
        return 0

cache_service = RedisCacheService()
