"""Unit tests for AmadeusClient."""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amadeus_client import AmadeusClient, AuthenticationError, APIError, TimeoutError


class TestAmadeusClientValidation:
    """Test input validation."""

    def test_validate_search_params_valid_iata(self, amadeus_credentials):
        """Should accept valid IATA codes."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)
            # Should not raise exception
            client._validate_search_params('EZE', 'MIA', '2026-08-01', 2)

    def test_validate_search_params_invalid_origin_iata(self, amadeus_credentials):
        """Should reject invalid origin IATA code."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)
            with pytest.raises(ValueError, match="Código IATA de origen inválido"):
                client._validate_search_params('INVALID', 'MIA', '2026-08-01', 2)

    def test_validate_search_params_invalid_destination_iata(self, amadeus_credentials):
        """Should reject invalid destination IATA code."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)
            with pytest.raises(ValueError, match="Código IATA de destino inválido"):
                client._validate_search_params('EZE', 'invalid', '2026-08-01', 2)

    def test_validate_search_params_same_origin_destination(self, amadeus_credentials):
        """Should reject when origin equals destination."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)
            with pytest.raises(ValueError, match="no pueden ser iguales"):
                client._validate_search_params('EZE', 'EZE', '2026-08-01', 2)

    def test_validate_search_params_past_date(self, amadeus_credentials):
        """Should reject dates in the past."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)
            with pytest.raises(ValueError, match="debe ser futura"):
                client._validate_search_params('EZE', 'MIA', '2020-01-01', 2)

    def test_validate_search_params_invalid_date_format(self, amadeus_credentials):
        """Should reject invalid date format."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)
            with pytest.raises(ValueError, match="Formato de fecha inválido"):
                client._validate_search_params('EZE', 'MIA', '01-01-2026', 2)

    def test_validate_search_params_invalid_adults(self, amadeus_credentials):
        """Should reject invalid number of adults."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)
            with pytest.raises(ValueError, match="entre 1 y 9"):
                client._validate_search_params('EZE', 'MIA', '2026-08-01', 10)

    def test_validate_search_params_zero_adults(self, amadeus_credentials):
        """Should reject zero adults."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)
            with pytest.raises(ValueError, match="entre 1 y 9"):
                client._validate_search_params('EZE', 'MIA', '2026-08-01', 0)


class TestAmadeusClientParsing:
    """Test parsing of API responses."""

    def test_parse_duration_valid(self, amadeus_credentials):
        """Should parse ISO 8601 duration correctly."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)
            assert client._parse_duration('PT10H30M') == '10h 30m'
            assert client._parse_duration('PT5M') == '0h 5m'
            assert client._parse_duration('PT2H') == '2h 0m'

    def test_parse_duration_invalid(self, amadeus_credentials):
        """Should handle invalid duration format."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)
            assert client._parse_duration('INVALID') == 'N/A'
            assert client._parse_duration('') == 'N/A'

    def test_get_airline_name_valid(self, amadeus_credentials):
        """Should convert airline code to name."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)
            assert client._get_airline_name('AA') == 'American Airlines'
            assert client._get_airline_name('AR') == 'Aerolíneas Argentinas'
            assert client._get_airline_name('LA') == 'LATAM Airlines'

    def test_get_airline_name_unknown(self, amadeus_credentials):
        """Should return code if airline not found."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)
            assert client._get_airline_name('XX') == 'XX'
            assert client._get_airline_name('UNKNOWN') == 'UNKNOWN'

    def test_process_flight_offer_valid(self, amadeus_credentials, sample_flight_offer):
        """Should process valid flight offer."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)
            result = client._process_flight_offer(sample_flight_offer)

            assert result is not None
            assert result['price'] == 450.50
            assert result['airline'] == 'American Airlines'
            assert result['currency'] == 'USD'

    def test_process_flight_offer_zero_price(self, amadeus_credentials):
        """Should reject offer with zero price."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)
            offer = {
                'price': {'total': '0', 'currency': 'USD'},
                'itineraries': [{'segments': []}]
            }
            result = client._process_flight_offer(offer)
            assert result is None

    def test_process_flight_offer_none_price(self, amadeus_credentials):
        """Should handle None price gracefully."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)
            offer = {
                'price': None,
                'itineraries': [{'segments': []}]
            }
            result = client._process_flight_offer(offer)
            assert result is None

    def test_process_flight_offer_missing_itineraries(self, amadeus_credentials):
        """Should reject offer without itineraries."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)
            offer = {
                'price': {'total': '450', 'currency': 'USD'},
                'itineraries': []
            }
            result = client._process_flight_offer(offer)
            assert result is None


class TestAmadeusClientAuthentication:
    """Test authentication handling."""

    @patch('amadeus_client.requests.post')
    def test_authenticate_success(self, mock_post, amadeus_credentials):
        """Should authenticate successfully."""
        mock_post.return_value.json.return_value = {
            'access_token': 'test_token',
            'expires_in': 1800
        }

        client = AmadeusClient(**amadeus_credentials)
        assert client.access_token == 'test_token'

    @patch('amadeus_client.requests.post')
    def test_authenticate_failure(self, mock_post, amadeus_credentials):
        """Should raise AuthenticationError on failure."""
        mock_post.side_effect = Exception("Connection failed")

        with pytest.raises(AuthenticationError):
            AmadeusClient(**amadeus_credentials)

    def test_invalid_credentials(self):
        """Should raise ValueError for missing credentials."""
        with pytest.raises(ValueError, match="requeridos"):
            AmadeusClient('', 'secret')

    def test_invalid_secret(self):
        """Should raise ValueError for missing secret."""
        with pytest.raises(ValueError, match="requeridos"):
            AmadeusClient('key', '')


class TestAmadeusClientEdgeCases:
    """Test edge cases and error handling."""

    def test_lowercase_iata_codes_converted(self, amadeus_credentials):
        """Should convert lowercase IATA codes to uppercase."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)
            # Should not raise - codes get converted to uppercase
            client._validate_search_params('eze', 'mia', '2026-08-01', 2)

    def test_search_flights_timeout(self, amadeus_credentials):
        """Should handle API timeout."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)

        with patch('amadeus_client.requests.get') as mock_get:
            mock_get.side_effect = __import__('requests').exceptions.Timeout()

            with pytest.raises(TimeoutError):
                client.search_flights('EZE', 'MIA', '2026-08-01')

    def test_search_flights_connection_error(self, amadeus_credentials):
        """Should handle connection error."""
        with patch.object(AmadeusClient, '_authenticate'):
            client = AmadeusClient(**amadeus_credentials)

        with patch('amadeus_client.requests.get') as mock_get:
            mock_get.side_effect = __import__('requests').exceptions.ConnectionError()

            with pytest.raises(APIError):
                client.search_flights('EZE', 'MIA', '2026-08-01')
