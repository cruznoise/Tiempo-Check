from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.coach.engine import run_coach
from app.services.coach_alerta import generar_alertas_exceso
import os


TZ = ZoneInfo("America/Mexico_City")


def _hoy():
    return datetime.now(TZ).date()


def coach_short(app, usuario_id:int):
    with app.app_context():
        run_coach(usuario_id, _hoy())
        print(f"[SCHED][coach_short] user={usuario_id}")


def coach_daily(app, usuario_id:int):
    with app.app_context():
    # corre después del cierre diario de agregados
        d = _hoy()
        run_coach(usuario_id, d)
        print(f"[SCHED][coach_daily] user={usuario_id} d={d}")


def coach_catchup(app, usuario_id:int, dias:int=14):
    with app.app_context():
        ffin = _hoy()
    for i in range(dias, -1, -1):
        run_coach(usuario_id, ffin - timedelta(days=i))
    print(f"[SCHED][coach_catchup] user={usuario_id} lookback={dias}")

def job_coach_alertas(app, usuario_id: int):
    """
    Ejecuta al cierre del día (o primera hora del siguiente) para el día de MX.
    """
    with app.app_context():
        d = _hoy() - timedelta(days=1)  # generar para el día que terminó
        res = generar_alertas_exceso(usuario_id=usuario_id, dia=d)
        print(f"[SCHED][coach_alertas] pid={os.getpid()} {d} user={usuario_id} -> {res}")