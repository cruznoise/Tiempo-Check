"""
Configuración para TiempoCheck v3.2 - Railway Production
Este archivo lee las variables de entorno proporcionadas por Railway
"""
import os
from datetime import timedelta

class Config:
    """Configuración base para la aplicación"""
    
    # Flask Core
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
    DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'
    
    # MySQL Database - Railway proporciona estas variables automáticamente
    MYSQL_HOST = os.environ.get('MYSQLHOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQLPORT', '3306'))
    MYSQL_USER = os.environ.get('MYSQLUSER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQLPASSWORD', '')
    MYSQL_DATABASE = os.environ.get('MYSQLDATABASE', 'tiempocheck')
    
    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Cambiar a True para debug
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_POOL_RECYCLE = 3600
    SQLALCHEMY_POOL_PRE_PING = True
    
    # Session
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True  # HTTPS only en producción
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Upload folders
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    
    # ML Configuration
    ML_ARTIFACTS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ml', 'artifacts')
    ML_MODELS_PATH = os.path.join(ML_ARTIFACTS_PATH, 'models')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Public URL (opcional, útil para webhooks o redirects)
    PUBLIC_URL = os.environ.get('PUBLIC_URL', '')
    
    @staticmethod
    def init_app(app):
        """Inicializar configuración específica de la aplicación"""
        # Crear directorios necesarios
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.ML_ARTIFACTS_PATH, exist_ok=True)
        os.makedirs(Config.ML_MODELS_PATH, exist_ok=True)


class DevelopmentConfig(Config):
    """Configuración para desarrollo local"""
    DEBUG = True
    FLASK_ENV = 'development'
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Configuración para producción (Railway)"""
    DEBUG = False
    FLASK_ENV = 'production'
    SESSION_COOKIE_SECURE = True
    SQLALCHEMY_ECHO = False
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log a syslog en producción si es necesario
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


# Diccionario de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}


# Función helper para obtener la configuración actual
def get_config():
    """Obtiene la configuración basada en FLASK_ENV"""
    env = os.environ.get('FLASK_ENV', 'production')
    return config.get(env, config['default'])