"""
Script para inicializar la base de datos PostgreSQL
Crea las tablas necesarias y verifica la conexión
"""

import os
import sys
from database import Database

def main():
    print("=" * 60)
    print("FLIGHT SCAN - Inicialización de Base de Datos")
    print("=" * 60)
    print()
    
    # Leer variables de entorno o usar valores por defecto
    db_config = {
        'host': os.getenv('DB_HOST', 'dpg-d3g6g1p5pdvs73e8c0rg-a.oregon-postgres.render.com'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'vuelos_9lrw'),
        'user': os.getenv('DB_USER', 'vuelos'),
        'password': os.getenv('DB_PASSWORD', 'FOa7NtnssHMgheHCMilCRXYmLYQn7pko')
    }
    
    print("Configuración de base de datos:")
    print(f"  Host: {db_config['host']}")
    print(f"  Port: {db_config['port']}")
    print(f"  Database: {db_config['database']}")
    print(f"  User: {db_config['user']}")
    print()
    
    try:
        # Inicializar base de datos
        print("Conectando a PostgreSQL...")
        db = Database(**db_config)
        
        print()
        print("=" * 60)
        print("✅ ÉXITO: Base de datos inicializada correctamente")
        print("=" * 60)
        print()
        print("La tabla 'flight_searches' está lista para usar.")
        print("Puedes ejecutar ahora: streamlit run app.py")
        print()
        
        # Mostrar estadísticas si hay datos
        try:
            import psycopg2
            with db.conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM flight_searches")
                count = cur.fetchone()[0]
                print(f"Registros existentes en la base: {count}")
        except:
            pass
        
        db.close()
        return 0
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ERROR: No se pudo inicializar la base de datos")
        print("=" * 60)
        print()
        print(f"Detalles del error: {str(e)}")
        print()
        print("Verifica que:")
        print("  1. Las credenciales sean correctas")
        print("  2. La base de datos en Render esté activa")
        print("  3. Tu IP esté permitida en el firewall de Render")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
