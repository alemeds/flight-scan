import requests
import logging
import re
import time
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """RapidAPI key inválida o suscripción inactiva"""
    pass


class APIError(Exception):
    """Error general de la API Sky Scrapper"""
    pass


class TimeoutError(Exception):
    """Timeout en conexión"""
    pass


class SkyScrapperClient:
    """
    Cliente para la API Sky Scrapper (RapidAPI).

    Reemplaza al antiguo cliente de Amadeus manteniendo la misma interfaz:
    search_flights() devuelve la misma estructura de ofertas que consumía app.py.
    Sin OAuth2: la autenticación es por headers de RapidAPI en cada request.
    """

    BASE_URL = "https://sky-scrapper.p.rapidapi.com"

    # La búsqueda es asíncrona del lado de Sky Scrapper: la primera respuesta
    # puede venir vacía con context.status == "incomplete" y hay que reintentar
    INCOMPLETE_RETRIES = 3
    RETRY_DELAY_SECONDS = 2

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("RapidAPI key es requerida")

        self.headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': 'sky-scrapper.p.rapidapi.com'
        }
        # Cache IATA -> {skyId, entityId} para no repetir searchAirport por búsqueda
        self._airport_cache: Dict[str, Dict[str, str]] = {}

    def _get(self, path: str, params: Dict) -> Dict:
        """Ejecuta un GET autenticado y mapea errores HTTP a excepciones propias"""
        try:
            response = requests.get(
                f"{self.BASE_URL}{path}",
                headers=self.headers,
                params=params,
                timeout=30
            )

            if response.status_code in (401, 403):
                raise AuthenticationError("RapidAPI key inválida o suscripción inactiva")
            if response.status_code == 429:
                raise APIError("Rate limit de RapidAPI excedido. Espera antes de reintentar.")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            raise TimeoutError("Timeout consultando Sky Scrapper")
        except requests.exceptions.ConnectionError:
            raise APIError("Error de conexión a Sky Scrapper")
        except requests.exceptions.HTTPError as e:
            raise APIError(f"Error HTTP {e.response.status_code}")
        except ValueError:
            raise APIError("Respuesta de Sky Scrapper no es JSON válido")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Error en solicitud HTTP: {type(e).__name__}")

    def _resolve_airport(self, iata_code: str) -> Dict[str, str]:
        """
        Resuelve un código IATA a skyId + entityId via searchAirport
        (paso previo obligatorio antes de buscar vuelos)
        """
        code = iata_code.upper()

        if code in self._airport_cache:
            return self._airport_cache[code]

        data = self._get(
            '/api/v1/flights/searchAirport',
            {'query': code, 'locale': 'en-US'}
        )

        results = data.get('data') or []

        # El skyId vive en navigation.relevantFlightParams; preferir el
        # aeropuerto cuyo skyId coincide exacto con el IATA consultado
        airport_params = None
        fallback_params = None
        for item in results:
            nav = item.get('navigation') or {}
            flight_params = nav.get('relevantFlightParams') or {}
            if flight_params.get('skyId') != code:
                continue
            if nav.get('entityType') == 'AIRPORT':
                airport_params = flight_params
                break
            if fallback_params is None:
                fallback_params = flight_params

        matched = airport_params or fallback_params
        if matched is None:
            raise APIError(f"Aeropuerto {code} no encontrado en Sky Scrapper")

        resolved = {
            'skyId': matched['skyId'],
            'entityId': str(matched['entityId'])
        }

        self._airport_cache[code] = resolved
        return resolved

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
        Busca ofertas de vuelos punto a punto

        Args:
            origin: Código IATA del aeropuerto de origen (ej: 'EZE')
            destination: Código IATA del aeropuerto de destino (ej: 'MIA')
            departure_date: Fecha de salida en formato YYYY-MM-DD
            return_date: Fecha de regreso en formato YYYY-MM-DD (opcional)
            adults: Número de adultos (default: 1)
            max_results: Número máximo de resultados (default: 10)

        Returns:
            Lista de diccionarios con ofertas de vuelos (misma estructura
            que el antiguo cliente de Amadeus)

        Raises:
            ValueError: Si los parámetros son inválidos
            TimeoutError: Si la API no responde a tiempo
            AuthenticationError: Si la key de RapidAPI es inválida
            APIError: Si la API retorna un error
        """
        self._validate_search_params(origin, destination, departure_date, adults)

        origin_airport = self._resolve_airport(origin)
        destination_airport = self._resolve_airport(destination)

        params = {
            'originSkyId': origin_airport['skyId'],
            'destinationSkyId': destination_airport['skyId'],
            'originEntityId': origin_airport['entityId'],
            'destinationEntityId': destination_airport['entityId'],
            'date': departure_date,
            'adults': adults,
            'currency': 'USD',
            'market': 'en-US',
            'countryCode': 'US'
        }

        if return_date:
            params['returnDate'] = return_date

        payload = (self._get('/api/v1/flights/searchFlights', params)).get('data') or {}
        itineraries = payload.get('itineraries') or []

        retries = 0
        while (
            not itineraries
            and (payload.get('context') or {}).get('status') == 'incomplete'
            and retries < self.INCOMPLETE_RETRIES
        ):
            retries += 1
            time.sleep(self.RETRY_DELAY_SECONDS)
            payload = (self._get('/api/v1/flights/searchFlights', params)).get('data') or {}
            itineraries = payload.get('itineraries') or []

        offers = []
        for itinerary in itineraries[:max_results]:
            processed = self._process_itinerary(itinerary)
            if processed:
                offers.append(processed)

        return offers

    def _process_itinerary(self, itinerary: Dict) -> Optional[Dict]:
        """Procesa un itinerario de Sky Scrapper al formato interno de ofertas"""
        try:
            price = float((itinerary.get('price') or {}).get('raw', 0))

            if price <= 0:
                logger.warning(f"Oferta descartada: precio inválido ({price})")
                return None

            legs = itinerary.get('legs') or []
            if not legs:
                logger.warning("Oferta descartada: sin tramos")
                return None

            first_leg = legs[0]

            duration_minutes = int(first_leg.get('durationInMinutes') or 0)
            duration = f"{duration_minutes // 60}h {duration_minutes % 60}m"

            carriers = (first_leg.get('carriers') or {}).get('marketing') or []
            airline = carriers[0].get('name', 'N/A') if carriers else 'N/A'
            airline_code = carriers[0].get('alternateId', 'N/A') if carriers else 'N/A'

            return {
                'id': itinerary.get('id', 'unknown'),
                'price': price,
                'currency': 'USD',
                'airline': airline,
                'airline_code': airline_code,
                'duration': duration,
                'stops': int(first_leg.get('stopCount') or 0),
                'departure_time': first_leg.get('departure', ''),
                'arrival_time': first_leg.get('arrival', ''),
                'raw_data': itinerary
            }

        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error procesando itinerario: {type(e).__name__}")
            return None

    def _validate_search_params(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int
    ) -> None:
        """Valida los parámetros de búsqueda antes de llamar a la API"""
        if not re.match(r'^[A-Z]{3}$', origin.upper()):
            raise ValueError(f"Código IATA de origen inválido: {origin}")

        if not re.match(r'^[A-Z]{3}$', destination.upper()):
            raise ValueError(f"Código IATA de destino inválido: {destination}")

        try:
            departure = datetime.strptime(departure_date, '%Y-%m-%d')
        except ValueError:
            raise ValueError(f"Fecha de salida inválida (formato YYYY-MM-DD): {departure_date}")

        if departure.date() < datetime.now().date():
            raise ValueError("La fecha de salida debe ser futura")

        if not (1 <= adults <= 9):
            raise ValueError("Adults debe estar entre 1 y 9")

    def validate_airport_code(self, iata_code: str) -> bool:
        """Verifica que un código IATA exista en Sky Scrapper"""
        try:
            self._resolve_airport(iata_code)
            return True
        except APIError:
            return False
