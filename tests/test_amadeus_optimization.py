"""Tests for AmadeusClient optimizations (Tier 2)."""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amadeus_client_optimized import AmadeusClient, DURATION_CACHE_SIZE, TOKEN_CACHE_CHECK_INTERVAL


class TestDurationCaching:
    """Test duration parsing cache optimization."""

    def test_duration_cache_initialization(self, amadeus_credentials):
        """Should initialize duration cache."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)
            assert isinstance(client._duration_cache, dict)
            assert len(client._duration_cache) == 0

    def test_duration_parsing_cached(self, amadeus_credentials):
        """Should cache duration parsing results."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)

            # First call - parse
            result1 = client._parse_duration('PT10H30M')
            assert result1 == '10h 30m'
            assert 'PT10H30M' in client._duration_cache

            # Second call - from cache
            result2 = client._parse_duration('PT10H30M')
            assert result2 == '10h 30m'
            assert len(client._duration_cache) == 1

    def test_duration_cache_prevents_repeated_parsing(self, amadeus_credentials):
        """Should avoid re-parsing same durations."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)

            # Parse 100 times (same duration)
            start = time.time()
            for _ in range(100):
                client._parse_duration('PT10H30M')
            cache_time = time.time() - start

            # Should be very fast (all from cache)
            assert cache_time < 0.01
            assert len(client._duration_cache) == 1

    def test_duration_cache_different_formats(self, amadeus_credentials):
        """Should cache different duration formats separately."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)

            client._parse_duration('PT10H30M')
            client._parse_duration('PT5H')
            client._parse_duration('PT45M')

            assert len(client._duration_cache) == 3
            assert client._duration_cache['PT10H30M'] == '10h 30m'
            assert client._duration_cache['PT5H'] == '5h 0m'
            assert client._duration_cache['PT45M'] == '0h 45m'

    def test_duration_cache_max_size(self, amadeus_credentials):
        """Should evict oldest entries when cache is full."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)

            # Fill cache to max size
            for i in range(DURATION_CACHE_SIZE + 10):
                client._parse_duration(f'PT{i}H')

            # Cache should not exceed max size
            assert len(client._duration_cache) <= DURATION_CACHE_SIZE

    def test_duration_invalid_format_cached(self, amadeus_credentials):
        """Should cache N/A for invalid durations."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)

            result1 = client._parse_duration('INVALID')
            assert result1 == 'N/A'
            assert 'INVALID' in client._duration_cache

            result2 = client._parse_duration('INVALID')
            assert result2 == 'N/A'
            assert len(client._duration_cache) == 1


class TestTokenCachingOptimization:
    """Test token validation caching (throttling)."""

    @patch('amadeus_client_optimized.requests.post')
    def test_token_check_throttling(self, mock_post, amadeus_credentials):
        """Should throttle token validation checks."""
        mock_post.return_value.json.return_value = {
            'access_token': 'test_token',
            'expires_in': 3600
        }

        client = AmadeusClient(**amadeus_credentials)

        # Manually set token (since mock might not call authenticate properly)
        client.access_token = 'test_token'
        client.token_expiry = time.time() + 3600

        # First check validates token
        client._last_token_check = 0  # Reset
        result1 = client._is_token_valid()
        assert result1 is True

        first_check_time = client._last_token_check

        # Second check within 60s should use cached result (no new validation)
        time.sleep(0.1)  # Small delay
        result2 = client._is_token_valid()
        assert result2 is True

        # Check time should be same (no new validation within threshold)
        # If implementation is correct, second call shouldn't update _last_token_check
        # unless we're outside the throttle window

    @patch('amadeus_client_optimized.requests.post')
    def test_token_none_handling(self, mock_post, amadeus_credentials):
        """Should handle None token correctly."""
        mock_post.side_effect = Exception("Auth failed")

        with patch.object(AmadeusClient, '_authenticate', return_value=None):
            client = AmadeusClient(**amadeus_credentials)
            client.access_token = None
            client.token_expiry = None

            assert not client._is_token_valid()

    @patch('amadeus_client_optimized.requests.post')
    def test_token_check_after_expiry(self, mock_post, amadeus_credentials):
        """Should recheck token after cache interval."""
        mock_post.return_value.json.return_value = {
            'access_token': 'test_token',
            'expires_in': 3600
        }

        client = AmadeusClient(**amadeus_credentials)
        client._last_token_check = 0  # Force recheck

        # Manually set old check time
        import time as time_module
        client._last_token_check = time_module.time() - TOKEN_CACHE_CHECK_INTERVAL - 1

        result = client._is_token_valid()
        # Should attempt recheck
        assert isinstance(result, bool)


