# 🚀 Flight Scan — DEPLOYMENT GUIDE

---

## 📋 Tabla de Contenidos

1. [Deployment en Streamlit Cloud](#streamlit-cloud)
2. [Deployment Privado (Docker)](#docker)
3. [Configuración de Base de Datos](#configuración-de-base-de-datos)
4. [Monitoreo & Alertas](#monitoreo--alertas)
5. [Troubleshooting](#troubleshooting)

---

## ☁️ Streamlit Cloud

### Opción Recomendada (Easiest)

**Ventajas:**
- ✅ Cero infraestructura
- ✅ Auto-deploy en cada push
- ✅ HTTPS automático
- ✅ Scaling automático

**Limitaciones:**
- ❌ Solo para 1 app gratuita
- ❌ BD externa requerida
- ❌ Recursos limitados (1GB RAM)

### Setup

#### 1. Conectar GitHub
```bash
# En https://streamlit.io/cloud
1. Click "New app"
2. Seleccionar repo: alemeds/flight-scan
3. Branch: main
4. File: app.py
```

#### 2. Configurar Secrets
En Streamlit Cloud dashboard:
```
Settings → Secrets management
```

Agregar en `secrets.toml`:
```toml
# Amadeus API
AMADEUS_API_KEY = "your_api_key_here"
AMADEUS_API_SECRET = "your_api_secret_here"

# Database
DATABASE_URL = "postgresql://user:pass@host:5432/flight_scan"

# Environment
ENV = "production"
```

#### 3. Configurar BD
```bash
# Crear instancia PostgreSQL (e.g., AWS RDS, Heroku Postgres)
# Ejecutar migrations
python scripts/setup_database.py
```

#### 4. Deploy
```bash
# Push a GitHub trigger auto-deploy
git push origin main

# Verificar en https://share.streamlit.io/alemeds/flight-scan
```

---

## 🐳 Docker (Privado)

Para deployar en infraestructura propia.

### 1. Crear Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY app.py amadeus_client.py database.py ./
COPY scripts/ ./scripts/

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501"]
```

### 2. Crear .dockerignore

```
.git
.env
__pycache__
*.pyc
.pytest_cache
.mypy_cache
*.egg-info
.venv
venv
```

### 3. Build & Run Localmente

```bash
# Build image
docker build -t flight-scan:latest .

# Run container
docker run -p 8501:8501 \
  -e AMADEUS_API_KEY="xxx" \
  -e AMADEUS_API_SECRET="yyy" \
  -e DATABASE_URL="postgresql://..." \
  flight-scan:latest
```

Acceder en: `http://localhost:8501`

### 4. Push a Registry

```bash
# Docker Hub
docker tag flight-scan:latest username/flight-scan:latest
docker login
docker push username/flight-scan:latest

# GitHub Container Registry
docker tag flight-scan:latest ghcr.io/alemeds/flight-scan:latest
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
docker push ghcr.io/alemeds/flight-scan:latest
```

### 5. Deploy a Producción

#### Opción A: Docker Compose (Simple)

`docker-compose.yml`:
```yaml
version: '3.8'

services:
  flight-scan:
    image: flight-scan:latest
    ports:
      - "8501:8501"
    environment:
      AMADEUS_API_KEY: ${AMADEUS_API_KEY}
      AMADEUS_API_SECRET: ${AMADEUS_API_SECRET}
      DATABASE_URL: ${DATABASE_URL}
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: flight_scan
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

volumes:
  postgres_data:
```

Ejecutar:
```bash
docker-compose up -d
```

#### Opción B: Kubernetes

Ver `k8s/deployment.yaml` (no incluido, ejemplo):
```bash
kubectl apply -f k8s/
kubectl get pods
kubectl logs -f deployment/flight-scan
```

---

## 🗄️ Configuración de Base de Datos

### 1. Crear Instancia PostgreSQL

#### AWS RDS
```bash
# CLI
aws rds create-db-instance \
  --db-instance-identifier flight-scan-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username postgres \
  --master-user-password yourpassword \
  --allocated-storage 20
```

#### Heroku Postgres
```bash
heroku addons:create heroku-postgresql:hobby-dev -a flight-scan
```

#### Local PostgreSQL
```bash
# macOS
brew install postgresql
brew services start postgresql

# Linux
sudo apt-get install postgresql
sudo systemctl start postgresql

# Windows
# Download from postgresql.org
```

### 2. Setup Tables

```bash
# Conectar a BD
psql DATABASE_URL

# Crear schema
\i scripts/setup_database.py
```

O programáticamente:
```bash
python scripts/setup_database.py
```

### 3. Configurar Conexión

En `.env`:
```
DATABASE_URL=postgresql://user:password@host:5432/flight_scan
```

En Streamlit secrets:
```toml
DATABASE_URL = "postgresql://user:password@host:5432/flight_scan"
```

### 4. Backup & Restore

```bash
# Backup
pg_dump DATABASE_URL > flight_scan_backup.sql

# Restore
psql DATABASE_URL < flight_scan_backup.sql

# Automated (AWS)
aws rds create-db-snapshot \
  --db-instance-identifier flight-scan-db \
  --db-snapshot-identifier flight-scan-backup-$(date +%s)
```

---

## 📊 Monitoreo & Alertas

### 1. Application Monitoring

#### Streamlit Cloud
- Dashboard built-in (streamlit.io/cloud)
- Ver logs en real-time
- View analytics

#### Stackdriver (Google Cloud)
```python
# En app.py
import logging
from google.cloud import logging as cloud_logging

# Setup
client = cloud_logging.Client()
client.setup_logging()

logger = logging.getLogger(__name__)
logger.info("App started")
```

#### Datadog/New Relic
Agregar agent a Dockerfile:
```dockerfile
RUN pip install ddtrace
CMD ["ddtrace-run", "streamlit", "run", "app.py"]
```

### 2. Database Monitoring

```bash
# Connection count
SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;

# Query performance
SELECT query, mean_exec_time, calls FROM pg_stat_statements ORDER BY mean_exec_time DESC;

# Table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 3. Alertas

#### Health Check Endpoint
```python
# En app.py
@app.route("/health")
def health():
    try:
        db.test_connection()
        amadeus = AmadeusClient(...)
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 500
```

#### Uptime Monitoring
```bash
# Usar uptimerobot.com o similar
# Check: https://flight-scan-app.streamlit.app/health
# Intervalo: 5 minutos
# Alert si falla
```

#### Log Monitoring
```bash
# Alertar si detecta errores
# En Streamlit Cloud: Integración con Sentry.io

import sentry_sdk
sentry_sdk.init("https://xxx@sentry.io/yyy")
```

---

## 🔧 Configuración de Seguridad

### 1. Environment Secrets
```bash
# NUNCA commitear .env
echo ".env" >> .gitignore

# Usar secrets manager
# - Streamlit Cloud: secrets.toml
# - AWS: Secrets Manager
# - HashiCorp: Vault
# - Git: git-secret
```

### 2. Database Security
```bash
# SSL/TLS para conexión
DATABASE_URL=postgresql://user:pass@host:5432/flight_scan?sslmode=require

# IP Whitelist (AWS RDS)
aws rds modify-db-instance \
  --db-instance-identifier flight-scan-db \
  --vpc-security-group-ids sg-xxxxxx
```

### 3. API Keys
- Rotar cada 90 días
- Usar diferentes keys para staging/prod
- Monitorear uso en Amadeus dashboard
- Revocar si se exponen

### 4. HTTPS/TLS
- ✅ Streamlit Cloud: Automático
- ✅ Docker + Nginx: Usar Let's Encrypt
  ```bash
  certbot certonly --standalone -d flight-scan.example.com
  ```

---

## 📈 Escalado

### Cuando Crecer

**Síntomas:**
- App lenta (>2s response time)
- Errores 503 (out of memory)
- CPU >80% consistente
- Database connections al máximo

### Opciones de Escalado

#### 1. Vertical (Más recursos)
```bash
# Streamlit Cloud: Cambiar plan a Pro
# Docker: Cambiar instancetype
# DB: Aumentar db.t3.micro → db.t3.small

# Fácil pero limitado
```

#### 2. Horizontal (Más instancias)
```bash
# Kubernetes
kubectl scale deployment flight-scan --replicas=3

# Load balancer (nginx, HAProxy, AWS ELB)
# Cache (Redis)
# CDN (CloudFront, Cloudflare)
```

#### 3. Optimizar
- Ver FASE5_PERFORMANCE_REPORT.md
- Implementar batch inserts
- Agregar connection pooling
- Caché de búsquedas (Redis)

---

## 🐛 Troubleshooting

### App no inicia

```bash
# Ver logs
streamlit run app.py

# Errores comunes:
# 1. Missing imports → pip install -r requirements.txt
# 2. .env file missing → cp .env.example .env
# 3. Database down → Verificar DATABASE_URL
```

### Base de datos no se conecta

```bash
# Verificar conexión
psql DATABASE_URL

# Errores comunes:
# 1. Invalid URL → postgresql://user:pass@host:5432/db
# 2. Server down → Verificar instancia
# 3. IP whitelist → Agregar IP pública en security group
# 4. Credenciales wrongas → Verificar user/pass
```

### API Amadeus lenta/fallando

```bash
# Verificar credenciales
# En app.py:
from amadeus_client import AmadeusClient
client = AmadeusClient(api_key=KEY, api_secret=SECRET)
print(client.access_token)  # Si es None, hay problema

# Errores comunes:
# 1. API quota exceeded → Verificar limits en Amadeus
# 2. Invalid credentials → Regenerar en Amadeus dashboard
# 3. Rate limit hit → Implementar backoff (ya en código)
```

### High memory usage

```bash
# Monitorear
docker stats

# Optimizaciones:
# 1. Reducir QUERY_LIMIT en config
# 2. Agregar garbage collection
# 3. Usar generator en lugar de lists
# 4. Ver FASE5_PERFORMANCE_REPORT.md
```

### Crashes aleatorios

```bash
# Logs
docker logs -f flight-scan

# Errores comunes:
# 1. OOM (out of memory) → Aumentar resources
# 2. Database connection pool exhausted → Usar pooling
# 3. Memory leak → Revisar resource cleanup
# 4. Crashes en parsing → Ver test logs
```

---

## 📚 Documentación Adicional

- **CLAUDE.md** — Reglas técnicas de código
- **ARCHITECTURE.md** — Diseño de sistemas
- **FASE4_TESTING_REPORT.md** — Tests y cobertura
- **FASE5_PERFORMANCE_REPORT.md** — Performance y optimizaciones
- **README.md** — Guía de uso

---

## ✅ Deployment Checklist

### Antes de Deploy
- [ ] Todos los tests pasando (`pytest -v`)
- [ ] Coverage 80%+ (`--cov`)
- [ ] Linting OK (`flake8`)
- [ ] Tipos OK (`mypy`)
- [ ] Secrets configurados (DATABASE_URL, API_KEY)
- [ ] Database schema creado (`setup_database.py`)
- [ ] Backup de datos existentes
- [ ] Monitoreo configurado

### Post-Deploy
- [ ] Health check OK (api/health)
- [ ] UI accesible en navegador
- [ ] Búsquedas funcionar (EZE→MIA)
- [ ] Datos guardados en BD
- [ ] Logs sin errores
- [ ] Performance <2s
- [ ] Alertas configuradas

---

**Última actualización:** 2026-07-10  
**Versión:** v1.0  
**Status:** Production Ready
