"""Unit tests for the Sky Scrapper (RapidAPI) flight client."""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skyscrapper_client import (
    SkyScrapperClient,
    AuthenticationError,
    APIError,
    TimeoutError,
)


@pytest.fixture
def client():
    return SkyScrapperClient(api_key='test-rapidapi-key')


class TestClientInit:
    def test_should_reject_empty_api_key(self):
        with pytest.raises(ValueError):
            SkyScrapperClient(api_key='')

    def test_should_set_rapidapi_headers(self, client):
        assert client.headers['x-rapidapi-key'] == 'test-rapidapi-key'
        assert client.headers['x-rapidapi-host'] == 'sky-scrapper.p.rapidapi.com'


class TestValidation:
    def test_should_reject_invalid_iata_code(self, client, valid_dates):
        with pytest.raises(ValueError, match='IATA'):
            client.search_flights('INVALID', 'MIA', valid_dates['future'])

    def test_should_reject_past_departure_date(self, client, valid_dates):
        with pytest.raises(ValueError, match='futura'):
            client.search_flights('EZE', 'MIA', valid_dates['past'])

    def test_should_reject_invalid_date_format(self, client, valid_dates):
        with pytest.raises(ValueError, match='YYYY-MM-DD'):
            client.search_flights('EZE', 'MIA', valid_dates['invalid_format'])

    def test_should_reject_adults_out_of_range(self, client, valid_dates):
        with pytest.raises(ValueError, match='Adults'):
            client.search_flights('EZE', 'MIA', valid_dates['future'], adults=10)


class TestErrorMapping:
    @patch('skyscrapper_client.requests.get')
    def test_should_raise_authentication_error_on_403(self, mock_get, client):
        mock_get.return_value = MagicMock(status_code=403)
        with pytest.raises(AuthenticationError):
            client._get('/api/v1/flights/searchAirport', {'query': 'EZE'})

    @patch('skyscrapper_client.requests.get')
    def test_should_raise_api_error_on_429(self, mock_get, client):
        mock_get.return_value = MagicMock(status_code=429)
        with pytest.raises(APIError, match='Rate limit'):
            client._get('/api/v1/flights/searchAirport', {'query': 'EZE'})

    @patch('skyscrapper_client.requests.get')
    def test_should_raise_timeout_error_on_timeout(self, mock_get, client):
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()
        with pytest.raises(TimeoutError):
            client._get('/api/v1/flights/searchAirport', {'query': 'EZE'})


class TestAirportResolution:
    def test_should_resolve_iata_to_sky_and_entity_ids(self, client, sample_airport_response):
        with patch.object(client, '_get', return_value=sample_airport_response):
            resolved = client._resolve_airport('EZE')

        assert resolved == {'skyId': 'EZE', 'entityId': '95673318'}

    def test_should_cache_resolved_airports(self, client, sample_airport_response):
        with patch.object(client, '_get', return_value=sample_airport_response) as mock_get:
            client._resolve_airport('EZE')
            client._resolve_airport('EZE')

        assert mock_get.call_count == 1

    def test_should_raise_api_error_when_airport_not_found(self, client):
        with patch.object(client, '_get', return_value={'status': True, 'data': []}):
            with pytest.raises(APIError, match='no encontrado'):
                client._resolve_airport('XXX')


