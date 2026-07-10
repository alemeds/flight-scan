"""Shared fixtures and configuration for Flight Scan tests."""

import pytest
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


@pytest.fixture
def valid_iata_codes():
    """Válid IATA codes for testing."""
    return {
        'origin': 'EZE',  # Buenos Aires
        'destination': 'MIA',  # Miami
        'invalid': 'INVALID',
        'lowercase': 'eze',
        'empty': '',
    }


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
def amadeus_credentials():
    """Amadeus API credentials for testing."""
    return {
        'api_key': 'test_key_12345',
        'api_secret': 'test_secret_67890',
    }


@pytest.fixture
def db_credentials():
    """Database connection credentials."""
    return {
        'host': 'localhost',
        'port': 5432,
        'database': 'flight_scan_test',
        'user': 'test_user',
        'password': 'test_password',
    }


@pytest.fixture
def sample_flight_offer():
    """Sample flight offer from Amadeus API."""
    return {
        'id': 'SIM1_EZEMAI',
        'price': {
            'total': '450.50',
            'currency': 'USD'
        },
        'itineraries': [
            {
                'duration': 'PT10H30M',
                'segments': [
                    {
                        'carrierCode': 'AA',
                        'departure': {'at': '2026-08-01T10:00:00'},
                        'arrival': {'at': '2026-08-01T20:30:00'},
                    }
                ]
            }
        ],
        'numberOfBookableSeats': 5,
    }


@pytest.fixture
def mock_amadeus_response():
    """Mock response from Amadeus API."""
    return {
        'data': [
            {
                'id': 'SIM1_EZEMAI',
                'price': {
                    'total': '450.50',
                    'currency': 'USD'
                },
                'itineraries': [
                    {
                        'duration': 'PT10H30M',
                        'segments': [
                            {
                                'carrierCode': 'AA',
                                'departure': {'at': '2026-08-01T10:00:00'},
                                'arrival': {'at': '2026-08-01T20:30:00'},
                            }
                        ]
                    }
                ],
                'numberOfBookableSeats': 5,
            },
            {
                'id': 'SIM2_EZEMAI',
                'price': {
                    'total': '520.75',
                    'currency': 'USD'
                },
                'itineraries': [
                    {
                        'duration': 'PT12H00M',
                        'segments': [
                            {
                                'carrierCode': 'LA',
                                'departure': {'at': '2026-08-01T14:00:00'},
                                'arrival': {'at': '2026-08-02T02:00:00'},
                            }
                        ]
                    }
                ],
                'numberOfBookableSeats': 3,
            }
        ]
    }


@pytest.fixture
def mock_amadeus_empty_response():
    """Mock empty response from Amadeus API."""
    return {'data': []}


@pytest.fixture
def mock_amadeus_no_results():
    """Mock response with no flight offers."""
    return {
        'data': []
    }


@pytest.fixture(autouse=True)
def reset_imports():
    """Reset imports before each test to avoid side effects."""
    yield
    # Cleanup after test
    if 'amadeus_client' in __import__('sys').modules:
        del __import__('sys').modules['amadeus_client']
    if 'database' in __import__('sys').modules:
        del __import__('sys').modules['database']
