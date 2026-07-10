"""Performance and profiling tests for Flight Scan."""

import pytest
import time
import cProfile
import pstats
from io import StringIO
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amadeus_client import AmadeusClient, AuthenticationError
from database import Database


class TestAmadeusClientPerformance:
    """Performance tests for AmadeusClient."""

    @patch('amadeus_client.requests.post')
    def test_authentication_performance(self, mock_post, amadeus_credentials):
        """Measure authentication speed."""
        mock_post.return_value.json.return_value = {
            'access_token': 'test_token',
            'expires_in': 1800
        }

        start = time.time()
        client = AmadeusClient(**amadeus_credentials)
        auth_time = time.time() - start

        assert auth_time < 1.0, f"Auth took {auth_time:.3f}s, target: <1.0s"

    @patch('amadeus_client.requests.post')
    @patch('amadeus_client.requests.get')
    def test_search_performance(self, mock_get, mock_post, amadeus_credentials):
        """Measure search flight speed."""
        mock_post.return_value.json.return_value = {
            'access_token': 'test_token',
            'expires_in': 1800
        }

        # Mock 50 flight offers
        mock_offers = [
            {
                'id': f'FLIGHT_{i}',
                'price': {'total': str(400 + i), 'currency': 'USD'},
                'itineraries': [{
                    'duration': 'PT10H30M',
                    'segments': [{
                        'carrierCode': 'AA',
                        'departure': {'at': '2026-08-01T10:00:00'},
                        'arrival': {'at': '2026-08-01T20:30:00'},
                    }]
                }]
            }
            for i in range(50)
        ]

        mock_get.return_value.json.return_value = {'data': mock_offers}

        client = AmadeusClient(**amadeus_credentials)

        start = time.time()
        offers = client.search_flights('EZE', 'MIA', '2026-08-01', adults=2)
        search_time = time.time() - start

        assert len(offers) == 50
        assert search_time < 2.0, f"Search took {search_time:.3f}s, target: <2.0s"

    @patch('amadeus_client.requests.post')
    def test_input_validation_performance(self, mock_post, amadeus_credentials):
        """Measure validation speed."""
        mock_post.return_value.json.return_value = {
            'access_token': 'test_token',
            'expires_in': 1800
        }

        client = AmadeusClient(**amadeus_credentials)

        # Validate 100 search parameters
        start = time.time()
        for i in range(100):
            try:
                client._validate_search_params('EZE', 'MIA', '2026-08-01', 2)
            except Exception:
                pass
        validation_time = time.time() - start

        avg_per_validation = validation_time / 100
        assert avg_per_validation < 0.01, f"Avg validation: {avg_per_validation:.6f}s"