class TestItineraryParsing:
    def test_should_parse_itinerary_to_internal_offer_format(self, client, sample_itinerary):
        offer = client._process_itinerary(sample_itinerary)

        assert offer['id'] == 'itin-123'
        assert offer['price'] == 850.50
        assert offer['currency'] == 'USD'
        assert offer['airline'] == 'LATAM Airlines'
        assert offer['airline_code'] == 'LA'
        assert offer['duration'] == '9h 55m'
        assert offer['stops'] == 1
        assert offer['departure_time'] == '2026-09-01T09:00:00'
        assert offer['arrival_time'] == '2026-09-01T18:55:00'

    def test_should_discard_itinerary_with_invalid_price(self, client, sample_itinerary):
        sample_itinerary['price'] = {'raw': 0}
        assert client._process_itinerary(sample_itinerary) is None

    def test_should_discard_itinerary_without_legs(self, client, sample_itinerary):
        sample_itinerary['legs'] = []
        assert client._process_itinerary(sample_itinerary) is None

    def test_should_default_airline_when_carriers_missing(self, client, sample_itinerary):
        sample_itinerary['legs'][0]['carriers'] = {}
        offer = client._process_itinerary(sample_itinerary)
        assert offer['airline'] == 'N/A'


def airport_response_for(code: str) -> dict:
    """Respuesta de searchAirport (estructura real) para el código consultado."""
    return {
        'status': True,
        'data': [
            {
                'navigation': {
                    'entityId': f'entity-{code}',
                    'entityType': 'AIRPORT',
                    'relevantFlightParams': {
                        'skyId': code,
                        'entityId': f'entity-{code}',
                        'flightPlaceType': 'AIRPORT'
                    }
                }
            }
        ]
    }


class TestSearchFlights:
    def test_should_return_processed_offers(self, client, valid_dates, sample_itinerary):
        flights_response = {'data': {'itineraries': [sample_itinerary]}}

        def fake_get(path, params):
            if 'searchAirport' in path:
                return airport_response_for(params['query'])
            return flights_response

        with patch.object(client, '_get', side_effect=fake_get):
            offers = client.search_flights('EZE', 'MIA', valid_dates['future'])

        assert len(offers) == 1
        assert offers[0]['price'] == 850.50

    def test_should_limit_results_to_max_results(self, client, valid_dates, sample_itinerary):
        flights_response = {'data': {'itineraries': [sample_itinerary] * 20}}

        def fake_get(path, params):
            if 'searchAirport' in path:
                return airport_response_for(params['query'])
            return flights_response

        with patch.object(client, '_get', side_effect=fake_get):
            offers = client.search_flights('EZE', 'MIA', valid_dates['future'], max_results=5)

        assert len(offers) == 5

    def test_should_retry_when_search_incomplete_and_empty(
        self, client, valid_dates, sample_itinerary
    ):
        responses = iter([
            {'data': {'context': {'status': 'incomplete'}, 'itineraries': []}},
            {'data': {'context': {'status': 'complete'}, 'itineraries': [sample_itinerary]}},
        ])

        def fake_get(path, params):
            if 'searchAirport' in path:
                return airport_response_for(params['query'])
            return next(responses)

        with patch.object(client, '_get', side_effect=fake_get), \
             patch('skyscrapper_client.time.sleep'):
            offers = client.search_flights('EZE', 'MIA', valid_dates['future'])

        assert len(offers) == 1

    def test_should_return_empty_list_when_no_itineraries(self, client, valid_dates):
        def fake_get(path, params):
            if 'searchAirport' in path:
                return airport_response_for(params['query'])
            return {'data': {'itineraries': []}}

        with patch.object(client, '_get', side_effect=fake_get):
            offers = client.search_flights('EZE', 'MIA', valid_dates['future'])

        assert offers == []

    def test_should_include_return_date_when_provided(self, client, valid_dates):
        captured = {}

        def fake_get(path, params):
            if 'searchAirport' in path:
                return airport_response_for(params['query'])
            captured.update(params)
            return {'data': {'itineraries': []}}

        with patch.object(client, '_get', side_effect=fake_get):
            client.search_flights(
                'EZE', 'MIA', valid_dates['future'],
                return_date=valid_dates['far_future']
            )

        assert captured['returnDate'] == valid_dates['far_future']
        assert captured['originSkyId'] == 'EZE'
        assert captured['originEntityId'] == 'entity-EZE'
        assert captured['destinationSkyId'] == 'MIA'
        assert captured['destinationEntityId'] == 'entity-MIA'
