# Flight Scan — CLAUDE.md

> Archivo de configuración para Claude Code — Contiene reglas técnicas y arquitectura del proyecto.

---

## 🏗️ Arquitectura

Flight Scan es una aplicación Streamlit que monitorea tarifas aéreas utilizando la API de Amadeus. Tiene 3 capas claramente separadas:

### Capa 1: Presentación (app.py)
- **Framework:** Streamlit
- **Responsabilidad:** UI, input del usuario, visualización de datos
- **No hace:** Lógica de negocio, acceso a BD

### Capa 2: Lógica de Negocio (amadeus_client.py)
- **Responsabilidad:** Interacción con API Amadeus, validación, parsing
- **No hace:** Acceso a BD, presentación, autenticación de usuario

### Capa 3: Datos (database.py)
- **Responsabilidad:** Persistencia en PostgreSQL, queries
- **No hace:** Lógica de negocio, formateo de respuestas

---

## 📋 Requisitos de Código

### Obligatorios

1. **Type Hints en todo**
   ```python
   def search_flights(origin: str, destination: str, departure_date: str) -> List[Dict]:
       pass
   ```
   - Sin excepciones
   - Incluir tipos de retorno y parámetros
   - Usar `typing` module (List, Dict, Optional, etc.)

2. **Validación en límites del sistema**
   - Entrada de usuario: SIEMPRE validar
   - API externa: SIEMPRE validar respuesta
   - BD: SIEMPRE usar prepared statements
   - Interno: confiar en garantías

3. **Manejo de recursos con try/finally**
   ```python
   cursor = connection.cursor()
   try:
       cursor.execute(query, params)
   finally:
       cursor.close()
   ```
   - Conexiones BD: Cerrar SIEMPRE
   - Archivos: Usar `with` context manager
   - Sockets: Cerrar explícitamente

4. **Logging en lugar de print()**
   ```python
   import logging
   logger = logging.getLogger(__name__)
   logger.info("Mensaje seguro")
   logger.error("Error sin datos sensibles")
   ```
   - NUNCA loguear tokens, passwords, datos personales
   - Loguear `type(e).__name__` no `str(e)` en excepciones

5. **Excepciones Custom**
   - `AuthenticationError` — Token inválido, auth fallida
   - `APIError` — Respuesta inválida de Amadeus
   - `TimeoutError` — Timeout en API
   - `DatabaseError` — Error en operación de BD

---

## 🔒 Seguridad — Reglas No Negociables

### Secretos
- **CERO hardcoding:** `API_KEY`, `DATABASE_URL`, passwords JAMÁS en código
- **.env siempre:** Variables sensibles en `.env`, excluido en `.gitignore`
- **.env.example:** Documentar variables requeridas SIN valores
- **Rotation:** Cambiar credenciales si se exponen

### Validación de Entrada
```python
# IATA codes: Exactamente 3 letras mayúsculas
import re
if not re.match(r'^[A-Z]{3}$', iata_code):
    raise ValueError("Código IATA inválido")

# Dates: ISO 8601, deben ser futuras
from datetime import datetime
departure = datetime.fromisoformat(date_str)
if departure < datetime.now():
    raise ValueError("Fecha debe ser futura")

# Adults: Entre 1 y 9
if not (1 <= adults <= 9):
    raise ValueError("Adults debe estar entre 1 y 9")
```

### SQL Injection Prevention
```python
# ✅ CORRECTO: Prepared statements
cursor.execute("SELECT * FROM flights WHERE origin = %s", (origin,))

# ❌ NUNCA: String formatting
cursor.execute(f"SELECT * FROM flights WHERE origin = '{origin}'")  # VULNERABLE
```

### Información Sensible en Logs
```python
# ✅ CORRECTO: Solo tipo de error
except Exception as e:
    logger.error(f"Auth failed: {type(e).__name__}")

# ❌ NUNCA: Exponer datos
logger.error(f"Auth failed: {e}")  # Puede contener token
```

---

## 📁 Estructura de Proyecto

```
flight-scan/
├── src/                      # Código fuente (opcional, actual: raíz)
│   ├── app.py               # UI Streamlit
│   ├── amadeus_client.py    # Cliente API Amadeus
│   └── database.py          # Acceso a datos PostgreSQL
│
├── tests/                   # Suite de tests
│   ├── conftest.py         # Fixtures pytest
│   ├── test_amadeus_client.py
│   ├── test_database.py
│   ├── test_integration.py
│   └── test_performance.py
│
├── scripts/                # Utilidades
│   ├── setup_database.py
│   └── monitor_script.py
│
├── docs/                   # Documentación
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   └── API_GUIDE.md
│
├── .github/workflows/      # CI/CD
│   ├── ci.yml             # Tests + linting
│   └── deploy.yml         # Deploy a Streamlit Cloud
│
├── .env.example            # Plantilla de variables de entorno
├── .gitignore             # Excluir .env, __pycache__, etc.
├── requirements.txt        # Dependencias principales
├── requirements-dev.txt    # Dependencias de desarrollo
├── pytest.ini             # Configuración de pytest
└── README.md              # Guía de uso
```

---

## 🧪 Testing & Calidad

### Coverage Mínimo
- **Lógica crítica:** 80%+ (amadeus_client.py, database.py)
- **UI (app.py):** Manual testing acceptable
- **Utilidades:** 60%+ acceptable

### Naming de Tests
```python
# ✅ CORRECTO: Claro qué se testea
def test_should_reject_invalid_iata_code():
    pass

def test_should_parse_iso8601_duration_correctly():
    pass

# ❌ EVITAR: Vago o incompleto
def test_iata():
    pass

def test_duration():
    pass
```