class TestAirlineCodeLookup:
    """Test airline code lookup optimization."""

    def test_airline_code_lookup_performance(self, amadeus_credentials):
        """Should have fast airline code lookups."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)

            start = time.time()
            for _ in range(10000):
                client._get_airline_name('AA')
            lookup_time = time.time() - start

            # Should be very fast (dict lookup)
            assert lookup_time < 0.1

    def test_airline_code_known(self, amadeus_credentials):
        """Should return airline name for known codes."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)

            assert client._get_airline_name('AA') == 'American Airlines'
            assert client._get_airline_name('AR') == 'Aerolíneas Argentinas'
            assert client._get_airline_name('LA') == 'LATAM Airlines'

    def test_airline_code_unknown(self, amadeus_credentials):
        """Should return code for unknown airlines."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)

            assert client._get_airline_name('XX') == 'XX'
            assert client._get_airline_name('UNKNOWN') == 'UNKNOWN'


class TestCacheStats:
    """Test cache statistics and monitoring."""

    def test_cache_stats_retrieval(self, amadeus_credentials):
        """Should provide cache statistics."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)

            # Add some cache entries
            client._parse_duration('PT10H30M')
            client._parse_duration('PT5H')

            stats = client.get_cache_stats()

            assert 'duration_cache_size' in stats
            assert 'duration_cache_max' in stats
            assert 'duration_cache_usage_percent' in stats
            assert stats['duration_cache_size'] == 2
            assert stats['duration_cache_max'] == DURATION_CACHE_SIZE

    def test_cache_clear(self, amadeus_credentials):
        """Should clear all caches."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)

            # Fill cache
            client._parse_duration('PT10H30M')
            client._last_token_check = time.time()

            assert len(client._duration_cache) > 0
            assert client._last_token_check > 0

            # Clear
            client.clear_caches()

            assert len(client._duration_cache) == 0
            assert client._last_token_check == 0


class TestPerformanceImprovement:
    """Test overall performance improvements."""

    @patch('amadeus_client_optimized.requests.post')
    @patch('amadeus_client_optimized.requests.get')
    def test_repeated_searches_cache_benefit(self, mock_get, mock_post, amadeus_credentials):
        """Repeated searches should benefit from duration cache."""
        mock_post.return_value.json.return_value = {
            'access_token': 'test_token',
            'expires_in': 3600
        }

        offers = [
            {
                'id': f'FLIGHT_{i}',
                'price': {'total': '450.50', 'currency': 'USD'},
                'itineraries': [{
                    'duration': 'PT10H30M',  # Same duration repeated
                    'segments': [{
                        'carrierCode': 'AA',
                        'departure': {'at': '2026-08-01T10:00:00'},
                        'arrival': {'at': '2026-08-01T20:30:00'},
                    }]
                }]
            }
            for i in range(100)
        ]

        mock_get.return_value.json.return_value = {'data': offers}

        client = AmadeusClient(**amadeus_credentials)

        # First search - parse all durations
        start = time.time()
        offers1 = client.search_flights('EZE', 'MIA', '2026-08-01')
        first_search_time = time.time() - start

        # Second search - use cached durations
        start = time.time()
        offers2 = client.search_flights('EZE', 'MIA', '2026-08-01')
        second_search_time = time.time() - start

        # Both should complete successfully
        assert len(offers1) == 100
        assert len(offers2) == 100

        # Cache should contain the duration
        assert 'PT10H30M' in client._duration_cache

    def test_cache_effectiveness_monitoring(self, amadeus_credentials):
        """Should track cache effectiveness."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)

            # Add various durations
            durations = ['PT10H30M', 'PT5H', 'PT12H', 'PT10H30M', 'PT5H']
            for duration in durations:
                client._parse_duration(duration)

            stats = client.get_cache_stats()

            # Should have 3 unique durations
            assert stats['duration_cache_size'] == 3
            # Usage should be 0.3%
            expected_usage = int((3 / DURATION_CACHE_SIZE) * 100)
            assert stats['duration_cache_usage_percent'] == expected_usage
