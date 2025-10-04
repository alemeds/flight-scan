# Guía de Deployment en Streamlit Cloud

## 📋 Archivos Necesarios

Asegúrate de tener todos estos archivos en tu repositorio:

```
flight-scan/
├── app.py                    # ✅ LISTO
├── database.py               # ✅ LISTO
├── amadeus_client.py         # ✅ LISTO
├── requirements.txt          # ✅ LISTO
├── setup_database.py         # ✅ LISTO (opcional)
├── monitor_script.py         # ✅ LISTO (opcional)
└── README.md
```

## 🚀 Pasos para Deploy en Streamlit Cloud

### 1. Preparar el Repositorio

1. Sube todos los archivos a tu repositorio de GitHub
2. **NO INCLUYAS** el archivo `.streamlit/secrets.toml` en GitHub
3. Asegúrate de tener un archivo `.gitignore` con:

```
.streamlit/
__pycache__/
*.pyc
.env
venv/
.DS_Store
```

### 2. Configurar Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Inicia sesión con tu cuenta de GitHub
3. Click en "New app"
4. Selecciona tu repositorio `flight-scan`
5. Branch: `main`
6. Main file path: `app.py`

### 3. Configurar Secrets en Streamlit Cloud

En la configuración de la app en Streamlit Cloud:

1. Ve a "Settings" → "Secrets"
2. Copia y pega el siguiente contenido:

```toml
# Database Configuration
DB_HOST = "dpg-d3g6g1p5pdvs73e8c0rg-a.oregon-postgres.render.com"
DB_PORT = 5432
DB_NAME = "vuelos_9lrw"
DB_USER = "vuelos"
DB_PASSWORD = "FOa7NtnssHMgheHCMilCRXYmLYQn7pko"

# Amadeus API Configuration
AMADEUS_API_KEY = "KAomv16lpjbjJFAmj42OgXtzEOzCHHlx"
AMADEUS_API_SECRET = "mwHaoM1gEV9bweN2"
```

3. Click en "Save"

### 4. Deploy

1. Click en "Deploy!"
2. Espera a que la aplicación se construya (2-3 minutos)
3. ¡Tu app estará disponible en una URL pública!

## 🧪 Prueba Local (Opcional)

Si quieres probar localmente antes de hacer deploy:

```bash
# 1. Clonar repositorio
git clone https://github.com/alemeds/flight-scan.git
cd flight-scan

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Crear archivo de secrets
mkdir .streamlit
# Copia el contenido del template en .streamlit/secrets.toml

# 5. Inicializar base de datos (opcional, ya está creada)
python setup_database.py

# 6. Ejecutar app
streamlit run app.py
```

## 🔍 Verificación Post-Deploy

Una vez deployada la app, verifica:

1. ✅ La página carga sin errores
2. ✅ Puedes hacer una búsqueda de vuelos
3. ✅ Los resultados se guardan en la base de datos
4. ✅ Las visualizaciones funcionan correctamente
5. ✅ El historial muestra datos

## ⚠️ Solución de Problemas

### Error: "Could not connect to database"
- Verifica que las credenciales en Secrets sean correctas
- Asegúrate de que la base de datos en Render esté activa

### Error: "Error obteniendo token: 401"
- Verifica las credenciales de Amadeus API
- Asegúrate de estar usando las claves del ambiente correcto (test/production)

### Error: "ModuleNotFoundError"
- Verifica que `requirements.txt` tenga todas las dependencias
- Reconstruye la app en Streamlit Cloud

### La app se queda "cargando"
- Revisa los logs en Streamlit Cloud
- Verifica que no haya errores de sintaxis en el código

## 📊 Estructura de Datos Consistente

Los archivos están diseñados para ser consistentes entre sí:

### `amadeus_client.py` retorna:
```python
{
    'id': str,
    'price': float,
    'currency': str,
    'airline': str,
    'airline_code': str,
    'duration': str,
    'stops': int,
    'departure_time': str,
    'arrival_time': str,
    'raw_data': dict
}
```

### `database.py` espera:
```python
insert_flight_offer(
    origin: str,           # Código IATA
    destination: str,      # Código IATA
    departure_date: str,   # YYYY-MM-DD
    return_date: str,      # YYYY-MM-DD
    price: float,
    currency: str,
    airline: str,
    flight_data: dict,     # JSON con datos completos
    adults: int
)
```

### `app.py` usa:
- Los datos de `amadeus_client.py` para mostrar resultados
- Los métodos de `database.py` para guardar y consultar
- Ambos son compatibles sin conversiones adicionales

## 🎯 Funcionalidades Implementadas

✅ **Búsqueda de Vuelos**
- Consulta en tiempo real a Amadeus API
- Almacenamiento automático en PostgreSQL
- Soporte para vuelos de ida y vuelta

✅ **Dashboard Interactivo**
- Métricas principales
- Gráficos de evolución temporal
- Distribución por aerolínea

✅ **Análisis de Tarifas**
- Filtros por ruta y período
- Estadísticas detalladas
- Exportación a CSV

✅ **Historial**
- Visualización completa de búsquedas
- Filtros múltiples
- Exportación de datos

## 📝 Notas Adicionales

- La API de Amadeus en modo Test tiene límites de rate limiting
- Los datos se almacenan en PostgreSQL de forma permanente
- El monitoreo automático requiere GitHub Actions o similar
- Streamlit Cloud tiene algunas limitaciones para procesos en background

## 🆘 Soporte

Si encuentras problemas:
1. Revisa los logs en Streamlit Cloud
2. Verifica la documentación de Amadeus: https://developers.amadeus.com
3. Consulta la documentación de Streamlit: https://docs.streamlit.io

---

**Desarrollado para:** Programación Avanzada en Ciencia de Datos  
**Universidad:** Ciudad de Buenos Aires  
**Powered by:** Amadeus API & PostgreSQL on Render
