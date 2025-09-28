import subprocess
from datetime import date, timedelta
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
    print(f"[SCHED][ML] Catch-up últimos {dias} días user={usuario_id}")
    with app.app_context():
        conexion = get_mysql()
        try:
            with conexion.cursor() as cursor:
                for i in range(dias, 0, -1):
                    d = (date.today() - timedelta(days=i)).isoformat()
                    
                    # Verificamos si ya existe predicción en BD
                    cursor.execute("""
                        SELECT COUNT(*) FROM ml_preds_diarias
                        WHERE usuario_id=%s AND fecha_pred=%s
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
                            print(f"[CATCHUP] Generada predicción {d} para u{usuario_id}")
                        except subprocess.CalledProcessError as e:
                            print(f"[CATCHUP][ERROR] u{usuario_id} fecha={d} -> {e}")
                    else:
                        print(f"[CATCHUP] Ya existe predicción {d} user={usuario_id}, skip")
        finally:
            conexion.close()
