import argparse, json, glob, shutil
from datetime import date, timedelta, datetime
from pathlib import Path

import pandas as pd
from joblib import dump, load

from ml.data import load_fc_diaria
from ml.features import make_lagged, get_feature_cols, split_train_holdout, latest_X_per_categoria
from ml.estimators import NaiveLast, MA7, RFReg
from ml.metrics import mae, rmse, smape, _best_baseline, log_metrics
from ml.models import BaselineHybrid, RandomForestWrapper
from ml.utils import canon_cat_filename, ensure_dir
from ml.scripts.build_model_selector import build_model_selector 
import numpy as np
import unicodedata
import re as _re
import sqlalchemy as sa
from app.extensions import db
import json


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
    ts = date.today().isoformat()

    # ---------------- Baseline case ----------------
    if df.empty or n_dias < threshold:
        from ml.estimators import BaselineHybrid
        X_cols = get_feature_cols(d) if (d is not None and len(getattr(d, "index", [])) > 0) else \
                 ["min_t-1","MA7","dow","is_weekend","day","days_to_eom"]

        bundle = {"model": BaselineHybrid(), "features": X_cols, "mode": "baseline"}
        model_path = ARTIF_DIR / f"model_{ts}_baseline.joblib"
        dump(bundle, model_path)
        shutil.copyfile(model_path, LATEST)

        reason = "sin datos" if df.empty else f"hist_insuficiente: n_dias={n_dias} < threshold={threshold}"
        metrics = {
            "usuario_id": usuario_id,
            "mode": "baseline",
            "hist_days": n_dias,
            "hist_requested": hist_days,
            "holdout_days": 0,
            "timestamp": ts,
            "rows_train": 0,
            "rows_test": 0,
            "note": f"baseline-only ({reason})"
        }
        _save_json(ARTIF_DIR / f"metrics_{ts}_baseline.json", metrics)
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

    # ---------------- RandomForest case ----------------
    X_cols = get_feature_cols(d) or \
             [c for c in ["min_t-1","MA7","dow","is_weekend","day","days_to_eom"] if c in d.columns]

    if not X_cols:
        raise RuntimeError("No hay columnas de features útiles para entrenar.")
    train_df, test_df = split_train_holdout(d, holdout_days=holdout_days)
    Xtr, ytr = train_df[X_cols], train_df["minutos"]
    Xte, yte = test_df[X_cols], test_df["minutos"]

    if len(Xtr) < 20 or len(Xte) < 5:
        raise RuntimeError("Muy pocas filas útiles para entrenar/evaluar. Aumenta hist o espera más días.")

    # baselines
    naive, ma7 = NaiveLast(), MA7()
    yhat_naive, yhat_ma7 = naive.predict(Xte), ma7.predict(Xte)
    m_naive = {"MAE": mae(yte, yhat_naive), "RMSE": rmse(yte, yhat_naive), "sMAPE": smape_safe(yte, yhat_naive)}
    m_ma7   = {"MAE": mae(yte, yhat_ma7),   "RMSE": rmse(yte, yhat_ma7),   "sMAPE": smape_safe(yte, yhat_ma7)}

    # rf
    rf = RFReg()
    rf.fit(Xtr, ytr)
    yhat_rf = rf.predict(Xte)
    m_rf = {"MAE": mae(yte, yhat_rf), "RMSE": rmse(yte, yhat_rf), "sMAPE": smape_safe(yte, yhat_rf)}

    model_path = ARTIF_DIR / f"model_{ts}_rf.joblib"
    dump({"model": rf, "features": X_cols, "mode": "rf"}, model_path)

    try:
        hyperparams = rf.get_params()
    except AttributeError:
        hyperparams = rf.model.get_params() if hasattr(rf, "model") else {}

    metrics = {
        "usuario_id": usuario_id,
        "mode": "rf",
        "hist_days": int(n_dias),
        "hist_requested": int(hist_days),
        "holdout_days": holdout_days,
        "timestamp": ts,
        "rows_train": int(len(Xtr)),
        "rows_test": int(len(Xte)),
        "baselines": {"naive": m_naive, "MA7": m_ma7},
        "rf": m_rf,
        "hyperparams": hyperparams
    }
    _save_json(ARTIF_DIR / f"metrics_{ts}_rf.json", metrics)
    _save_json(LATEST_METRICS, metrics)

    best_base = _best_baseline(metrics.get("baselines"), prefer="MAE")

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
        "is_promoted": 0,
        "artifact_path": str(model_path),
    })

    promote = (m_rf["MAE"] <= m_ma7["MAE"]) and (m_rf["RMSE"] <= m_ma7["RMSE"])
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

