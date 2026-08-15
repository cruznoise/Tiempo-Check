"""
Configuración LOCAL para TiempoCheck v3.2
"""
import os

class Config:
    # Flask
    SECRET_KEY = "dev-local-secret-key"
    
    # MySQL Local
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://angel:base@localhost/tiempocheck_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True if os.getenv('DEBUG_SQL') == '1' else False
    
    # CORS
    CORS_ORIGINS = "*"
    
    # Scheduler (desactivado en local para arranque rápido)
    ENABLE_SCHEDULER = False
    ENABLE_BOOT_CATCHUP = False
    SCHED_USUARIO_ID = 1
    
    # Timezone
    TZ = "America/Mexico_City"
    
    # Jobs config
    JOB_FH_MINUTES = 1
    JOB_CLOSE_HOUR = 0
    JOB_CLOSE_MINUTE = 5
    JOB_CATCHUP_HOURS = 1
    JOB_CATCHUP_LOOKBACK = 3
    JOB_AGG_SHORT_MINUTES = 15
    JOB_AGG_CLOSE_HOUR = 0
    JOB_AGG_CLOSE_MINUTE = 10
    JOB_AGG_CATCHUP_HOURS = 6
    JOB_AGG_CATCHUP_LOOKBACK = 30
    
    # ML
    IS_ML_PROCESS = False

#wsl
#cd /mnt/c/Users/Angel/Desktop/TiempoCheck_CON_BACKGROUND_COMPLETO
#code .
