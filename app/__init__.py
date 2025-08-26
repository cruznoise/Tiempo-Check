# app/__init__.py
import os
from flask import Flask
from app.extensions import db
from app.schedule.scheduler import start_scheduler

def create_app():
    app = Flask(__name__)


    app.config.from_object("config.Config")

    db.init_app(app)

    from app.schedule.scheduler import start_scheduler
    
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_scheduler(app, usuario_id=1)

    with app.app_context():
        from app.models.models import Usuario, Registro

        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            from app.schedule.scheduler import start_scheduler
            start_scheduler(app, usuario_id=1)

    return app
