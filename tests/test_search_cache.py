"""Tests for Redis-based search caching (Tier 3)."""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from search_cache import SearchCache, get_search_cache, disable_cache, CACHE_TTL_SECONDS


class TestSearchCacheBasics:
    """Test basic search cache functionality."""

    @patch('search_cache.redis.Redis')
    def test_cache_initialization(self, mock_redis_class):
        """Should initialize search cache with Redis connection."""
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis
        mock_redis.ping.return_value = True

        cache = SearchCache(enabled=True)

        assert cache.enabled is True
        assert cache.redis_client is not None
        mock_redis.ping.assert_called_once()

    def test_cache_disabled(self):
        """Should handle disabled cache gracefully."""
        cache = SearchCache(enabled=False)

        assert cache.enabled is False
        assert cache.redis_client is None

    @patch('search_cache.redis.Redis')
    def test_cache_connection_failure(self, mock_redis_class):
        """Should disable cache on connection failure."""
        import redis
        mock_redis_class.side_effect = redis.ConnectionError("Connection failed")

        cache = SearchCache(enabled=True)

        assert cache.enabled is False
        assert cache.redis_client is None


class TestCacheKeyGeneration:
    """Test cache key generation."""

    def test_cache_key_generation(self):
        """Should generate consistent cache keys."""
        cache = SearchCache(enabled=False)

        key1 = cache._generate_cache_key('EZE', 'MIA', '2026-08-01')
        key2 = cache._generate_cache_key('EZE', 'MIA', '2026-08-01')

        # Same parameters should generate same key
        assert key1 == key2

    def test_cache_key_different_params(self):
        """Should generate different keys for different parameters."""
        cache = SearchCache(enabled=False)

        key1 = cache._generate_cache_key('EZE', 'MIA', '2026-08-01')
        key2 = cache._generate_cache_key('EZE', 'MIA', '2026-08-02')  # Different date

        # Different dates should generate different keys
        assert key1 != key2

    def test_cache_key_with_return_date(self):
        """Should include return date in cache key."""
        cache = SearchCache(enabled=False)

        key1 = cache._generate_cache_key('EZE', 'MIA', '2026-08-01', '2026-08-08')
        key2 = cache._generate_cache_key('EZE', 'MIA', '2026-08-01', '2026-08-09')

        # Different return dates should generate different keys
        assert key1 != key2


class TestCacheGetSet:
    """Test cache get/set operations."""

    @patch('search_cache.redis.Redis')
    def test_cache_set_and_get(self, mock_redis_class):
        """Should set and retrieve cached results."""
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis
        mock_redis.ping.return_value = True

        cache = SearchCache(enabled=True)

        # Mock set operation
        mock_redis.setex.return_value = True

        # Mock get operation
        test_results = [{'id': 'flight_1', 'price': 450.50}]
        mock_redis.get.return_value = json.dumps(test_results)

        # Set cache
        cache.set('EZE', 'MIA', '2026-08-01', test_results)

        # Get from cache
        results = cache.get('EZE', 'MIA', '2026-08-01')

        assert results == test_results
        assert cache.stats['sets'] == 1
        assert cache.stats['hits'] == 1

    @patch('search_cache.redis.Redis')
    def test_cache_miss(self, mock_redis_class):
        """Should return None on cache miss."""
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = None

        cache = SearchCache(enabled=True)

        result = cache.get('EZE', 'MIA', '2026-08-01')

        assert result is None
        assert cache.stats['misses'] == 1

    @patch('search_cache.redis.Redis')
    def test_cache_ttl_setting(self, mock_redis_class):
        """Should set cache TTL correctly."""
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis
        mock_redis.ping.return_value = True
        mock_redis.setex.return_value = True

        cache = SearchCache(enabled=True)

        test_results = [{'id': 'flight_1', 'price': 450.50}]
        cache.set('EZE', 'MIA', '2026-08-01', test_results)

        # Verify setex was called with correct TTL
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == CACHE_TTL_SECONDS  # TTL in seconds


class TestCacheDelete:
    """Test cache deletion."""

    @patch('search_cache.redis.Redis')
    def test_cache_delete(self, mock_redis_class):
        """Should delete cached results."""
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis
        mock_redis.ping.return_value = True
        mock_redis.delete.return_value = 1

        cache = SearchCache(enabled=True)

        result = cache.delete('EZE', 'MIA', '2026-08-01')

        assert result is True
        assert cache.stats['deletes'] == 1
        mock_redis.delete.assert_called_once()

    @patch('search_cache.redis.Redis')
    def test_cache_clear_all(self, mock_redis_class):
        """Should clear all cached entries."""
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis
        mock_redis.ping.return_value = True

        # Mock scan and delete
        mock_redis.scan.side_effect = [
            (0, ['flight_search:key1', 'flight_search:key2']),
        ]
        mock_redis.delete.return_value = 2

        cache = SearchCache(enabled=True)

        result = cache.clear_all()

        assert result is True
        mock_redis.scan.assert_called_once()
        mock_redis.delete.assert_called_once()


