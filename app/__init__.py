import os
from pathlib import Path
from flask import Flask, jsonify
from app.extensions import db, cors, migrate
from dotenv import load_dotenv 

env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ [ENV] Variables cargadas desde {env_path}")

def create_app(config_object=None):
    """
    Crea y configura la aplicación Flask.
    
            Args:
                config_object: Objeto de configuración o None para usar env var
                
            Returns:
                app: Instancia configurada de Flask
    """
    app = Flask(__name__)
    #app.config["DEBUG"] = True

    # ========================================================================
    # CONFIGURACIÓN
    # ========================================================================
    
    if config_object:
        app.config.from_object(config_object)
    else:
        cfg = os.getenv("TIEMPOCHECK_CONFIG", "config.Config")
        app.config.from_object(cfg)
    
    # Verificar qué config se cargó realmente
    print(f"✅ [CONFIG] Config final cargada: {app.config.get('SQLALCHEMY_DATABASE_URI', 'NO DEFINIDA')}")

    # ========================================================================
    # EXTENSIONES
    # ========================================================================
    
    db.init_app(app)
    
    cors.init_app(
        app,
        resources={
            r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")},
            r"/admin/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")},
        },
        supports_credentials=True,
    )
    
    migrate.init_app(app, db)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """Cierra y limpia la sesión SQLAlchemy después de cada request."""
        db.session.remove()

    # ========================================================================
    # BLUEPRINTS (RUTAS)
    # ========================================================================
    
    from .controllers.app_base import bp as app_base_bp
    from .controllers.admin_controller import bp as admin_bp
    from .controllers.api_controller import bp as api_bp
    from .controllers.agg_controller import bp as agg_bp
    from .controllers.coach_controller import bp as coach_bp
    from .controllers.anomalias_controller import bp as anomalias_bp
    from .controllers.clasificacion_controller import bp as clasificacion_bp  

    app.register_blueprint(app_base_bp)         
    app.register_blueprint(admin_bp, url_prefix="/admin")  
    app.register_blueprint(api_bp)                
    app.register_blueprint(agg_bp, url_prefix="/api/agg")  
    app.register_blueprint(coach_bp)              
    app.register_blueprint(anomalias_bp)          
    app.register_blueprint(clasificacion_bp)    

    # ========================================================================
    # ERROR HANDLERS
    # ========================================================================
    
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request"}), 400

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    # ========================================================================
    # HEALTH CHECK
    # ========================================================================
    
    if "health" not in app.view_functions:
        def health():
            return {"status": "ok", "version": "3.2"}
        app.add_url_rule("/api/health", endpoint="health", view_func=health, methods=["GET"])

    # ========================================================================
    # INFORMACIÓN DE INICIO
    # ========================================================================
    
    db_url = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    # Ocultar password en logs
    db_url_safe = db_url.split('@')[-1] if '@' in db_url else db_url
    
    print("="*70)
    print(" TiempoCheck v3.2 - Iniciando...")
    print("="*70)
    print(f" Config: {os.getenv('TIEMPOCHECK_CONFIG','config.Config')}")
    print(f" Database: {db_url_safe}")
    print(f" Debug: {app.debug}")
    
    # ========================================================================
    # BOOT CATCHUP (OPCIONAL)
    # ========================================================================
    
    should_catchup = app.config.get("ENABLE_BOOT_CATCHUP", True)
    is_ml_mode = os.environ.get("TIEMPOCHECK_ML_MODE") == "1"
    is_main = os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug
    
    print(f" Boot Catchup: {'ENABLED' if should_catchup else 'DISABLED'}")
    print(f" ML Mode: {'YES' if is_ml_mode else 'NO'}")
    print(f" Is Main Process: {'YES' if is_main else 'NO (reloader child)'}")
    
    if should_catchup and not is_ml_mode and is_main:
        print(" Ejecutando boot catchup...")
        with app.app_context():
            try:
                from app.schedule.boot_catchup import boot_catchup
                usuario_id = int(app.config.get("SCHED_USUARIO_ID", 1))
                boot_catchup(app, usuario_id)
                print(" Boot catchup completado")
            except Exception as e:
                print(f" Error en boot catchup: {e}")
                print("   El servidor continuará sin catchup")
    else:
        if not should_catchup:
            print("ℹ  Boot catchup deshabilitado (para arranque rápido)")
        elif is_ml_mode:
            print("ℹ  Boot catchup omitido (modo ML)")
        elif not is_main:
            print("ℹ  Boot catchup omitido (proceso secundario)")

# ========================================================================
    # SCHEDULER (JOBS AUTOMÁTICOS)
    # ========================================================================
    
    
    should_start_scheduler = app.config.get("ENABLE_SCHEDULER", True)
    
    print(f"🔧 Scheduler: {'ENABLED' if should_start_scheduler else 'DISABLED'}")
    
    if should_start_scheduler and is_main:
        print(" Iniciando scheduler...")
        try:
            from app.schedule.scheduler import start_scheduler
            start_scheduler(app)
            print(" Scheduler iniciado correctamente")
        except Exception as e:
            print(f" Error al iniciar scheduler: {type(e).__name__}: {e}")
            print("   El servidor continuará sin jobs automáticos")
    else:
        if not should_start_scheduler:
            print("ℹ  Scheduler deshabilitado")
            print("  Para ejecutar jobs: python scripts/run_jobs_manually.py")
        elif not is_main:
            print("ℹ  Scheduler omitido (proceso secundario)")

    print("="*70)
    print(" Servidor listo!")
    print("="*70)
    print()

    return app


# ============================================================================
# NOTAS DE IMPLEMENTACIÓN
# ============================================================================

"""
COMPARACIÓN CON VERSIÓN ANTERIOR:

ANTES:
- boot_catchup siempre se ejecutaba (tardaba minutos)
- Scheduler siempre intentaba iniciar
- Sin logging claro de qué se estaba ejecutando
- Sin manejo de errores robusto

AHORA:
- boot_catchup es OPCIONAL (config: ENABLE_BOOT_CATCHUP)
- Scheduler es OPCIONAL (config: ENABLE_SCHEDULER)
- Logging detallado de cada paso
- Try-except en boot_catchup y scheduler
- Servidor continúa aunque falle algún componente

BENEFICIOS:
- Arranque <5 segundos sin scheduler
- Control fino de qué se ejecuta
- Mejor para desarrollo y demos
- Más robusto ante errores

CONFIGURACIONES RECOMENDADAS:

1. Demo rápida (presentación):
   ENABLE_BOOT_CATCHUP=false
   ENABLE_SCHEDULER=false
   
2. Testing completo:
   ENABLE_BOOT_CATCHUP=true
   ENABLE_SCHEDULER=true
   
3. Desarrollo normal:
   ENABLE_BOOT_CATCHUP=false
   ENABLE_SCHEDULER=false
   # Ejecutar jobs manualmente según necesites
"""