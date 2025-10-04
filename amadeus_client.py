import requests
import json
from datetime import datetime

class AmadeusClient:
    """Cliente para interactuar con la API de Amadeus"""
    
    def __init__(self, api_key, api_secret):
        """
        Inicializa el cliente de Amadeus
        
        Args:
            api_key: API Key de Amadeus
            api_secret: API Secret de Amadeus
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://test.api.amadeus.com"
        self.access_token = None
        self.token_expiry = None
        self._authenticate()
    
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
            response = requests.post(auth_url, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            
            # Calcular tiempo de expiración (generalmente 1800 segundos)
            expires_in = token_data.get('expires_in', 1800)
            self.token_expiry = datetime.now().timestamp() + expires_in
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error obteniendo token de autenticación: {str(e)}")
    
    def _is_token_valid(self):
        """Verifica si el token actual es válido"""
        if not self.access_token or not self.token_expiry:
            return False
        
        # Renovar si faltan menos de 60 segundos
        return datetime.now().timestamp() < (self.token_expiry - 60)
    
    def _ensure_authenticated(self):
        """Asegura que haya un token válido"""
        if not self._is_token_valid():
            self._authenticate()
    
    def search_flights(self, origin, destination, departure_date, return_date=None, adults=1, max_results=10):
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
        """
        self._ensure_authenticated()
        
        search_url = f"{self.base_url}/v2/shopping/flight-offers"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        params = {
            'originLocationCode': origin,
            'destinationLocationCode': destination,
            'departureDate': departure_date,
            'adults': adults,
            'max': max_results,
            'currencyCode': 'USD'
        }
        
        # Agregar fecha de regreso si existe
        if return_date:
            params['returnDate'] = return_date
        
        try:
            response = requests.get(search_url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Procesar y formatear los resultados
            offers = []
            
            if 'data' in data:
                for offer in data['data']:
                    processed_offer = self._process_flight_offer(offer)
                    offers.append(processed_offer)
            
            return offers
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error buscando vuelos: {str(e)}")
    
    def _process_flight_offer(self, offer):
        """
        Procesa una oferta de vuelo de Amadeus al formato interno
        
        Args:
            offer: Diccionario con datos de la oferta de Amadeus
        
        Returns:
            Diccionario procesado con campos simplificados
        """
        try:
            # Extraer precio
            price = float(offer.get('price', {}).get('total', 0))
            currency = offer.get('price', {}).get('currency', 'USD')
            
            # Extraer información de los segmentos de vuelo
            itineraries = offer.get('itineraries', [])
            
            # Calcular duración total
            total_duration = self._parse_duration(
                itineraries[0].get('duration', 'PT0H0M') if itineraries else 'PT0H0M'
            )
            
            # Contar escalas (número de segmentos - 1)
            segments = itineraries[0].get('segments', []) if itineraries else []
            stops = max(0, len(segments) - 1)
            
            # Obtener aerolínea del primer segmento
            airline = None
            airline_code = None
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
                'id': offer.get('id'),
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
            
        except Exception as e:
            # En caso de error, retornar estructura mínima
            return {
                'id': offer.get('id', 'unknown'),
                'price': float(offer.get('price', {}).get('total', 0)),
                'currency': offer.get('price', {}).get('currency', 'USD'),
                'airline': 'N/A',
                'airline_code': 'N/A',
                'duration': 'N/A',
                'stops': 0,
                'departure_time': None,
                'arrival_time': None,
                'number_of_bookable_seats': 0,
                'raw_data': offer
            }
    
    def _parse_duration(self, duration_str):
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
                duration = duration.split('H')[1]
            
            # Extraer minutos
            if 'M' in duration:
                minutes_str = duration.split('M')[0]
                minutes = int(minutes_str)
            
            return f"{hours}h {minutes}m"
            
        except Exception:
            return duration_str
    
    def _get_airline_name(self, carrier_code):
        """
        Convierte código de aerolínea a nombre (mapeo básico)
        
        Args:
            carrier_code: Código IATA de la aerolínea
        
        Returns:
            Nombre de la aerolínea o el código si no se encuentra
        """
        # Mapeo básico de códigos IATA a nombres de aerolíneas
        airline_map = {
            'AA': 'American Airlines',
            'UA': 'United Airlines',
            'DL': 'Delta Air Lines',
            'BA': 'British Airways',
            'IB': 'Iberia',
            'AF': 'Air France',
            'KL': 'KLM',
            'LH': 'Lufthansa',
            'AR': 'Aerolíneas Argentinas',
            'LA': 'LATAM Airlines',
            'CM': 'Copa Airlines',
            'AV': 'Avianca',
            'G3': 'Gol',
            'JJ': 'LATAM Brasil',
            'AD': 'Azul',
            'TP': 'TAP Portugal',
            'UX': 'Air Europa',
            'VY': 'Vueling',
            'NK': 'Spirit Airlines',
            'F9': 'Frontier Airlines',
            'WN': 'Southwest Airlines',
            'B6': 'JetBlue',
            'AS': 'Alaska Airlines',
            'AC': 'Air Canada',
            'EK': 'Emirates',
            'QR': 'Qatar Airways',
            'TK': 'Turkish Airlines',
            'SQ': 'Singapore Airlines',
            'QF': 'Qantas',
            'NZ': 'Air New Zealand',
            'EY': 'Etihad Airways',
            'SU': 'Aeroflot',
            'AZ': 'ITA Airways',
            'LX': 'Swiss',
            'OS': 'Austrian Airlines',
            'SK': 'SAS',
            'AY': 'Finnair',
            'FI': 'Icelandair'
        }
        
        return airline_map.get(carrier_code, carrier_code)
    
    def get_airport_info(self, iata_code):
        """
        Obtiene información de un aeropuerto
        
        Args:
            iata_code: Código IATA del aeropuerto
        
        Returns:
            Diccionario con información del aeropuerto
        """
        self._ensure_authenticated()
        
        url = f"{self.base_url}/v1/reference-data/locations"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        params = {
            'subType': 'AIRPORT',
            'keyword': iata_code
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                return data['data'][0]
            else:
                return None
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error obteniendo información del aeropuerto: {str(e)}")
