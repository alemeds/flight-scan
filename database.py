import psycopg2
from psycopg2.extras import RealDictCursor, Json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json

class Database:
    """Clase para manejar operaciones de base de datos PostgreSQL"""
    
    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        """
        Inicializa la conexión a PostgreSQL
        
        Args:
            host: Host de la base de datos
            port: Puerto de PostgreSQL (default 5432)
            database: Nombre de la base de datos
            user: Usuario de PostgreSQL
            password: Contraseña del usuario
        """
        self.connection_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
        self._create_tables()
    
    def _get_connection(self):
        """Crea una nueva conexión a la base de datos"""
        return psycopg2.connect(**self.connection_params)
    
    def _create_tables(self):
        """Crea las tablas necesarias si no existen"""
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
            airline VARCHAR(100),
            flight_data JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_origin_dest ON flight_searches(origin, destination);
        CREATE INDEX IF NOT EXISTS idx_search_timestamp ON flight_searches(search_timestamp);
        CREATE INDEX IF NOT EXISTS idx_departure_date ON flight_searches(departure_date);
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(create_table_query)
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error creando tablas: {str(e)}")
            raise
    
    def insert_flight_offer(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str],
        adults: int,
        price: float,
        currency: str,
        airline: Optional[str],
        flight_data: Dict
    ) -> int:
        """
        Inserta una oferta de vuelo en la base de datos
        
        Args:
            origin: Código IATA de origen
            destination: Código IATA de destino
            departure_date: Fecha de salida (YYYY-MM-DD)
            return_date: Fecha de regreso (YYYY-MM-DD) o None
            adults: Número de adultos
            price: Precio del vuelo
            currency: Moneda (USD, EUR, etc.)
            airline: Nombre de la aerolínea
            flight_data: Datos completos del vuelo en formato dict
            
        Returns:
            ID del registro insertado
        """
        insert_query = """
        INSERT INTO flight_searches 
        (origin, destination, departure_date, return_date, adults, price, currency, airline, flight_data)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                insert_query,
                (origin, destination, departure_date, return_date, adults, 
                 price, currency, airline, Json(flight_data))
            )
            
            flight_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            
            return flight_id
            
        except Exception as e:
            print(f"Error insertando oferta: {str(e)}")
            raise
    
    def get_recent_searches(self, limit: int = 100) -> List[Dict]:
        """
        Obtiene las búsquedas más recientes
        
        Args:
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de diccionarios con los datos de búsquedas
        """
        query = """
        SELECT 
            id,
            search_timestamp,
            origin,
            destination,
            departure_date,
            return_date,
            adults,
            price,
            currency,
            airline,
            created_at
        FROM flight_searches
        ORDER BY search_timestamp DESC
        LIMIT %s;
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, (limit,))
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Convertir a lista de diccionarios
            return [dict(row) for row in results]
            
        except Exception as e:
            print(f"Error obteniendo búsquedas recientes: {str(e)}")
            return []
    
    def get_unique_routes(self) -> List[Tuple[str, str]]:
        """
        Obtiene todas las rutas únicas (origen-destino) en la base de datos
        
        Returns:
            Lista de tuplas (origen, destino)
        """
        query = """
        SELECT DISTINCT origin, destination
        FROM flight_searches
        ORDER BY origin, destination;
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            
            routes = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return routes
            
        except Exception as e:
            print(f"Error obteniendo rutas: {str(e)}")
            return []
    
    def get_searches_by_route(
        self,
        origin: str,
        destination: str,
        days: int = 30
    ) -> List[Dict]:
        """
        Obtiene búsquedas para una ruta específica en los últimos N días
        
        Args:
            origin: Código IATA de origen
            destination: Código IATA de destino
            days: Número de días hacia atrás
            
        Returns:
            Lista de diccionarios con los datos
        """
        query = """
        SELECT 
            id,
            search_timestamp,
            origin,
            destination,
            departure_date,
            return_date,
            adults,
            price,
            currency,
            airline,
            created_at
        FROM flight_searches
        WHERE origin = %s 
          AND destination = %s
          AND search_timestamp >= %s
        ORDER BY search_timestamp DESC;
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cutoff_date = datetime.now() - timedelta(days=days)
            cursor.execute(query, (origin, destination, cutoff_date))
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            print(f"Error obteniendo búsquedas por ruta: {str(e)}")
            return []
    
    def get_price_statistics(
        self,
        origin: str,
        destination: str,
        days: int = 30
    ) -> Dict:
        """
        Obtiene estadísticas de precios para una ruta
        
        Args:
            origin: Código IATA de origen
            destination: Código IATA de destino
            days: Número de días hacia atrás
            
        Returns:
            Diccionario con estadísticas (min, max, avg, count)
        """
        query = """
        SELECT 
            MIN(price) as min_price,
            MAX(price) as max_price,
            AVG(price) as avg_price,
            COUNT(*) as search_count
        FROM flight_searches
        WHERE origin = %s 
          AND destination = %s
          AND search_timestamp >= %s;
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cutoff_date = datetime.now() - timedelta(days=days)
            cursor.execute(query, (origin, destination, cutoff_date))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return dict(result) if result else {}
            
        except Exception as e:
            print(f"Error obteniendo estadísticas: {str(e)}")
            return {}
    
    def get_cheapest_by_airline(
        self,
        origin: str,
        destination: str,
        days: int = 30
    ) -> List[Dict]:
        """
        Obtiene el precio más barato por aerolínea para una ruta
        
        Args:
            origin: Código IATA de origen
            destination: Código IATA de destino
            days: Número de días hacia atrás
            
        Returns:
            Lista con el precio mínimo por aerolínea
        """
        query = """
        SELECT 
            airline,
            MIN(price) as min_price,
            COUNT(*) as occurrences
        FROM flight_searches
        WHERE origin = %s 
          AND destination = %s
          AND search_timestamp >= %s
          AND airline IS NOT NULL
        GROUP BY airline
        ORDER BY min_price ASC;
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cutoff_date = datetime.now() - timedelta(days=days)
            cursor.execute(query, (origin, destination, cutoff_date))
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            print(f"Error obteniendo precios por aerolínea: {str(e)}")
            return []
    
    def delete_old_searches(self, days: int = 90) -> int:
        """
        Elimina búsquedas más antiguas que N días
        
        Args:
            days: Número de días (registros más antiguos se eliminan)
            
        Returns:
            Número de registros eliminados
        """
        query = """
        DELETE FROM flight_searches
        WHERE search_timestamp < %s;
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days)
            cursor.execute(query, (cutoff_date,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            return deleted_count
            
        except Exception as e:
            print(f"Error eliminando registros antiguos: {str(e)}")
            return 0
    
    def get_flight_by_id(self, flight_id: int) -> Optional[Dict]:
        """
        Obtiene un vuelo específico por ID
        
        Args:
            flight_id: ID del registro
            
        Returns:
            Diccionario con los datos del vuelo o None
        """
        query = """
        SELECT 
            id,
            search_timestamp,
            origin,
            destination,
            departure_date,
            return_date,
            adults,
            price,
            currency,
            airline,
            flight_data,
            created_at
        FROM flight_searches
        WHERE id = %s;
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, (flight_id,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return dict(result) if result else None
            
        except Exception as e:
            print(f"Error obteniendo vuelo por ID: {str(e)}")
            return None
    
    def test_connection(self) -> bool:
        """
        Prueba la conexión a la base de datos
        
        Returns:
            True si la conexión es exitosa, False en caso contrario
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error de conexión: {str(e)}")
            return False
