# ✈️ Flight Scan - Monitor de Tarifas Aéreas

Sistema de monitoreo y análisis de tarifas de vuelos usando la API de Amadeus y PostgreSQL.

## 📋 Descripción

Flight Scan es una aplicación que permite:

- 🔍 Consultar ofertas de vuelos en tiempo real mediante la API de Amadeus
- 💾 Almacenar histórico de búsquedas en PostgreSQL
- 📊 Visualizar evolución de precios con gráficos interactivos
- 📈 Analizar tendencias y comparar precios por aerolínea
- ⏰ Configurar monitoreo automático con diferentes frecuencias

## 🎯 Trabajo Práctico

Este proyecto fue desarrollado como parte del **Trabajo Práctico del Segundo Módulo** de la materia:
- **Programación Avanzada en Ciencia de Datos**
- Universidad de la Ciudad de Buenos Aires

## 🛠️ Tecnologías Utilizadas

- **Python 3.9+**
- **Streamlit**: Dashboard interactivo
- **PostgreSQL**: Base de datos relacional (alojada en Render)
- **Amadeus API**: Consulta de ofertas de vuelos
- **Plotly**: Visualizaciones interactivas
- **Pandas**: Manipulación de datos
- **psycopg2**: Conexión a PostgreSQL

## 📁 Estructura del Proyecto

```
flight-scan/
│
├── app.py                 # Aplicación principal de Streamlit
├── database.py            # Módulo de gestión de base de datos
├── amadeus_client.py      # Cliente para API de Amadeus
├── requirements.txt       # Dependencias del proyecto
├── .streamlit/
│   └── secrets.toml      # Configuración de credenciales (no incluido en repo)
├── setup_database.py     # Script para inicializar la BD
└── README.md             # Este archivo
```

## 🚀 Instalación y Configuración

### 1. Clonar el repositorio

```bash
git clone https://github.com/alemeds/flight-scan.git
cd flight-scan
```

### 2. Crear entorno virtual

```bash
python -m venv venv

# En Windows
venv\Scripts\activate

# En Mac/Linux
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar credenciales

Crea el archivo `.streamlit/secrets.toml` con el siguiente contenido:

```toml
# Database Configuration (Render PostgreSQL)
DB_HOST = "your-database-host.com"
DB_PORT = 5432
DB_NAME = "your-database-name"
DB_USER = "your-database-user"
DB_PASSWORD = "your-database-password"

# Amadeus API Configuration
AMADEUS_API_KEY = "your-amadeus-api-key"
AMADEUS_API_SECRET = "your-amadeus-api-secret"

```

⚠️ **Importante**: No subas este archivo al repositorio. Ya está incluido en `.gitignore`.

### 5. Inicializar la base de datos

```bash
python setup_database.py
```

Este script creará las tablas necesarias en PostgreSQL.

### 6. Ejecutar la aplicación

```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

## 📊 Uso de la Aplicación

### Búsqueda Manual

1. En la barra lateral, ingresa:
   - **Origen**: Código IATA del aeropuerto (ej: EZE para Buenos Aires)
   - **Destino**: Código IATA del aeropuerto (ej: MIA para Miami)
   - **Fechas**: Ida y vuelta
   - **Adultos**: Número de pasajeros

2. Haz clic en **"🔍 Buscar Vuelos Ahora"**

3. Los resultados se guardarán automáticamente en la base de datos

### Monitoreo Automático

1. Selecciona la **frecuencia de consulta**:
   - Cada 5 minutos
   - Cada 30 minutos
   - Cada 2 horas
   - Cada 24 horas

2. Define la **duración del monitoreo** (en días)

3. Haz clic en **"▶️ Iniciar Monitoreo Automático"**

⚠️ **Nota**: Para monitoreo 24/7 continuo, se recomienda usar un scheduler externo (ver sección de Automatización)

### Análisis de Tarifas

En la pestaña **"📈 Análisis de Tarifas"** puedes:

- Ver gráficos de evolución de precios
- Comparar precios entre aerolíneas
- Consultar estadísticas (mínimo, promedio, máximo)
- Filtrar por ruta y período de tiempo
- Exportar datos a CSV

## 🔄 Automatización con GitHub Actions

Para ejecutar el monitoreo automático de forma continua, puedes usar GitHub Actions.

Crea el archivo `.github/workflows/monitor.yml`:

```yaml
name: Flight Monitor

on:
  schedule:
    # Ejecuta cada 2 horas
    - cron: '0 */2 * * *'
  workflow_dispatch: # Permite ejecución manual

jobs:
  monitor:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run monitoring script
      env:
        DB_HOST: ${{ secrets.DB_HOST }}
        DB_PORT: ${{ secrets.DB_PORT }}
        DB_NAME: ${{ secrets.DB_NAME }}
        DB_USER: ${{ secrets.DB_USER }}
        DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
        AMADEUS_API_KEY: ${{ secrets.AMADEUS_API_KEY }}
        AMADEUS_API_SECRET: ${{ secrets.AMADEUS_API_SECRET }}
      run: |
        python monitor_script.py
```

