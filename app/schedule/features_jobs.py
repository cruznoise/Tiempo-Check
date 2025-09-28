# app/schedule/features_jobs.py
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.services.features_engine import calcular_persistir_features
from app.extensions import db  

def _hoy(app):
    tz = ZoneInfo(app.config.get("TZ", "America/Mexico_City"))
    return datetime.now(tz).date()

def job_features_horarias(app, usuario_id: int):
    with app.app_context():
        d = _hoy(app)
        res = calcular_persistir_features(usuario_id=usuario_id, dia=d)
        print(f"[SCHED][horarias] user={usuario_id} fecha={d} → diarias={res.get('diarias',0)} horarias={res.get('horarias',0)} ok={res.get('ok',0)}")


def job_features_diarias(app, usuario_id: int):
    with app.app_context():
        # cerramos el día anterior para asegurar consistencia
        tz = ZoneInfo(app.config.get("TZ", "America/Mexico_City"))
        ayer = (datetime.now(tz).date() - timedelta(days=1))
        res = calcular_persistir_features(usuario_id=usuario_id, dia=ayer)
        print(f"[SCHED][diarias]  pid={os.getpid()} file={__file__} {ayer} user={usuario_id} → {res}")

def job_catchup(app, usuario_id: int, dias_atras: int = 3):
    with app.app_context():
        tz = ZoneInfo(app.config.get("TZ", "America/Mexico_City"))
        hoy = datetime.now(tz).date()
        first = hoy - timedelta(days=dias_atras)
        d = first
        res = []
        while d <= hoy:
            r = calcular_persistir_features(usuario_id=usuario_id, dia=d)
            res.append(r)
            d += timedelta(days=1)
        print(f"[SCHED][catchup] user={usuario_id} dias_atras={dias_atras} → {res}")
        return res
