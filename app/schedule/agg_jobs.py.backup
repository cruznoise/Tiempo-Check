# app/schedule/agg_jobs.py
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from app.services.agregados_engine import AgregadosEngine
from flask import current_app

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
def job_agg_close_day(app=None, usuario_id: int = 1, fecha: date = None):
    """
    Job diario: ejecuta los cálculos de agregados para el usuario en la fecha indicada.
    Incluye: estado diario, ventanas y KPIs.
    """
    app = app or current_app
    engine = AgregadosEngine()

    with app.app_context():
        if fecha is None:
            fecha = date.today()

        print(f"[SCHED][agg_close_day] user={usuario_id} fecha={fecha}")

        try:
            res1 = engine.calcular_estado_dia_usuario(usuario_id, fecha)
            res2 = engine.calcular_ventanas_usuario(usuario_id, fecha)
            res3 = engine.calcular_kpis_usuario(usuario_id, fecha)

            print(f"[SCHED][OK][agg_close_day] {fecha} → estado={res1['procesadas']} ventanas={res2['ventanas']} kpis={res3['rangos_procesados']}")
            return {"estado": res1, "ventanas": res2, "kpis": res3}
        except Exception as e:
            print(f"[SCHED][ERR][agg_close_day] user={usuario_id} fecha={fecha} → {e}")
            return None
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