class TestDatabasePerformance:
    """Performance tests for Database operations."""

    @patch('database.psycopg2.connect')
    def test_insert_performance(self, mock_connect, db_credentials):
        """Measure insert speed."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)
        mock_connect.return_value = mock_connection

        db = Database(**db_credentials)

        # Insert 100 records
        start = time.time()
        with patch.object(db, '_get_connection', return_value=mock_connection):
            for i in range(100):
                db.insert_flight_offer(
                    origin='EZE',
                    destination='MIA',
                    departure_date='2026-08-01',
                    return_date=None,
                    adults=1,
                    price=450.50 + i,
                    currency='USD',
                    airline='AA',
                    flight_data={'id': f'test_{i}'}
                )
        insert_time = time.time() - start

        avg_per_insert = insert_time / 100
        assert avg_per_insert < 0.01, f"Avg insert: {avg_per_insert:.6f}s"

    @patch('database.psycopg2.connect')
    def test_query_performance(self, mock_connect, db_credentials):
        """Measure query speed."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        # Mock 1000 results
        mock_results = [
            {'id': i, 'price': 450.50, 'origin': 'EZE', 'destination': 'MIA'}
            for i in range(1000)
        ]
        mock_cursor.fetchall.return_value = mock_results
        mock_connect.return_value = mock_connection

        db = Database(**db_credentials)

        start = time.time()
        with patch.object(db, '_get_connection', return_value=mock_connection):
            results = db.get_recent_searches(limit=1000)
        query_time = time.time() - start

        assert len(results) == 1000
        assert query_time < 0.5, f"Query took {query_time:.3f}s, target: <0.5s"

    @patch('database.psycopg2.connect')
    def test_connection_pool_efficiency(self, mock_connect, db_credentials):
        """Test efficiency of connection reuse."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)
        mock_cursor.fetchall.return_value = []
        mock_connect.return_value = mock_connection

        db = Database(**db_credentials)

        # Multiple operations in sequence
        start = time.time()
        with patch.object(db, '_get_connection', return_value=mock_connection):
            for i in range(50):
                db.insert_flight_offer(
                    origin='EZE',
                    destination='MIA',
                    departure_date='2026-08-01',
                    return_date=None,
                    adults=1,
                    price=450.50,
                    currency='USD',
                    airline='AA',
                    flight_data={}
                )
                db.get_recent_searches(limit=10)
        total_time = time.time() - start

        assert total_time < 1.0, f"50 ops took {total_time:.3f}s, target: <1.0s"


class TestMemoryUsage:
    """Memory usage tests."""

    @patch('amadeus_client.requests.post')
    @patch('amadeus_client.requests.get')
    def test_large_response_memory(self, mock_get, mock_post, amadeus_credentials):
        """Test memory usage with large API responses."""
        mock_post.return_value.json.return_value = {
            'access_token': 'test_token',
            'expires_in': 1800
        }

        # Create 1000 flight offers
        large_offers = [
            {
                'id': f'FLIGHT_{i}',
                'price': {'total': str(400 + (i % 200)), 'currency': 'USD'},
                'itineraries': [{
                    'duration': f'PT{10 + (i % 10)}H{30 - (i % 30)}M',
                    'segments': [{
                        'carrierCode': 'AA',
                        'departure': {'at': '2026-08-01T10:00:00'},
                        'arrival': {'at': '2026-08-01T20:30:00'},
                    }]
                }],
                'validatingAirlineCodes': ['AA'],
                'numberOfBookableSeats': 5 + (i % 10)
            }
            for i in range(1000)
        ]

        mock_get.return_value.json.return_value = {'data': large_offers}

        client = AmadeusClient(**amadeus_credentials)
        offers = client.search_flights('EZE', 'MIA', '2026-08-01')

        # Should handle 1000 offers without memory issues
        assert len(offers) == 1000


class TestProfiledOperations:
    """Tests with profiling output."""

    @patch('amadeus_client.requests.post')
    def test_profile_authentication(self, mock_post, amadeus_credentials):
        """Profile authentication operation."""
        mock_post.return_value.json.return_value = {
            'access_token': 'test_token',
            'expires_in': 1800
        }

        profiler = cProfile.Profile()
        profiler.enable()

        # Run multiple authentications
        for _ in range(10):
            client = AmadeusClient(**amadeus_credentials)

        profiler.disable()

        # Generate report
        s = StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(10)

        report = s.getvalue()
        # Verify profiling ran
        assert 'function calls' in report

    @patch('amadeus_client.requests.post')
    @patch('amadeus_client.requests.get')
    def test_profile_search_parsing(self, mock_get, mock_post, amadeus_credentials):
        """Profile search and parsing operations."""
        mock_post.return_value.json.return_value = {
            'access_token': 'test_token',
            'expires_in': 1800
        }

        # Create test offers
        offers_data = [
            {
                'id': f'FLIGHT_{i}',
                'price': {'total': str(400 + i), 'currency': 'USD'},
                'itineraries': [{
                    'duration': 'PT10H30M',
                    'segments': [
                        {
                            'carrierCode': 'AA',
                            'departure': {'at': '2026-08-01T10:00:00'},
                            'arrival': {'at': '2026-08-01T20:30:00'},
                        },
                        {
                            'carrierCode': 'AA',
                            'departure': {'at': '2026-08-02T08:00:00'},
                            'arrival': {'at': '2026-08-02T18:30:00'},
                        }
                    ]
                }]
            }
            for i in range(100)
        ]

        mock_get.return_value.json.return_value = {'data': offers_data}

        client = AmadeusClient(**amadeus_credentials)

        profiler = cProfile.Profile()
        profiler.enable()

        offers = client.search_flights('EZE', 'MIA', '2026-08-01')

        profiler.disable()

        # Generate report
        s = StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(15)

        report = s.getvalue()
        assert len(offers) == 100
        assert 'function calls' in report


class TestConcurrencyPerformance:
    """Test performance under concurrent-like conditions."""

    @patch('database.psycopg2.connect')
    def test_rapid_sequential_inserts(self, mock_connect, db_credentials):
        """Test rapid sequential inserts."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        # Return different IDs
        mock_cursor.fetchone.side_effect = [(i,) for i in range(1, 201)]
        mock_connect.return_value = mock_connection

        db = Database(**db_credentials)

        start = time.time()
        with patch.object(db, '_get_connection', return_value=mock_connection):
            for i in range(200):
                db.insert_flight_offer(
                    origin='EZE',
                    destination='MIA',
                    departure_date='2026-08-01',
                    return_date=None,
                    adults=1,
                    price=450.50,
                    currency='USD',
                    airline='AA',
                    flight_data={'id': f'test_{i}'}
                )
        total_time = time.time() - start

        avg_per_op = total_time / 200
        assert avg_per_op < 0.01, f"Avg per operation: {avg_per_op:.6f}s"

    @patch('database.psycopg2.connect')
    def test_mixed_operations_throughput(self, mock_connect, db_credentials):
        """Test throughput with mixed read/write operations."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        mock_cursor.fetchone.side_effect = [(i,) for i in range(1, 51)]
        mock_cursor.fetchall.return_value = [{'id': 1, 'price': 450.50}]
        mock_connect.return_value = mock_connection

        db = Database(**db_credentials)

        start = time.time()
        with patch.object(db, '_get_connection', return_value=mock_connection):
            for i in range(50):
                # Insert
                db.insert_flight_offer(
                    origin='EZE',
                    destination='MIA',
                    departure_date='2026-08-01',
                    return_date=None,
                    adults=1,
                    price=450.50 + i,
                    currency='USD',
                    airline='AA',
                    flight_data={}
                )
                # Read
                db.get_recent_searches(limit=10)
        total_time = time.time() - start

        assert total_time < 1.0, f"100 ops took {total_time:.3f}s"
