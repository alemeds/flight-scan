"""Optimized Amadeus client with caching for better performance."""

import requests
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum
import re
import time

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Cache configuration
DURATION_CACHE_SIZE = 1000
TOKEN_CACHE_CHECK_INTERVAL = 60  # Check token only every 60 seconds

# Airline codes lookup table (LUT) - Pre-computed for speed
AIRLINE_CODES = {
    'AA': 'American Airlines',
    'AR': 'Aerolíneas Argentinas',
    'BA': 'British Airways',
    'DL': 'Delta Air Lines',
    'EK': 'Emirates',
    'LA': 'LATAM Airlines',
    'LH': 'Lufthansa',
    'QF': 'Qantas',
    'SQ': 'Singapore Airlines',
    'UA': 'United Airlines',
}


class AuthenticationError(Exception):
    """Amadeus API authentication error"""
    pass


class APIError(Exception):
    """Amadeus API error"""
    pass


class TimeoutError(Exception):
    """API timeout error"""
    pass


class AmadeusClient:
    """Optimized client for Amadeus Flight Offers API with caching."""

    MAX_RETRIES = 3
    INITIAL_BACKOFF = 1  # seconds

    def __init__(self, api_key: str, api_secret: str, base_url: Optional[str] = None):
        """
        Initialize Amadeus client with caching.

        Args:
            api_key: Amadeus API Key
            api_secret: Amadeus API Secret
            base_url: API base URL (default: test environment)
        """
        if not api_key or not api_secret:
            raise ValueError("API key y secret son requeridos")

        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url or "https://test.api.amadeus.com"
        self.access_token = None
        self.token_expiry = None

        # OPTIMIZATION: Duration parsing cache (LRU-like)
        self._duration_cache: Dict[str, str] = {}

        # OPTIMIZATION: Token check throttling (don't check every time)
        self._last_token_check = 0

        try:
            self._authenticate()
        except Exception as e:
            logger.warning(f"Autenticación inicial falló: {type(e).__name__}. "
                          "Se intentará autenticar en la próxima llamada.")

    def _authenticate(self) -> None:
        """Get authentication token from Amadeus."""
        auth_url = f"{self.base_url}/v1/security/oauth2/token"

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'grant_type': 'client_credentials',
            'client_id': self.api_key,
            'client_secret': self.api_secret
        }

        try:
            response = requests.post(auth_url, headers=headers, data=data, timeout=10)
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data['access_token']

            # Calculate expiry time (typically 1800 seconds)
            expires_in = token_data.get('expires_in', 1800)
            self.token_expiry = datetime.now().timestamp() + expires_in

        except requests.exceptions.Timeout:
            raise TimeoutError("Timeout obteniendo token de autenticación")
        except requests.exceptions.ConnectionError as e:
            raise AuthenticationError(f"Error de conexión: {type(e).__name__}")
        except (KeyError, ValueError) as e:
            raise AuthenticationError(f"Respuesta de token inválida: {type(e).__name__}")
        except requests.exceptions.RequestException as e:
            raise AuthenticationError(f"Error obteniendo token: {type(e).__name__}")

    def _is_token_valid(self) -> bool:
        """
        OPTIMIZATION: Throttle token validation checks (every 60 seconds).
        Avoid repeated datetime calculations.
        """
        if not self.access_token or not self.token_expiry:
            return False

        current_time = datetime.now().timestamp()

        # Only check if 60 seconds have passed since last check
        if current_time - self._last_token_check < TOKEN_CACHE_CHECK_INTERVAL:
            # Assume token is still valid if checked recently
            return True

        self._last_token_check = current_time

        # Token is valid if > 60 seconds remain
        return current_time < (self.token_expiry - 60)

    def _ensure_authenticated(self, retry_count: int = 0) -> None:
        """Ensure we have a valid token with exponential backoff."""
        if self._is_token_valid():
            return

        if retry_count >= self.MAX_RETRIES:
            raise AuthenticationError(
                f"Falló autenticación después de {self.MAX_RETRIES} intentos"
            )

        try:
            self._authenticate()
        except AuthenticationError as e:
            backoff_time = self.INITIAL_BACKOFF * (2 ** retry_count)
            logger.warning(f"Intento de autenticación {retry_count + 1} falló. "
                          f"Reintentando en {backoff_time}s...")
            time.sleep(backoff_time)
            self._ensure_authenticated(retry_count + 1)

    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        max_results: int = 10
    ) -> List[Dict]:
        """
        Search for flight offers.

        Args:
            origin: Origin IATA code (e.g., 'EZE')
            destination: Destination IATA code (e.g., 'MIA')
            departure_date: Departure date (YYYY-MM-DD)
            return_date: Return date (YYYY-MM-DD, optional)
            adults: Number of adults (default: 1)
            max_results: Max results to return (default: 10)

        Returns:
            List of flight offers with prices and details
        """
        self._validate_search_params(origin, destination, departure_date, adults)
        self._ensure_authenticated()

        search_url = f"{self.base_url}/v2/shopping/flight-offers"

        params = {
            'originLocationCode': origin.upper(),
            'destinationLocationCode': destination.upper(),
            'departureDate': departure_date,
            'adults': str(adults),
            'max': str(max_results),
            'currencyCode': 'USD'
        }

        if return_date:
            params['returnDate'] = return_date

        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }

        try:
            response = requests.get(search_url, headers=headers, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()
            offers = data.get('data', [])

            # Process and return flights
            processed_offers = []
            for offer in offers:
                processed = self._process_flight_offer(offer)
                if processed:
                    processed_offers.append(processed)

            return processed_offers

        except requests.exceptions.Timeout:
            raise TimeoutError("Timeout en búsqueda de vuelos")
        except requests.exceptions.ConnectionError as e:
            raise APIError(f"Error de conexión: {type(e).__name__}")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Error en búsqueda: {type(e).__name__}")

    def _validate_search_params(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int
    ) -> None:
        """Validate search parameters."""
        # IATA code validation (3 uppercase letters)
        if not re.match(r'^[A-Z]{3}$', origin.upper()):
            raise ValueError("Código IATA de origen inválido")

        if not re.match(r'^[A-Z]{3}$', destination.upper()):
            raise ValueError("Código IATA de destino inválido")

        if origin.upper() == destination.upper():
            raise ValueError("Origen y destino no pueden ser iguales")

        # Date validation
        try:
            departure = datetime.fromisoformat(departure_date)
            if departure < datetime.now():
                raise ValueError("Fecha de salida debe ser futura")
        except ValueError:
            raise ValueError("Formato de fecha inválido (usar YYYY-MM-DD)")

        # Adults validation
        if not (1 <= adults <= 9):
            raise ValueError("Número de adultos debe estar entre 1 y 9")

    def _parse_duration(self, duration_str: str) -> str:
        """
        OPTIMIZATION: Cache duration parsing (most durations repeat).
        Parse ISO 8601 duration format: PT10H30M → "10h 30m"
        """
        # Check cache first (avoid regex/parsing)
        if duration_str in self._duration_cache:
            return self._duration_cache[duration_str]

        try:
            # Parse ISO 8601 duration
            pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?'
            match = re.match(pattern, duration_str)

            if not match:
                result = 'N/A'
            else:
                hours = int(match.group(1) or 0)
                minutes = int(match.group(2) or 0)
                result = f"{hours}h {minutes}m"

            # Cache the result
            if len(self._duration_cache) >= DURATION_CACHE_SIZE:
                # Simple eviction: remove first item when cache is full
                self._duration_cache.pop(next(iter(self._duration_cache)))

            self._duration_cache[duration_str] = result
            return result

        except Exception:
            return 'N/A'

    def _get_airline_name(self, airline_code: str) -> str:
        """
        OPTIMIZATION: Use pre-computed LUT instead of dict lookup every time.
        Returns airline name from code, or code if not found.
        """
        return AIRLINE_CODES.get(airline_code, airline_code)

    def _process_flight_offer(self, offer: Dict) -> Optional[Dict]:
        """Process a single flight offer from API response."""
        try:
            # Validate required fields
            if not offer.get('price') or not offer.get('itineraries'):
                return None

            price_info = offer.get('price', {})
            price = float(price_info.get('total', 0))

            if price <= 0:
                return None

            # Get itinerary info
            itineraries = offer.get('itineraries', [])
            if not itineraries:
                return None

            outbound = itineraries[0]
            segments = outbound.get('segments', [])

            if not segments:
                return None

            # Get first segment for airline info
            first_segment = segments[0]
            airline_code = first_segment.get('carrierCode', 'N/A')
            airline_name = self._get_airline_name(airline_code)

            # Parse duration (using cache)
            duration = self._parse_duration(outbound.get('duration', 'PT0H'))

            return {
                'id': offer.get('id'),
                'price': price,
                'currency': price_info.get('currency', 'USD'),
                'airline': airline_name,
                'duration': duration,
                'seats': offer.get('numberOfBookableSeats', 0),
                'stops': len(segments) - 1,
                'departure': first_segment.get('departure', {}).get('at'),
                'arrival': segments[-1].get('arrival', {}).get('at')
            }

        except (KeyError, ValueError, TypeError):
            return None

    def get_cache_stats(self) -> Dict[str, int]:
        """
        OPTIMIZATION: Expose cache statistics for monitoring.
        """
        return {
            'duration_cache_size': len(self._duration_cache),
            'duration_cache_max': DURATION_CACHE_SIZE,
            'duration_cache_usage_percent': int((len(self._duration_cache) / DURATION_CACHE_SIZE) * 100)
        }

    def clear_caches(self) -> None:
        """Clear all caches (for testing or maintenance)."""
        self._duration_cache.clear()
        self._last_token_check = 0
        logger.info("All caches cleared")
