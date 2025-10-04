import requests
from typing import List, Dict, Optional
from datetime import datetime
import time

class AmadeusClient:
    """
    Cliente para interactuar con la API de Amadeus Flight Offers
    """
    
    BASE_URL = "https://test.api.amadeus.com"
    TOKEN_URL = f"{BASE_URL}/v1/security/oauth2/token"
    FLIGHT_OFFERS_URL = f"{BASE_URL}/v2/shopping/flight-offers"
    
    def __init__(self, api_key: str, api_secret: str):
        """
        Inicializa el cliente de Amadeus
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = None
        self.token_expires_at = None
        self._get_access_token()
    
    def _get_access_token(self):
        """
        Obtiene un token de acceso de Amadeus
        """
        try:
            response = requests.post(
                self.TOKEN_URL,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.api_key,
                    'client_secret': self.api_secret
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data['access_token']
                # El token expira en segundos, lo guardamos
                expires_in = data.get('expires_in', 1799)
                self.token_expires_at = time.time() + expires_in
                print("✅ Token de Amadeus obtenido exitosamente")
            else:
                raise Exception(f"Error obteniendo token: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Error en autenticación Amadeus: {e}")
            raise
    
    def _ensure_valid_token(self):
        """
        Verifica que el token sea válido, lo renueva si es necesario
        """
        if not self.access_token or time.time() >= self.token_expires_at - 60:
            self._get_access_token()
    
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
            departure_date: Fecha de ida en formato 'YYYY-MM-DD'
            return_date: Fecha de vuelta en formato 'YYYY-MM-DD' (opcional)
            adults: Número de adultos
            max_results: Número máximo de resultados
            
        Returns:
            Lista de ofertas de vuelos
        """
        self._ensure_valid_token()
        
        params = {
            'originLocationCode': origin,
            'destinationLocationCode': destination,
            'departureDate': departure_date,
            'adults': adults,
            'max': max_results,
            'currencyCode': 'USD'
        }
        
        if return_date:
            params['returnDate'] = return_date
        
        try:
            response = requests.get(
                self.FLIGHT_OFFERS_URL,
                headers={
                    'Authorization': f'Bearer {self.access_token}'
                },
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                offers = self._parse_flight_offers(data)
                print(f"✅ Se encontraron {len(offers)} ofertas")
                return offers
            else:
                print(f"❌ Error en búsqueda: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Error buscando vuelos: {e}")
            return []
    
    def _parse_flight_offers(self, data: Dict) -> List[Dict]:
        """
        Parsea la respuesta de Amadeus a un formato simplificado
        """
        offers = []
        
        if 'data' not in data:
            return offers
        
        for offer in data['data']:
            try:
                # Extraer información básica
                price_info = offer.get('price', {})
                price = float(price_info.get('total', 0))
                currency = price_info.get('currency', 'USD')
                
                # Extraer información de itinerarios
                itineraries = offer.get('itineraries', [])
                
                # Obtener la aerolínea del primer segmento
                airline = 'Unknown'
                if itineraries and len(itineraries) > 0:
                    segments = itineraries[0].get('segments', [])
                    if segments and len(segments) > 0:
                        carrier_code = segments[0].get('carrierCode', 'XX')
                        airline = self._get_airline_name(carrier_code)
                
                # Crear oferta simplificada
                parsed_offer = {
                    'id': offer.get('id'),
                    'price': price,
                    'currency': currency,
                    'airline': airline,
                    'number_of_bookable_seats': offer.get('numberOfBookableSeats', 0),
                    'itineraries': itineraries,
                    'raw_data': offer  # Guardar datos completos
                }
                
                offers.append(parsed_offer)
                
            except Exception as e:
                print(f"⚠️ Error parseando oferta: {e}")
                continue
        
        return offers
    
    def _get_airline_name(self, carrier_code: str) -> str:
        """
        Convierte código de aerolínea a nombre
        (Lista simplificada, se puede expandir)
        """
        airlines = {
            'AA': 'American Airlines',
            'UA': 'United Airlines',
            'DL': 'Delta Air Lines',
            'AR': 'Aerolíneas Argentinas',
            'LA': 'LATAM Airlines',
            'CM': 'Copa Airlines',
            'AV': 'Avianca',
            'G3': 'Gol',
            'JJ': 'LATAM Brasil',
            'IB': 'Iberia',
            'AF': 'Air France',
            'KL': 'KLM',
            'LH': 'Lufthansa',
            'BA': 'British Airways',
            'TP': 'TAP Portugal',
            'EK': 'Emirates',
            'QR': 'Qatar Airways',
            'TK': 'Turkish Airlines'
        }
        
        return airlines.get(carrier_code, f'Airline {carrier_code}')
    
    def get_flight_details(self, offer_id: str) -> Optional[Dict]:
        """
        Obtiene detalles completos de una oferta específica
        """
        self._ensure_valid_token()
        
        url = f"{self.FLIGHT_OFFERS_URL}/{offer_id}"
        
        try:
            response = requests.get(
                url,
                headers={
                    'Authorization': f'Bearer {self.access_token}'
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error obteniendo detalles: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error obteniendo detalles del vuelo: {e}")
            return None
