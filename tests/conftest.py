"""Shared fixtures and configuration for Flight Scan tests."""

import pytest
from datetime import datetime, timedelta


@pytest.fixture
def valid_dates():
    """Valid dates for flight searches."""
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    next_week = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    return {
        'future': tomorrow,
        'far_future': next_week,
        'past': yesterday,
        'invalid_format': '01-01-2026',
    }


@pytest.fixture
def sample_itinerary():
    """Sample itinerary from Sky Scrapper searchFlights response."""
    return {
        'id': 'itin-123',
        'price': {'raw': 850.50, 'formatted': '$851'},
        'legs': [
            {
                'durationInMinutes': 595,
                'stopCount': 1,
                'departure': '2026-09-01T09:00:00',
                'arrival': '2026-09-01T18:55:00',
                'carriers': {
                    'marketing': [
                        {'id': -32171, 'name': 'LATAM Airlines', 'alternateId': 'LA'}
                    ]
                }
            }
        ]
    }


@pytest.fixture
def sample_airport_response():
    """Sample response from Sky Scrapper searchAirport endpoint (real shape)."""
    return {
        'status': True,
        'data': [
            {
                'presentation': {'title': 'Buenos Aires', 'suggestionTitle': 'Buenos Aires (Any)'},
                'navigation': {
                    'entityId': '27536465',
                    'entityType': 'CITY',
                    'relevantFlightParams': {
                        'skyId': 'BUEA',
                        'entityId': '27536465',
                        'flightPlaceType': 'CITY'
                    }
                }
            },
            {
                'presentation': {'title': 'Buenos Aires Ministro Pistarini'},
                'navigation': {
                    'entityId': '95673318',
                    'entityType': 'AIRPORT',
                    'relevantFlightParams': {
                        'skyId': 'EZE',
                        'entityId': '95673318',
                        'flightPlaceType': 'AIRPORT'
                    }
                }
            }
        ]
    }