class TestCacheStats:
    """Test cache statistics."""

    @patch('search_cache.redis.Redis')
    def test_cache_stats(self, mock_redis_class):
        """Should provide cache statistics."""
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis
        mock_redis.ping.return_value = True
        mock_redis.info.return_value = {
            'used_memory': 1024 * 1024,  # 1MB
        }
        mock_redis.dbsize.return_value = 42  # 42 keys

        cache = SearchCache(enabled=True)

        # Simulate some cache activity
        cache.stats['hits'] = 80
        cache.stats['misses'] = 20
        cache.stats['sets'] = 50

        stats = cache.get_stats()

        assert stats['hits'] == 80
        assert stats['misses'] == 20
        assert stats['hit_rate_percent'] == 80  # 80/(80+20) = 80%
        assert stats['keys_count'] == 42

    def test_cache_stats_disabled(self):
        """Should return disabled status if cache disabled."""
        cache = SearchCache(enabled=False)

        stats = cache.get_stats()

        assert stats['enabled'] is False


class TestCacheHealthCheck:
    """Test cache health check."""

    @patch('search_cache.redis.Redis')
    def test_health_check_ok(self, mock_redis_class):
        """Should return True if Redis is healthy."""
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis
        mock_redis.ping.return_value = True

        cache = SearchCache(enabled=True)

        assert cache.health_check() is True

    @patch('search_cache.redis.Redis')
    def test_health_check_failed(self, mock_redis_class):
        """Should return False if Redis is down."""
        import redis
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis
        mock_redis.ping.return_value = True
        mock_redis.ping.side_effect = redis.ConnectionError("Connection lost")

        cache = SearchCache(enabled=True)

        assert cache.health_check() is False


class TestGlobalCacheInstance:
    """Test global cache instance."""

    def test_singleton_pattern(self):
        """Should return same instance on multiple calls."""
        cache1 = get_search_cache()
        cache2 = get_search_cache()

        assert cache1 is cache2


class TestCacheErrorHandling:
    """Test cache error handling."""

    @patch('search_cache.redis.Redis')
    def test_cache_json_error(self, mock_redis_class):
        """Should handle JSON decode errors gracefully."""
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = "INVALID_JSON"

        cache = SearchCache(enabled=True)

        result = cache.get('EZE', 'MIA', '2026-08-01')

        assert result is None
        assert cache.stats['errors'] == 1

    @patch('search_cache.redis.Redis')
    def test_cache_redis_error_on_set(self, mock_redis_class):
        """Should handle Redis errors on set."""
        import redis
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis
        mock_redis.ping.return_value = True
        mock_redis.setex.side_effect = redis.RedisError("Connection lost")

        cache = SearchCache(enabled=True)

        test_results = [{'id': 'flight_1', 'price': 450.50}]
        result = cache.set('EZE', 'MIA', '2026-08-01', test_results)

        assert result is False
        assert cache.stats['errors'] == 1


class TestCachePerformanceImpact:
    """Test performance benefits of caching."""

    @patch('search_cache.redis.Redis')
    def test_cache_hit_rate_tracking(self, mock_redis_class):
        """Should accurately track hit/miss ratio."""
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis
        mock_redis.ping.return_value = True

        cache = SearchCache(enabled=True)

        # Simulate 100 hits, 20 misses
        cache.stats['hits'] = 100
        cache.stats['misses'] = 20

        stats = cache.get_stats()

        assert stats['hit_rate_percent'] == 83  # 100/(100+20) = 83.33% → 83%

    @patch('search_cache.redis.Redis')
    def test_cache_memory_tracking(self, mock_redis_class):
        """Should report memory usage."""
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis
        mock_redis.ping.return_value = True
        mock_redis.info.return_value = {
            'used_memory': 10 * 1024 * 1024,  # 10MB
        }
        mock_redis.dbsize.return_value = 1000

        cache = SearchCache(enabled=True)

        stats = cache.get_stats()

        assert stats['used_memory_mb'] == 10.0
        assert stats['keys_count'] == 1000
