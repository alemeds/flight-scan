import psycopg2
from psycopg2.extras import RealDictCursor, Json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    """
    Clase para gestionar la conexión y operaciones con PostgreSQL
    """
    
    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        """
        Inicializa la conexión a la base de datos
        """
        self.connection_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
        self.conn = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """
        Establece conexión con la base de datos
        """
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            print("✅ Conexión exitosa a PostgreSQL")
        except Exception as e:
            print(f"❌ Error conectando a PostgreSQL: {e}")
            raise
    
    def create_tables(self):
        """
        Crea las tablas necesarias si no existen
        """
        create_table_query = """
        CREATE TABLE IF NOT EXISTS flight_searches (
            id SERIAL PRIMARY KEY,
            search_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            origin VARCHAR(3) NOT NULL,
            destination VARCHAR(3) NOT NULL,
            departure_date DATE NOT NULL,
            return_date DATE,
            adults INTEGER DEFAULT 1,
            price DECIMAL(10, 2) NOT NULL,
            currency VARCHAR(3) DEFAULT 'USD',
            airline VARCHAR(50),
            flight_data JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_origin_dest 
        ON flight_searches(origin, destination);
        
        CREATE INDEX IF NOT EXISTS idx_search_timestamp 
        ON flight_searches(search_timestamp);
        
        CREATE INDEX IF NOT EXISTS idx_departure_date 
        ON flight_searches(departure_date);
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(create_table_query)
                self.conn.commit()
                print("✅ Tablas creadas/verificadas correctamente")
        except Exception as e:
            print(f"❌ Error creando tablas: {e}")
            self.conn.rollback()
            raise
    
    def insert_flight_offer(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str],
        price: float,
        currency: str = 'USD',
        airline: str = None,
        flight_data: Dict = None,
        adults: int = 1
    ) -> int:
        """
        Inserta una nueva oferta de vuelo en la base de datos
        """
        insert_query = """
        INSERT INTO flight_searches 
        (origin, destination, departure_date, return_date, adults, price, currency, airline, flight_data)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    insert_query,
                    (origin, destination, departure_date, return_date, adults, 
                     price, currency, airline, Json(flight_data) if flight_data else None)
                )
                flight_id = cur.fetchone()[0]
                self.conn.commit()
                return flight_id
        except Exception as e:
            print(f"❌ Error insertando vuelo: {e}")
            self.conn.rollback()
            raise
    
    def get_price_history(
        self,
        origin: str,
        destination: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Obtiene el historial de precios para una ruta específica
        """
        query = """
        SELECT 
            search_timestamp,
            origin,
            destination,
            departure_date,
            return_date,
            price,
            currency,
            airline,
            adults
        FROM flight_searches
        WHERE origin = %s AND destination = %s
        """
        
        params = [origin, destination]
        
        if date_from:
            query += " AND search_timestamp >= %s"
            params.append(date_from)
        
        if date_to:
            query += " AND search_timestamp <= %s"
            params.append(date_to)
        
        query += " ORDER BY search_timestamp ASC"
        
        try:
            df = pd.read_sql_query(query, self.conn, params=params)
            return df
        except Exception as e:
            print(f"❌ Error obteniendo historial: {e}")
            return pd.DataFrame()
    
    def get_all_searches(self, limit: int = 100) -> pd.DataFrame:
        """
        Obtiene todas las búsquedas recientes
        """
        query = """
        SELECT 
            id,
            search_timestamp,
            origin,
            destination,
            departure_date,
            return_date,
            price,
            currency,
            airline,
            adults
        FROM flight_searches
        ORDER BY search_timestamp DESC
        LIMIT %s
        """
        
        try:
            df = pd.read_sql_query(query, self.conn, params=(limit,))
            return df
        except Exception as e:
            print(f"❌ Error obteniendo búsquedas: {e}")
            return pd.DataFrame()
    
    def get_statistics(
        self,
        origin: str,
        destination: str,
        days_back: int = 30
    ) -> Dict:
        """
        Obtiene estadísticas de precios para una ruta
        """
        query = """
        SELECT 
            MIN(price) as min_price,
            AVG(price) as avg_price,
            MAX(price) as max_price,
            COUNT(*) as total_searches,
            COUNT(DISTINCT airline) as total_airlines
        FROM flight_searches
        WHERE origin = %s 
        AND destination = %s
        AND search_timestamp >= CURRENT_TIMESTAMP - INTERVAL '%s days'
        """
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (origin, destination, days_back))
                result = cur.fetchone()
                return dict(result) if result else {}
        except Exception as e:
            print(f"❌ Error obteniendo estadísticas: {e}")
            return {}
    
    def delete_old_searches(self, days_to_keep: int = 90):
        """
        Elimina búsquedas antiguas para mantener la base limpia
        """
        delete_query = """
        DELETE FROM flight_searches
        WHERE search_timestamp < CURRENT_TIMESTAMP - INTERVAL '%s days'
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(delete_query, (days_to_keep,))
                deleted_count = cur.rowcount
                self.conn.commit()
                print(f"✅ Se eliminaron {deleted_count} registros antiguos")
                return deleted_count
        except Exception as e:
            print(f"❌ Error eliminando registros antiguos: {e}")
            self.conn.rollback()
            return 0
    
    def close(self):
        """
        Cierra la conexión a la base de datos
        """
        if self.conn:
            self.conn.close()
            print("✅ Conexión cerrada")
    
    def __del__(self):
        """
        Destructor para asegurar que la conexión se cierre
        """
        self.close()
