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

def job_ml_predict(app, usuario_id: int):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    print(f"[SCHED][ML] Predicción {tomorrow} user={usuario_id}")
    cmd = [
        "python3", "-m", "ml.pipeline", "predict",
        "--usuario", str(usuario_id),
        "--fecha", tomorrow,
        "--save-csv"
    ]
    subprocess.run(cmd, check=True)

def job_ml_catchup(app, usuario_id: int, dias: int = 3):
    """
    Verifica si existen predicciones faltantes en los últimos N días
    y las genera usando ml.pipeline.predict si es necesario.
    Compatible con v3.2 (usa ml_predicciones_future en lugar de ml_preds_diarias).
    """
    print(f"[SCHED][ML] Catch-up últimos {dias} días user={usuario_id}")

    with app.app_context():
        conexion = get_mysql()
        try:
            with conexion.cursor() as cursor:
                for i in range(dias, 0, -1):
                    d = (date.today() - timedelta(days=i)).isoformat()

                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM ml_predicciones_future 
                        WHERE usuario_id = %s AND fecha_pred = %s
                    """, (usuario_id, d))
                    existe = cursor.fetchone()[0]

                    if existe == 0:
                        cmd = [
                            "python3", "-m", "ml.pipeline", "predict",
                            "--usuario", str(usuario_id),
                            "--fecha", d,
                            "--save-csv"
                        ]
                        try:
                            subprocess.run(cmd, check=True)
                            print(f"[CATCHUP]  Generada predicción {d} para u{usuario_id}")
                        except subprocess.CalledProcessError as e:
                            print(f"[CATCHUP][ERROR]  u{usuario_id} fecha={d} -> {e}")
                    else:
                        print(f"[CATCHUP]  Ya existe predicción {d} user={usuario_id}, skip")

        except Exception as e:
            print(f"[CATCHUP][FATAL] {e}")
        finally:
            conexion.close()


def job_ml_train_cat(app, usuario_id: int):
    with app.app_context():
        from ml.pipeline import train_por_categoria
        print(f"[JOB][ML] Entrenamiento por categoría iniciado → usuario {usuario_id}")
        train_por_categoria(usuario_id)
        print(f"[JOB][ML] Entrenamiento por categoría finalizado → usuario {usuario_id}")

def job_ml_predict_multi(app, usuario_id: int, fecha_base=None):
    print(f"[SCHED][ML][MULTI] Predicciones extendidas user={usuario_id}")

    if isinstance(fecha_base, str):
        target = fecha_base
    elif fecha_base is None:
        target = date.today().isoformat()
    else:
        target = fecha_base.isoformat()

    cmd = [
        "python3", "-m", "ml.pipeline", "multi",
        "--usuario", str(usuario_id),
        "--fecha", target,
        "--save-csv"
    ]

    env = os.environ.copy()
    env["TIEMPOCHECK_ML_MODE"] = "1"  

    try:
        subprocess.run(cmd, check=True, env=env)
        print(f"[SCHED][OK][MULTI] Predicciones multi-horizonte generadas para user={usuario_id}")
    except subprocess.CalledProcessError as e:
        print(f"[SCHED][ERR][MULTI] user={usuario_id} → {e}")


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
