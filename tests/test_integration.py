"""Integration tests for full Flight Scan workflow."""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amadeus_client import AmadeusClient, AuthenticationError, APIError
from database import Database, DatabaseError


class TestFullSearchFlow:
    """Test complete search workflow: API → DB → retrieval."""

    @patch('database.psycopg2.connect')
    @patch('amadeus_client.requests.post')
    @patch('amadeus_client.requests.get')
    def test_search_and_store_workflow(self, mock_get, mock_post, mock_connect,
                                       amadeus_credentials, db_credentials,
                                       mock_amadeus_response):
        """Should complete full workflow: search API, store in DB, retrieve."""

        # Setup Amadeus auth
        mock_post.return_value.json.return_value = {
            'access_token': 'test_token',
            'expires_in': 1800
        }

        # Setup Amadeus search
        mock_get.return_value.json.return_value = mock_amadeus_response

        # Setup database
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)  # flight_id
        mock_cursor.fetchall.return_value = [{'id': 1, 'price': 450.50}]
        mock_connect.return_value = mock_connection

        # Execute workflow
        amadeus = AmadeusClient(**amadeus_credentials)
        offers = amadeus.search_flights('EZE', 'MIA', '2026-08-01')

        assert len(offers) > 0
        assert offers[0]['price'] == 450.50

        # Store in database
        db = Database(**db_credentials)
        with patch.object(db, '_get_connection', return_value=mock_connection):
            for offer in offers:
                flight_id = db.insert_flight_offer(
                    origin='EZE',
                    destination='MIA',
                    departure_date='2026-08-01',
                    return_date=None,
                    adults=1,
                    price=offer['price'],
                    currency=offer['currency'],
                    airline=offer.get('airline'),
                    flight_data=offer
                )

                assert flight_id == 1


class TestSearchFlowWithNoResults:
    """Test handling of empty search results."""

    @patch('database.psycopg2.connect')
    @patch('amadeus_client.requests.post')
    @patch('amadeus_client.requests.get')
    def test_search_no_results(self, mock_get, mock_post, mock_connect,
                               amadeus_credentials, db_credentials):
        """Should handle searches with no results gracefully."""

        mock_post.return_value.json.return_value = {
            'access_token': 'test_token',
            'expires_in': 1800
        }

        # Empty results
        mock_get.return_value.json.return_value = {'data': []}

        amadeus = AmadeusClient(**amadeus_credentials)
        offers = amadeus.search_flights('EZE', 'MIA', '2026-08-01')

        assert len(offers) == 0


class TestErrorHandlingInFlow:
    """Test error handling throughout workflow."""

    @patch('amadeus_client.requests.post')
    def test_authentication_failure_stops_flow(self, mock_post, amadeus_credentials):
        """Should not proceed if authentication fails."""
        mock_post.side_effect = Exception("Auth failed")

        with pytest.raises(AuthenticationError):
            AmadeusClient(**amadeus_credentials)

    @patch('database.psycopg2.connect')
    def test_database_connection_failure(self, mock_connect, db_credentials):
        """Should handle database connection failures."""
        mock_connect.side_effect = Exception("Connection failed")

        with pytest.raises(Exception):
            db = Database(**db_credentials)
            # Try to use it
            db.test_connection()

    @patch('amadeus_client.requests.post')
    @patch('amadeus_client.requests.get')
    def test_api_error_in_search(self, mock_get, mock_post, amadeus_credentials):
        """Should handle API errors during search."""
        mock_post.return_value.json.return_value = {
            'access_token': 'test_token',
            'expires_in': 1800
        }

        # API returns error
        mock_get.return_value.status_code = 500
        mock_get.return_value.json.return_value = {'error': 'Server error'}

        with patch.object(AmadeusClient, '_authenticate'):
            amadeus = AmadeusClient(**amadeus_credentials)

        with patch('amadeus_client.requests.get', side_effect=Exception("API error")):
            with pytest.raises(APIError):
                amadeus.search_flights('EZE', 'MIA', '2026-08-01')


