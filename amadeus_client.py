import requests
import json
from datetime import datetime
from typing import List, Dict, Optional

class AmadeusClient:
    """Cliente para interactuar con la API de Amadeus"""
    
    def __init__(self, api_key: str, api_secret: str):
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
            response = requests.post(auth_url, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            
            # Calcular tiempo de expiración (generalmente 1800 segundos)
            expires_in = token_data.get('expires_in', 1800)
            self.token_expiry = datetime.now().timestamp() + expires_in
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error obteniendo token de autenticación: {str(e)}")
    
    def _is_token_valid(self) -> bool:
        """Verifica si el token actual es válido"""
        if not self.access_token or not self.token_expiry:
            return False
        
        # Renovar si faltan menos de 60 segundos
        return datetime.now().timestamp() < (self.token_expiry - 60)
    
    def _ensure_authenticated(self):
        """Asegura que haya un token válido"""
        if not self._is_token_valid():
            self._authenticate()
    
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
            raise Exception("Timeout buscando vuelos. La API de Amadeus no respondió a tiempo.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error buscando vuelos: {str(e)}")
    
    def _process_flight_offer(self, offer: Dict) -> Optional[Dict]:
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
            
            # Validar precio
            if price <= 0:
                return None
            
            # Extraer información de los segmentos de vuelo
            itineraries = offer.get('itineraries', [])
            
            if not itineraries:
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
            
        except Exception as e:
            # En caso de error, retornar None para evitar datos corruptos
            print(f"Error procesando oferta: {str(e)}")
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
            
        except Exception:
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
            'keyword': iata_code
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                return data['data'][0]
            else:
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error obteniendo información del aeropuerto: {str(e)}")
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
