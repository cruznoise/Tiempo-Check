# app/schedule/scheduler.py
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.events import (
    EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED, EVENT_JOB_MAX_INSTANCES,
)
from .features_jobs import job_features_horarias, job_features_diarias, job_catchup

_SCHED = None  # singleton en el proceso

def _listener(event):
    if event.code == EVENT_JOB_EXECUTED:
        print(f"[SCHED][OK]    job_id={event.job_id} at={event.scheduled_run_time}")
    elif event.code == EVENT_JOB_ERROR:
        ex = getattr(event, "exception", None)
        print(f"[SCHED][ERROR] job_id={event.job_id} ex={ex!r}")
        tb = getattr(event, "traceback", None)
        if tb:
            print(tb)
    elif event.code == EVENT_JOB_MISSED:
        print(f"[SCHED][MISSED] job_id={event.job_id} scheduled={event.scheduled_run_time}")
    elif event.code == EVENT_JOB_MAX_INSTANCES:
        print(f"[SCHED][SKIP]  job_id={event.job_id} still running at scheduled={event.scheduled_run_time}")

def get_scheduler():
    """Permite a los endpoints /admin/api/features_health leer los jobs."""
    return _SCHED

def start_scheduler(app, usuario_id: int = 1):
    """
    Arranca el scheduler con frecuencias tomadas de app.config.
    Usa guard con WERKZEUG_RUN_MAIN para evitar doble arranque.
    """
    global _SCHED

    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        print("[SCHED] Ignorando arranque en proceso padre (reloader).")
        return None

    if _SCHED is None:
        tz = ZoneInfo(app.config.get("TZ", "America/Mexico_City"))
        _SCHED = BackgroundScheduler(
            jobstores={"default": MemoryJobStore()},
            timezone=tz,
            job_defaults={
                "coalesce": True,
                "misfire_grace_time": 60,
                "max_instances": 1,
            }
        )
        _SCHED.add_listener(
            _listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED | EVENT_JOB_MAX_INSTANCES
        )

    # --- Frecuencias desde config.py ---
    every_min   = int(app.config.get("JOB_FH_MINUTES", 1))
    close_hour  = int(app.config.get("JOB_CLOSE_HOUR", 0))
    close_min   = int(app.config.get("JOB_CLOSE_MINUTE", 5))
    cu_hours    = int(app.config.get("JOB_CATCHUP_HOURS", 1))
    cu_lookback = int(app.config.get("JOB_CATCHUP_LOOKBACK", 3))

    # 1) Día en curso (horarias): cada N minutos
    _SCHED.add_job(
        job_features_horarias, trigger="interval",
        minutes=every_min,
        kwargs={"app": app, "usuario_id": usuario_id},
        id="features_horarias",
        replace_existing=True,
        jitter=5,
        next_run_time=datetime.now(ZoneInfo(app.config.get("TZ", "America/Mexico_City"))),
    )

    # 2) Cierre diario (diarias): cron configurable (por default 00:05)
    _SCHED.add_job(
        job_features_diarias, trigger="cron",
        hour=close_hour, minute=close_min,
        kwargs={"app": app, "usuario_id": usuario_id},
        id="features_diarias",
        replace_existing=True,
        jitter=10,
    )

    # 3) Catch-up: cada N horas, con lookback M días
    _SCHED.add_job(
        job_catchup, trigger="interval",
        hours=cu_hours,
        kwargs={"app": app, "usuario_id": usuario_id, "dias_atras": cu_lookback},
        id="features_catchup",
        replace_existing=True,
    )

    if not _SCHED.running:
        _SCHED.start()
        print("[SCHED] Features scheduler iniciado (Bloque 1)")
    return _SCHED
