# ✈️ Flight Scan - Monitor de Tarifas Aéreas

Sistema de monitoreo y análisis de tarifas de vuelos usando la API Sky Scrapper (RapidAPI) y Google Sheets como base de datos.

## 📋 Descripción

Flight Scan es una aplicación que permite:

- 🔍 Consultar ofertas de vuelos en tiempo real mediante la API Sky Scrapper
- 💾 Almacenar histórico de búsquedas en una planilla de Google Sheets
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
- **Google Sheets**: Base de datos (via gspread + service account)
- **Sky Scrapper API (RapidAPI)**: Consulta de ofertas de vuelos
- **Plotly**: Visualizaciones interactivas
- **Pandas**: Manipulación de datos

## 📁 Estructura del Proyecto

```
flight-scan/
│
├── app.py                  # Aplicación principal de Streamlit
├── sheets_db.py            # Persistencia en Google Sheets
├── skyscrapper_client.py   # Cliente para API Sky Scrapper (RapidAPI)
├── config.py               # Helper de secrets (st.secrets / entorno)
├── monitor_script.py       # Monitoreo automático de alertas (cron/Actions)
├── requirements.txt        # Dependencias del proyecto
├── .streamlit/
│   └── secrets.toml        # Configuración de credenciales (no incluido en repo)
├── tests/                  # Tests unitarios
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
# Sky Scrapper (RapidAPI)
RAPIDAPI_KEY = "your-rapidapi-key"

# Google Sheets
SHEET_NAME = "flight-scan-db"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "..."
client_email = "..."
client_id = "..."
token_uri = "https://oauth2.googleapis.com/token"
```

> ⚠️ **IMPORTANTE**: Nunca compartas estas credenciales públicamente. El archivo `secrets.toml` ya está incluido en `.gitignore`. Ver `secrets.toml.example` para la plantilla completa.

### 5. Obtener credenciales

#### Sky Scrapper (RapidAPI)

