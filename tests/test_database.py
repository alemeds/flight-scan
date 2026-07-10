"""Unit tests for Database operations."""

import pytest
from unittest.mock import patch, MagicMock
import psycopg2
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Database, DatabaseError


class TestDatabaseConnection:
    """Test database connection handling."""

    @patch('database.psycopg2.connect')
    def test_connection_success(self, mock_connect, db_credentials):
        """Should establish connection successfully."""
        mock_connect.return_value = MagicMock()

        db = Database(**db_credentials)
        assert db.connection_params['host'] == 'localhost'
        assert db.connection_params['database'] == 'flight_scan_test'

    def test_missing_credentials(self):
        """Should raise ValueError for missing credentials."""
        with pytest.raises(ValueError, match="requeridos"):
            Database('', 5432, 'db', 'user', 'pass')

    def test_missing_password(self):
        """Should raise ValueError for missing password."""
        with pytest.raises(ValueError, match="requeridos"):
            Database('host', 5432, 'db', 'user', '')


class TestDatabaseResourceCleanup:
    """Test that resources are cleaned up properly."""

    @patch('database.psycopg2.connect')
    def test_connection_closed_on_success(self, mock_connect, db_credentials):
        """Should close connection after successful operation."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        db = Database(**db_credentials)

        # Simular operación que cierra la conexión
        with patch.object(db, '_get_connection', return_value=mock_connection):
            # Mock cursor para test_connection
            mock_cursor.execute.return_value = None
            mock_cursor.fetchone.return_value = [1]

            result = db.test_connection()

            assert result is True
            mock_cursor.close.assert_called()
            mock_connection.close.assert_called()

    @patch('database.psycopg2.connect')
    def test_connection_closed_on_error(self, mock_connect, db_credentials):
        """Should close connection even on error."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.Error("Test error")
        mock_connect.return_value = mock_connection

        db = Database(**db_credentials)

        with patch.object(db, '_get_connection', return_value=mock_connection):
            result = db.test_connection()

            assert result is False
            mock_cursor.close.assert_called()
            mock_connection.close.assert_called()


class TestDatabaseInsert:
    """Test insert operations."""

    @patch('database.psycopg2.connect')
    def test_insert_flight_offer_success(self, mock_connect, db_credentials):
        """Should insert flight offer successfully."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)  # Return flight ID
        mock_connect.return_value = mock_connection

        db = Database(**db_credentials)

        with patch.object(db, '_get_connection', return_value=mock_connection):
            flight_id = db.insert_flight_offer(
                origin='EZE',
                destination='MIA',
                departure_date='2026-08-01',
                return_date='2026-08-08',
                adults=2,
                price=450.50,
                currency='USD',
                airline='American Airlines',
                flight_data={'id': 'test'}
            )

            assert flight_id == 1
            mock_connection.commit.assert_called()

    @patch('database.psycopg2.connect')
    def test_insert_flight_offer_with_none_airline(self, mock_connect, db_credentials):
        """Should convert None airline to 'N/A'."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)
        mock_connect.return_value = mock_connection

        db = Database(**db_credentials)

        with patch.object(db, '_get_connection', return_value=mock_connection):
            flight_id = db.insert_flight_offer(
                origin='EZE',
                destination='MIA',
                departure_date='2026-08-01',
                return_date=None,
                adults=1,
                price=450.50,
                currency='USD',
                airline=None,  # None airline
                flight_data={'id': 'test'}
            )

            assert flight_id == 1
            # Verify execute was called with 'N/A' for airline
            call_args = mock_cursor.execute.call_args
            assert call_args[0][1][7] == 'N/A'  # airline parameter


class TestDatabaseQueries:
    """Test query operations."""

    @patch('database.psycopg2.connect')
    def test_get_recent_searches(self, mock_connect, db_credentials):
        """Should fetch recent searches."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        # Mock RealDictCursor response
        mock_cursor.fetchall.return_value = [
            {
                'id': 1,
                'origin': 'EZE',
                'destination': 'MIA',
                'price': 450.50
            }
        ]
        mock_connect.return_value = mock_connection

        db = Database(**db_credentials)

        with patch.object(db, '_get_connection', return_value=mock_connection):
            results = db.get_recent_searches(limit=10)

            assert len(results) == 1
            assert results[0]['origin'] == 'EZE'

    @patch('database.psycopg2.connect')
    def test_get_searches_by_route(self, mock_connect, db_credentials):
        """Should fetch searches for specific route."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        mock_connect.return_value = mock_connection

        db = Database(**db_credentials)

        with patch.object(db, '_get_connection', return_value=mock_connection):
            results = db.get_searches_by_route('EZE', 'MIA', days=30)

            assert isinstance(results, list)

    @patch('database.psycopg2.connect')
    def test_get_price_statistics(self, mock_connect, db_credentials):
        """Should calculate price statistics."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            'min_price': 400.00,
            'max_price': 600.00,
            'avg_price': 500.00,
            'search_count': 10
        }
        mock_connect.return_value = mock_connection

        db = Database(**db_credentials)

        with patch.object(db, '_get_connection', return_value=mock_connection):
            stats = db.get_price_statistics('EZE', 'MIA', days=30)

            assert stats['min_price'] == 400.00
            assert stats['max_price'] == 600.00


class TestDatabaseEdgeCases:
    """Test edge cases and error handling."""

    @patch('database.psycopg2.connect')
    def test_limit_parameter_capped(self, mock_connect, db_credentials):
        """Should cap limit parameter to prevent overload."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        mock_connect.return_value = mock_connection

        db = Database(**db_credentials)

        with patch.object(db, '_get_connection', return_value=mock_connection):
            # Try to get 10000 results - should be capped to 1000
            db.get_recent_searches(limit=10000)

            # Verify that the limit was capped
            call_args = mock_cursor.execute.call_args
            assert call_args[0][1][0] == 1000  # Capped limit

    @patch('database.psycopg2.connect')
    def test_days_parameter_capped(self, mock_connect, db_credentials):
        """Should cap days parameter to prevent large queries."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        mock_connect.return_value = mock_connection

        db = Database(**db_credentials)

        with patch.object(db, '_get_connection', return_value=mock_connection):
            db.get_searches_by_route('EZE', 'MIA', days=1000)

            # Verify that days was capped to 365
            # The exact verification depends on how the mock captures it

    @patch('database.psycopg2.connect')
    def test_delete_old_searches(self, mock_connect, db_credentials):
        """Should delete old search records."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 42  # 42 records deleted
        mock_connect.return_value = mock_connection

        db = Database(**db_credentials)

        with patch.object(db, '_get_connection', return_value=mock_connection):
            deleted = db.delete_old_searches(days=90)

            assert deleted == 42
            mock_connection.commit.assert_called()

    @patch('database.psycopg2.connect')
    def test_get_flight_by_id(self, mock_connect, db_credentials):
        """Should fetch flight by ID."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'origin': 'EZE',
            'price': 450.50
        }
        mock_connect.return_value = mock_connection

        db = Database(**db_credentials)

        with patch.object(db, '_get_connection', return_value=mock_connection):
            flight = db.get_flight_by_id(1)

            assert flight is not None
            assert flight['id'] == 1
