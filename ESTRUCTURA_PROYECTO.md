# 📁 Estructura del Proyecto Flight Scan

## 🌳 Árbol de Archivos

```
flight-scan/
│
├── 📄 app.py                          # Aplicación principal de Streamlit
├── 📄 database.py                     # Módulo de gestión de PostgreSQL
├── 📄 amadeus_client.py               # Cliente para API de Amadeus
├── 📄 setup_database.py               # Script de inicialización de BD
├── 📄 monitor_script.py               # Script de monitoreo automático
├── 📄 test_connection.py              # Script de pruebas de conexión
│
├── 📄 requirements.txt                # Dependencias de Python
├── 📄 .gitignore                      # Archivos a ignorar en Git
├── 📄 README.md                       # Documentación principal
├── 📄 DEPLOY.md                       # Guía de despliegue
├── 📄 secrets.toml.example            # Plantilla de configuración
│
├── 📁 .streamlit/                     # Configuración de Streamlit
│   └── 📄 secrets.toml                # Credenciales (NO en repo)
│
└── 📁 .github/                        # Configuración de GitHub
    └── 📁 workflows/
        └── 📄 monitor.yml             # GitHub Actions workflow
```

## 📋 Checklist de Entrega

### ✅ Archivos Principales

- [x] `app.py` - Dashboard interactivo con Streamlit
- [x] `database.py` - Conexión y operaciones con PostgreSQL
- [x] `amadeus_client.py` - Integración con API de Amadeus
- [x] `requirements.txt` - Todas las dependencias listadas

### ✅ Scripts Auxiliares

- [x] `setup_database.py` - Inicialización de base de datos
- [x] `monitor_script.py` - Monitoreo automático
- [x] `test_connection.py` - Pruebas de conexión

### ✅ Documentación

- [x] `README.md` - Documentación completa del proyecto
- [x] `DEPLOY.md` - Instrucciones de despliegue
- [x] `secrets.toml.example` - Plantilla de configuración
- [x] Comentarios en código Python

### ✅ Configuración

- [x] `.gitignore` - Protección de credenciales
- [x] `.github/workflows/monitor.yml` - Automatización

### ✅ Base de Datos

- [x] Conexión a PostgreSQL en Render configurada
- [x] Tabla `flight_searches` creada
- [x] Índices para optimización
- [x] Funciones de inserción y consulta

### ✅ API de Amadeus

- [x] Autenticación OAuth2 implementada
- [x] Búsqueda de vuelos funcional
- [x] Manejo de respuestas y errores
- [x] Parseo de ofertas

### ✅ Dashboard

- [x] Búsqueda manual de vuelos
- [x] Configuración de monitoreo automático
- [x] Gráficos de evolución de precios
- [x] Estadísticas (min, max, promedio)
- [x] Comparación por aerolíneas
- [x] Exportación a CSV
- [x] Filtros interactivos

### ✅ Visualizaciones

- [x] Gráfico de líneas (evolución temporal)
- [x] Box plot (distribución por aerolínea)
- [x] Métricas (cards con estadísticas)
- [x] Tabla interactiva de datos

### ✅ Funcionalidades

- [x] Consulta en tiempo real
- [x] Almacenamiento persistente
- [x] Análisis histórico
- [x] Exportación de datos
- [x] Configuración de frecuencias

### ✅ Replicabilidad

- [x] Instrucciones claras en README
- [x] Script de inicialización
- [x] Script de pruebas
- [x] Ejemplo de configuración
- [x] Manejo de errores documentado

---

## 📝 Descripción de Archivos

### `app.py`
**Propósito**: Aplicación principal del dashboard  
**Funciones clave**:
- Interfaz de usuario con Streamlit
- Búsqueda manual de vuelos
- Configuración de monitoreo
- Visualización de datos históricos
- Exportación de resultados

### `database.py`
**Propósito**: Gestión de PostgreSQL  
**Funciones clave**:
- `connect()` - Conexión a la base de datos
- `create_tables()` - Creación de esquema
- `insert_flight_offer()` - Guardar ofertas
- `get_price_history()` - Obtener histórico
- `get_statistics()` - Calcular estadísticas

### `amadeus_client.py`
**Propósito**: Cliente para API de Amadeus  
**Funciones clave**:
- `_get_access_token()` - Autenticación OAuth2
- `search_flights()` - Búsqueda de vuelos
- `_parse_flight_offers()` - Procesar respuestas
- `_get_airline_name()` - Mapeo de aerolíneas

### `setup_database.py`
**Propósito**: Inicialización del proyecto  
**Uso**: `python setup_database.py`  
**Resultado**: Crea tablas e índices en PostgreSQL

### `monitor_script.py`
**Propósito**: Monitoreo automático  
**Uso**: `python monitor_script.py` (manual o con cron/GitHub Actions)  
**Resultado**: Consulta rutas definidas y guarda en BD

### `test_connection.py`
**Propósito**: Verificación del sistema  
**Uso**: `python test_connection.py`  
**Pruebas**:
1. Conexión a PostgreSQL
2. Autenticación con Amadeus
3. Flujo completo (opcional)

---

## 🎯 Cumplimiento del Trabajo Práctico

### 1. Consulta del Dataset ✅

- [x] **Dataset seleccionado**: Amadeus Flight Offers API
- [x] **Método de obtención**: API REST
- [x] **Documentación**: README con enlace a la fuente

### 2. Almacenamiento en Base de Datos ✅

- [x] **Motor elegido**: PostgreSQL
- [x] **Alojamiento**: Render.com
- [x] **Diseño**: Tabla `flight_searches` con estructura normalizada
- [x] **Carga de datos**: Sistema robusto con manejo de errores

### 3. Construcción del Dashboard ✅

- [x] **Herramienta**: Streamlit (notebook interactiva)
- [x] **Visualizaciones**: Plotly para gráficos interactivos
- [x] **Funcionalidades**: 
  - Exploración de datos
  - Filtros interactivos
  - Múltiples vistas (tabs)
  - Exportación de datos

### 4. Documentación y Entrega ✅

- [x] **Repositorio**: [github.com/alemeds/flight-scan](https://github.com/alemeds/flight-scan)
- [x] **README completo** con:
  - Dataset y fuente
  - Motor de BD e instrucciones
  - Pasos para ejecutar