No olvides agregar los secrets en GitHub:
- Settings → Secrets and variables → Actions → New repository secret

## 📦 Base de Datos

### Esquema de la tabla `flight_searches`

```sql
CREATE TABLE flight_searches (
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
```

### Índices

- `idx_origin_dest`: Búsquedas por ruta
- `idx_search_timestamp`: Búsquedas por fecha
- `idx_departure_date`: Búsquedas por fecha de salida

## 🌐 Dataset Utilizado

- **Fuente**: [Amadeus Flight Offers API](https://developers.amadeus.com/self-service/category/flights)
- **Tipo**: API REST
- **Datos**: Ofertas de vuelos en tiempo real
- **Actualización**: Consultas bajo demanda

## 📈 Ejemplos de Visualización

El dashboard incluye:

1. **Gráfico de líneas**: Evolución temporal de precios
2. **Box plot**: Distribución de precios por aerolínea
3. **Métricas**: Min, Max, Promedio, Total de consultas
4. **Tabla interactiva**: Historial completo de búsquedas

## 🔧 Scripts Adicionales

### setup_database.py

Inicializa las tablas en PostgreSQL:

```python
from database import Database
import os

# Configuración desde variables de entorno o archivo
db = Database(
    host=os.getenv('DB_HOST'),
    port=int(os.getenv('DB_PORT', 5432)),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)

print("✅ Base de datos configurada correctamente")
```

### monitor_script.py

Script para monitoreo automático (para usar con cron o GitHub Actions):

```python
from database import Database
from amadeus_client import AmadeusClient
import os
from datetime import datetime, timedelta

# Inicializar
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

# Configuración de rutas a monitorear
routes = [
    {'origin': 'EZE', 'destination': 'MIA', 'days_ahead': 30},
    {'origin': 'EZE', 'destination': 'MAD', 'days_ahead': 45},
    {'origin': 'AEP', 'destination': 'SCL', 'days_ahead': 20}
]

# Buscar y guardar
for route in routes:
    departure = (datetime.now() + timedelta(days=route['days_ahead'])).strftime('%Y-%m-%d')
    return_date = (datetime.now() + timedelta(days=route['days_ahead'] + 7)).strftime('%Y-%m-%d')
    
    offers = amadeus.search_flights(
        origin=route['origin'],
        destination=route['destination'],
        departure_date=departure,
        return_date=return_date,
        adults=1
    )
    
    for offer in offers:
        db.insert_flight_offer(
            origin=route['origin'],
            destination=route['destination'],
            departure_date=departure,
            return_date=return_date,
            price=offer['price'],
            currency=offer['currency'],
            airline=offer.get('airline'),
            flight_data=offer
        )
    
    print(f"✅ {route['origin']} → {route['destination']}: {len(offers)} ofertas guardadas")

print("✅ Monitoreo completado")
```

## 🐛 Troubleshooting

### Error de conexión a PostgreSQL

```
OperationalError: could not connect to server
```

**Solución**: Verifica que las credenciales en `secrets.toml` sean correctas y que la base de datos en Render esté activa.

### Error de autenticación Amadeus

```
Error obteniendo token: 401
```

**Solución**: Verifica que `AMADEUS_API_KEY` y `AMADEUS_API_SECRET` sean correctos.

### La aplicación no encuentra módulos

```
ModuleNotFoundError: No module named 'streamlit'
```

**Solución**: Asegúrate de haber activado el entorno virtual y ejecutado `pip install -r requirements.txt`

## 📝 Criterios de Evaluación Cumplidos

✅ **Claridad y organización del repositorio**: Estructura clara con separación de responsabilidades

✅ **Correcta carga de datos**: Sistema robusto de inserción con manejo de errores

✅ **Funcionalidad del dashboard**: Dashboard interactivo con múltiples visualizaciones

✅ **Calidad del README**: Documentación completa con instrucciones detalladas

✅ **Replicabilidad**: Instrucciones paso a paso para clonar y ejecutar

## 👨‍💻 Autor

Lic. Antonio Luis E. Martinez

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

## 🔗 Enlaces

- **Repositorio**: [github.com/alemeds/flight-scan](https://github.com/alemeds/flight-scan)
- **Proyecto publicado**: [strimlit.app/alemeds/flight-scan](https://flight-scan.streamlit.app)
- **Amadeus API**: [developers.amadeus.com](https://developers.amadeus.com)
- **Render**: [render.com](https://render.com)

## 📧 Contacto

Para preguntas o sugerencias, por favor abre un issue en el repositorio.

---

**Desarrollado para el Trabajo Práctico - Segundo Módulo**  
**Programación Avanzada en Ciencia de Datos**  
**Universidad de la Ciudad de Buenos Aires**
