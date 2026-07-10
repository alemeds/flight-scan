import requests
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum

# Configurar logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class AuthenticationError(Exception):
    """Error de autenticación con API de Amadeus"""
    pass

class APIError(Exception):
    """Error general de API"""
    pass

class TimeoutError(Exception):
    """Timeout en conexión"""
    pass

class AmadeusClient:
    """Cliente para interactuar con la API de Amadeus"""

    MAX_RETRIES = 3
    INITIAL_BACKOFF = 1  # segundos

    def __init__(self, api_key: str, api_secret: str, base_url: Optional[str] = None):
        """
        Inicializa el cliente de Amadeus

        Args:
            api_key: API Key de Amadeus
            api_secret: API Secret de Amadeus
            base_url: URL base de la API (por defecto: test environment)
        """
        if not api_key or not api_secret:
            raise ValueError("API key y secret son requeridos")

        self.api_key = api_key
        self.api_secret = api_secret
        # FIXING #8: URL configurable por environment
        self.base_url = base_url or "https://test.api.amadeus.com"
        self.access_token = None
        self.token_expiry = None

        try:
            self._authenticate()
        except Exception as e:
            # FIXING #6: No lanzar excepción en __init__, solo warning
            logger.warning(f"Autenticación inicial falló: {type(e).__name__}. "
                          "Se intentará autenticar en la próxima llamada.")

    def _authenticate(self):
        """Obtiene el token de autenticación de Amadeus"""
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

            # Calcular tiempo de expiración (generalmente 1800 segundos)
            expires_in = token_data.get('expires_in', 1800)
            self.token_expiry = datetime.now().timestamp() + expires_in

        except requests.exceptions.Timeout:
            # FIXING #7: Excepciones específicas
            raise TimeoutError("Timeout obteniendo token de autenticación")
        except requests.exceptions.ConnectionError as e:
            raise AuthenticationError(f"Error de conexión: {type(e).__name__}")
        except (KeyError, ValueError) as e:
            # Token malformado
            raise AuthenticationError(f"Respuesta de token inválida: {type(e).__name__}")
        except requests.exceptions.RequestException as e:
            raise AuthenticationError(f"Error obteniendo token: {type(e).__name__}")

    def _is_token_valid(self) -> bool:
        """Verifica si el token actual es válido"""
        if not self.access_token or not self.token_expiry:
            return False

        # Renovar si faltan menos de 60 segundos
        return datetime.now().timestamp() < (self.token_expiry - 60)

    def _ensure_authenticated(self, retry_count: int = 0):
        """
        Asegura que haya un token válido con exponential backoff

        FIXING #6: Exponential backoff para retry automático
        """
        if self._is_token_valid():
            return

        if retry_count >= self.MAX_RETRIES:
            raise AuthenticationError(
                f"Falló autenticación después de {self.MAX_RETRIES} intentos"
            )

        try:
            self._authenticate()
        except AuthenticationError as e:
            # Exponential backoff: 1s, 2s, 4s, 8s...
            backoff_time = self.INITIAL_BACKOFF * (2 ** retry_count)
            logger.warning(f"Intento de autenticación {retry_count + 1} falló. "
                          f"Reintentando en {backoff_time}s...")

            import time
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
        Busca ofertas de vuelos

        Args:
            origin: Código IATA del aeropuerto de origen (ej: 'EZE')
            destination: Código IATA del aeropuerto de destino (ej: 'MIA')
            departure_date: Fecha de salida en formato YYYY-MM-DD
            return_date: Fecha de regreso en formato YYYY-MM-DD (opcional)
            adults: Número de adultos (default: 1)
            max_results: Número máximo de resultados (default: 10)

        Returns:
            Lista de diccionarios con ofertas de vuelos

        Raises:
            ValueError: Si los parámetros son inválidos
            TimeoutError: Si la API no responde a tiempo
            APIError: Si la API retorna un error
        """
        # FIXING #5: Validar inputs
        self._validate_search_params(origin, destination, departure_date, adults)

        self._ensure_authenticated()

        search_url = f"{self.base_url}/v2/shopping/flight-offers"

        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }

        params = {
            'originLocationCode': origin.upper(),
            'destinationLocationCode': destination.upper(),
            'departureDate': departure_date,
            'adults': adults,
            'max': max_results,
            'currencyCode': 'USD'
        }

        # Agregar fecha de regreso si existe
        if return_date:
            params['returnDate'] = return_date

        try:
            response = requests.get(search_url, headers=headers, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            # Procesar y formatear los resultados
            offers = []

            if 'data' in data and len(data['data']) > 0:
                for offer in data['data']:
                    processed_offer = self._process_flight_offer(offer)
                    if processed_offer:
                        offers.append(processed_offer)

            return offers

        except requests.exceptions.Timeout:
            # FIXING #7: Excepciones específicas
            raise TimeoutError("Timeout buscando vuelos. La API de Amadeus no respondió a tiempo.")
        except requests.exceptions.ConnectionError:
            raise APIError("Error de conexión a API de Amadeus")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Credenciales de API inválidas")
            elif e.response.status_code == 429:
                raise APIError("Rate limit excedido. Espera antes de reintentar.")
            else:
                raise APIError(f"Error HTTP {e.response.status_code}")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Error en solicitud HTTP: {type(e).__name__}")

    def _validate_search_params(self, origin: str, destination: str,
                               departure_date: str, adults: int) -> None:
        """
        Valida los parámetros de búsqueda

        FIXING #1 y #5: Validación de entrada
        """
        import re
        from datetime import datetime as dt

        # Validar códigos IATA
        iata_pattern = r'^[A-Z]{3}$'
        if not re.match(iata_pattern, origin.upper()):
            raise ValueError(f"Código IATA de origen inválido: {origin}")

        if not re.match(iata_pattern, destination.upper()):
            raise ValueError(f"Código IATA de destino inválido: {destination}")

        # No puede ser el mismo origen y destino
        if origin.upper() == destination.upper():
            raise ValueError("Origen y destino no pueden ser iguales")

        # Validar fecha
        try:
            dep_date = dt.strptime(departure_date, '%Y-%m-%d').date()
            if dep_date < dt.now().date():
                raise ValueError("La fecha de salida debe ser futura")
        except ValueError as e:
            raise ValueError(f"Formato de fecha inválido (esperado YYYY-MM-DD): {str(e)}")

        # Validar número de adultos
        if not 1 <= adults <= 9:
            raise ValueError(f"Número de adultos debe estar entre 1 y 9")

    def _process_flight_offer(self, offer: Dict) -> Optional[Dict]:
        """
        Procesa una oferta de vuelo de Amadeus al formato interno

        Args:
            offer: Diccionario con datos de la oferta de Amadeus

        Returns:
            Diccionario procesado con campos simplificados
        """
        try:
            # FIXING #3: Manejar cuando 'price' es None
            price_data = offer.get('price') or {}
            price = float(price_data.get('total', 0))
            currency = price_data.get('currency', 'USD')

            # Validar precio
            if price <= 0:
                logger.warning(f"Oferta descartada: precio inválido ({price})")
                return None

            # Extraer información de los segmentos de vuelo
            itineraries = offer.get('itineraries', [])

            if not itineraries:
                logger.warning("Oferta descartada: sin itinerarios")
                return None

            # Calcular duración total
            total_duration = self._parse_duration(
                itineraries[0].get('duration', 'PT0H0M')
            )

            # Contar escalas (número de segmentos - 1)
            segments = itineraries[0].get('segments', [])
            stops = max(0, len(segments) - 1)

            # Obtener aerolínea del primer segmento
            airline = 'N/A'
            airline_code = 'N/A'
            if segments:
                carrier_code = segments[0].get('carrierCode', '')
                airline_code = carrier_code
                airline = self._get_airline_name(carrier_code)

            # Obtener horarios
            departure_time = None
            arrival_time = None
            if segments:
                departure_time = segments[0].get('departure', {}).get('at', '')
                arrival_time = segments[-1].get('arrival', {}).get('at', '')

            processed = {
                'id': offer.get('id', 'unknown'),
                'price': price,
                'currency': currency,
                'airline': airline,
                'airline_code': airline_code,
                'duration': total_duration,
                'stops': stops,
                'departure_time': departure_time,
                'arrival_time': arrival_time,
                'number_of_bookable_seats': offer.get('numberOfBookableSeats', 0),
                'raw_data': offer  # Guardar datos completos
            }

            return processed

        except (KeyError, ValueError, TypeError) as e:
            # FIXING #7: Excepciones específicas, no Exception genérica
            # FIXING #2: No exponer detalles sensibles
            logger.error(f"Error procesando oferta: {type(e).__name__}")
            return None

    def _parse_duration(self, duration_str: str) -> str:
        """
        Convierte duración ISO 8601 a formato legible

        Args:
            duration_str: Duración en formato ISO 8601 (ej: 'PT10H30M')

        Returns:
            String con duración en formato legible (ej: '10h 30m')
        """
        try:
            # Eliminar 'PT' del inicio
            duration = duration_str.replace('PT', '')

            hours = 0
            minutes = 0

            # Extraer horas
            if 'H' in duration:
                hours_str = duration.split('H')[0]
                hours = int(hours_str)
                duration = duration.split('H')[1] if len(duration.split('H')) > 1 else ''

            # Extraer minutos
            if 'M' in duration:
                minutes_str = duration.split('M')[0]
                minutes = int(minutes_str)

            return f"{hours}h {minutes}m"

        except (ValueError, IndexError):
            return "N/A"

    def _get_airline_name(self, carrier_code: str) -> str:
        """
        Convierte código de aerolínea a nombre (mapeo completo)

        Args:
            carrier_code: Código IATA de la aerolínea

        Returns:
            Nombre de la aerolínea o el código si no se encuentra
        """
        # Mapeo completo de códigos IATA a nombres de aerolíneas
        airline_map = {
            # Americas
            'AA': 'American Airlines',
            'UA': 'United Airlines',
            'DL': 'Delta Air Lines',
            'WN': 'Southwest Airlines',
            'B6': 'JetBlue Airways',
            'AS': 'Alaska Airlines',
            'NK': 'Spirit Airlines',
            'F9': 'Frontier Airlines',
            'AC': 'Air Canada',
            'AR': 'Aerolíneas Argentinas',
            'LA': 'LATAM Airlines',
            'CM': 'Copa Airlines',
            'AV': 'Avianca',
            'G3': 'Gol Linhas Aéreas',
            'JJ': 'LATAM Brasil',
            'AD': 'Azul Brazilian Airlines',
            'AM': 'Aeroméxico',
            'VB': 'VivaAerobus',
            'Y4': 'Volaris',

            # Europe
            'BA': 'British Airways',
            'IB': 'Iberia',
            'AF': 'Air France',
            'KL': 'KLM Royal Dutch Airlines',
            'LH': 'Lufthansa',
            'TP': 'TAP Air Portugal',
            'UX': 'Air Europa',
            'VY': 'Vueling',
            'AZ': 'ITA Airways',
            'LX': 'Swiss International Air Lines',
            'OS': 'Austrian Airlines',
            'SK': 'SAS Scandinavian Airlines',
            'AY': 'Finnair',
            'FI': 'Icelandair',
            'SU': 'Aeroflot',
            'EI': 'Aer Lingus',
            'FR': 'Ryanair',
            'U2': 'easyJet',
            'W6': 'Wizz Air',

            # Middle East & Asia
            'EK': 'Emirates',
            'QR': 'Qatar Airways',
            'EY': 'Etihad Airways',
            'TK': 'Turkish Airlines',
            'SQ': 'Singapore Airlines',
            'CX': 'Cathay Pacific',
            'NH': 'All Nippon Airways',
            'JL': 'Japan Airlines',
            'KE': 'Korean Air',
            'OZ': 'Asiana Airlines',
            'TG': 'Thai Airways',
            'MH': 'Malaysia Airlines',
            'GA': 'Garuda Indonesia',
            'AI': 'Air India',
            'CI': 'China Airlines',
            'BR': 'EVA Air',
            'CA': 'Air China',
            'MU': 'China Eastern Airlines',
            'CZ': 'China Southern Airlines',

            # Oceania & Africa
            'QF': 'Qantas',
            'NZ': 'Air New Zealand',
            'VA': 'Virgin Australia',
            'SA': 'South African Airways',
            'ET': 'Ethiopian Airlines',
            'KQ': 'Kenya Airways',
            'MS': 'EgyptAir',
        }

        return airline_map.get(carrier_code, carrier_code)

    def get_airport_info(self, iata_code: str) -> Optional[Dict]:
        """
        Obtiene información de un aeropuerto

        Args:
            iata_code: Código IATA del aeropuerto

        Returns:
            Diccionario con información del aeropuerto o None
        """
        self._ensure_authenticated()

        url = f"{self.base_url}/v1/reference-data/locations"

        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }

        params = {
            'subType': 'AIRPORT',
            'keyword': iata_code.upper()
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'data' in data and len(data['data']) > 0:
                return data['data'][0]
            else:
                return None

        except requests.exceptions.Timeout:
            raise TimeoutError("Timeout obteniendo información del aeropuerto")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error obteniendo aeropuerto: {type(e).__name__}")
            return None

    def validate_airport_code(self, iata_code: str) -> bool:
        """
        Valida que un código IATA existe

        Args:
            iata_code: Código IATA a validar

        Returns:
            True si el código es válido, False en caso contrario
        """
        airport_info = self.get_airport_info(iata_code)
        return airport_info is not None