1. Regístrate en [RapidAPI](https://rapidapi.com)
2. Suscribite a [Sky Scrapper](https://rapidapi.com/apiheya/api/sky-scrapper) (tiene plan gratuito)
3. Copia tu API key desde el dashboard de RapidAPI

#### Google Service Account (para Sheets)

1. En [Google Cloud Console](https://console.cloud.google.com), crea un proyecto (o usa uno existente)
2. Habilita las APIs **Google Sheets API** y **Google Drive API**
3. IAM → Service Accounts → crear una service account → Keys → agregar clave JSON
4. Guarda el JSON localmente (NO lo subas al repo) y copia sus campos a `secrets.toml`

### 6. Crear la planilla de base de datos

1. Crea en Google Sheets una planilla llamada **`flight-scan-db`**
2. Compártela con el `client_email` de la service account con rol **Editor** (una sola vez)
3. Las hojas y encabezados se crean solos al arrancar la app

> 🔒 **Privacidad**: la app desplegada en streamlit.app es pública en su URL, pero los datos de la planilla NO son accesibles públicamente — el acceso está mediado por la service account. Solo quien tenga acceso al Sheet en Drive puede verlo directamente.

### 7. Ejecutar la aplicación

```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

## 📖 Uso de la Aplicación

### Búsqueda Manual de Vuelos

1. En la barra lateral, selecciona el modo:
   - **🌐 Modo Real**: Usa la API Sky Scrapper (requiere RAPIDAPI_KEY)
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
- No consumir cuota de la API de vuelos
- Datos realistas basados en patrones de precios reales

Los datos simulados se guardan marcados como tales y no se mezclan con los reales en los análisis.

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
    
    - name: Write service account file
      run: echo '${{ secrets.GCP_SERVICE_ACCOUNT_JSON }}' > sa.json

    - name: Run monitoring script
      env:
        GCP_SERVICE_ACCOUNT_FILE: sa.json
        SHEET_NAME: flight-scan-db
        RAPIDAPI_KEY: ${{ secrets.RAPIDAPI_KEY }}
        SMTP_HOST: ${{ secrets.SMTP_HOST }}
        SMTP_USER: ${{ secrets.SMTP_USER }}
        SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
        ALERT_EMAIL_TO: ${{ secrets.ALERT_EMAIL_TO }}
      run: |
        python monitor_script.py
```

**No olvides agregar los secrets en GitHub:**
- Settings → Secrets and variables → Actions → New repository secret

## 🗄️ Estructura de la Base de Datos (planilla `flight-scan-db`)

**Hoja `busquedas`** — una fila por oferta encontrada:

| Columna | Descripción |
|---------|-------------|
| `timestamp` | Fecha y hora de la búsqueda |
| `origen` / `destino` | Códigos IATA |
| `fecha_salida` / `fecha_regreso` | Fechas del viaje |
| `adultos` | Cantidad de pasajeros |
| `precio` / `moneda` | Precio de la oferta |
| `aerolinea` | Aerolínea de la oferta |
| `simulado` | TRUE si proviene del Modo Demo |

**Hoja `alertas_precio`** — una fila por alerta:

| Columna | Descripción |
|---------|-------------|
| `id` | Identificador de la alerta |
| `origen` / `destino` / `fecha_salida` / `fecha_regreso` / `adultos` | Parámetros de la búsqueda |
| `precio_objetivo` | Precio que dispara la notificación |
| `ultimo_precio` | Último precio visto por el monitor |
| `activa` | TRUE mientras la alerta esté vigente |
| `ultima_revision` / `disparada_en` / `creada_en` | Timestamps de seguimiento |

Las hojas y encabezados se crean automáticamente al iniciar la app.

## 📊 Fuente de Datos

- **Fuente**: [Sky Scrapper API](https://rapidapi.com/apiheya/api/sky-scrapper) (RapidAPI)
- **Tipo**: API REST (datos de Google Flights)
- **Datos**: Ofertas de vuelos en tiempo real
- **Actualización**: Consultas bajo demanda
- **Límites**: según el plan contratado en RapidAPI (existe plan gratuito)

## 📈 Dashboard

El dashboard incluye:

- **Gráfico de líneas**: Evolución temporal de precios
- **Box plot**: Distribución de precios por aerolínea
- **Scatter plot**: Precios por fecha con código de colores por aerolínea
- **Métricas**: Min, Max, Promedio, Total de consultas
- **Tabla interactiva**: Historial completo de búsquedas con filtros

## 💡 Ejemplos de Uso

### Buscar y guardar desde código

```python
from sheets_db import SheetsDatabase
from skyscrapper_client import SkyScrapperClient
from config import get_gcp_credentials
import os

db = SheetsDatabase(credentials_info=get_gcp_credentials())
client = SkyScrapperClient(api_key=os.getenv('RAPIDAPI_KEY'))

offers = client.search_flights(
    origin='EZE',
    destination='MIA',
    departure_date='2026-09-01',
    return_date='2026-09-10',
    adults=1
)

saved = db.insert_flight_offers(
    origin='EZE', destination='MIA',
    departure_date='2026-09-01', return_date='2026-09-10',
    adults=1, offers=offers
)

print(f"✅ {saved} ofertas guardadas")
```

El monitoreo automático de alertas ya está implementado en `monitor_script.py` (ver sección de GitHub Actions).

## 🔧 Solución de Problemas

### Error de conexión a Google Sheets

```
DatabaseError: No se encontró la planilla 'flight-scan-db'
```

**Solución**: Verifica que la planilla exista en Google Sheets y esté compartida (rol Editor) con el `client_email` de la service account.

### Error de autenticación de Sky Scrapper

```
AuthenticationError: RapidAPI key inválida o suscripción inactiva
```

**Solución**: Verifica que `RAPIDAPI_KEY` sea correcta y que tu suscripción a Sky Scrapper en RapidAPI esté activa.

### Módulo no encontrado

```
ModuleNotFoundError: No module named 'streamlit'
```

**Solución**: Asegúrate de haber activado el entorno virtual y ejecutado `pip install -r requirements.txt`

### Límite de API excedido

```
APIError: Rate limit de RapidAPI excedido
```

**Solución**: Has alcanzado el límite de tu plan de Sky Scrapper en RapidAPI. Opciones:
- Espera hasta el próximo período de facturación
- Usa el **Modo Demo** para continuar probando
- Considera actualizar tu plan en RapidAPI

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
- **Sky Scrapper API**: [rapidapi.com/apiheya/api/sky-scrapper](https://rapidapi.com/apiheya/api/sky-scrapper)
- **gspread**: [docs.gspread.org](https://docs.gspread.org)
- **Documentación de Streamlit**: [docs.streamlit.io](https://docs.streamlit.io)

## 📧 Contacto

Para preguntas o sugerencias, por favor abre un **issue** en el repositorio.

---

**Desarrollado para el Trabajo Práctico - Segundo Módulo**  
**Programación Avanzada en Ciencia de Datos**  
**Universidad de la Ciudad de Buenos Aires**
