import os
import subprocess
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from app.services.features_engine import calcular_persistir_features
from app.extensions import db  
from flask import current_app

def _hoy(app):
    tz = ZoneInfo(app.config.get("TZ", "America/Mexico_City"))
    return datetime.now(tz).date()

def job_features_horarias(app, usuario_id: int, dia: date = None):
    """Calcula features horarias para el día especificado o el actual."""
    app = app or current_app
    with app.app_context():
        d = dia or _hoy(app)
        res = calcular_persistir_features(usuario_id=usuario_id, dia=d)
        print(f"[SCHED][horarias] user={usuario_id} fecha={d} → diarias={res.get('diarias',0)} horarias={res.get('horarias',0)} ok={res.get('ok',0)}")
        return res
    
def job_features_diarias(app=None, usuario_id=1, fecha=None):
    """Calcula y guarda las features diarias del usuario para un día específico."""
    app = app or current_app
    with app.app_context():
        from datetime import date
        if fecha is None:
            fecha = date.today()

        print(f"[ENG][RUN] calcular_persistir_features usuario={usuario_id} dia={fecha}")
        try:
            res = calcular_persistir_features(usuario_id=usuario_id, dia=fecha)
            print(f"[SCHED][diarias] user={usuario_id} fecha={fecha} → diarias={res.get('diarias',0)} horarias={res.get('horarias',0)} ok={res.get('ok',0)}")
            return res
        except Exception as e:
            print(f"[ENG][ERR] Fallo en job_features_diarias({fecha}): {e}")
            return None
        
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

