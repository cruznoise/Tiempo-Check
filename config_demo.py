"""
Configuración optimizada para demo y desarrollo de TiempoCheck v3.2

Uso:
    export TIEMPOCHECK_CONFIG=config_demo.DemoConfig
    python -m app.app

Características:
- Scheduler deshabilitado por default (activar manualmente si necesitas)
- Base de datos específica para demo
- Logs limpios
- Arranque rápido (<5 segundos)
"""
import os

# ============================================================================
# DETECTAR SI ESTAMOS EN RAILWAY
# ============================================================================
IS_RAILWAY = os.getenv("RAILWAY_ENVIRONMENT") is not None

# ============================================================================
# CONFIGURACIÓN DE BASE DE DATOS
# ============================================================================
if IS_RAILWAY:
    # En Railway: usar variables proporcionadas por Railway
    MYSQL_HOST = os.environ.get('MYSQLHOST')
    MYSQL_PORT = int(os.environ.get('MYSQLPORT', 3306))
    MYSQL_USER = os.environ.get('MYSQLUSER')
    MYSQL_PASSWORD = os.environ.get('MYSQLPASSWORD')
    MYSQL_DATABASE = os.environ.get('MYSQLDATABASE', 'tiempocheck')
    
    DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    )
else:
    # Local: usar configuración de demo
    DATABASE_URI = "mysql+pymysql://root:base@localhost/tiempocheck_demo"


class DemoConfig:
    """
    Configuración para demos y presentaciones.
    Prioriza arranque rápido y estabilidad sobre automatización.
    """
    
    # ============================================================================
    # BASE DE DATOS
    # ============================================================================
    
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:base@localhost/tiempocheck_demo"
    )
    
    # Deshabilitar tracking de modificaciones (mejora performance)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # No logear todas las queries SQL (mantiene consola limpia)
    SQLALCHEMY_ECHO = False
    
    # Pool de conexiones optimizado para desarrollo
    SQLALCHEMY_POOL_SIZE = 5
    SQLALCHEMY_POOL_RECYCLE = 3600
    SQLALCHEMY_POOL_TIMEOUT = 30
    
    # ============================================================================
    # SEGURIDAD
    # ============================================================================
    
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "demo-secret-key-change-in-production"  # ⚠️ Cambiar en producción
    )
    
    # ============================================================================
    # CORS
    # ============================================================================
    
    CORS_ORIGINS = "*"  # Permitir todos los orígenes en demo
    
    # ============================================================================
    # SCHEDULER (JOBS AUTOMÁTICOS)
    # ============================================================================
    
    # ⚠️ IMPORTANTE: Scheduler DESHABILITADO por default
    # Para arranque rápido y control manual de jobs
    ENABLE_SCHEDULER = os.getenv("ENABLE_SCHEDULER", "false").lower() in ("1", "true", "yes")
    
    # Usuario por default para jobs (si habilitas scheduler)
    SCHED_USUARIO_ID = int(os.getenv("SCHED_USUARIO_ID", "1"))
    
    # ============================================================================
    # TIMEZONE
    # ============================================================================
    
    TZ = os.getenv("TZ", "America/Mexico_City")
    
    # ============================================================================
    # CONFIGURACIÓN DE JOBS (si habilitas scheduler)
    # ============================================================================
    
    # Features: cada 30 minutos (en lugar de cada minuto)
    JOB_FH_MINUTES = 30
    
    # Cierre de día: 00:05
    JOB_CLOSE_HOUR = 0
    JOB_CLOSE_MINUTE = 5
    
    # Catchup de features: cada 6 horas
    JOB_CATCHUP_HOURS = 6
    JOB_CATCHUP_LOOKBACK = 3  # Solo últimos 3 días
    
    # Agregaciones
    JOB_AGG_SHORT_MINUTES = 30  # Cada 30 min (en lugar de 15)
    JOB_AGG_CLOSE_HOUR = 0
    JOB_AGG_CLOSE_MINUTE = 10
    JOB_AGG_CATCHUP_HOURS = 12  # Cada 12 horas
    JOB_AGG_CATCHUP_LOOKBACK = 7
    
    # ============================================================================
    # FLASK
    # ============================================================================
    
    DEBUG = True
    TESTING = False
    
    # ============================================================================
    # LOGGING
    # ============================================================================
    
    # Nivel de logging (INFO para consola limpia, DEBUG para troubleshooting)
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # ============================================================================
    # ML PIPELINE
    # ============================================================================
    
    # No estamos en modo ML standalone
    IS_ML_PROCESS = False
    
    # ============================================================================
    # MODO BOOT CATCHUP
    # ============================================================================
    
    # ⚠️ DESHABILITAR boot_catchup para arranque rápido
    # Ejecutar manualmente cuando necesites: python scripts/run_catchup.py
    ENABLE_BOOT_CATCHUP = os.getenv("ENABLE_BOOT_CATCHUP", "false").lower() in ("1", "true", "yes")


class DemoConfigWithScheduler(DemoConfig):
    """
    Variante de DemoConfig con scheduler HABILITADO.
    
    Uso:
        export TIEMPOCHECK_CONFIG=config_demo.DemoConfigWithScheduler
        python -m app.app
    """
    ENABLE_SCHEDULER = True
    ENABLE_BOOT_CATCHUP = True  # Con scheduler, sí queremos catchup


# Alias para compatibilidad
Config = DemoConfig


# ============================================================================
# NOTAS DE USO
# ============================================================================

"""
MODOS DE EJECUCIÓN:

1. DEMO SIN SCHEDULER (arranque rápido):
   export TIEMPOCHECK_CONFIG=config_demo.DemoConfig
   python -m app.app
   
   Características:
   - Arranca en <5 segundos
   - Sin jobs automáticos
   - Ideal para demos y desarrollo
   - Ejecutar jobs manualmente: python scripts/run_jobs_manually.py

2. DEMO CON SCHEDULER (funcionalidad completa):
   export TIEMPOCHECK_CONFIG=config_demo.DemoConfigWithScheduler
   python -m app.app
   
   Características:
   - Jobs automáticos activos
   - Boot catchup habilitado
   - Tarda ~30-60 segundos en arrancar
   - Ideal para pruebas de integración

3. ACTIVAR SCHEDULER VÍA ENV VAR:
   export TIEMPOCHECK_CONFIG=config_demo.DemoConfig
   export ENABLE_SCHEDULER=true
   python -m app.app

4. MODO NORMAL (producción):
   export TIEMPOCHECK_CONFIG=config.Config
   python -m app.app

TROUBLESHOOTING:

Q: El servidor no arranca?
A: Verificar:
   - MySQL está corriendo: sudo systemctl status mysql
   - Base de datos existe: mysql -u root -p -e "SHOW DATABASES LIKE 'tiempocheck_demo'"
   - Credenciales correctas en DATABASE_URL

Q: Jobs no se ejecutan?
A: Verificar ENABLE_SCHEDULER=true y que hay usuarios en la BD

Q: Servidor tarda mucho en arrancar?
A: Deshabilitar boot_catchup:
   export ENABLE_BOOT_CATCHUP=false
   o usar DemoConfig sin scheduler

Q: Necesito ejecutar jobs manualmente?
A: Usar: python scripts/run_jobs_manually.py

"""
