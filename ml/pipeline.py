import argparse, json, glob, shutil
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from joblib import dump, load

from ml.data import load_fc_diaria
from ml.features import make_lagged, get_feature_cols, split_train_holdout, latest_X_per_categoria
from ml.estimators import NaiveLast, MA7, RFReg
from ml.metrics import mae, rmse, smape, _best_baseline, log_metrics
import numpy as np
import unicodedata
import re as _re
import sqlalchemy as sa
from app.extensions import db


def _strip_accents(s: str) -> str:
    if not isinstance(s, str):
        return s
    nfkd = unicodedata.normalize('NFKD', s)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)])

_CANON_EQ = {
    "sincategoria": "Sin categoría",
    "sin categoria": "Sin categoría",
    "sin categoría": "Sin categoría",
}
def canon_cat(name: str) -> str:
    if not name:
        return "Sin categoría"
    key = _strip_accents(str(name)).strip().lower()
    key = _re.sub(r"[\s_\-]+", " ", key)
    return _CANON_EQ.get(key, str(name).strip())

def smape_safe(y_true, y_pred, eps: float = 1e-6):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    denom = (np.abs(y_true) + np.abs(y_pred))
    denom = np.where(denom < eps, eps, denom)
    return 100.0 * np.mean(np.abs(y_pred - y_true) / denom)

def clamp_and_round(y, rnd=2):
    y = np.maximum(y, 0.0)
    return np.round(y, rnd)


def _bootstrap_flask_context():
    """
    Empuja un app_context para que SQLAlchemy (db) funcione desde CLI.
    Intenta varios paths comunes de factory u objeto app.
    """
    try:
        from flask import current_app
        _ = current_app.name 
        return None
    except Exception:
        pass

    app = None
    try:
        from app import create_app
        app = create_app()
    except Exception:
        try:
            from app.app import create_app
            app = create_app()
        except Exception:
            try:
                from app.app import app as _app  
                app = _app
            except Exception as e:
                raise RuntimeError(
                    "No pude inicializar Flask. Expone create_app() en app/__init__.py "
                    "o en app/app.py, o un objeto app en app/app.py."
                ) from e

    app.app_context().push()
    return app



ARTIF_DIR = Path("ml/artifacts")
ARTIF_DIR.mkdir(parents=True, exist_ok=True)
LATEST = ARTIF_DIR / "model_latest.joblib"
LATEST_METRICS = ARTIF_DIR / "metrics_latest.json"

