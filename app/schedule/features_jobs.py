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

def job_features_diarias(app, usuario_id, fecha_override=None):
    """
    Job que calcula features diarias
    
    Args:
        app: Instancia Flask
        usuario_id: ID del usuario
        fecha_override: Fecha específica (opcional, default: ayer)
    """
    from datetime import date, timedelta
    
    with app.app_context():
        try:
            # Usar fecha_override si se proporciona, sino ayer
            if fecha_override:
                fecha_calcular = fecha_override
            else:
                fecha_calcular = date.today() - timedelta(days=1)
            
            print(f"[FEATURES][DIARIAS] Usuario {usuario_id}, fecha: {fecha_calcular}")
            
            # Calcular features
            calcular_persistir_features(usuario_id, fecha_calcular)
            
            print(f"[FEATURES][DIARIAS] ✅ Completado para {fecha_calcular}")
            
        except Exception as e:
            print(f"[FEATURES][DIARIAS] ❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
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

