"""
Script de monitoreo automático de tarifas de vuelos
Puede ejecutarse con cron jobs o GitHub Actions
"""

import os
import sys
from datetime import datetime, timedelta
from database import Database
from amadeus_client import AmadeusClient
import time

def load_config():
    """Carga la configuración desde variables de entorno"""
    return {
        'db': {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        },
        'amadeus': {
            'api_key': os.getenv('AMADEUS_API_KEY'),
            'api_secret': os.getenv('AMADEUS_API_SECRET')
        }
    }

def validate_config(config):
    """Valida que todas las credenciales estén presentes"""
    required_db = ['host', 'database', 'user', 'password']
    required_amadeus = ['api_key', 'api_secret']
    
    for key in required_db:
        if not config['db'].get(key):
            raise ValueError(f"Falta configuración de DB: {key}")
    
    for key in required_amadeus:
        if not config['amadeus'].get(key):
            raise ValueError(f"Falta configuración de Amadeus: {key}")

def define_routes():
    """
    Define las rutas a monitorear
    Puedes personalizar esta función según tus necesidades
    """
    routes = [
        {
            'origin': 'EZE',
            'destination': 'MIA',
            'days_ahead': 30,
            'adults': 1,
            'description': 'Buenos Aires → Miami'
        },
        {
            'origin': 'EZE',
            'destination': 'MAD',
            'days_ahead': 45,
            'adults': 1,
            'description': 'Buenos Aires → Madrid'
        },
        {
            'origin': 'AEP',
            'destination': 'SCL',
            'days_ahead': 20,
            'adults': 1,
            'description': 'Buenos Aires Aeroparque → Santiago'
        },
        {
            'origin': 'EZE',
            'destination': 'NYC',
            'days_ahead': 35,
            'adults': 1,
            'description': 'Buenos Aires → Nueva York'
        }
    ]
    
    return routes

def monitor_route(db, amadeus, route):
    """
    Monitorea una ruta específica
    """
    print(f"\n{'='*60}")
    print(f"Monitoreando: {route['description']}")
    print(f"{'='*60}")
    
    # Calcular fechas
    departure_date = (datetime.now() + timedelta(days=route['days_ahead'])).strftime('%Y-%m-%d')
    return_date = (datetime.now() + timedelta(days=route['days_ahead'] + 7)).strftime('%Y-%m-%d')
    
    print(f"Fecha de ida: {departure_date}")
    print(f"Fecha de vuelta: {return_date}")
    print(f"Pasajeros: {route['adults']}")
    print()
    
    try:
        # Buscar vuelos
        print("Consultando API de Amadeus...")
        offers = amadeus.search_flights(
            origin=route['origin'],
            destination=route['destination'],
            departure_date=departure_date,
            return_date=return_date,
            adults=route['adults'],
            max_results=10
        )
        
        if not offers:
            print("⚠️ No se encontraron ofertas para esta ruta")
            return 0
        
        # Guardar en base de datos
        saved_count = 0
        for offer in offers:
            try:
                db.insert_flight_offer(
                    origin=route['origin'],
                    destination=route['destination'],
                    departure_date=departure_date,
                    return_date=return_date,
                    price=offer['price'],
                    currency=offer['currency'],
                    airline=offer.get('airline', 'Unknown'),
                    flight_data=offer,
                    adults=route['adults']
                )
                saved_count += 1
            except Exception as e:
                print(f"⚠️ Error guardando oferta: {e}")
        
        # Mostrar resumen
        print(f"✅ {saved_count} ofertas guardadas exitosamente")
        
        # Mostrar precios
        prices = [offer['price'] for offer in offers]
        print(f"\nPrecios encontrados:")
        print(f"  Mínimo: ${min(prices):.2f}")
        print(f"  Promedio: ${sum(prices)/len(prices):.2f}")
        print(f"  Máximo: ${max(prices):.2f}")
        
        return saved_count
        
    except Exception as e:
        print(f"❌ Error monitoreando ruta: {e}")
        return 0

def main():
    """
    Función principal del script
    """
    print("\n" + "="*60)
    print("FLIGHT SCAN - Monitor Automático de Tarifas")
    print("="*60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # Cargar y validar configuración
        print("\n1. Cargando configuración...")
        config = load_config()
        validate_config(config)
        print("✅ Configuración cargada correctamente")
        
        # Conectar a base de datos
        print("\n2. Conectando a PostgreSQL...")
        db = Database(**config['db'])
        print("✅ Conexión establecida")
        
        # Inicializar cliente Amadeus
        print("\n3. Inicializando cliente Amadeus...")
        amadeus = AmadeusClient(**config['amadeus'])
        print("✅ Cliente Amadeus listo")
        
        # Obtener rutas a monitorear
        print("\n4. Cargando rutas a monitorear...")
        routes = define_routes()
        print(f"✅ {len(routes)} rutas configuradas")
        
        # Monitorear cada ruta
        print("\n5. Iniciando monitoreo...")
        total_saved = 0
        
        for i, route in enumerate(routes, 1):
            print(f"\nRuta {i}/{len(routes)}")
            saved = monitor_route(db, amadeus, route)
            total_saved += saved
            
            # Pausa entre consultas para no saturar la API
            if i < len(routes):
                print("\nEsperando 5 segundos antes de la siguiente consulta...")
                time.sleep(5)
        
        # Resumen final
        print("\n" + "="*60)
        print("RESUMEN DEL MONITOREO")
        print("="*60)
        print(f"Total de ofertas guardadas: {total_saved}")
        print(f"Rutas monitoreadas: {len(routes)}")
        print(f"Timestamp final: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        print("\n✅ Monitoreo completado exitosamente\n")
        
        # Cerrar conexión
        db.close()
        
        return 0
        
    except ValueError as e:
        print(f"\n❌ Error de configuración: {e}")
        print("\nAsegúrate de definir todas las variables de entorno:")
        print("  - DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
        print("  - AMADEUS_API_KEY, AMADEUS_API_SECRET")
        return 1
        
    except Exception as e:
        print(f"\n❌ Error ejecutando monitoreo: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