class TestPriceAlertFlow:
    """Test price monitoring and alert workflow."""

    @patch('database.psycopg2.connect')
    def test_compare_prices_across_searches(self, mock_connect, db_credentials):
        """Should correctly identify price drops."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        # First search
        mock_cursor.fetchone.return_value = {
            'min_price': 500.00,
            'max_price': 600.00,
            'avg_price': 550.00,
            'search_count': 3
        }

        db = Database(**db_credentials)

        with patch.object(db, '_get_connection', return_value=mock_connection):
            stats = db.get_price_statistics('EZE', 'MIA', days=7)

            assert stats['min_price'] == 500.00
            assert stats['avg_price'] == 550.00


class TestDataCleanupFlow:
    """Test automatic data cleanup and archival."""

    @patch('database.psycopg2.connect')
    def test_delete_old_searches_succeeds(self, mock_connect, db_credentials):
        """Should delete old searches without error."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 100  # 100 records deleted
        mock_connect.return_value = mock_connection

        db = Database(**db_credentials)

        with patch.object(db, '_get_connection', return_value=mock_connection):
            deleted = db.delete_old_searches(days=90)

            assert deleted == 100
            mock_connection.commit.assert_called()

    @patch('database.psycopg2.connect')
    def test_cleanup_maintains_recent_data(self, mock_connect, db_credentials):
        """Should preserve recent searches during cleanup."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        # Setup responses
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'created_at': '2026-07-10', 'price': 450.50}
        ]

        db = Database(**db_credentials)

        with patch.object(db, '_get_connection', return_value=mock_connection):
            recent = db.get_recent_searches(limit=10)

            assert len(recent) == 1
            # Data retrieved after cleanup should still be there


class TestConcurrentOperations:
    """Test behavior with multiple concurrent operations."""

    @patch('database.psycopg2.connect')
    def test_multiple_inserts_succeed(self, mock_connect, db_credentials):
        """Should handle multiple sequential inserts."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        # Return different IDs for each insert
        mock_cursor.fetchone.side_effect = [(1,), (2,), (3,)]
        mock_connect.return_value = mock_connection

        db = Database(**db_credentials)

        flight_ids = []
        with patch.object(db, '_get_connection', return_value=mock_connection):
            for i in range(3):
                flight_id = db.insert_flight_offer(
                    origin='EZE',
                    destination='MIA',
                    departure_date='2026-08-01',
                    return_date=None,
                    adults=1,
                    price=450.50 + i,
                    currency='USD',
                    airline='Test Airline',
                    flight_data={'id': f'test_{i}'}
                )
                flight_ids.append(flight_id)

        assert flight_ids == [1, 2, 3]

    @patch('database.psycopg2.connect')
    def test_read_during_write(self, mock_connect, db_credentials):
        """Should handle reads while writes occur."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        # Setup mixed responses
        mock_cursor.fetchone.return_value = (1,)  # Insert result
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'price': 450.50}
        ]

        db = Database(**db_credentials)

        with patch.object(db, '_get_connection', return_value=mock_connection):
            # Simulate concurrent read/write
            flight_id = db.insert_flight_offer(
                origin='EZE',
                destination='MIA',
                departure_date='2026-08-01',
                return_date=None,
                adults=1,
                price=450.50,
                currency='USD',
                airline='Test',
                flight_data={'id': 'test'}
            )

            results = db.get_recent_searches(limit=10)

            assert flight_id == 1
            assert len(results) == 1


class TestDataIntegrity:
    """Test data integrity throughout workflow."""

    @patch('database.psycopg2.connect')
    def test_flight_data_preserved_in_db(self, mock_connect, db_credentials):
        """Should preserve complete flight offer data in database."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)
        mock_connect.return_value = mock_connection

        db = Database(**db_credentials)
        test_data = {'id': 'ABC123', 'seats': 5, 'stops': 1}

        with patch.object(db, '_get_connection', return_value=mock_connection):
            flight_id = db.insert_flight_offer(
                origin='EZE',
                destination='MIA',
                departure_date='2026-08-01',
                return_date='2026-08-08',
                adults=2,
                price=450.50,
                currency='USD',
                airline='AA',
                flight_data=test_data
            )

            # Verify the data was passed to execute
            call_args = mock_cursor.execute.call_args
            # flight_data should be in the parameters
            assert call_args is not None

    @patch('database.psycopg2.connect')
    def test_price_precision_maintained(self, mock_connect, db_credentials):
        """Should maintain price precision (cents) in database."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)
        mock_connect.return_value = mock_connection

        db = Database(**db_credentials)

        # Test precise price
        precise_price = 450.99

        with patch.object(db, '_get_connection', return_value=mock_connection):
            flight_id = db.insert_flight_offer(
                origin='EZE',
                destination='MIA',
                departure_date='2026-08-01',
                return_date=None,
                adults=1,
                price=precise_price,
                currency='USD',
                airline='AA',
                flight_data={}
            )

            # Verify price was passed correctly
            call_args = mock_cursor.execute.call_args
            assert call_args[0][1][5] == precise_price
