import numpy as np
from app.extensions import db
import sqlalchemy as sa


def mae(y_true, y_pred): 
    return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred))))

def rmse(y_true, y_pred):
    y_true = np.asarray(y_true); y_pred = np.asarray(y_pred)
    return float(np.sqrt(np.mean((y_true - y_pred)**2)))

def smape(y_true, y_pred):
    y_true = np.asarray(y_true); y_pred = np.asarray(y_pred)
    denom = np.abs(y_true) + np.abs(y_pred)
    denom[denom == 0] = 1.0
    return float(100.0 * np.mean(2.0 * np.abs(y_pred - y_true) / denom))

def _best_baseline(bdict: dict, prefer: str = "MAE") -> str | None:
    """Devuelve el nombre de la baseline con menor MAE/RMSE."""
    if not bdict:
        return None
    prefer = prefer.upper()
    candidatos = []
    for nombre, m in bdict.items():
        if not m:
            continue
        val = m.get(prefer)
        if val is not None:
            candidatos.append((float(val), nombre))
    return min(candidatos)[1] if candidatos else None

def log_metrics(payload: dict):
    db.session.execute(sa.text("""
        INSERT INTO ml_metrics
        (fecha, usuario_id, modelo, categoria, hist_days, rows_train, rows_test,
         metric_mae, metric_rmse, baseline, is_promoted, artifact_path)
        VALUES
        (:fecha, :usuario_id, :modelo, :categoria, :hist_days, :rows_train, :rows_test,
         :metric_mae, :metric_rmse, :baseline, :is_promoted, :artifact_path)
    """), payload)
    db.session.commit()