def train_por_categoria(usuario_id: int, hist_days: int = 180):
    """
    Entrena un modelo RandomForest por cada categoría del usuario.
    Guarda los artefactos en ml/artifacts/<categoria>/rf_<categoria>.joblib
    (ML-005: actualiza automáticamente model_selector.json)
    """
    start = date.today() - timedelta(days=hist_days)
    end = date.today() - timedelta(days=1)
    df = load_fc_diaria(usuario_id, start=start, end=end)
    if df.empty:
        print(" No hay datos para entrenar.")
        return

    categorias = df["categoria"].unique()
    print(f"[TRAIN] Entrenando {len(categorias)} categorías...")

    for cat in categorias:
        sub = df[df["categoria"] == cat].copy()
        if len(sub) < 10:
            print(f"[SKIP] {cat}: insuficiente historial ({len(sub)} registros)")
            continue

        d = make_lagged(sub)
        X_cols = get_feature_cols(d)
        train_df, test_df = split_train_holdout(d, holdout_days=7)
        Xtr, ytr = train_df[X_cols], train_df["minutos"]

        rf = RFReg()
        rf.fit(Xtr, ytr)

        # --- ML-003 & ML-005 fixes ---
        cat_name = canon_cat_filename(cat)
        outdir = ARTIF_DIR / cat_name
        ensure_dir(outdir)
        artifact_path = outdir / f"rf_{cat_name}.joblib"
        dump(rf, artifact_path)
        print(f"[OK] Guardado modelo RF para {cat} → {artifact_path}")

    # --- ML-005 fix: actualizar automáticamente el selector ---
    try:
        build_model_selector()
        print("[ML-005] model_selector.json actualizado correctamente.")
    except Exception as e:
        print(f"[WARN][ML-005] No se pudo actualizar model_selector.json: {e}")

def _load_latest_model():
    if not LATEST.exists():
        cands = sorted(glob.glob(str(ARTIF_DIR / "model_*.joblib")))
        if not cands:
            raise FileNotFoundError("No hay modelo entrenado. Corre: python -m ml.pipeline train --usuario 1")
        return load(cands[-1])
    return load(LATEST)

print("[TEST] ml/pipeline.py cargado correctamente ✅")

def predict(usuario_id: int, fecha: date | None = None, save_csv: bool = False):
    """
    Genera predicción por categoría usando el selector automático de modelos.
    Si pasas fecha=X, se usa historia hasta X-1 y se predice X.
    """
    if fecha is None:
        fecha = date.today() + timedelta(days=1)

    df = load_fc_diaria(usuario_id, end=fecha - timedelta(days=1))
    print(f"[DEBUG] predict(): usuario={usuario_id}, fecha={fecha}, registros={len(df)}")

    if df.empty:
        return {"usuario_id": usuario_id, "fecha_pred": fecha.isoformat(), "predicciones": []}

    d = make_lagged(df)
    latest, feats = latest_X_per_categoria(d)
    latest = (
        latest
        .sort_values("fecha", ascending=True)
        .drop_duplicates(subset=["categoria"], keep="last")
        .reset_index(drop=True)
    )
    print("[DEBUG] latest_X_per_categoria (post-clean) →")
    print(latest.head())
    if isinstance(feats, list):
        print(f"[DEBUG] feats → lista con {len(feats)} columnas: {feats}")
    else:
        print("[DEBUG] feats →")
        print(feats.head())


    if latest.empty:
        return {"usuario_id": usuario_id, "fecha_pred": fecha.isoformat(), "predicciones": []}

    preds = []
    for idx, row in latest.iterrows():
        categoria = canon_cat(row["categoria"])
        valid_feats = ['min_t-1', 'min_t-2', 'min_t-3', 'min_t-7', 'MA7', 'dow', 'is_weekend', 'day', 'days_to_eom']
        feats_cat = row[valid_feats].to_dict()
        hist_cat = df[df["categoria"] == categoria]["minutos"]
        yhat = predict_categoria(categoria, feats_cat, df_hist=hist_cat)
        preds.append({"categoria": categoria, "yhat_minutos": round(float(yhat), 2)})


    print("[DEBUG] predicciones crudas →", preds)

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

    for p in preds:
        cap = float(p95_cat.get(p["categoria"], p["yhat_minutos"]))
        if p["yhat_minutos"] > cap:
            p["yhat_minutos"] = cap

    HIDE_SIN_CAT = True
    REDISTRIBUIR_SIN_CAT = False
    if HIDE_SIN_CAT:
        preds = [p for p in preds if p["categoria"] != "Sin categoría"]

    MIN_MIN = 2.0
    preds = [p for p in preds if p["yhat_minutos"] >= MIN_MIN]
    preds.sort(key=lambda x: x["yhat_minutos"], reverse=True)

    print("[DEBUG] predicciones finales (después de filtros) →", preds)

    total_pred = round(float(sum(p["yhat_minutos"] for p in preds)), 2)
    total_pred_raw = round(float(sum(p["yhat_minutos"] for p in preds)), 2)

    meta = {
        "dow": dow,
        "total_pred_raw": total_pred_raw,
        "total_pred": total_pred,
        "med_total_dow": round(float(med_total), 2) if med_total is not None else None,
        "p95_aplicados": {
            p["categoria"]: round(float(p95_cat[p["categoria"]]), 2)
            for p in preds
            if p["categoria"] in p95_cat and p["yhat_minutos"] >= float(p95_cat[p["categoria"]])
        },
        "min_threshold": MIN_MIN,
        "oculto_sin_categoria": 0.0,
        "redistribuido": bool(REDISTRIBUIR_SIN_CAT),
    }

    result = {
        "usuario_id": usuario_id,
        "fecha_pred": fecha.isoformat(),
        "predicciones": preds,
        "meta": meta,
    }

    if save_csv:
        ts = datetime.now().strftime("%Y%m%dT%H%M%S")
        outdir = Path("ml/preds") / str(usuario_id)
        outdir.mkdir(parents=True, exist_ok=True)

        df_out = pd.DataFrame(preds)
        df_out.insert(0, "usuario_id", usuario_id)
        df_out.insert(1, "fecha_pred", fecha.isoformat())
        df_out.insert(2, "generated_at", datetime.now().isoformat())
        df_out.to_csv(outdir / f"{fecha.isoformat()}_{ts}.csv", index=False)
        df_out.to_csv(outdir / f"{fecha.isoformat()}.csv", index=False)

    return result

