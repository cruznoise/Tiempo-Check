# 🚀 Guía de Despliegue - TiempoCheck v3.2

Guía completa para desplegar TiempoCheck en diferentes entornos.

---

## 📑 Tabla de Contenidos

1. [Requisitos](#requisitos)
2. [Desarrollo Local](#desarrollo-local)
3. [Producción (Railway)](#producción-railway)
4. [Docker](#docker)
5. [Variables de Entorno](#variables-de-entorno)
6. [Monitoreo](#monitoreo)
7. [Troubleshooting](#troubleshooting)

---

## 📋 Requisitos

### Mínimos
```
CPU:      2 cores
RAM:      2 GB
Disco:    10 GB
SO:       Ubuntu 20.04+ / Debian 10+
Python:   3.10+
MySQL:    8.0+
```

### Recomendados (Producción)
```
CPU:      4 cores
RAM:      4 GB
Disco:    20 GB SSD
SO:       Ubuntu 22.04 LTS
Python:   3.10.12
MySQL:    8.0.35
```

---

## 💻 Desarrollo Local

### Paso 1: Clonar Repositorio
```bash
git clone https://github.com/cruznoise/Tiempo-Check.git
cd TiempoCheck
```

### Paso 2: Entorno Virtual
```bash
python3 -m venv venv
source venv/bin/activate
```

### Paso 3: Dependencias
```bash
pip install -r requirements.txt
```

### Paso 4: Base de Datos
```bash
# Crear BD
mysql -u root -p -e "CREATE DATABASE tiempocheck_db CHARACTER SET utf8mb4;"

# Importar esquema
mysql -u root -p tiempocheck_db < database/schema.sql

# Datos iniciales
mysql -u root -p tiempocheck_db < database/seed_data.sql
```

### Paso 5: Configuración
```bash
cp .env.example .env
nano .env
```
```bash
DATABASE_URL=mysql+pymysql://root:PASSWORD@localhost/tiempocheck_db
SECRET_KEY=tu-secret-key-desarrollo
ENABLE_SCHEDULER=true
ENABLE_ML=true
FLASK_ENV=development
FLASK_DEBUG=True
```

### Paso 6: Iniciar
```bash
python3 -m app.app
```

**Servidor:** http://localhost:5000

---

## ☁️ Producción (Railway)

Railway es la opción recomendada para despliegue académico/demo.

### Ventajas

- ✅ $5/mes de crédito gratis
- ✅ MySQL incluido
- ✅ Deploy automático desde Git
- ✅ Variables de entorno fáciles
- ✅ Logs en tiempo real
- ✅ Dominio HTTPS automático

### Paso 1: Preparar Proyecto
```bash
# Crear Procfile
echo "web: gunicorn app.app:app" > Procfile

# Crear runtime.txt
echo "python-3.10.12" > runtime.txt

# Actualizar requirements.txt
echo "gunicorn==21.2.0" >> requirements.txt
```

### Paso 2: Crear Cuenta Railway

1. Ir a https://railway.app
2. Sign up con GitHub
3. Verificar email

### Paso 3: Crear Proyecto
```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Crear proyecto
railway init
```

### Paso 4: Agregar MySQL
```bash
# En Railway dashboard
1. Click "New"
2. Seleccionar "Database"
3. Seleccionar "MySQL"
4. Esperar provisioning (2-3 min)
```

### Paso 5: Variables de Entorno
```bash
# En Railway dashboard → Variables
DATABASE_URL=${{MySQL.DATABASE_URL}}
SECRET_KEY=tu-secret-key-produccion-muy-seguro
ENABLE_SCHEDULER=true
ENABLE_ML=true
FLASK_ENV=production
TZ=America/Mexico_City
```

### Paso 6: Deploy
```bash
railway up
```

### Paso 7: Importar BD
```bash
# Obtener credenciales MySQL
railway variables

# Conectar
mysql -h RAILWAY_HOST -u RAILWAY_USER -p RAILWAY_DB

# Importar
mysql -h RAILWAY_HOST -u RAILWAY_USER -p RAILWAY_DB < database/schema.sql
mysql -h RAILWAY_HOST -u RAILWAY_USER -p RAILWAY_DB < database/seed_data.sql
```

### Paso 8: Verificar
```bash
# Ver logs
railway logs

# Abrir app
railway open
```

---

## 🐳 Docker

### Dockerfile
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código
COPY . .

# Puerto
EXPOSE 5000

# Comando
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app.app:app"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=mysql+pymysql://root:password@db:3306/tiempocheck_db
      - SECRET_KEY=tu-secret-key
      - ENABLE_SCHEDULER=true
      - ENABLE_ML=true
    depends_on:
      - db
    volumes:
      - ./ml/artifacts:/app/ml/artifacts
      - ./ml/preds:/app/ml/preds

  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=password
      - MYSQL_DATABASE=tiempocheck_db
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./database/schema.sql:/docker-entrypoint-initdb.d/schema.sql

volumes:
  mysql_data:
```

### Comandos Docker
```bash
# Build
docker-compose build

# Iniciar
docker-compose up -d

# Ver logs
docker-compose logs -f web

# Detener
docker-compose down

# Limpiar
docker-compose down -v
```

---

## 🔐 Variables de Entorno

### Desarrollo
```bash
DATABASE_URL=mysql+pymysql://root:PASSWORD@localhost/tiempocheck_db
SECRET_KEY=dev-secret-key-not-for-production
ENABLE_SCHEDULER=true
ENABLE_BOOT_CATCHUP=false
ENABLE_ML=true
FLASK_ENV=development
FLASK_DEBUG=True
TZ=America/Mexico_City
```

### Producción
```bash
DATABASE_URL=mysql+pymysql://USER:PASS@HOST:PORT/DB
SECRET_KEY=super-secret-key-change-this-in-production-min-32-chars
ENABLE_SCHEDULER=true
ENABLE_BOOT_CATCHUP=false
ENABLE_ML=true
FLASK_ENV=production
FLASK_DEBUG=False
TZ=America/Mexico_City

# Opcional
SENTRY_DSN=https://...
LOG_LEVEL=INFO
MAX_WORKERS=4
```

---

## 📊 Monitoreo

### Logs
```bash
# Desarrollo
tail -f logs/tiempocheck.log

# Producción (Railway)
railway logs --tail

# Docker
docker-compose logs -f web
```

### Health Check
```bash
# Endpoint de salud
curl http://localhost:5000/api/health

# Esperado
{
  "status": "ok",
  "version": "3.2.0",
  "timestamp": "2025-11-05T15:30:00"
}
```

### Métricas
```bash
# Jobs del scheduler
curl http://localhost:5000/admin/api/jobs_status

# ML evaluación
curl http://localhost:5000/api/ml/eval/latest
```

### Sentry (Opcional)
```bash
# Instalar
pip install sentry-sdk[flask]

# Configurar en app/__init__.py
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

if os.environ.get('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.environ['SENTRY_DSN'],
        integrations=[FlaskIntegration()],
        traces_sample_rate=1.0
    )
```

---

## 🔧 Troubleshooting

### Problema: "Can't connect to MySQL"
```bash
# Verificar MySQL corriendo
sudo systemctl status mysql

# Verificar credenciales
mysql -u root -p -e "SELECT 1;"

# Verificar DATABASE_URL
echo $DATABASE_URL
```

**Solución:**
```bash
# Reiniciar MySQL
sudo systemctl restart mysql

# Verificar firewall
sudo ufw allow 3306/tcp
```

---

### Problema: "Scheduler no inicia jobs"
```bash
# Ver logs
tail -f logs/tiempocheck.log | grep SCHED

# Verificar variable
echo $ENABLE_SCHEDULER
```

**Solución:**
```bash
# Asegurar que esté habilitado
export ENABLE_SCHEDULER=true

# Reiniciar servidor
```

---

### Problema: "Modelos ML no encontrados"
```bash
# Verificar existencia
ls -la ml/artifacts/*/

# Re-entrenar si es necesario
python3 scripts/entrenar_modelo.py --categoria productividad
```

---

### Problema: "Import Error: No module named..."
```bash
# Verificar entorno virtual activo
which python3
# Debe apuntar a venv/bin/python3

# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

---

### Problema: "500 Internal Server Error"
```bash
# Ver logs detallados
tail -100 logs/tiempocheck.log

# Activar debug
export FLASK_DEBUG=True
python3 -m app.app
```

---

## 📝 Checklist de Deploy

### Pre-Deploy

- [ ] Tests pasando
- [ ] BD respaldada
- [ ] Variables de entorno configuradas
- [ ] SECRET_KEY único y seguro
- [ ] Modelos ML entrenados
- [ ] Datos iniciales cargados

### Post-Deploy

- [ ] Health check OK
- [ ] Logs sin errores
- [ ] Scheduler funcionando
- [ ] BD conectada
- [ ] Extensión conectada al nuevo endpoint
- [ ] ML predicciones funcionando
- [ ] Dashboard accesible

---

## 🎯 Ambientes Sugeridos

### Desarrollo
```
URL:      http://localhost:5000
Debug:    True
BD:       Local MySQL
Scheduler: Habilitado
ML:       Habilitado
```

### Staging (Opcional)
```
URL:      https://staging.tiempocheck.com
Debug:    False
BD:       Railway MySQL
Scheduler: Habilitado
ML:       Habilitado
```

### Producción
```
URL:      https://tiempocheck.com
Debug:    False
BD:       Railway MySQL (o AWS RDS)
Scheduler: Habilitado
ML:       Habilitado
Monitoring: Sentry
```

---

## 📞 Soporte

**Issues:** https://github.com/cruznoise/Tiempo-Check/issues  
**Email:** soporte@tiempocheck.com  
**Docs:** https://docs.tiempocheck.com

---

**Última actualización:** 5 de Noviembre de 2025
