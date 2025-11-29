import subprocess
from datetime import date, timedelta, datetime
import os
from app.mysql_conn import get_mysql


def job_ml_train(app, usuario_id: int):
    print(f"[SCHED][ML] Entrenando modelo para user={usuario_id}")
    cmd = [
        "python3", "-m", "ml.pipeline", "train",
        "--usuario", str(usuario_id),
        "--hist", "90", "--holdout", "7"
    ]
    subprocess.run(cmd, check=True)

def job_ml_train_daily(app, usuario_id: int):
    """
    Wrapper explícito para entrenamiento periódico.
    Mantiene la importación usada por scheduler.py.
    """
    print(f"[SCHED][ML] Entrenamiento programado (weekly) user={usuario_id}")
    cmd = [
        "python3", "-m", "ml.pipeline", "train",
        "--usuario", str(usuario_id),
        "--hist", "180", "--holdout", "7"
    ]
    subprocess.run(cmd, check=True)

def job_ml_predict(app, usuario_id: int = None):
    """Genera predicciones para usuario(s)"""
    # Si no se especifica usuario, usar todos los activos
    if usuario_id is None:
        with app.app_context():
            from app.models.models import Usuario
            usuarios = Usuario.query.all()
            usuario_ids = [u.id for u in usuarios]
    else:
        usuario_ids = [usuario_id]
    
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    
    for uid in usuario_ids:
        print(f"[SCHED][ML] Predicción {tomorrow} user={uid}")
        cmd = [
            "python3", "-m", "ml.pipeline", "predict",
            "--usuario", str(uid),
            "--fecha", tomorrow,
            "--save-csv"
        ]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"[SCHED][ERR][PREDICT] user={uid} → {e}")

def job_ml_train_cat(app, usuario_id: int):
    with app.app_context():
        from ml.pipeline import train_por_categoria
        print(f"[JOB][ML] Entrenamiento por categoría iniciado → usuario {usuario_id}")
        train_por_categoria(usuario_id)
        print(f"[JOB][ML] Entrenamiento por categoría finalizado → usuario {usuario_id}")

def job_ml_predict_multi(app, usuario_id: int = None, fecha_base=None):
    """
    Genera predicciones multi-horizonte POR USUARIO
    Ya no necesita --save-csv porque SIEMPRE guarda por usuario
    """
    if usuario_id is None:
        with app.app_context():
            from app.models.models import Usuario
            usuarios = Usuario.query.all()
            usuario_ids = [u.id for u in usuarios]
    else:
        usuario_ids = [usuario_id]
    
    if isinstance(fecha_base, str):
        target = fecha_base
    elif fecha_base is None:
        target = date.today().isoformat()
    else:
        target = fecha_base.isoformat()
    
    for uid in usuario_ids:
        print(f"[SCHED][ML] Predicción multi-horizonte {target} user={uid}")
        cmd = [
            "python3", "-m", "ml.pipeline", "multi",
            "--usuario", str(uid),
            "--fecha", target
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"[SCHED][OK][MULTI] user={uid} → {result.stdout[:200]}")
        except subprocess.CalledProcessError as e:
            print(f"[SCHED][ERR][MULTI] user={uid} → {e.stderr}")

def job_ml_eval_daily(app=None, usuario_id=None):
    """Ejecuta evaluación diaria de desempeño multihorizonte"""
    print(f"[JOB][ML_EVAL] Iniciando evaluación diaria ({datetime.now().isoformat()})")
    try:
        subprocess.run(["python3", "-m", "ml.pipeline_eval"], check=True)
        print("[JOB][ML_EVAL] Evaluación completada con éxito.")
    except Exception as e:
        print(f"[JOB][ML_EVAL][ERROR] {e}")

def job_ml_eval_weekly(app=None):
    from ml.pipeline_eval_weekly import generar_resumen_semanal
    with app.app_context():
        print("[JOB][EVAL] Generando resumen semanal de precisión...")
        generar_resumen_semanal()