def _save_json(path: Path, obj: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def _load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def train(usuario_id: int, hist_days: int = 180, holdout_days: int = 7):
    start = date.today() - timedelta(days=hist_days)
    end = date.today() - timedelta(days=1)
    df = load_fc_diaria(usuario_id, start=start, end=end)

    n_dias = 0 if df.empty else df["fecha"].nunique()
    d = make_lagged(df) if not df.empty else df
    threshold = min(hist_days, max(10, int(0.5 * hist_days)))
    if df.empty or n_dias < threshold:
        from ml.estimators import BaselineHybrid
        if d is None or len(getattr(d, "index", [])) == 0:
            X_cols = ["min_t-1","MA7","dow","is_weekend","day","days_to_eom"]
        else:

            X_cols = get_feature_cols(d)
        bundle = {"model": BaselineHybrid(), "features": X_cols, "mode": "baseline"}
        ts = date.today().isoformat()
        model_path = ARTIF_DIR / f"model_{ts}_baseline.joblib"
        dump(bundle, model_path)
        shutil.copyfile(model_path, LATEST)
        reason = "sin datos" if df.empty else f"hist_insuficiente: n_dias={n_dias} < threshold={threshold}"
        metrics = {
            "usuario_id": usuario_id, "hist_days": n_dias,
            "hist_requested": hist_days,
            "holdout_days": 0, "timestamp": ts,
            "rows_train": 0, "rows_test": 0,
            "note": f"baseline-only ({reason})"
        }
        _save_json(ARTIF_DIR / f"metrics_{ts}.json", metrics)
        _save_json(LATEST_METRICS, metrics)

        log_metrics({
            "fecha": date.today(),
            "usuario_id": usuario_id,
            "modelo": "baseline",
            "categoria": "ALL",
            "hist_days": int(n_dias),
            "rows_train": 0,
            "rows_test": 0,
            "metric_mae": None,
            "metric_rmse": None,
            "baseline": "baseline",
            "is_promoted": 1,
            "artifact_path": str(model_path),
        })

        return {"model_path": str(model_path), "metrics": metrics, "promoted": True}
    
    X_cols = get_feature_cols(d) 

    if not X_cols:
        fallback = ["min_t-1", "MA7", "dow", "is_weekend", "day", "days_to_eom"]
        X_cols = [c for c in fallback if c in d.columns]

    if not X_cols:
        from ml.estimators import BaselineHybrid
        bundle = {"model": BaselineHybrid(), "features": [], "mode": "baseline"}
        ts = date.today().isoformat()
        model_path = ARTIF_DIR / f"model_{ts}_baseline.joblib"
        dump(bundle, model_path)
        shutil.copyfile(model_path, LATEST)
        reason = f"sin features X_cols (n_dias={n_dias}, threshold={threshold})"
        metrics = {
            "usuario_id": usuario_id, "hist_days": n_dias,
            "hist_requested": hist_days,
            "holdout_days": 0, "timestamp": ts,
            "rows_train": 0, "rows_test": 0,
            "note": f"baseline-only ({reason})"
        }
        _save_json(ARTIF_DIR / f"metrics_{ts}.json", metrics)
        _save_json(LATEST_METRICS, metrics)

        log_metrics({
            "fecha": date.today(),
            "usuario_id": usuario_id,
            "modelo": "baseline",
            "categoria": "ALL",
            "hist_days": int(n_dias),
            "rows_train": 0,
            "rows_test": 0,
            "metric_mae": None,
            "metric_rmse": None,
            "baseline": "baseline",
            "is_promoted": 1,
            "artifact_path": str(model_path),
        })

        return {"model_path": str(model_path), "metrics": metrics, "promoted": True}


    train_df, test_df = split_train_holdout(d, holdout_days=holdout_days)
    Xtr, ytr = train_df[X_cols], train_df["minutos"]
    Xte, yte = test_df[X_cols], test_df["minutos"]
    if len(Xtr) < 20 or len(Xte) < 5:
        raise RuntimeError("Muy pocas filas útiles para entrenar/evaluar. Aumenta hist o espera más días.")
   
    naive, ma7 = NaiveLast(), MA7()
    yhat_naive = naive.predict(Xte)
    yhat_ma7 = ma7.predict(Xte)

    m_naive = {"MAE": mae(yte, yhat_naive), "RMSE": rmse(yte, yhat_naive), "sMAPE": smape_safe(yte, yhat_naive)}
    m_ma7   = {"MAE": mae(yte, yhat_ma7),   "RMSE": rmse(yte, yhat_ma7),   "sMAPE": smape_safe(yte, yhat_ma7)}

    rf = RFReg()
    rf.fit(Xtr, ytr)
    yhat_rf = rf.predict(Xte)
    m_rf = {"MAE": mae(yte, yhat_rf), "RMSE": rmse(yte, yhat_rf), "sMAPE": smape_safe(yte, yhat_rf)}

    ts = date.today().isoformat()
    model_path = ARTIF_DIR / f"model_{ts}.joblib"
    dump({"model": rf, "features": X_cols}, model_path)

    metrics = {
        "usuario_id": usuario_id,
        "hist_days": int(n_dias),
        "hist_requested": int(hist_days),
        "holdout_days": holdout_days,
        "timestamp": ts,
        "rows_train": int(len(Xtr)),
        "rows_test": int(len(Xte)),
        "baselines": {"naive": m_naive, "MA7": m_ma7},
        "rf": m_rf
    }
    _save_json(ARTIF_DIR / f"metrics_{ts}.json", metrics)

    best_base = _best_baseline(metrics.get("baselines"), prefer="MAE")

    log_metrics({
        "fecha": date.today(),
        "usuario_id": usuario_id,
        "modelo": "rf",
        "categoria": "ALL",  # si luego entrenas por categoría, cambia aquí
        "hist_days": int(n_dias),
        "rows_train": int(len(Xtr)),
        "rows_test": int(len(Xte)),
        "metric_mae": float(m_rf["MAE"]),
        "metric_rmse": float(m_rf["RMSE"]),
        "baseline": best_base,
        "is_promoted": 0,
        "artifact_path": str(model_path),
    })
    
    # Política de promoción: RF debe ganarle a MA7 en MAE y RMSE por un margen.
    margin = 0.0  # 0.01 => 1% de mejora mínima
    promote = (m_rf["MAE"] <= m_ma7["MAE"] * (1 - margin)) and (m_rf["RMSE"] <= m_ma7["RMSE"] * (1 - margin))

    if promote:
        shutil.copyfile(model_path, LATEST)
        _save_json(LATEST_METRICS, metrics)

        log_metrics({
            "fecha": date.today(),
            "usuario_id": usuario_id,
            "modelo": "rf",
            "categoria": "ALL",
            "hist_days": int(n_dias),
            "rows_train": int(len(Xtr)),
            "rows_test": int(len(Xte)),
            "metric_mae": float(m_rf["MAE"]),
            "metric_rmse": float(m_rf["RMSE"]),
            "baseline": best_base,
            "is_promoted": 1,
            "artifact_path": str(model_path),
        })

    return {"model_path": str(model_path), "metrics": metrics, "promoted": promote}

def _load_latest_model():
    if not LATEST.exists():
        cands = sorted(glob.glob(str(ARTIF_DIR / "model_*.joblib")))
        if not cands:
            raise FileNotFoundError("No hay modelo entrenado. Corre: python -m ml.pipeline train --usuario 1")
        return load(cands[-1])
    return load(LATEST)

def predict(usuario_id: int, fecha: date | None = None):
    """
    Genera predicción para la 'próxima fecha' respecto al último dato disponible.
    Si pasas fecha=X, se usa historia hasta X-1 y se predice X.
    """
    if fecha is None:
        fecha = date.today() + timedelta(days=1)

    df = load_fc_diaria(usuario_id, end=fecha - timedelta(days=1))
    if df.empty:
        return {"usuario_id": usuario_id, "fecha_pred": fecha.isoformat(), "predicciones": []}

    d = make_lagged(df)
    latest, feats = latest_X_per_categoria(d)
    if latest.empty:
        return {"usuario_id": usuario_id, "fecha_pred": fecha.isoformat(), "predicciones": []}

    bundle = _load_latest_model()
    model = bundle["model"]
    trained_feats = bundle.get("features", [])
    candidate_feats = feats
    use_feats = [c for c in candidate_feats if c in trained_feats] or trained_feats
    if not use_feats:
        return {"usuario_id": usuario_id, "fecha_pred": fecha.isoformat(), "predicciones": []}

    X = latest[use_feats]

    yhat = model.predict(X)
    yhat = np.maximum(yhat, 0.0)      
    yhat = np.round(yhat, 2)    
    agg = {}
    for cat, yh in zip(latest["categoria"], yhat):
        c = canon_cat(cat)
        agg[c] = float(agg.get(c, 0.0) + float(yh))

    hist = df.copy()
    if "fecha" in hist.columns:
        hist["fecha"] = pd.to_datetime(hist["fecha"], errors="coerce")
        hist = hist.dropna(subset=["fecha"])
    if "minutos" in hist.columns:
        hist["minutos"] = pd.to_numeric(hist["minutos"], errors="coerce").fillna(0)
    if "categoria" in hist.columns:
        hist["categoria"] = hist["categoria"].astype(str).map(canon_cat)

    dow = int(fecha.weekday())  
    hist_dow = hist.assign(dow=hist["fecha"].dt.weekday)
    hist_dow = hist_dow[hist_dow["dow"] == dow]

    p95_cat = {}
    if not hist_dow.empty:
        p95_cat = hist_dow.groupby("categoria")["minutos"].quantile(0.95).to_dict()

        totals = hist_dow.groupby("fecha")["minutos"].sum()
        med_total = float(totals.median()) if not totals.empty else None
    else:
        med_total = None

    for c in list(agg.keys()):
        cap = float(p95_cat.get(c, agg[c]))
        if agg[c] > cap:
            agg[c] = cap

    total_pred_raw = round(float(sum(agg.values())), 2)

    if med_total is not None:
        total_pred = sum(agg.values())
        if total_pred > med_total and total_pred > 0:
            factor = med_total / total_pred
            for c in agg:
                agg[c] = round(agg[c] * factor, 2)

    HIDE_SIN_CAT = True
    REDISTRIBUIR_SIN_CAT = False
    hidden_sin_cat = 0.0
    total_pre_hide = sum(agg.values())

    if HIDE_SIN_CAT:
        hidden_sin_cat = float(agg.pop("Sin categoría", 0.0))
        if REDISTRIBUIR_SIN_CAT and hidden_sin_cat > 0 and agg:
            total_now = sum(agg.values()) or 1.0
            factor = (total_now + hidden_sin_cat) / total_now
            for c in list(agg.keys()):
                agg[c] = round(agg[c] * factor, 2)

    MIN_MIN = 2.0
    preds = [{"categoria": c, "yhat_minutos": round(float(v), 2)} for c, v in agg.items()]
    preds = [p for p in preds if p["yhat_minutos"] >= MIN_MIN]
    preds.sort(key=lambda x: x["yhat_minutos"], reverse=True)

    total_pred = round(float(sum(p["yhat_minutos"] for p in preds)), 2)

    meta = {
        "dow": dow,
        "total_pred_raw": round(float(total_pred_raw), 2),
        "total_pred": total_pred,
        "med_total_dow": round(float(med_total), 2) if med_total is not None else None,
        "p95_aplicados": {
            p["categoria"]: round(float(p95_cat[p["categoria"]]), 2)
            for p in preds
            if p["categoria"] in p95_cat and p["yhat_minutos"] >= float(p95_cat[p["categoria"]])
        },
        "min_threshold": MIN_MIN,
        "oculto_sin_categoria": round(hidden_sin_cat, 2),
        "redistribuido": bool(REDISTRIBUIR_SIN_CAT),
    }

    return {"usuario_id": usuario_id, "fecha_pred": fecha.isoformat(), "predicciones": preds, "meta": meta}

def main():
    _bootstrap_flask_context()
    parser = argparse.ArgumentParser(description="Pipeline V3.0 (train/predict)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_train = sub.add_parser("train")
    p_train.add_argument("--usuario", type=int, required=True)
    p_train.add_argument("--hist", type=int, default=180)
    p_train.add_argument("--holdout", type=int, default=7)

    p_pred = sub.add_parser("predict")
    p_pred.add_argument("--usuario", type=int, required=True)
    p_pred.add_argument("--fecha", type=str, default=None)  

    args = parser.parse_args()
    if args.cmd == "train":
        res = train(args.usuario, hist_days=args.hist, holdout_days=args.holdout)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.cmd == "predict":
        f = date.fromisoformat(args.fecha) if args.fecha else None
        res = predict(args.usuario, fecha=f)
        print(json.dumps(res, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
