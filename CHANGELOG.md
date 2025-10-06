
## Changelog

# 📝 Registro de Cambios - Flight Trading Monitor

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [2.0.0] - 2025-10-06

### Agregado
- Sistema de precios objetivo con alertas visuales
  - Los usuarios pueden definir un precio meta para sus búsquedas
  - Alerta con confeti cuando se alcanza el precio objetivo
  - Indicador visual en la tabla de resultados
- Modo simulación (Demo) para pruebas sin API
  - Generación de datos realistas basados en patrones de precios
  - Factor de anticipación (precios varían según días hasta el vuelo)
  - No consume cuota de API de Amadeus
- Gestión de búsquedas activas
  - Panel en sidebar con búsquedas monitoreadas
  - Barra de progreso hacia precio objetivo
  - Capacidad de eliminar búsquedas completadas
- Fallback automático a modo simulación si API falla
- Validación de códigos IATA en `amadeus_client.py`
- Índice en columna `price` para optimización de consultas
- Timeout de 10-15 segundos en peticiones HTTP

### Cambiado
- Tamaño fijo de marcadores en gráfico scatter (corrige error de tipo)
- Campo `airline` en BD cambiado de VARCHAR(50) a VARCHAR(100)
- Mejora en manejo de errores con validaciones robustas
- Mapeo extendido de aerolíneas (50+ códigos IATA)
- Retorno consistente de listas vacías en métodos de `database.py`

### Corregido
- Error "DataFrame is ambiguous" en validaciones condicionales
- Error en gráfico scatter por tipo incorrecto en parámetro `size`
- Validación de `airline = None` antes de insertar en BD
- Manejo de respuestas vacías de la API de Amadeus
- Parsing de duración ISO 8601 con manejo de errores

### Seguridad
- Eliminación de credenciales expuestas del README
- Uso de placeholders genéricos en documentación
- Advertencias sobre protección de credenciales

## [1.0.0] - 2024-11-15

### Agregado
- Implementación inicial de la aplicación
- Integración con API de Amadeus para búsqueda de vuelos
- Conexión a base de datos PostgreSQL en Render
- Dashboard interactivo con Streamlit
- Visualizaciones con Plotly:
  - Gráfico de líneas: Evolución temporal de precios
  - Box plot: Distribución por aerolínea
  - Scatter plot: Precios por fecha
- Tres pestañas principales:
  - Dashboard: Resumen general
  - Análisis de Tarifas: Análisis detallado por ruta
  - Historial: Búsquedas realizadas con filtros
- Sistema de exportación a CSV
- Módulo `database.py` con métodos principales:
  - `insert_flight_offer()`
  - `get_recent_searches()`
  - `get_unique_routes()`
  - `get_searches_by_route()`
- Módulo `amadeus_client.py` con:
  - Autenticación OAuth2
  - Búsqueda de vuelos
  - Procesamiento de ofertas
  - Conversión de códigos IATA a nombres de aerolíneas
- Script `setup_database.py` para inicialización
- Documentación completa en README.md
- Archivo `.gitignore` para protección de credenciales

### Características Técnicas
- Arquitectura modular con separación de responsabilidades
- Caché de recursos con `@st.cache_resource`
- Manejo de autenticación con tokens temporales
- Índices en BD para optimización de consultas
- Almacenamiento de datos completos en JSONB

---

## Tipos de Cambios

- **Agregado**: Nuevas características
- **Cambiado**: Cambios en funcionalidad existente
- **Obsoleto**: Características que serán removidas
- **Eliminado**: Características removidas
- **Corregido**: Corrección de bugs
- **Seguridad**: Cambios relacionados con vulnerabilidades

## Versionado

Este proyecto utiliza Semantic Versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Cambios incompatibles en la API
- **MINOR**: Nuevas funcionalidades compatibles
- **PATCH**: Correcciones de bugs compatibles

## Próximas Versiones

### [2.1.0] - Planeado
- Notificaciones por email cuando se alcanza precio objetivo
- Modo oscuro / claro para la interfaz
- Gráficos de predicción de precios con ML
- Comparador de múltiples rutas simultáneas
- Exportación a Excel con formato
- Historial de precios por vuelo específico

### [3.0.0] - Futuro
- Integración con múltiples APIs de vuelos (Skyscanner, Kayak)
- Sistema de autenticación de usuarios
- Perfiles personalizados con preferencias guardadas
- API REST para integración con otras aplicaciones
- Aplicación móvil (React Native)
- Alertas push en tiempo real
