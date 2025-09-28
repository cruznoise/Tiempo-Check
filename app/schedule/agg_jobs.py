# app/schedule/agg_jobs.py
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.services.agregados_engine import AgregadosEngine 

TZ = ZoneInfo("America/Mexico_City")
eng = AgregadosEngine()

def _hoy():
    return datetime.now(TZ).date()

def job_agg_short(app, usuario_id: int):
    """
    Corre frecuente. Actualiza ventanas (7/14/30d) y KPIs para 'hoy'.
    """
    with app.app_context():
        f = _hoy()
        eng.calcular_ventanas_usuario(usuario_id, f)
        eng.calcular_kpis_usuario(usuario_id, f)
        print(f"[SCHED][agg_short] {f} user={usuario_id}")

def job_agg_close_day(app, usuario_id: int):
    """
    Corre al cierre del día (después de medianoche). Cierra el 'ayer' completo.
    """
    with app.app_context():
        ayer = _hoy() - timedelta(days=1)
        eng.calcular_estado_dia_usuario(usuario_id, ayer)
        eng.calcular_ventanas_usuario(usuario_id, ayer)
        eng.calcular_kpis_usuario(usuario_id, ayer)
        print(f"[SCHED][agg_close] {ayer} user={usuario_id}")

def job_agg_catchup(app, usuario_id: int, dias: int = 30):
    """
    Corre en fondo cada N horas para rellenar huecos recientes.
    """
    with app.app_context():
        ffin = _hoy()
        fini = ffin - timedelta(days=dias)
        cur = fini
        while cur <= ffin:
            eng.calcular_estado_dia_usuario(usuario_id, cur)
            eng.calcular_ventanas_usuario(usuario_id, cur)
            cur += timedelta(days=1)
        eng.calcular_kpis_usuario(usuario_id, ffin)
        print(f"[SCHED][agg_catchup] {fini}→{ffin} user={usuario_id}")
