"""
Script para monitoreo automático de vuelos
Puede ejecutarse con cron o GitHub Actions
"""

from database import Database
from amadeus_client import AmadeusClient
import os
from datetime import datetime, timedelta

def monitor_flights():
    """Ejecuta el monitoreo de vuelos configurado"""
    
    print(f"🚀 Iniciando monitoreo de vuelos - {datetime.now()}")
    
    # Inicializar conexiones
    try:
        db = Database(
            host=os.getenv('DB_HOST'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        
        amadeus = AmadeusClient(
            api_key=os.getenv('AMADEUS_API_KEY'),
            api_secret=os.getenv('AMADEUS_API_SECRET')
        )
        
        print("✅ Conexiones inicializadas correctamente")
        
    except Exception as e:
        print(f"❌ Error inicializando conexiones: {str(e)}")
        return
    
    # Configuración de rutas a monitorear
    # Personaliza estas rutas según tus necesidades
    routes = [
        {
            'origin': 'EZE',
            'destination': 'MIA',
            'days_ahead': 30,
            'return_days': 7
        },
        {
            'origin': 'EZE',
            'destination': 'MAD',
            'days_ahead': 45,
            'return_days': 10
        },
        {
            'origin': 'AEP',
            'destination': 'SCL',
            'days_ahead': 20,
            'return_days': 5
        }
    ]
    
    total_saved = 0
    
    # Procesar cada ruta
    for route in routes:
        try:
            print(f"\n🔍 Buscando: {route['origin']} → {route['destination']}")
            
            # Calcular fechas
            departure = (datetime.now() + timedelta(days=route['days_ahead'])).strftime('%Y-%m-%d')
            return_date = (datetime.now() + timedelta(days=route['days_ahead'] + route['return_days'])).strftime('%Y-%m-%d')
            
            # Buscar vuelos
            offers = amadeus.search_flights(
                origin=route['origin'],
                destination=route['destination'],
                departure_date=departure,
                return_date=return_date,
                adults=1,
                max_results=10
            )
            
            # Guardar ofertas en la base de datos
            saved_count = 0
            for offer in offers:
                try:
                    db.insert_flight_offer(
                        origin=route['origin'],
                        destination=route['destination'],
                        departure_date=departure,
                        return_date=return_date,
                        adults=1,
                        price=offer['price'],
                        currency=offer['currency'],
                        airline=offer.get('airline', 'N/A'),
                        flight_data=offer
                    )
                    saved_count += 1
                except Exception as e:
                    print(f"   ⚠️  Error guardando oferta: {str(e)}")
            
            total_saved += saved_count
            print(f"   ✅ {saved_count} ofertas guardadas")
            
        except Exception as e:
            print(f"   ❌ Error procesando ruta {route['origin']}-{route['destination']}: {str(e)}")
    
    print(f"\n🎉 Monitoreo completado: {total_saved} ofertas guardadas en total")
    print(f"⏰ Finalizado: {datetime.now()}")

if __name__ == "__main__":
    monitor_flights()
