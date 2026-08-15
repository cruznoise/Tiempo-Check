from datetime import date, timedelta, datetime
import os
from pathlib import Path

import pandas as pd
from flask import current_app
from sqlalchemy import text
from zoneinfo import ZoneInfo

from app.extensions import db
from .features_jobs import job_features_diarias          
from .agg_jobs import job_agg_close_day                 
from .ml_jobs import job_ml_predict_multi               
from .rachas_jobs import job_rachas                      


def _is_reloader_child(app) -> bool:
    return (app.debug and os.environ.get("WERKZEUG_RUN_MAIN") == "true") or (not app.debug)


def _csv_has_rows(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        chk = pd.read_csv(path, nrows=1)
        return not chk.empty
    except Exception:
        return False


def _daterange(d0: date, d1: date):
    cur = d0
    while cur <= d1:
        yield cur
        cur = cur + timedelta(days=1)


def _dias_faltantes_features(app, usuario_id: int, lookback_days: int = 7):
    """
    Busca días faltantes de features en [hoy-lookback .. hoy] usando tz de config.
    Intenta columna 'dia'; si no existe, usa 'fecha'.
    """
    tz = ZoneInfo(app.config.get("TZ", "America/Mexico_City"))
    hoy = datetime.now(tz).date()
    start = hoy - timedelta(days=lookback_days)
    expected = list(_daterange(start, hoy))

    try:
        sql = text("""
            SELECT DISTINCT dia
            FROM features_diarias
            WHERE usuario_id = :uid AND dia BETWEEN :d0 AND :d1
        """)
        rows = db.session.execute(sql, {"uid": usuario_id, "d0": start, "d1": hoy}).fetchall()
        present = {pd.to_datetime(r[0]).date() for r in rows}
    except Exception:
        sql = text("""
            SELECT DISTINCT fecha
            FROM features_diarias
            WHERE usuario_id = :uid AND fecha BETWEEN :d0 AND :d1
        """)
        rows = db.session.execute(sql, {"uid": usuario_id, "d0": start, "d1": hoy}).fetchall()
        present = {pd.to_datetime(r[0]).date() for r in rows}

    missing = [d for d in expected if d not in present]
    if missing:
        print(f"[BOOT][CATCHUP] Días faltantes (features): {', '.join(map(str, missing))}")
    else:
        print("[BOOT][CATCHUP] Sin días pendientes. Todo en orden (según features_diarias)")
    return missing

def boot_catchup(app, usuario_id: int):
    if not _is_reloader_child(app):
        print("[BOOT][SKIP] Proceso primario del reloader (dev).")
        return

    print(f"[BOOT][CATCHUP] Verificando integridad temporal del sistema para usuario {usuario_id}...")
    dias_faltantes = _dias_faltantes_features(app, usuario_id, lookback_days=7)

    preds_dir = Path(current_app.root_path).parent / "ml" / "preds"
    
    # ✅ CAMBIO 1: Crear directorio por usuario
    usuario_preds_dir = preds_dir / f"usuario_{usuario_id}"
    usuario_preds_dir.mkdir(parents=True, exist_ok=True)

    for dia in dias_faltantes:
        print(f"[BOOT][CATCHUP] Corrigiendo día {dia} ...")

        try:
            job_features_diarias(current_app, usuario_id, dia)
            job_agg_close_day(current_app, usuario_id, dia)
        except Exception as e:
            print(f"[BOOT][CATCHUP][ERR] Fallo en features/agg para {dia}: {e}")
            continue

        # ✅ CAMBIO 2: Buscar en directorio del usuario
        target = usuario_preds_dir / f"preds_future_{dia}.csv"
        
        if not _csv_has_rows(target):
            print(f"[BOOT][CATCHUP][PRED-MISS] No existe/está vacío {target.name} para usuario {usuario_id}, generando...")
            try:
                job_ml_predict_multi(current_app, usuario_id, fecha_base=dia)
            except Exception as e:
                print(f"[BOOT][CATCHUP][ERR] multi para {dia}: {e}")

            if not _csv_has_rows(target):
                print(f"[BOOT][CATCHUP][WARN] {target.name} sigue vacío. Revisar pipeline/logs.")
            else:
                print(f"[BOOT][CATCHUP][OK] {target.name} generado.")
        else:
            print(f"[BOOT][CATCHUP] Predicciones OK para {dia}.")

        try:
            job_rachas(current_app, usuario_id, dia)
        except Exception as e:
            print(f"[SCHED][ERR][rachas] user={usuario_id} dia={dia} → {e}")

    print(f"[BOOT][CATCHUP] Finalizado para usuario {usuario_id}.")