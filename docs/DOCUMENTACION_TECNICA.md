# Documentación Técnica - Flight Scan

Documentación detallada de los módulos, clases y funciones del proyecto.

## Tabla de Contenidos

- [Módulo: database.py](#módulo-databasepy)
- [Módulo: amadeus_client.py](#módulo-amadeus_clientpy)
- [Módulo: app.py](#módulo-apppy)
- [Estructuras de Datos](#estructuras-de-datos)
- [Flujo de Datos](#flujo-de-datos)
- [Variables de Entorno](#variables-de-entorno)

---

## Módulo: database.py

Gestiona todas las operaciones con PostgreSQL.

### Clase: Database

```python
class Database:
    def __init__(self, host: str, port: int, database: str, user: str, password: str)
```

**Descripción**: Inicializa la conexión a PostgreSQL y crea las tablas necesarias.

**Parámetros**:
- `host` (str): Host de la base de datos
- `port` (int): Puerto (default: 5432)
- `database` (str): Nombre de la base de datos
- `user` (str): Usuario de PostgreSQL
- `password` (str): Contraseña del usuario

**Ejemplo**:
```python
db = Database(
    host="localhost",
    port=5432,
    database="vuelos_db",
    user="postgres",
    password="mi_password"
)
```

---

### Métodos Principales

#### insert_flight_offer()

```python
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
) -> int
```

**Descripción**: Inserta una oferta de vuelo en la base de datos.

**Parámetros**:
- `origin` (str): Código IATA de origen (3 letras)
- `destination` (str): Código IATA de destino (3 letras)
- `departure_date` (str): Fecha de salida (YYYY-MM-DD)
- `return_date` (str, optional): Fecha de regreso (YYYY-MM-DD)
- `adults` (int): Número de adultos (1-9)
- `price` (float): Precio del vuelo
- `currency` (str): Código de moneda (USD, EUR, etc.)
- `airline` (str, optional): Nombre de la aerolínea
- `flight_data` (dict): Datos completos del vuelo

**Retorna**: ID del registro insertado (int)

**Excepciones**: `Exception` si falla la inserción

**Ejemplo**:
```python
flight_id = db.insert_flight_offer(
    origin="EZE",
    destination="MIA",
    departure_date="2025-12-15",
    return_date="2025-12-22",
    adults=2,
    price=1250.50,
    currency="USD",
    airline="American Airlines",
    flight_data={
        'id': 'FLIGHT123',
        'duration': '10h 30m',
        'stops': 1
    }
)
```

---

#### get_recent_searches()

```python
def get_recent_searches(self, limit: int = 100) -> List[Dict]
```

**Descripción**: Obtiene las búsquedas más recientes ordenadas por fecha.

**Parámetros**:
- `limit` (int): Número máximo de registros (default: 100)

**Retorna**: Lista de diccionarios con campos:
- `id` (int)
- `search_timestamp` (datetime)
- `origin` (str)
- `destination` (str)
- `departure_date` (date)
- `return_date` (date)
- `adults` (int)
- `price` (float)
- `currency` (str)
- `airline` (str)
- `created_at` (datetime)

**Ejemplo**:
```python
recent = db.get_recent_searches(limit=50)
for search in recent:
    print(f"{search['origin']} → {search['destination']}: ${search['price']}")
```

---

#### get_unique_routes()

```python
def get_unique_routes(self) -> List[Tuple[str, str]]
```

**Descripción**: Obtiene todas las rutas únicas almacenadas.

**Retorna**: Lista de tuplas `(origen, destino)`

**Ejemplo**:
```python
routes = db.get_unique_routes()
# [('EZE', 'MIA'), ('EZE', 'MAD'), ('AEP', 'SCL')]
```

---

#### get_searches_by_route()

```python
def get_searches_by_route(
    self,
    origin: str,
    destination: str,
    days: int = 30
) -> List[Dict]
```

**Descripción**: Obtiene búsquedas para una ruta específica en los últimos N días.

**Parámetros**:
- `origin` (str): Código IATA de origen
- `destination` (str): Código IATA de destino
- `days` (int): Días hacia atrás (default: 30)

**Retorna**: Lista de diccionarios con los mismos campos que `get_recent_searches()`

**Ejemplo**:
```python
route_data = db.get_searches_by_route("EZE", "MIA", days=60)
prices = [search['price'] for search in route_data]
avg_price = sum(prices) / len(prices)
```

---

#### get_price_statistics()

```python
def get_price_statistics(
    self,
    origin: str,
    destination: str,
    days: int = 30
) -> Dict
```

**Descripción**: Obtiene estadísticas de precios para una ruta.

**Retorna**: Diccionario con:
- `min_price` (float): Precio mínimo
- `max_price` (float): Precio máximo
- `avg_price` (float): Precio promedio
- `search_count` (int): Número de búsquedas

**Ejemplo**:
```python
stats = db.get_price_statistics("EZE", "MIA")
print(f"Mín: ${stats['min_price']}, Máx: ${stats['max_price']}")
```

---

#### get_cheapest_by_airline()

```python
def get_cheapest_by_airline(
    self,
    origin: str,
    destination: str,
    days: int = 30
) -> List[Dict]
```

**Descripción**: Obtiene el precio más bajo por aerolínea.

**Retorna**: Lista de diccionarios con:
- `airline` (str): Nombre de la aerolínea
- `min_price` (float): Precio mínimo encontrado
- `occurrences` (int): Número de veces encontrada

**Ejemplo**:
```python
cheapest = db.get_cheapest_by_airline("EZE", "MIA")
for airline in cheapest:
    print(f"{airline['airline']}: ${airline['min_price']}")
```

---

## Módulo: amadeus_client.py

Cliente para interactuar con la API de Amadeus.

### Clase: AmadeusClient

```python
class AmadeusClient:
    def __init__(self, api_key: str, api_secret: str)
```

**Descripción**: Inicializa el cliente y obtiene token de autenticación.

**Parámetros**:
- `api_key` (str): API Key de Amadeus
- `api_secret` (str): API Secret de Amadeus

**Atributos**:
- `base_url` (str): URL base de la API (test o production)
- `access_token` (str): Token OAuth2 activo
- `token_expiry` (timestamp): Expiración del token

**Excepciones**: `Exception` si falla la autenticación

---

### Métodos Principales

#### search_flights()

```python
def search_flights(
    self,
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    max_results: int = 10
) -> List[Dict]
```

**Descripción**: Busca ofertas de vuelos usando la API de Amadeus.

**Parámetros**:
- `origin` (str): Código IATA de origen (ej: 'EZE')
- `destination` (str): Código IATA de destino (ej: 'MIA')
- `departure_date` (str): Fecha de salida (YYYY-MM-DD)
- `return_date` (str, optional): Fecha de regreso (YYYY-MM-DD)
- `adults` (int): Número de adultos (1-9, default: 1)
- `max_results` (int): Máximo de resultados (default: 10)

**Retorna**: Lista de diccionarios con:
- `id` (str): ID único de la oferta
- `price` (float): Precio total
- `currency` (str): Moneda
- `airline` (str): Nombre de la aerolínea
- `airline_code` (str): Código IATA de la aerolínea
- `duration` (str): Duración (formato: "Xh Ym")
- `stops` (int): Número de escalas
- `departure_time` (str): Hora de salida (ISO 8601)
- `arrival_time` (str): Hora de llegada (ISO 8601)
- `number_of_bookable_seats` (int): Asientos disponibles
- `raw_data` (dict): Datos completos de Amadeus

**Excepciones**: 
- `Exception`: Error en la petición HTTP
- `Timeout`: Si la API no responde en 15 segundos

**Ejemplo**:
```python
amadeus = AmadeusClient(api_key="xxx", api_secret="yyy")

offers = amadeus.search_flights(
    origin="EZE",
    destination="MIA",
    departure_date="2025-12-15",
    return_date="2025-12-22",
    adults=2,
    max_results=20
)

for offer in offers:
    print(f"{offer['airline']}: ${offer['price']} - {offer['duration']}")
```

---

#### get_airport_info()

```python
def get_airport_info(self, iata_code: str) -> Optional[Dict]
```

**Descripción**: Obtiene información detallada de un aeropuerto.

**Parámetros**:
- `iata_code` (str): Código IATA del aeropuerto (3 letras)

**Retorna**: Diccionario con información del aeropuerto o `None` si no se encuentra

**Ejemplo**:
```python
airport = amadeus.get_airport_info("EZE")
if airport:
    print(f"Nombre: {airport['name']}")
    print(f"Ciudad: {airport['address']['cityName']}")
```

---

#### validate_airport_code()

```python
def validate_airport_code(self, iata_code: str) -> bool
```

**Descripción**: Valida que un código IATA existe.

**Parámetros**:
- `iata_code` (str): Código IATA a validar

**Retorna**: `True` si válido, `False` si no existe

**Ejemplo**:
```python
if amadeus.validate_airport_code("EZE"):
    print("Código válido")
else:
    print("Código inválido")
```

---

## Módulo: app.py

Aplicación principal de Streamlit.

### Funciones Principales

#### init_database()

```python
@st.cache_resource
def init_database() -> Optional[Database]
```

**Descripción**: Inicializa la conexión a PostgreSQL con caché.

**Retorna**: Instancia de `Database` o `None` si falla

---

#### init_amadeus()

```python
@st.cache_resource
def init_amadeus() -> Optional[AmadeusClient]
```

**Descripción**: Inicializa el cliente de Amadeus con caché.

**Retorna**: Instancia de `AmadeusClient` o `None` si falla

---

#### simulate_flight_search()

```python
def simulate_flight_search(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str,
    adults: int
) -> List[Dict]
```

**Descripción**: Genera datos simulados de vuelos cuando la API no está disponible.

**Parámetros**:
- `origin` (str): Código IATA de origen
- `destination` (str): Código IATA de destino
- `departure_date` (str): Fecha de salida (YYYY-MM-DD)
- `return_date` (str): Fecha de regreso (YYYY-MM-DD)
- `adults` (int): Número de adultos

**Retorna**: Lista de diccionarios con el mismo formato que `amadeus.search_flights()`

**Algoritmo**:
1. Calcula precio base (300-1500 USD)
2. Aplica factor de anticipación:
   - < 7 días: +80%
   - < 30 días: +30%
   - > 90 días: -30%
3. Genera 5-12 ofertas con variación aleatoria
4. Asigna aerolíneas, escalas y horarios realistas

---

## Estructuras de Datos

### Oferta de Vuelo

Estructura estándar retornada por `amadeus.search_flights()` y `simulate_flight_search()`:

```python
{
    'id': 'FLIGHT123',                    # ID único
    'price': 1250.50,                      # Precio (float)
    'currency': 'USD',                     # Moneda
    'airline': 'American Airlines',        # Nombre aerolínea
    'airline_code': 'AA',                  # Código IATA
    'duration': '10h 30m',                 # Duración
    'stops': 1,                            # Escalas (int)
    'departure_time': '2025-12-15T08:30:00',  # ISO 8601
    'arrival_time': '2025-12-15T19:00:00',    # ISO 8601
    'number_of_bookable_seats': 5,         # Asientos disponibles
    'raw_data': {...}                      # Datos completos
}
```

### Búsqueda Activa

Estructura almacenada en `st.session_state.active_searches`:

```python
{
    'origin': 'EZE',                       # Origen
    'destination': 'MIA',                  # Destino
    'departure_date': '2025-12-15',        # Fecha salida
    'return_date': '2025-12-22',           # Fecha regreso
    'adults': 2,                           # Pasajeros
    'target_price': 1000.00,               # Precio objetivo
    'current_price': 1250.50,              # Precio actual
    'created_at': '2025-10-06 14:30:00'    # Timestamp
}
```

### Registro en Base de Datos

Estructura en tabla `flight_searches`:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | SERIAL | ID autoincremental |
| search_timestamp | TIMESTAMP | Fecha/hora de búsqueda |
| origin | VARCHAR(3) | Código IATA origen |
| destination | VARCHAR(3) | Código IATA destino |
| departure_date | DATE | Fecha de salida |
| return_date | DATE | Fecha de regreso (nullable) |
| adults | INTEGER | Número de adultos |
| price | DECIMAL(10,2) | Precio del vuelo |
| currency | VARCHAR(3) | Código de moneda |
| airline | VARCHAR(100) | Nombre aerolínea (nullable) |
| flight_data | JSONB | Datos completos en JSON |
| created_at | TIMESTAMP | Fecha de creación |

---

## Flujo de Datos

### 1. Búsqueda de Vuelos

```
Usuario ingresa parámetros
         ↓
¿Modo simulación?
    ├─ SÍ → simulate_flight_search()
    └─ NO → amadeus.search_flights()
         ↓
Procesar ofertas
         ↓
Guardar en PostgreSQL (database.insert_flight_offer)
         ↓
¿Precio objetivo definido?
    └─ SÍ → Agregar a búsquedas activas
         ↓
Mostrar resultados en tabla
```

### 2. Análisis de Tarifas

```
Usuario selecciona ruta
         ↓
database.get_searches_by_route()
         ↓
Procesar DataFrame con pandas
         ↓
Generar visualizaciones con Plotly
    ├─ Scatter plot (precios por fecha)
    ├─ Estadísticas (min, max, avg)
    └─ Tabla detallada
         ↓
Opción de exportar a CSV
```

### 3. Dashboard

```
Al cargar página
         ↓
database.get_recent_searches(100)
         ↓
Calcular métricas
    ├─ Total búsquedas
    ├─ Precio promedio
    ├─ Precio mínimo
    └─ Precio máximo
         ↓
Generar gráficos
    ├─ Línea: Evolución temporal
    └─ Box plot: Por aerolínea
```

---

## Variables de Entorno

### Configuración en .streamlit/secrets.toml

```toml
# Base de Datos PostgreSQL
DB_HOST = "host.render.com"
DB_PORT = 5432
DB_NAME = "nombre_bd"
DB_USER = "usuario"
DB_PASSWORD = "password_seguro"

# API de Amadeus
AMADEUS_API_KEY = "tu_api_key"
AMADEUS_API_SECRET = "tu_api_secret"
```

### Acceso en Código

```python
import streamlit as st

# Acceder a secrets
db_host = st.secrets["DB_HOST"]
api_key = st.secrets["AMADEUS_API_KEY"]

# Con valor por defecto
db_port = st.secrets.get("DB_PORT", 5432)
```

---

## Estado de Sesión (Session State)

### Variables Globales

```python
# Modo de operación
st.session_state.simulation_mode: bool

# Búsquedas activas
st.session_state.active_searches: List[Dict]

# Ejemplo de uso:
if 'simulation_mode' not in st.session_state:
    st.session_state.simulation_mode = False
```

---

## Índices de Base de Datos

```sql
-- Índice compuesto para búsquedas por ruta
CREATE INDEX idx_origin_dest 
ON flight_searches(origin, destination);

-- Índice para ordenar por fecha
CREATE INDEX idx_search_timestamp 
ON flight_searches(search_timestamp);

-- Índice para filtrar por fecha de salida
CREATE INDEX idx_departure_date 
ON flight_searches(departure_date);

-- Índice para consultas por precio
CREATE INDEX idx_price 
ON flight_searches(price);
```

**Uso**: Estos índices optimizan las consultas más comunes:
- Búsqueda por ruta específica
- Ordenamiento temporal
- Filtros por fecha
- Estadísticas de precios

---

## Códigos de Error Comunes

### PostgreSQL

| Error | Código | Causa | Solución |
|-------|--------|-------|----------|
| Connection refused | 2002 | BD no accesible | Verificar host/puerto |
| Authentication failed | 28P01 | Credenciales incorrectas | Revisar user/password |
| Database does not exist | 3D000 | BD no creada | Crear base de datos |
| Relation does not exist | 42P01 | Tabla no existe | Ejecutar setup_database.py |

### Amadeus API

| Error | Código HTTP | Causa | Solución |
|-------|-------------|-------|----------|
| Unauthorized | 401 | API key inválido | Verificar credenciales |
| Too Many Requests | 429 | Límite excedido | Esperar o usar modo demo |
| Bad Request | 400 | Parámetros inválidos | Validar formato de fecha |
| Not Found | 404 | Código IATA inválido | Verificar códigos |
| Timeout | - | API no responde | Reintentar o modo demo |

---

## Límites y Restricciones

### API de Amadeus (Test Environment)

- **Llamadas**: 2,000 por mes
- **Rate limit**: 10 peticiones por segundo
- **Timeout**: 15 segundos
- **Resultados máximos**: 250 por búsqueda
- **Datos históricos**: Solo tiempo real

### PostgreSQL (Render Free Tier)

- **Almacenamiento**: 1 GB
- **Conexiones**: 97 simultáneas
- **Inactividad**: Se suspende después de 90 días sin uso
- **Backup**: No incluido en plan gratuito

### Streamlit Cloud

- **Memoria RAM**: 1 GB
- **CPU**: Compartida
- **Timeout**: Apps inactivas se suspenden
- **Recursos**: Reinicio cada 7 días
- **Secrets**: 50 KB máximo

---

## Optimizaciones Recomendadas

### Base de Datos

```python
# Usar conexión persistente en producción
# En lugar de crear conexión por operación:
with db._get_connection() as conn:
    cursor = conn.cursor()
    # Múltiples operaciones...
    conn.commit()

# Batch inserts para mejor rendimiento
values = [(offer['origin'], offer['destination'], ...) 
          for offer in offers]
cursor.executemany(insert_query, values)
```

### Streamlit

```python
# Cache datos que no cambian frecuentemente
@st.cache_data(ttl=3600)  # Cache por 1 hora
def load_static_data():
    return expensive_computation()

# Cache recursos globales
@st.cache_resource
def init_connections():
    return Database(...), AmadeusClient(...)
```

### API Calls

```python
# Implementar exponential backoff para reintentos
import time

def retry_with_backoff(func, max_retries=3):
    for i in range(max_retries):
        try:
            return func()
        except Exception:
            if i == max_retries - 1:
                raise
            time.sleep(2 ** i)  # 1s, 2s, 4s
```

---

## Extensiones Futuras

### Arquitectura Propuesta

```
Frontend (Streamlit)
    ↓
API Layer (FastAPI) ← Nuevo
    ↓
Service Layer ← Nuevo
    ├─ Database Service
    ├─ Flight API Service
    └─ Notification Service ← Nuevo
    ↓
Data Layer (PostgreSQL + Redis) ← Redis nuevo
```

### Nuevos Módulos Planificados

1. **notification_service.py**: Envío de emails/SMS
2. **ml_predictor.py**: Predicción de precios con ML
3. **api_router.py**: API REST con FastAPI
4. **cache_manager.py**: Gestión de caché con Redis
5. **user_manager.py**: Autenticación y perfiles

---

## Referencias

- [Amadeus API Reference](https://developers.amadeus.com/self-service/category/flights/api-doc/flight-offers-search)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Streamlit API Reference](https://docs.streamlit.io/library/api-reference)
- [Plotly Python](https://plotly.com/python/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
