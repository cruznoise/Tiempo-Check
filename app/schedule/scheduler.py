import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from flask import current_app
from app.schedule.features_jobs import job_features_diarias
from app.schedule.agg_jobs import job_agg_close_day
from app.schedule.ml_jobs import (
    job_ml_train,
    job_ml_train_cat,
    job_ml_predict,
)
from app.schedule.ml_jobs import job_ml_train_daily
from app.schedule.ml_jobs import job_ml_predict_multi
from app.schedule.ml_jobs import job_ml_eval_weekly
from app.schedule.coach_jobs import job_coach_alertas
from app.schedule.rachas_jobs import job_rachas
from .ml_jobs import job_ml_eval_daily

_SCHED = None 

def _is_reloader_child(app) -> bool:
    return (app.debug and os.environ.get("WERKZEUG_RUN_MAIN") == "true") or (not app.debug)

def get_scheduler(app) -> BackgroundScheduler:
    """
    Crea/obtiene el BackgroundScheduler singleton guardado en app.extensions["scheduler"].
    Úsalo en runtime normal (tienes acceso a 'app').
    """
    if "scheduler" not in app.extensions:
        tz = app.config.get("TZ", "America/Mexico_City")
        app.extensions["scheduler"] = BackgroundScheduler(timezone=tz)
    return app.extensions["scheduler"]

def get_scheduler_global():
    """
    Acceso auxiliar para CLI/tests:
    intenta current_app.extensions["scheduler"] y cae a _SCHED si no hay contexto.
    """
    try:
        return current_app.extensions.get("scheduler")
    except Exception:
        return _SCHED

def _usuarios_activos():
    """Devuelve IDs de usuarios activos en el sistema."""
    from app.models import Usuario
    try:
        return [u.id for u in Usuario.query.all()]
    except Exception:
        return [1]

def start_scheduler(app):
    """
    Inicia el scheduler principal de TiempoCheck.
    Se asegura de no duplicar jobs en modo debug ni crear conflictos entre procesos.
    """
    debug = app.debug
    is_child = (debug and os.environ.get("WERKZEUG_RUN_MAIN") == "true") or (not debug)
    if not is_child:
        print("[SCHED][SKIP] Dev reloader (proceso primario).")
        return

    sched = get_scheduler(app)
    if getattr(sched, "started", False):
        print("[SCHED] ya estaba corriendo")
        return

    with app.app_context():
        usuarios = _usuarios_activos()

        for uid in usuarios:
            sched.add_job(
                func=job_features_diarias,
                trigger=CronTrigger(minute="*/30", timezone=sched.timezone),
                args=[app, uid],
                id=f"features_diarias_u{uid}",
                replace_existing=True,
                coalesce=True,
                max_instances=1,
            )

            sched.add_job(
                func=job_agg_close_day,
                trigger=CronTrigger(hour=0, minute=5, timezone=sched.timezone),
                args=[app, uid],
                id=f"agg_close_u{uid}",
                replace_existing=True,
                coalesce=True,
                max_instances=1,
            )

            sched.add_job(
                func=job_ml_train_daily,
                trigger=CronTrigger(day_of_week="sun", hour=0, minute=5, timezone=sched.timezone),
                args=[app, uid],
                id=f"ml_train_weekly_u{uid}",
                replace_existing=True,
                coalesce=True,
                max_instances=1,
            )

            sched.add_job(
                func=job_ml_predict_multi,
                trigger=CronTrigger(hour=0, minute=20, timezone=sched.timezone),
                args=[app, uid],
                id=f"ml_predict_multi_u{uid}",
                replace_existing=True,
                coalesce=True,
                max_instances=1,
            )

            sched.add_job(
                func=job_coach_alertas,
                trigger=CronTrigger(hour=0, minute=25, timezone=sched.timezone),
                args=[app, uid],
                id=f"coach_alertas_u{uid}",
                replace_existing=True,
                coalesce=True,
                max_instances=1,
            )

            sched.add_job(
                func=job_rachas,
                trigger=CronTrigger(hour=23, minute=59, timezone=sched.timezone),
                args=[app, uid],
                id=f"rachas_cierre_u{uid}",
                replace_existing=True,
                coalesce=True,
                max_instances=1,
            )

            sched.add_job(
                func=job_ml_eval_daily,
                trigger=CronTrigger(hour=23, minute=45, timezone=sched.timezone),
                args=[app, uid],
                id=f"ml_eval_daily_u{uid}",
                replace_existing=True,
                coalesce=True,
                max_instances=1,
            )

            sched.add_job(
                func=job_ml_eval_weekly,
                trigger="cron",
                day_of_week="sun",
                hour=23,
                minute=59,
                timezone=sched.timezone,
                args=[app],
                id="ml_eval_weekly",
                replace_existing=True,
            )

            print(f"[SCHED][LOAD] Jobs registrados para user={uid}")

        sched.start()
        register_scheduler(app, sched)
        sched.started = True

        global _SCHED
        _SCHED = sched

        print("[SCHED][OK] scheduler iniciado")

    return sched


def register_scheduler(app, scheduler):
    """Guarda el scheduler en current_app.extensions."""
    if hasattr(app, 'extensions'):
        app.extensions['scheduler'] = scheduler
        print("[SCHED][LINK] scheduler registrado en app.extensions")
    else:
        print("[SCHED][WARN] app.extensions no disponible")