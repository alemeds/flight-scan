"""
Script para probar las conexiones a PostgreSQL y Amadeus
Útil para verificar que todo esté configurado correctamente
"""

import os
import sys
from datetime import datetime, timedelta

def test_database_connection():
    """Prueba la conexión a PostgreSQL"""
    print("\n" + "="*60)
    print("PROBANDO CONEXIÓN A POSTGRESQL")
    print("="*60)
    
    try:
        from database import Database
        
        db_config = {
            'host': os.getenv('DB_HOST', 'dpg-d3g6g1p5pdvs73e8c0rg-a.oregon-postgres.render.com'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'vuelos_9lrw'),
            'user': os.getenv('DB_USER', 'vuelos'),
            'password': os.getenv('DB_PASSWORD', 'FOa7NtnssHMgheHCMilCRXYmLYQn7pko')
        }
        
        print(f"\nConectando a: {db_config['host']}")
        db = Database(**db_config)
        
        # Contar registros
        with db.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM flight_searches")
            count = cur.fetchone()[0]
        
        print(f"✅ Conexión exitosa")
        print(f"📊 Registros en base de datos: {count}")
        
        # Obtener estadísticas básicas
        if count > 0:
            with db.conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        MIN(price) as min_price,
                        AVG(price) as avg_price,
                        MAX(price) as max_price,
                        COUNT(DISTINCT origin || '-' || destination) as routes
                    FROM flight_searches
                """)
                stats = cur.fetchone()
                print(f"\nEstadísticas:")
                print(f"  Precio mínimo: ${stats[0]:.2f}")
                print(f"  Precio promedio: ${stats[1]:.2f}")
                print(f"  Precio máximo: ${stats[2]:.2f}")
                print(f"  Rutas únicas: {stats[3]}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_amadeus_connection():
    """Prueba la conexión a la API de Amadeus"""
    print("\n" + "="*60)
    print("PROBANDO CONEXIÓN A AMADEUS API")
    print("="*60)
    
    try:
        from amadeus_client import AmadeusClient
        
        api_key = os.getenv('AMADEUS_API_KEY', 'KAomv16lpjbjJFAmj42OgXtzEOzCHHlx')
        api_secret = os.getenv('AMADEUS_API_SECRET', 'mwHaoM1gEV9bweN2')
        
        print(f"\nAPI Key: {api_key[:10]}...")
        amadeus = AmadeusClient(api_key=api_key, api_secret=api_secret)
        
        print("✅ Autenticación exitosa")
        print(f"🔑 Token obtenido")
        
        # Hacer una búsqueda de prueba
        print("\nRealizando búsqueda de prueba (EZE → MIA)...")
        departure = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        return_date = (datetime.now() + timedelta(days=37)).strftime('%Y-%m-%d')
        
        offers = amadeus.search_flights(
            origin='EZE',
            destination='MIA',
            departure_date=departure,
            return_date=return_date,
            adults=1,
            max_results=3
        )
        
        if offers:
            print(f"✅ Se encontraron {len(offers)} ofertas")
            print(f"\nEjemplos de ofertas:")
            for i, offer in enumerate(offers[:3], 1):
                print(f"  {i}. {offer.get('airline', 'N/A')} - ${offer['price']:.2f} {offer['currency']}")
        else:
            print("⚠️ No se encontraron ofertas (esto puede ser normal)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_full_workflow():
    """Prueba el flujo completo: consultar API y guardar en BD"""
    print("\n" + "="*60)
    print("PROBANDO FLUJO COMPLETO")
    print("="*60)
    
    try:
        from database import Database
        from amadeus_client import AmadeusClient
        
        # Inicializar
        db = Database(
            host=os.getenv('DB_HOST', 'dpg-d3g6g1p5pdvs73e8c0rg-a.oregon-postgres.render.com'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME', 'vuelos_9lrw'),
            user=os.getenv('DB_USER', 'vuelos'),
            password=os.getenv('DB_PASSWORD', 'FOa7NtnssHMgheHCMilCRXYmLYQn7pko')
        )
        
        amadeus = AmadeusClient(
            api_key=os.getenv('AMADEUS_API_KEY', 'KAomv16lpjbjJFAmj42OgXtzEOzCHHlx'),
            api_secret=os.getenv('AMADEUS_API_SECRET', 'mwHaoM1gEV9bweN2')
        )
        
        # Buscar vuelos
        print("\n1. Buscando vuelos...")
        departure = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        return_date = (datetime.now() + timedelta(days=37)).strftime('%Y-%m-%d')
        
        offers = amadeus.search_flights(
            origin='EZE',
            destination='MIA',
            departure_date=departure,
            return_date=return_date,
            adults=1,
            max_results=2
        )
        
        if not offers:
            print("⚠️ No se encontraron ofertas para guardar")
            return True
        
        print(f"   ✅ {len(offers)} ofertas encontradas")
        
        # Guardar en base de datos
        print("\n2. Guardando en base de datos...")
        saved_count = 0
        for offer in offers:
            try:
                flight_id = db.insert_flight_offer(
                    origin='EZE',
                    destination='MIA',
                    departure_date=departure,
                    return_date=return_date,
                    price=offer['price'],
                    currency=offer['currency'],
                    airline=offer.get('airline', 'Unknown'),
                    flight_data=offer,
                    adults=1
                )
                saved_count += 1
                print(f"   ✅ Oferta guardada con ID: {flight_id}")
            except Exception as e:
                print(f"   ⚠️ Error guardando oferta: {e}")
        
        print(f"\n✅ Flujo completo exitoso: {saved_count}/{len(offers)} ofertas guardadas")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error en flujo completo: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Ejecuta todas las pruebas"""
    print("\n" + "="*60)
    print("FLIGHT SCAN - PRUEBAS DE CONEXIÓN")
    print("="*60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        'database': False,
        'amadeus': False,
        'workflow': False
    }
    
    # Prueba 1: Base de datos
    results['database'] = test_database_connection()
    
    # Prueba 2: API Amadeus
    results['amadeus'] = test_amadeus_connection()
    
    # Prueba 3: Flujo completo (solo si las anteriores pasaron)
    if results['database'] and results['amadeus']:
        print("\n¿Deseas probar el flujo completo (guardará datos de prueba)?")
        response = input("Escribe 'si' para continuar: ").lower()
        if response in ['si', 'sí', 's', 'yes', 'y']:
            results['workflow'] = test_full_workflow()
    
    # Resumen final
    print("\n" + "="*60)
    print("RESUMEN DE PRUEBAS")
    print("="*60)
    print(f"PostgreSQL:      {'✅ PASS' if results['database'] else '❌ FAIL'}")
    print(f"Amadeus API:     {'✅ PASS' if results['amadeus'] else '❌ FAIL'}")
    print(f"Flujo completo:  {'✅ PASS' if results['workflow'] else '⏭️  SKIP'}")
    print("="*60)
    
    if all([results['database'], results['amadeus']]):
        print("\n🎉 ¡Todo está configurado correctamente!")
        print("Puedes ejecutar: streamlit run app.py")
        return 0
    else:
        print("\n⚠️ Algunas pruebas fallaron. Revisa la configuración.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
