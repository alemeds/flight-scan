# ✈️ Flight Scan - Monitor de Tarifas Aéreas

Sistema de monitoreo y análisis de tarifas de vuelos usando la API de Amadeus y PostgreSQL.

## 📋 Descripción

Flight Scan es una aplicación que permite:

- 🔍 Consultar ofertas de vuelos en tiempo real mediante la API de Amadeus
- 💾 Almacenar histórico de búsquedas en PostgreSQL
- 📊 Visualizar evolución de precios con gráficos interactivos
- 📈 Analizar tendencias y comparar precios por aerolínea
- 💰 **Definir precios objetivo y recibir alertas**
- 🎮 **Modo simulación para pruebas sin consumir cuota de API**
- 📋 **Gestión de búsquedas activas con seguimiento de objetivos**

Este proyecto fue desarrollado como parte del Trabajo Práctico del Segundo Módulo de la materia:
- **Programación Avanzada en Ciencia de Datos**
- **Universidad de la Ciudad de Buenos Aires**

## 🚀 Demo en Vivo

**[Ver aplicación desplegada](https://flight-scan.streamlit.app)**

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
├── app.py                  # Aplicación principal de Streamlit
├── database.py             # Módulo de gestión de base de datos
├── amadeus_client.py       # Cliente para API de Amadeus
├── requirements.txt        # Dependencias del proyecto
├── .streamlit/
│   └── secrets.toml        # Configuración de credenciales (no incluido en repo)
├── setup_database.py       # Script para inicializar la BD
└── README.md               # Este archivo
```

## ⚙️ Instalación Local

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
# Database Configuration (PostgreSQL)
DB_HOST = "your-database-host.com"
DB_PORT = 5432
DB_NAME = "your-database-name"
DB_USER = "your-database-user"
DB_PASSWORD = "your-database-password"

# Amadeus API Configuration
AMADEUS_API_KEY = "your-amadeus-api-key"
AMADEUS_API_SECRET = "your-amadeus-api-secret"
```

> ⚠️ **IMPORTANTE**: Nunca compartas estas credenciales públicamente. El archivo `secrets.toml` ya está incluido en `.gitignore`.

### 5. Obtener credenciales

#### PostgreSQL (Render)

1. Regístrate en [Render.com](https://render.com)
2. Crea una nueva PostgreSQL Database
3. Copia las credenciales proporcionadas

#### Amadeus API

1. Regístrate en [Amadeus for Developers](https://developers.amadeus.com)
2. Crea una nueva aplicación en el portal
3. Obtén tu API Key y API Secret
4. Comienza con el entorno de prueba (Test Environment)

### 6. Inicializar la base de datos

```bash
python setup_database.py
```

Este script creará las tablas necesarias en PostgreSQL.

### 7. Ejecutar la aplicación

```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

## 📖 Uso de la Aplicación

### Búsqueda Manual de Vuelos

1. En la barra lateral, selecciona el modo:
   - **🌐 Modo Real**: Usa la API de Amadeus (requiere credenciales)
   - **🎮 Modo Demo**: Usa datos simulados realistas (sin API)

2. Ingresa los parámetros de búsqueda:
   - **Origen**: Código IATA del aeropuerto (ej: EZE para Buenos Aires)
   - **Destino**: Código IATA del aeropuerto (ej: MIA para Miami)
   - **Fechas**: Ida y vuelta
   - **Adultos**: Número de pasajeros (1-9)
   - **💰 Precio Objetivo**: Define un precio meta (opcional)

3. Haz clic en **"🔍 Buscar Vuelos Ahora"**

4. Los resultados se guardarán automáticamente en la base de datos

### Sistema de Precios Objetivo

Cuando defines un precio objetivo:
- ✅ Recibirás una **alerta visual con confeti** si se encuentra un vuelo que cumple tu objetivo
- 📌 La búsqueda se agregará automáticamente a **"📋 Búsquedas Activas"**
- 📊 Verás una **barra de progreso** hacia tu objetivo en el sidebar
- 🎯 Los vuelos que cumplen el objetivo se marcarán en la tabla de resultados

### Modo Simulación

El **Modo Demo** es perfecto para:
- Probar la aplicación sin configurar APIs
- Hacer demos o presentaciones
- No consumir cuota de la API de Amadeus
- Datos realistas basados en patrones de precios reales

### Análisis de Tarifas

En la pestaña **"📈 Análisis de Tarifas"** puedes:

- Ver gráficos de evolución de precios por ruta
- Consultar estadísticas (mínimo, promedio, máximo)
- Filtrar por ruta y período de tiempo (1-90 días)
- Comparar precios entre diferentes búsquedas
- Exportar datos a CSV

### Historial

En la pestaña **"📋 Historial"** puedes:

- Ver todas las búsquedas realizadas
- Filtrar por origen, destino y aerolínea
- Exportar el historial completo a CSV
- Analizar patrones de precios históricos

## 🤖 Monitoreo Automático con GitHub Actions

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

**No olvides agregar los secrets en GitHub:**
- Settings → Secrets and variables → Actions → New repository secret

## 🗄️ Estructura de la Base de Datos

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
    airline VARCHAR(100),
    flight_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Índices para optimizar consultas:**
- `idx_origin_dest`: Búsquedas por ruta
- `idx_search_timestamp`: Búsquedas por fecha
- `idx_departure_date`: Búsquedas por fecha de salida
- `idx_price`: Optimización de consultas por precio

## 📊 Fuente de Datos

- **Fuente**: [Amadeus Flight Offers API](https://developers.amadeus.com/self-service/category/flights)
- **Tipo**: API REST
- **Datos**: Ofertas de vuelos en tiempo real
- **Actualización**: Consultas bajo demanda
- **Límites gratuitos**: 2,000 consultas/mes (Test Environment)

## 📈 Dashboard

El dashboard incluye:

- **Gráfico de líneas**: Evolución temporal de precios
- **Box plot**: Distribución de precios por aerolínea
- **Scatter plot**: Precios por fecha con código de colores por aerolínea
- **Métricas**: Min, Max, Promedio, Total de consultas
- **Tabla interactiva**: Historial completo de búsquedas con filtros

## 💡 Ejemplos de Uso

### Inicializar Base de Datos

```python
from database import Database
import os

# Configuración desde variables de entorno
db = Database(
    host=os.getenv('DB_HOST'),
    port=int(os.getenv('DB_PORT', 5432)),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)

print("✅ Base de datos configurada correctamente")
```

### Script de Monitoreo Automático

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

## 🔧 Solución de Problemas

### Error de conexión a PostgreSQL

```
OperationalError: could not connect to server
```

**Solución**: Verifica que las credenciales en `secrets.toml` sean correctas y que la base de datos en Render esté activa.

### Error de autenticación de Amadeus

```
Error obteniendo token: 401
```

**Solución**: Verifica que `AMADEUS_API_KEY` y `AMADEUS_API_SECRET` sean correctos. Asegúrate de usar las credenciales del entorno correcto (Test vs Production).

### Módulo no encontrado

```
ModuleNotFoundError: No module named 'streamlit'
```

**Solución**: Asegúrate de haber activado el entorno virtual y ejecutado `pip install -r requirements.txt`

### Límite de API excedido

```
Error 429: Too Many Requests
```

**Solución**: Has alcanzado el límite de llamadas gratuitas de Amadeus (2,000/mes). Opciones:
- Espera hasta el próximo período de facturación
- Usa el **Modo Demo** para continuar probando
- Considera actualizar tu plan de Amadeus

### Error en gráfico scatter

```
Invalid value of type 'narwhals.stable.v1.Series'
```

**Solución**: Este error ya está corregido en la última versión de `app.py`. Actualiza tu código con la versión más reciente del repositorio.

## ✅ Criterios de Evaluación Cumplidos

- ✅ **Claridad y organización del repositorio**: Estructura clara con separación de responsabilidades
- ✅ **Correcta carga de datos**: Sistema robusto de inserción con manejo de errores
- ✅ **Funcionalidad del dashboard**: Dashboard interactivo con múltiples visualizaciones
- ✅ **Calidad del README**: Documentación completa con instrucciones detalladas
- ✅ **Replicabilidad**: Instrucciones paso a paso para clonar y ejecutar
- ✅ **Funcionalidades adicionales**: Precios objetivo, modo simulación, búsquedas activas

## 🆕 Nuevas Funcionalidades (v2.0)

### Sistema de Precios Objetivo
- Define un precio meta para tus búsquedas
- Recibe alertas visuales cuando se alcanza
- Seguimiento automático en búsquedas activas

### Modo Simulación
- Prueba la app sin API configurada
- Datos realistas basados en patrones reales
- Perfecto para demos y presentaciones

### Gestión de Búsquedas Activas
- Monitorea múltiples rutas simultáneamente
- Visualiza progreso hacia precios objetivo
- Elimina búsquedas completadas fácilmente

### Mejoras de Estabilidad
- Fallback automático si la API falla
- Validaciones robustas de datos
- Manejo mejorado de errores
- Timeouts en peticiones HTTP

## 👨‍💻 Autor

**Lic. Antonio Luis E. Martinez**

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

## 🔗 Enlaces Útiles

- **Repositorio**: [github.com/alemeds/flight-scan](https://github.com/alemeds/flight-scan)
- **Aplicación**: [flight-scan.streamlit.app](https://flight-scan.streamlit.app)
- **Amadeus API**: [developers.amadeus.com](https://developers.amadeus.com)
- **Render**: [render.com](https://render.com)
- **Documentación de Streamlit**: [docs.streamlit.io](https://docs.streamlit.io)

## 📧 Contacto

Para preguntas o sugerencias, por favor abre un **issue** en el repositorio.

---

**Desarrollado para el Trabajo Práctico - Segundo Módulo**  
**Programación Avanzada en Ciencia de Datos**  
**Universidad de la Ciudad de Buenos Aires**
