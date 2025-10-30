import os
from flask import Flask, jsonify
from app.extensions import db, cors, migrate

def create_app(config_object=None):
    app = Flask(__name__)
    app.config["DEBUG"] = True

    from app.schedule.scheduler import start_scheduler

    if config_object:
        app.config.from_object(config_object)
    else:
        cfg = os.getenv("TIEMPOCHECK_CONFIG", "config.Config")
        app.config.from_object(cfg)

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

    from .controllers.app_base import bp as app_base_bp
    from .controllers.admin_controller import bp as admin_bp
    from .controllers.api_controller import bp as api_bp
    from .controllers.agg_controller import bp as agg_bp
    from .controllers.coach_controller import bp as coach_bp

    app.register_blueprint(app_base_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp)
    app.register_blueprint(agg_bp, url_prefix="/api/agg")
    app.register_blueprint(coach_bp)

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request"}), 400

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    if "health" not in app.view_functions:
        def health():
            return {"status": "ok"}
        app.add_url_rule("/api/health", endpoint="health", view_func=health, methods=["GET"])

    db_url = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    print(f"[BOOT] env={os.getenv('TIEMPOCHECK_CONFIG','config.Config')}  [DB] url={db_url}")
    should_start = app.config.get("ENABLE_SCHEDULER", True)
    is_main = os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug
    print(f"[SCHED][FLAGS] should_start={should_start} is_main={is_main} debug={app.debug} ext_sched={app.extensions.get('scheduler') is not None}")

    with app.app_context():
        try:
            from app.schedule.boot_catchup import boot_catchup
            if os.environ.get("TIEMPOCHECK_ML_MODE") != "1":
                usuario_id = int(app.config.get("SCHED_USUARIO_ID", 1))
                boot_catchup(app, usuario_id)
            else:
                print("[BOOT][SKIP] Proceso ML detectado — se omite boot_catchup durante create_app()")
        except Exception as e:
            print(f"[BOOT][CATCHUP][ERR] Error durante sincronización inicial: {e}")

    if should_start:
        try:
            start_scheduler(app)  
        except Exception as e:
            print(f"[SCHED][ERR] no se pudo iniciar: {type(e).__name__}: {e}")
    else:
        print("[SCHED][SKIP] ENABLE_SCHEDULER=0")

    return app