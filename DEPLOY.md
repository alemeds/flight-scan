# 🚀 Guía de Despliegue - Flight Scan

Esta guía te ayudará a desplegar Flight Scan tanto localmente como en Streamlit Cloud.

## 📋 Tabla de Contenidos

1. [Despliegue Local](#despliegue-local)
2. [Despliegue en Streamlit Cloud](#despliegue-en-streamlit-cloud)
3. [Configuración de GitHub Actions](#configuración-de-github-actions)
4. [Verificación y Pruebas](#verificación-y-pruebas)
5. [Troubleshooting](#troubleshooting)

---

## 🏠 Despliegue Local

### Paso 1: Clonar el Repositorio

```bash
git clone https://github.com/alemeds/flight-scan.git
cd flight-scan
```

### Paso 2: Crear Entorno Virtual

**En Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**En Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Paso 3: Instalar Dependencias

```bash
pip install -r requirements.txt
```

### Paso 4: Configurar Credenciales

1. Crea la carpeta `.streamlit`:
```bash
mkdir .streamlit
```

2. Crea el archivo `.streamlit/secrets.toml`:
```bash
# En Windows
copy secrets.toml.example .streamlit\secrets.toml

# En Mac/Linux
cp secrets.toml.example .streamlit/secrets.toml
```

3. Edita `.streamlit/secrets.toml` con tus credenciales (ya están incluidas en el ejemplo)

### Paso 5: Inicializar Base de Datos

```bash
python setup_database.py
```

Deberías ver:
```
✅ Conexión exitosa a PostgreSQL
✅ Tablas creadas/verificadas correctamente
```

### Paso 6: Probar Conexiones

```bash
python test_connection.py
```

Este script verificará:
- ✅ Conexión a PostgreSQL
- ✅ Autenticación con Amadeus
- ✅ Flujo completo (opcional)

### Paso 7: Ejecutar la Aplicación

```bash
streamlit run app.py
```

La aplicación se abrirá en `http://localhost:8501`

---

## ☁️ Despliegue en Streamlit Cloud

### Requisitos Previos

- Cuenta en [Streamlit Cloud](https://share.streamlit.io)
- Repositorio en GitHub (ya tienes: alemeds/flight-scan)
- Credenciales de PostgreSQL y Amadeus

### Paso 1: Conectar Repositorio

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Haz clic en **"New app"**
3. Conecta tu cuenta de GitHub si aún no lo has hecho
4. Selecciona:
   - **Repository**: `alemeds/flight-scan`
   - **Branch**: `main`
   - **Main file path**: `app.py`

### Paso 2: Configurar Secrets

1. En la configuración de tu app, ve a **"Settings"**
2. Haz clic en **"Secrets"**
3. Copia y pega el siguiente contenido:

```toml
DB_HOST = "dpg-d3g6g1p5pdvs73e8c0rg-a.oregon-postgres.render.com"
DB_PORT = 5432
DB_NAME = "vuelos_9lrw"
DB_USER = "vuelos"
DB_PASSWORD = "FOa7NtnssHMgheHCMilCRXYmLYQn7pko"

AMADEUS_API_KEY = "KAomv16lpjbjJFAmj42OgXtzEOzCHHlx"
AMADEUS_API_SECRET = "mwHaoM1gEV9bweN2"
```

4. Haz clic en **"Save"**

### Paso 3: Desplegar

1. Haz clic en **"Deploy!"**
2. Espera a que se complete el despliegue (2-3 minutos)
3. Tu app estará disponible en una URL como: `https://flight-scan-xxx.streamlit.app`

### Paso 4: Configuración Adicional (Opcional)

En **Settings** → **General**:
- **App name**: Flight Scan
- **Description**: Monitor de tarifas aéreas
- **Icon**: ✈️

---

## ⚙️ Configuración de GitHub Actions

Para habilitar el monitoreo automático cada 2 horas:

### Paso 1: Agregar Secrets en GitHub

1. Ve a tu repositorio: `github.com/alemeds/flight-scan`
2. Settings → Secrets and variables → Actions
3. Haz clic en **"New repository secret"**
4. Agrega los siguientes secrets uno por uno:

| Nombre | Valor |
|--------|-------|
| `DB_HOST` | `dpg-d3g6g1p5pdvs73e8c0rg-a.oregon-postgres.render.com` |
| `DB_PORT` | `5432` |
| `DB_NAME` | `vuelos_9lrw` |
| `DB_USER` | `vuelos` |
| `DB_PASSWORD` | `FOa7NtnssHMgheHCMilCRXYmLYQn7pko` |
| `AMADEUS_API_KEY` | `KAomv16lpjbjJFAmj42OgXtzEOzCHHlx` |
| `AMADEUS_API_SECRET` | `mwHaoM1gEV9bweN2` |

### Paso 2: Habilitar GitHub Actions

El archivo `.github/workflows/monitor.yml` ya está en el repositorio. GitHub Actions se activará automáticamente.

### Paso 3: Verificar Ejecución

1. Ve a la pestaña **"Actions"** en tu repositorio
2. Deberías ver el workflow **"Flight Monitor Automático"**
3. El workflow se ejecuta:
   - Automáticamente cada 2 horas
   - Manualmente desde la UI de GitHub (botón "Run workflow")

### Paso 4: Ejecutar Manualmente (Opcional)

1. Ve a Actions → Flight Monitor Automático
2. Haz clic en **"Run workflow"**
3. Selecciona la rama `main`
4. Haz clic en **"Run workflow"**

---

## ✅ Verificación y Pruebas

### Verificar Base de Datos

Conéctate a PostgreSQL para verificar los datos:

```bash
PGPASSWORD=FOa7NtnssHMgheHCMilCRXYmLYQn7pko psql -h dpg-d3g6g1p5pdvs73e8c0rg-a.oregon-postgres.render.com -U vuelos vuelos_9lrw
```

Consultas útiles:

```sql
-- Ver total de registros
SELECT COUNT(*) FROM flight_searches;

-- Ver últimas búsquedas
SELECT * FROM flight_searches ORDER BY search_timestamp DESC LIMIT 10;

-- Ver estadísticas por ruta
SELECT origin, destination, 
       COUNT(*) as searches,
       MIN(price) as min_price,
       AVG(price) as avg_price,
       MAX(price) as max_price
FROM flight_searches
GROUP BY origin, destination
ORDER BY searches DESC;
```

### Verificar API de Amadeus

Ejecuta el script de prueba:

```bash
python test_connection.py
```

### Verificar Dashboard

1. Abre la aplicación (local o en Streamlit Cloud)
2. Realiza una búsqueda de prueba:
   - Origen: EZE
   - Destino: MIA
   - Fecha: 30 días adelante
3. Verifica que:
   - ✅ Se muestran resultados
   - ✅ Los datos se guardan en la BD
   - ✅ Los gráficos se generan correctamente

---

## 🔧 Troubleshooting

### Error: "No module named 'streamlit'"

**Solución**: Asegúrate de haber activado el entorno virtual e instalado las dependencias:

```bash
source venv/bin/activate  # o venv\Scripts\activate en Windows
pip install -r requirements.txt
```

### Error: "Connection refused" (PostgreSQL)

**Causas posibles**:
1. Base de datos en Render inactiva
2. IP no autorizada
3. Credenciales incorrectas

**Solución**:
1. Verifica que la BD esté activa en Render
2. Render permite conexiones desde cualquier IP por defecto
3. Verifica las credenciales en `secrets.toml`

### Error: "401 Unauthorized" (Amadeus)

**Solución**: Verifica que `AMADEUS_API_KEY` y `AMADEUS_API_SECRET` sean correctos.

### Error: "No se encontraron ofertas"

**Causas posibles**:
1. Ruta no disponible
2. Fechas muy lejanas o muy cercanas
3. No hay disponibilidad

**Solución**:
- Intenta con rutas populares (EZE-MIA, EZE-MAD)
- Usa fechas entre 15 y 60 días adelante

### La aplicación en Streamlit Cloud se reinicia constantemente

**Solución**: 
1. Verifica los logs en Streamlit Cloud
2. Asegúrate de que todos los secrets estén configurados
3. Revisa que `requirements.txt` tenga todas las dependencias

### GitHub Actions falla

**Solución**:
1. Verifica que todos los secrets estén configurados en GitHub
2. Revisa los logs en la pestaña Actions
3. Asegúrate de que los nombres de los secrets coincidan exactamente

---

## 📊 Monitoreo de Uso

### Límites de Amadeus (Test Environment)

- **Requests por mes**: 10,000
- **Requests por segundo**: 10

### Límites de PostgreSQL (Render Free Tier)

- **Storage**: 1 GB
- **Conexiones**: 97 máximo

### Límites de Streamlit Cloud (Free Tier)

- **Resources**: 1 GB RAM
- **Uptime**: Puede entrar en sleep después de inactividad

---

## 🎯 Próximos Pasos

Una vez desplegado:

1. ✅ Personaliza las rutas en `monitor_script.py`
2. ✅ Ajusta la frecuencia en `.github/workflows/monitor.yml`
3. ✅ Configura alertas de precios (feature futura)
4. ✅ Exporta reportes periódicos
5. ✅ Comparte el dashboard con otros usuarios

---

## 📞 Soporte

Si encuentras problemas:

1. Revisa esta guía de troubleshooting
2. Consulta los logs de la aplicación
3. Abre un issue en GitHub

---

**¡Listo! Tu sistema de monitoreo de vuelos está operativo** ✈️📊
