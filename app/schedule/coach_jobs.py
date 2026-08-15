from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.coach.engine import run_coach
from app.services.coach_alerta import generar_alertas_exceso
import os
from app.extensions import db
from app.models.models_coach import CoachSugerencia
from app.controllers.coach_controller import registrar_meta_coach

TZ = ZoneInfo("America/Mexico_City")


def _hoy():
    return datetime.now(TZ).date()


def coach_short(app, usuario_id:int):
    with app.app_context():
        run_coach(usuario_id, _hoy())
        print(f"[SCHED][coach_short] user={usuario_id}")


def coach_daily(app, usuario_id:int):
    with app.app_context():
        d = _hoy()
        run_coach(usuario_id, d)
        print(f"[SCHED][coach_daily] user={usuario_id} d={d}")


def coach_catchup(app, usuario_id:int, dias:int=14):
    with app.app_context():
        ffin = _hoy()
    for i in range(dias, -1, -1):
        run_coach(usuario_id, ffin - timedelta(days=i))
    print(f"[SCHED][coach_catchup] user={usuario_id} lookback={dias}")

def job_coach_alertas(app, usuario_id: int = None):
    """
    Ejecuta al cierre del día (o primera hora del siguiente) para el día de MX.
    """
    with app.app_context():
        if usuario_id is None:
            from app.models.models import Usuario
            usuarios = Usuario.query.all()
            usuario_ids = [u.id for u in usuarios]
        else:
            usuario_ids = [usuario_id]
        
        d = _hoy() - timedelta(days=1) 
        
        for uid in usuario_ids:
            try:
                res = generar_alertas_exceso(usuario_id=uid, dia=d)
                print(f"[SCHED][coach_alertas] pid={os.getpid()} {d} user={uid} -> {res}")
            except Exception as e:
                print(f"[SCHED][ERR][coach_alertas] user={uid} → {e}")

def job_coach_autometas(app, usuario_id:int=1):
    """Genera metas automáticas a partir de sugerencias pendientes (meta_personalizada)."""
    with app.app_context():
        sugerencias = (CoachSugerencia.query
            .filter(CoachSugerencia.usuario_id == usuario_id,
                    CoachSugerencia.tipo == "meta_personalizada",
                    CoachSugerencia.status == "new")
            .order_by(CoachSugerencia.creado_en.desc())
            .all())
        ok, err = 0, 0
        for s in sugerencias:
            try:
                payload = s.action_payload or {}
                minutos = float(payload.get("minutos_predichos", 0))
                fecha = payload.get("fecha")
                registrar_meta_coach(usuario_id, s.categoria, minutos, fecha)
                s.status = "acted"
                db.session.commit()
                ok += 1
            except Exception as e:
                db.session.rollback()
                print(f"[COACH][AUTO][ERR] {e}")
                err += 1
        print(f"[COACH][AUTO] metas aplicadas={ok} errores={err}")
