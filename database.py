import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import streamlit as st
from datetime import datetime
import json

class Database:
    def __init__(self, host, port, database, user, password):
        """Inicializa la conexión a la base de datos"""
        try:
            self.conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password
            )
            st.success("✅ Conexión exitosa a PostgreSQL")
        except Exception as e:
            st.error(f"❌ Error conectando a la base de datos: {e}")
            raise
    
    def create_tables(self):
        """Crea las tablas necesarias si no existen"""
        try:
            cursor = self.conn.cursor()
            
            # Tabla de búsquedas de vuelos
            cursor.execute("""
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
                )
            """)
            
            # Crear índices para mejorar rendimiento
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_origin_dest 
                ON flight_searches(origin, destination)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_search_timestamp 
                ON flight_searches(search_timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_departure_date 
                ON flight_searches(departure_date)
            """)
            
            self.conn.commit()
            cursor.close()
            st.success("✅ Tablas creadas/verificadas correctamente")
            
        except Exception as e:
            st.error(f"❌ Error creando tablas: {e}")
            raise
    
    def insert_flight_offer(self, origin, destination, departure_date, 
                           return_date, adults, price, currency, 
                           airline=None, flight_data=None):
        """Inserta una oferta de vuelo en la base de datos"""
        try:
            cursor = self.conn.cursor()
            
            # Convertir flight_data a JSON si es necesario
            flight_data_json = json.dumps(flight_data) if flight_data else None
            
            cursor.execute("""
                INSERT INTO flight_searches 
                (origin, destination, departure_date, return_date, 
                 adults, price, currency, airline, flight_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (origin, destination, departure_date, return_date, 
                  adults, price, currency, airline, flight_data_json))
            
            self.conn.commit()
            cursor.close()
            
        except Exception as e:
            st.error(f"❌ Error insertando oferta: {e}")
            self.conn.rollback()
            raise
    
    def get_flights_by_route(self, origin=None, destination=None, 
                            from_date=None, to_date=None, limit=100):
        """Obtiene vuelos filtrados por ruta y fechas"""
        try:
            query = """
                SELECT id, search_timestamp, origin, destination, 
                       departure_date, return_date, adults, price, 
                       currency, airline
                FROM flight_searches
                WHERE 1=1
            """
            params = []
            
            if origin:
                query += " AND origin = %s"
                params.append(origin)
            
            if destination:
                query += " AND destination = %s"
                params.append(destination)
            
            if from_date:
                query += " AND search_timestamp >= %s"
                params.append(from_date)
            
            if to_date:
                query += " AND search_timestamp <= %s"
                params.append(to_date)
            
            query += " ORDER BY search_timestamp DESC LIMIT %s"
            params.append(limit)
            
            df = pd.read_sql_query(query, self.conn, params=params)
            return df
            
        except Exception as e:
            st.error(f"❌ Error consultando vuelos: {e}")
            return pd.DataFrame()
    
    def get_available_flights(self, origin=None, destination=None, 
                             from_date=None, to_date=None, limit=100):
        """Alias de get_flights_by_route para compatibilidad"""
        return self.get_flights_by_route(origin, destination, from_date, to_date, limit)
    
    def get_price_history(self, origin, destination, days=30):
        """Obtiene el historial de precios para una ruta específica"""
        try:
            query = """
                SELECT search_timestamp, price, currency, airline
                FROM flight_searches
                WHERE origin = %s AND destination = %s
                  AND search_timestamp >= NOW() - INTERVAL '%s days'
                ORDER BY search_timestamp ASC
            """
            
            df = pd.read_sql_query(query, self.conn, params=(origin, destination, days))
            return df
            
        except Exception as e:
            st.error(f"❌ Error obteniendo historial de precios: {e}")
            return pd.DataFrame()
    
    def get_recent_searches(self, limit=10):
        """Obtiene las búsquedas más recientes"""
        try:
            query = """
                SELECT origin, destination, departure_date, return_date,
                       price, currency, airline, search_timestamp
                FROM flight_searches
                ORDER BY search_timestamp DESC
                LIMIT %s
            """
            
            df = pd.read_sql_query(query, self.conn, params=(limit,))
            return df
            
        except Exception as e:
            st.error(f"❌ Error obteniendo búsquedas recientes: {e}")
            return pd.DataFrame()
    
    def get_price_statistics(self, origin, destination):
        """Obtiene estadísticas de precios para una ruta específica"""
        try:
            query = """
                SELECT 
                    MIN(price) as min_price,
                    MAX(price) as max_price,
                    AVG(price) as avg_price,
                    COUNT(*) as total_searches,
                    currency
                FROM flight_searches
                WHERE origin = %s AND destination = %s
                GROUP BY currency
            """
            
            df = pd.read_sql_query(query, self.conn, params=(origin, destination))
            return df
            
        except Exception as e:
            st.error(f"❌ Error obteniendo estadísticas: {e}")
            return pd.DataFrame()
    
    def get_airlines_by_route(self, origin, destination):
        """Obtiene todas las aerolíneas que operan una ruta específica"""
        try:
            query = """
                SELECT DISTINCT airline, COUNT(*) as frequency
                FROM flight_searches
                WHERE origin = %s AND destination = %s 
                  AND airline IS NOT NULL
                GROUP BY airline
                ORDER BY frequency DESC
            """
            
            df = pd.read_sql_query(query, self.conn, params=(origin, destination))
            return df
            
        except Exception as e:
            st.error(f"❌ Error obteniendo aerolíneas: {e}")
            return pd.DataFrame()
    
    def delete_old_searches(self, days=90):
        """Elimina búsquedas más antiguas que X días"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                DELETE FROM flight_searches
                WHERE search_timestamp < NOW() - INTERVAL '%s days'
            """, (days,))
            
            deleted_count = cursor.rowcount
            self.conn.commit()
            cursor.close()
            
            return deleted_count
            
        except Exception as e:
            st.error(f"❌ Error eliminando búsquedas antiguas: {e}")
            self.conn.rollback()
            return 0
    
    def export_to_csv(self, origin=None, destination=None):
        """Exporta datos a CSV"""
        try:
            df = self.get_flights_by_route(origin, destination, limit=10000)
            
            if not df.empty:
                csv = df.to_csv(index=False)
                return csv
            else:
                return None
                
        except Exception as e:
            st.error(f"❌ Error exportando a CSV: {e}")
            return None
    
    def close(self):
        """Cierra la conexión a la base de datos"""
        try:
            if self.conn:
                self.conn.close()
        except Exception as e:
            st.error(f"❌ Error cerrando conexión: {e}")
