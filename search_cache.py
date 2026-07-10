"""Redis-based search caching for Flight Scan."""

import redis
import json
import logging
import hashlib
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

# Cache configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

# Cache TTL (Time To Live)
CACHE_TTL_MINUTES = int(os.getenv('CACHE_TTL_MINUTES', 360))  # 6 hours default
CACHE_TTL_SECONDS = CACHE_TTL_MINUTES * 60

# Cache key prefix
CACHE_PREFIX = 'flight_search:'


class SearchCache:
    """Redis-based cache for flight search results."""

    def __init__(self, enabled: bool = True):
        """
        Initialize search cache.

        Args:
            enabled: Whether to use caching (default: True)
        """
        self.enabled = enabled
        self.redis_client = None
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0
        }

        if self.enabled:
            try:
                self.redis_client = redis.Redis(
                    host=REDIS_HOST,
                    port=REDIS_PORT,
                    db=REDIS_DB,
                    password=REDIS_PASSWORD,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_keepalive=True
                )
                # Test connection
                self.redis_client.ping()
                logger.info(f"Redis connected: {REDIS_HOST}:{REDIS_PORT}")
            except (redis.ConnectionError, redis.TimeoutError) as e:
                logger.warning(f"Redis connection failed: {type(e).__name__}. Cache disabled.")
                self.enabled = False
                self.redis_client = None

    def _generate_cache_key(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1
    ) -> str:
        """
        Generate cache key from search parameters.

        Uses hash to keep key short and consistent.
        """
        # Create canonical key string
        key_string = f"{origin}|{destination}|{departure_date}|{return_date}|{adults}"

        # Hash for consistency
        key_hash = hashlib.md5(key_string.encode()).hexdigest()

        return f"{CACHE_PREFIX}{key_hash}"

    def get(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1
    ) -> Optional[List[Dict]]:
        """
        Get cached search results.

        Args:
            origin: Origin IATA code
            destination: Destination IATA code
            departure_date: Departure date (YYYY-MM-DD)
            return_date: Return date (optional)
            adults: Number of adults

        Returns:
            List of flight offers if cached, None otherwise
        """
        if not self.enabled or not self.redis_client:
            return None

        try:
            cache_key = self._generate_cache_key(
                origin, destination, departure_date, return_date, adults
            )

            # Try to get from cache
            cached_data = self.redis_client.get(cache_key)

            if cached_data:
                # Deserialize and return
                results = json.loads(cached_data)
                self.stats['hits'] += 1
                logger.info(f"Cache HIT: {origin}-{destination}")
                return results
            else:
                self.stats['misses'] += 1
                logger.debug(f"Cache MISS: {origin}-{destination}")
                return None

        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.error(f"Cache get error: {type(e).__name__}")
            self.stats['errors'] += 1
            return None

    def set(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        results: List[Dict],
        return_date: Optional[str] = None,
        adults: int = 1
    ) -> bool:
        """
        Cache search results.

        Args:
            origin: Origin IATA code
            destination: Destination IATA code
            departure_date: Departure date
            results: Flight offers to cache
            return_date: Return date (optional)
            adults: Number of adults

        Returns:
            True if cached successfully, False otherwise
        """
        if not self.enabled or not self.redis_client or not results:
            return False

        try:
            cache_key = self._generate_cache_key(
                origin, destination, departure_date, return_date, adults
            )

            # Serialize results
            cached_data = json.dumps(results)

            # Set with TTL
            self.redis_client.setex(
                cache_key,
                CACHE_TTL_SECONDS,
                cached_data
            )

            self.stats['sets'] += 1
            logger.info(f"Cache SET: {origin}-{destination} (TTL: {CACHE_TTL_MINUTES}m)")
            return True

        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.error(f"Cache set error: {type(e).__name__}")
            self.stats['errors'] += 1
            return False

    def delete(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1
    ) -> bool:
        """
        Delete cached search results.

        Useful when results need to be refreshed.
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            cache_key = self._generate_cache_key(
                origin, destination, departure_date, return_date, adults
            )

            deleted = self.redis_client.delete(cache_key)
            self.stats['deletes'] += 1

            if deleted:
                logger.info(f"Cache DELETE: {origin}-{destination}")
            return bool(deleted)

        except redis.RedisError as e:
            logger.error(f"Cache delete error: {type(e).__name__}")
            self.stats['errors'] += 1
            return False

    def clear_all(self) -> bool:
        """Clear all flight search cache."""
        if not self.enabled or not self.redis_client:
            return False

        try:
            # Delete all keys with our prefix
            pattern = f"{CACHE_PREFIX}*"
            cursor = 0
            deleted_count = 0

            while True:
                cursor, keys = self.redis_client.scan(cursor, match=pattern, count=100)
                if keys:
                    deleted_count += self.redis_client.delete(*keys)
                if cursor == 0:
                    break

            logger.info(f"Cache CLEAR_ALL: deleted {deleted_count} entries")
            return True

        except redis.RedisError as e:
            logger.error(f"Cache clear error: {type(e).__name__}")
            self.stats['errors'] += 1
            return False

    def get_stats(self) -> Dict[str, any]:
        """Get cache statistics."""
        if not self.enabled or not self.redis_client:
            return {'enabled': False}

        try:
            info = self.redis_client.info()
            hit_rate = 0
            total = self.stats['hits'] + self.stats['misses']
            if total > 0:
                hit_rate = int((self.stats['hits'] / total) * 100)

            return {
                'enabled': True,
                'connected': True,
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'sets': self.stats['sets'],
                'deletes': self.stats['deletes'],
                'errors': self.stats['errors'],
                'hit_rate_percent': hit_rate,
                'used_memory_mb': info.get('used_memory', 0) / (1024 * 1024),
                'keys_count': self.redis_client.dbsize()
            }

        except redis.RedisError as e:
            logger.error(f"Cache stats error: {type(e).__name__}")
            return {
                'enabled': True,
                'connected': False,
                'error': str(e)
            }

    def health_check(self) -> bool:
        """Check if Redis is available."""
        if not self.enabled:
            return False

        try:
            return self.redis_client.ping()
        except (redis.ConnectionError, redis.TimeoutError):
            return False

    def close(self):
        """Close Redis connection."""
        if self.redis_client:
            try:
                self.redis_client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis: {type(e).__name__}")


# Global cache instance
_cache_instance: Optional[SearchCache] = None


def get_search_cache() -> SearchCache:
    """Get or create global search cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SearchCache()
    return _cache_instance


def disable_cache():
    """Disable caching (for testing or maintenance)."""
    global _cache_instance
    if _cache_instance:
        _cache_instance.enabled = False
