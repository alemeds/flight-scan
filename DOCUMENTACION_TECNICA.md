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
@
