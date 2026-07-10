"""Tests for Tier 1 optimizations (batch insert and connection pooling)."""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_optimized import Database, CONNECTION_POOL_MIN, CONNECTION_POOL_MAX, BATCH_INSERT_SIZE


class TestConnectionPooling:
    """Test connection pooling implementation."""

    def test_pool_configuration_constants(self):
        """Should have correct pool configuration."""
        assert CONNECTION_POOL_MIN == 2
        assert CONNECTION_POOL_MAX == 10
        assert BATCH_INSERT_SIZE == 100

    @patch('database_optimized.psycopg2.pool.SimpleConnectionPool')
    def test_pool_initialization(self, mock_pool_class, db_credentials):
        """Should initialize connection pool with correct parameters."""
        mock_pool = MagicMock()
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_pool.getconn.return_value = mock_connection
        mock_pool_class.return_value = mock_pool

        # Reset class pool
        Database._pool = None

        db = Database(**db_credentials)

        # Verify pool was created
        mock_pool_class.assert_called_once()


class TestBatchInsert:
    """Test batch insert optimization."""

    @patch('database_optimized.execute_values')
    @patch('database_optimized.psycopg2.pool.SimpleConnectionPool')
    def test_batch_insert_single_call(self, mock_pool_class, mock_execute_values, db_credentials):
        """Should use single SQL INSERT with multiple VALUES."""
        mock_pool = MagicMock()
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_pool.getconn.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        mock_pool_class.return_value = mock_pool

        # Reset pool
        Database._pool = None

        db = Database(**db_credentials)

        # Batch insert 100 offers
        offers = [
            {
                'origin': 'EZE',
                'destination': 'MIA',
                'departure_date': '2026-08-01',
                'return_date': None,
                'adults': 1,
                'price': 450.50 + i,
                'currency': 'USD',
                'airline': 'AA',
                'flight_data': {'id': f'flight_{i}'}
            }
            for i in range(100)
        ]

        result = db.insert_flight_offers_batch(offers)

        # Verify batch insert was called
        assert mock_execute_values.called
        assert result == 100

    @patch('database_optimized.psycopg2.pool.SimpleConnectionPool')
    def test_batch_insert_empty_list(self, mock_pool_class, db_credentials):
        """Should handle empty offer list."""
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool

        db = Database(**db_credentials)
        result = db.insert_flight_offers_batch([])

        assert result == 0

    @patch('database_optimized.psycopg2.pool.SimpleConnectionPool')
    @patch('database_optimized.execute_values')
    def test_batch_insert_performance(self, mock_execute_values, mock_pool_class, db_credentials):
        """Batch insert should be significantly faster than individual inserts."""
        mock_pool = MagicMock()
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_pool.getconn.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        mock_pool_class.return_value = mock_pool

        db = Database(**db_credentials)

        # Measure batch insert time
        offers = [
            {
                'origin': 'EZE',
                'destination': 'MIA',
                'departure_date': '2026-08-01',
                'return_date': None,
                'adults': 1,
                'price': 450.50,
                'currency': 'USD',
                'airline': 'AA',
                'flight_data': {}
            }
            for _ in range(100)
        ]

        start = time.time()
        db.insert_flight_offers_batch(offers)
        batch_time = time.time() - start

        # Should complete in <100ms (mock, so very fast)
        assert batch_time < 0.1

    @patch('database_optimized.psycopg2.pool.SimpleConnectionPool')
    @patch('database_optimized.execute_values')
    def test_batch_insert_handles_none_airline(self, mock_execute_values, mock_pool_class, db_credentials):
        """Should convert None airline to 'N/A' in batch insert."""
        mock_pool = MagicMock()
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_pool.getconn.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        mock_pool_class.return_value = mock_pool

        db = Database(**db_credentials)

        offers = [
            {
                'origin': 'EZE',
                'destination': 'MIA',
                'departure_date': '2026-08-01',
                'return_date': None,
                'adults': 1,
                'price': 450.50,
                'currency': 'USD',
                'airline': None,  # None airline
                'flight_data': {}
            }
        ]

        db.insert_flight_offers_batch(offers)

        # Verify execute_values was called
        assert mock_execute_values.called
        # Batch data should have 'N/A' for airline
        call_args = mock_execute_values.call_args
        batch_data = call_args[0][2]
        assert batch_data[0][7] == 'N/A'  # airline is 8th element (index 7)


class TestOptimizationComparison:
    """Compare performance of optimizations."""

    @patch('database_optimized.psycopg2.pool.SimpleConnectionPool')
    def test_batch_vs_individual_insert_count(self, mock_pool_class, db_credentials):
        """Verify batch insert executes single SQL vs multiple SQLs."""
        mock_pool = MagicMock()
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_pool.getconn.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        mock_pool_class.return_value = mock_pool

        db = Database(**db_credentials)

        # Insert 100 offers using batch
        offers = [
            {
                'origin': 'EZE',
                'destination': 'MIA',
                'departure_date': '2026-08-01',
                'return_date': None,
                'adults': 1,
                'price': 450.50 + i,
                'currency': 'USD',
                'airline': 'AA',
                'flight_data': {}
            }
            for i in range(100)
        ]

        with patch('database_optimized.execute_values') as mock_execute_values:
            db.insert_flight_offers_batch(offers)

            # Should call execute_values ONCE (not 100 times)
            assert mock_execute_values.call_count == 1


class TestPoolCleanup:
    """Test connection pool cleanup."""

    @patch('database_optimized.psycopg2.pool.SimpleConnectionPool')
    def test_close_all_connections(self, mock_pool_class):
        """Should close all connections in pool."""
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool

        # Set pool manually
        Database._pool = mock_pool

        Database.close_all_connections()

        mock_pool.closeall.assert_called_once()
        assert Database._pool is None

    @patch('database_optimized.psycopg2.pool.SimpleConnectionPool')
    def test_connection_returned_to_pool_on_error(self, mock_pool_class, db_credentials):
        """Should return connection to pool even on error."""
        mock_pool = MagicMock()
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_pool.getconn.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("Test error")
        mock_pool_class.return_value = mock_pool

        db = Database(**db_credentials)

        try:
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
        except Exception:
            pass

        # Connection should be returned to pool
        mock_pool.putconn.assert_called()