### Tipos de Tests
- **Unit:** Aislado, mockeado, <100ms
- **Integration:** Flujo completo, >100ms OK
- **Performance:** Benchmarks con targets

### Ejecución
```bash
# Tests unitarios
pytest tests/test_*.py -v

# Con coverage
pytest tests/ --cov=. --cov-report=term-missing

# Performance
pytest tests/test_performance.py -v
```

---

## 🔧 Desarrollo Local

### Setup
```bash
# 1. Clonar repo
git clone https://github.com/alemeds/flight-scan.git
cd flight-scan

# 2. Crear venv
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# source venv\Scripts\activate  # Windows

# 3. Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con credenciales reales

# 5. Setup BD (opcional)
python scripts/setup_database.py

# 6. Ejecutar app
streamlit run app.py
```

### Desarrollo Diario
```bash
# Ejecutar tests
pytest tests/ -v

# Correr app local
streamlit run app.py

# Profiling/benchmarks
pytest tests/test_performance.py -v

# Linting (opcional)
black src/ tests/
flake8 src/ tests/
mypy src/
```

---

## 📦 Dependencias

### Principales (requirements.txt)
```
streamlit>=1.28.0          # UI framework
pandas>=2.0.0              # Data manipulation
plotly>=5.17.0             # Visualizaciones
psycopg2-binary>=2.9.9     # PostgreSQL driver
requests>=2.31.0           # HTTP client
python-dateutil>=2.8.2     # Date utilities
```

### Desarrollo (requirements-dev.txt)
```
pytest>=7.4.0              # Testing framework
pytest-cov>=4.1.0          # Coverage reporting
pytest-mock>=3.12.0        # Mocking utilities
black>=23.12.0             # Code formatter
flake8>=6.1.0              # Linter
mypy>=1.7.0                # Type checker
```

**Nota:** TODAS las versiones fijadas para reproducibilidad.

---

## 🚀 Deployment

### Streamlit Cloud
```bash
# 1. Push a GitHub
git push origin main

# 2. Connect en streamlit.io
# - Repo: alemeds/flight-scan
# - Branch: main
# - Main file: app.py

# 3. Setup secrets (en Streamlit Cloud settings)
AMADEUS_API_KEY=xxx
AMADEUS_API_SECRET=yyy
DATABASE_URL=postgres://...
```

### Producción Privada (opcional)
```bash
# Docker
docker build -t flight-scan .
docker run -p 8501:8501 --env-file .env flight-scan

# Gunicorn + Nginx (para production real)
# Ver docs/DEPLOYMENT.md
```

---

## 🔍 Code Review Checklist

Antes de mergear cualquier PR, verificar:

- [ ] ✅ Type hints en todas las funciones nuevas
- [ ] ✅ Todos los inputs validados
- [ ] ✅ Exceptions custom usadas (no genéricas)
- [ ] ✅ Resource cleanup (try/finally)
- [ ] ✅ Logging seguro (sin datos sensibles)
- [ ] ✅ Tests unitarios con cobertura 80%+
- [ ] ✅ Tests pasando (pytest -v)
- [ ] ✅ Sin hardcoded secrets
- [ ] ✅ Prepared statements para BD
- [ ] ✅ Docstrings para funciones públicas

---

## 📊 Métricas & Monitoring

### En Desarrollo
```bash
# Coverage
pytest --cov=. --cov-report=html

# Profiling
pytest tests/test_performance.py -v
```

### En Producción
- Monitorizar API response time (target: <500ms)
- Monitorizar BD latency (target: <100ms)
- Monitorizar error rate (target: <1%)
- Monitorizar memory usage (target: <100MB)

---

## 🔗 Decisiones Arquitectónicas

### 1. Separación en 3 capas
**Ventaja:** Testeable, mantenible, escalable  
**Tradeoff:** Más archivos, menos integración  
**Alternativa rechazada:** Monolítico (difícil de testear)

### 2. PostgreSQL en lugar de SQLite
**Ventaja:** Escalable, concurrencia, seguridad  
**Tradeoff:** Requiere server externo  
**Alternativa rechazada:** SQLite (local, pero limitado)

### 3. Prepared statements para TODA BD
**Ventaja:** Prevenir SQL injection  
**Tradeoff:** Slightly más lento (pero negligible)  
**Alternativa rechazada:** ORM (más lento, abstracción innecesaria)

### 4. Lazy authentication en AmadeusClient
**Ventaja:** No falla init si API está down  
**Tradeoff:** Error más tarde (en search)  
**Alternativa rechazada:** Eager auth (fail-fast pero error al init)

---

## 🐛 Debugging

### Logging
```bash
# Ver logs en consola
streamlit run app.py

# Ver logs en archivo
python -u app.py > app.log 2>&1
```

### Database
```bash
# Conectar a BD
psql postgres://user:pass@localhost/flight_scan

# Ver tablas
\dt

# Query manual
SELECT * FROM flight_offers ORDER BY created_at DESC LIMIT 10;
```

### Amadeus API
```bash
# Test auth
curl -X POST https://api.amadeus.com/v1/security/oauth2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=xxx&client_secret=yyy&grant_type=client_credentials"
```

---

## 📞 Contacto & Soporte

- **Issues:** GitHub Issues
- **Documentación:** Ver `docs/` folder
- **Performance:** Ver FASE5_PERFORMANCE_REPORT.md
- **Tests:** Ver FASE4_TESTING_REPORT.md

---

## 📝 Changelog & Versioning

- **v1.0.0** — Beta stable (Fases 1-5 completadas)
- **v0.9.0** — Beta con tests (Fase 4)
- **v0.8.0** — Code review fixes (Fase 1-3)

---

**Última actualización:** 2026-07-10  
**Versión:** v1.0.0  
**Responsable:** Team Flight Scan
