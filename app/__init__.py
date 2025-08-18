# app/__init__.py
import os
from flask import Flask
from app.extensions import db
from app.schedule.scheduler import start_scheduler

def create_app():
    app = Flask(__name__)

    # --- Config desde objeto Config (raíz config.py) ---
    app.config.from_object("config.Config")

    # --- Inicializa ORM (una sola instancia) ---
    db.init_app(app)

    # --- Registra rutas/blueprints del Bloque 1 ---

    from app.schedule.scheduler import start_scheduler
    # ...
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_scheduler(app, usuario_id=1)
    # (Importa aquí para evitar ciclos de import)
    from app.routes.features_api import bp as features_bp
    app.register_blueprint(features_bp)

    # --- Registra modelos dentro del app_context si lo necesitas ---
    with app.app_context():
        from app.models.models import Usuario, Registro
        # from app.models_features import FeatureDiaria, FeatureHoraria
        # db.create_all()  # solo en dev, si ocupas

        # --- Scheduler: arranca solo en el proceso principal ---
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            from app.schedule.scheduler import start_scheduler
            start_scheduler(app, usuario_id=1)

    return app