def main():
    _bootstrap_flask_context()
    parser = argparse.ArgumentParser(description="Pipeline V3.1 (train/predict/train_cat)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_train = sub.add_parser("train")
    p_train.add_argument("--usuario", type=int, required=True)
    p_train.add_argument("--hist", type=int, default=180)
    p_train.add_argument("--holdout", type=int, default=7)
    p_pred = sub.add_parser("predict")
    p_pred.add_argument("--usuario", type=int, required=True)
    p_pred.add_argument("--fecha", type=str, default=None)
    p_pred.add_argument("--save-csv", action="store_true")
    p_train_cat = sub.add_parser("train_cat")
    p_train_cat.add_argument("--usuario", type=int, required=True)
    p_train_cat.add_argument("--hist", type=int, default=180)

    args = parser.parse_args()

    if args.cmd == "train":
        res = train(args.usuario, hist_days=args.hist, holdout_days=args.holdout)
        print(json.dumps(res, ensure_ascii=False, indent=2))

    elif args.cmd == "predict":
        f = date.fromisoformat(args.fecha) if args.fecha else None
        res = predict(args.usuario, fecha=f, save_csv=args.save_csv)
        print(json.dumps(res, ensure_ascii=False, indent=2))

    elif args.cmd == "train_cat":
        print(f"[CMD] Entrenamiento por categoría para usuario {args.usuario}")
        train_por_categoria(args.usuario, hist_days=args.hist)
        print("[DONE] Entrenamiento por categoría completado.")



SELECTOR_FILE = Path("ml/artifacts/model_selector.json")

if SELECTOR_FILE.exists():
    with open(SELECTOR_FILE, "r") as f:
        MODEL_SELECTOR = json.load(f)
else:
    MODEL_SELECTOR = {}

def get_model_for_categoria(categoria: str) -> str:
    """
    Devuelve el modelo elegido para la categoría.
    Si no existe en el selector → usa BaselineHybrid.
    """
    return MODEL_SELECTOR.get(categoria, "BaselineHybrid")

def predict_categoria(categoria: str, features, df_hist=None) -> float:
    """
    Aplica el modelo correcto según la categoría y devuelve la predicción.
    Si no hay modelo RF, usa BaselineHybrid entrenado con el histórico real (últimos 7 valores).
    """
    modelo = get_model_for_categoria(categoria)

    # Asegurar que features sea lista de valores
    if isinstance(features, dict):
        features = list(features.values())
    elif hasattr(features, "iloc"):
        features = list(features.iloc[0].values)

    # --- Si existe modelo RandomForest entrenado ---
    if modelo == "RandomForest":
        try:
            model = RandomForestWrapper.load(categoria)
            pred = model.predict(features)
            return float(pred)
        except FileNotFoundError:
            print(f"[WARN] RF no encontrado para {categoria}, usando BaselineHybrid.")
        except Exception as e:
            print(f"[ERROR RF] {categoria}: {e}")

    # --- Fallback: BaselineHybrid con histórico real ---
    if df_hist is not None and len(df_hist) > 0:
        # Usar últimos 7 valores
        serie = df_hist.tail(7)
        bh = BaselineHybrid().fit(serie)
        pred = bh.predict()
        print(f"[BASELINE] {categoria}: media={bh.mean_7d:.2f}, trend={bh.trend:.2f}, pred={pred:.2f}")
        return float(pred)
    else:
        print(f"[WARN] Sin histórico válido para {categoria}, devolviendo 0.0")
        return 0.0

if __name__ == "__main__":
    main()
