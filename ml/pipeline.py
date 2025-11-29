import argparse, json, glob, shutil
from datetime import date, timedelta, datetime
from pathlib import Path

import pandas as pd
from joblib import dump, load
import os
import sys 
from ml.data import load_fc_diaria
from ml.features import make_lagged, get_feature_cols, split_train_holdout, latest_X_per_categoria, build_features_for_day
from ml.estimators import NaiveLast, MA7, RFReg
from ml.metrics import mae, rmse, smape, _best_baseline, log_metrics
from ml.models import BaselineHybrid, RandomForestWrapper, load_model_for_categoria
from ml.utils_ml import canon_cat_filename, ensure_dir, guardar_predicciones
from ml.scripts.build_model_selector import build_model_selector 
import numpy as np
import unicodedata
import re as _re
import sqlalchemy as sa
from app.extensions import db
import json
import joblib

try:
    from app.services.contexto_ml_integration import ajustar_prediccion_con_contexto
    CONTEXTO_DISPONIBLE = True
except ImportError:
    CONTEXTO_DISPONIBLE = False
    print("[PIPELINE] Módulo de contexto no disponible")

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
    Empuja un app_context para que SQLAlchemy (db) funcione desde CLI o scheduler.
    Si detecta TIEMPOCHECK_ML_MODE=1, inicia un contexto mínimo para SQLAlchemy
    sin arrancar el servidor Flask ni ejecutar boot_catchup.
    """

    is_ml_mode = os.environ.get("TIEMPOCHECK_ML_MODE") == "1"

    if is_ml_mode:
        print("[PIPELINE][MODE] Modo ML detectado — inicializando contexto mínimo Flask.")
        try:
            from app import create_app
            app = create_app()
            ctx = app.app_context()
            ctx.push()
            print("[PIPELINE][CTX] Contexto mínimo Flask activado para SQLAlchemy.")
            return ctx
        except Exception as e:
            print(f"[PIPELINE][ERR] No se pudo iniciar contexto mínimo: {e}")
            return None

    try:
        from flask import current_app
        _ = current_app.name
        return None
    except Exception:
        pass

    try:
        from app import create_app
        app = create_app()
        ctx = app.app_context()
        ctx.push()
        print("[PIPELINE][CTX] Contexto Flask creado (modo normal).")
        return ctx
    except Exception as e:
        print(f"[PIPELINE][ERR] No se pudo crear contexto Flask: {e}")
        return None


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
    threshold = min(hist_days, max(10, int(0.3 * hist_days)))
    ts = date.today().isoformat()

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

def train_por_categoria(usuario_id, hist_days=180):
    """
    Entrena modelos RF por categoría para UN USUARIO específico.
    Guarda los artefactos en ml/artifacts/usuario_X/<categoria>/rf_<categoria>.joblib
    """
    start = date.today() - timedelta(days=hist_days)
    end = date.today() - timedelta(days=1)
    df = load_fc_diaria(usuario_id, start=start, end=end)
    
    if df.empty:
        print(f"No hay datos para entrenar (usuario={usuario_id})")
        return

    categorias = df["categoria"].unique()
    print(f"[TRAIN] Entrenando {len(categorias)} categorías para usuario {usuario_id}...")

    for cat in categorias:
        sub = df[df["categoria"] == cat].copy()
        if len(sub) < 10:
            print(f"[SKIP] {cat}: insuficiente historial ({len(sub)} registros)")
            continue

        d = make_lagged(sub)
        X_cols = get_feature_cols(d)
        train_df, test_df = split_train_holdout(d, holdout_days=7)
        Xtr = train_df[X_cols].astype(float)
        ytr = train_df["minutos"].astype(float)

        rf = RFReg()
        rf.fit(Xtr, ytr)
        rf.feature_names_in_ = list(Xtr.columns)

        #  Guardar POR USUARIO
        cat_name = canon_cat_filename(cat)
        outdir = ARTIF_DIR / f"usuario_{usuario_id}" / cat_name
        ensure_dir(outdir)
        artifact_path = outdir / f"rf_{cat_name}.joblib"
        dump(rf, artifact_path)
        print(f"[OK] Guardado modelo RF para usuario {usuario_id}, {cat} → {artifact_path}")
        
        # Métricas
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        import numpy as np

        ypred = rf.predict(train_df[X_cols])
        mae = float(mean_absolute_error(ytr, ypred))
        mse = float(mean_squared_error(ytr, ypred))
        rmse = float(np.sqrt(mse))
        r2 = float(r2_score(ytr, ypred))

        metrics = {"MAE": mae, "RMSE": rmse, "R2": r2}
        with open(outdir / "metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)

        print(f"[METRICS] {cat} → {metrics}")

    # Actualizar model_selector POR USUARIO
    try:
        build_model_selector(usuario_id)
        print(f"[ML-005] model_selector.json actualizado para usuario {usuario_id}")
    except Exception as e:
        print(f"[WARN][ML-005] No se pudo actualizar model_selector.json: {e}")

def _load_latest_model():
    if not LATEST.exists():
        cands = sorted(glob.glob(str(ARTIF_DIR / "model_*.joblib")))
        if not cands:
            raise FileNotFoundError("No hay modelo entrenado. Corre: python -m ml.pipeline train --usuario 1")
        return load(cands[-1])
    return load(LATEST)

print("[TEST] ml/pipeline.py cargado correctamente ")

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
        feats_cat = row[valid_feats]
        hist_cat = df[df["categoria"] == categoria]["minutos"]
        yhat = predict_categoria(
            usuario_id=usuario_id,
            categoria=categoria,
            features=feats_cat,
            df_hist=hist_cat
        )
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

    # ========================================================================
    # GUARDAR EN BASE DE DATOS
    # ========================================================================
    from app.models.ml import MLPrediccionFuture
    from app.extensions import db
    
    try:
        # Eliminar predicciones antiguas de esta fecha
        MLPrediccionFuture.query.filter_by(
            usuario_id=usuario_id,
            fecha_pred=fecha
        ).delete()
        
        # Guardar nuevas predicciones
        for p in preds:
            pred_obj = MLPrediccionFuture(
                usuario_id=usuario_id,
                fecha_pred=fecha,
                categoria=p['categoria'],
                yhat_minutos=p['yhat_minutos'],  # Ya es float, no necesitas int()
                modelo='RandomForest',  # O el modelo que uses
                version_modelo='v3.2',  # Tu versión actual
                fecha_creacion=datetime.now()
            )
            db.session.add(pred_obj)
                
        db.session.commit()
        print(f"[DEBUG] Guardadas {len(preds)} predicciones en BD para {fecha}")
        
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] No se pudieron guardar predicciones: {e}")

    return result

def predict_multi_horizon(usuario_id, fecha_base, horizontes=[1, 2, 3]):
    """
    Genera predicciones para múltiples horizontes (T+1..T+N) y las guarda en ml/preds/
    """
    all_preds = []
    fecha_base = pd.to_datetime(fecha_base)

    for h in horizontes:
        fecha_pred = fecha_base + timedelta(days=h)
        print(f"[ML][MULTI] Generando predicciones {fecha_pred.date()} (h={h})")
        df_features = build_features_for_day(usuario_id, fecha_base)
        if df_features.empty:
            print(f"[WARN][MULTI] Sin features para usuario={usuario_id}, salto día {fecha_pred.date()}")
            continue

        for _, row in df_features.iterrows():
            categoria = canon_cat(row["categoria"])
            X = row.drop(labels=["categoria"]).to_frame().T
            X = (
                X.apply(pd.to_numeric, errors="coerce")
                  .replace([np.inf, -np.inf], np.nan)
                  .fillna(0.0)
            )
            try:
                modelo = load_model_for_categoria(usuario_id, categoria)
                
                def _audit_X(X: pd.DataFrame | np.ndarray, feature_cols: list[str] | None = None, tag: str = "X"):
                    import numpy as np, pandas as pd
                    if isinstance(X, pd.DataFrame):
                        print(f"[AUDIT][{tag}] DF shape={X.shape}")
                        print(f"[AUDIT][{tag}] cols={list(X.columns)}")
                        print(f"[AUDIT][{tag}] head(3)=\n{X.head(3)}")
                        print(f"[AUDIT][{tag}] NaN total={int(X.isna().sum().sum())}")
                        ninf = np.isinf(X.values).sum()
                        print(f"[AUDIT][{tag}] Inf total={int(ninf)}")
                        sample_cols = list(X.columns[:5])
                        print(f"[AUDIT][{tag}] describe({sample_cols})=\n{X[sample_cols].describe()}")
                    else:
                        arr = np.asarray(X)
                        print(f"[AUDIT][{tag}] ND shape={arr.shape}")
                        print(f"[AUDIT][{tag}] NaN={int(np.isnan(arr).sum())} Inf={int(np.isinf(arr).sum())}")
                        if feature_cols:
                            print(f"[AUDIT][{tag}] feature_cols(len={len(feature_cols)}): {feature_cols[:10]}...")

                feature_cols = getattr(modelo, "feature_names_in_", None)
                if feature_cols is not None:
                    X = X.reindex(columns=list(feature_cols), fill_value=0.0)
                _audit_X(X, feature_cols, tag=f"{fecha_pred.date()}_X") # <--- CAMBIO de tag
                
                pred = modelo.predict(X)
                yhat_raw = float(pred[0]) if isinstance(pred, (list, tuple, np.ndarray)) else float(pred)
                yhat_base = float(clamp_and_round(max(yhat_raw, 0.0), rnd=2))
                if CONTEXTO_DISPONIBLE and yhat_base > 0:
                    try:
                        dia_semana = fecha_pred.weekday()
                        yhat_ajustada = ajustar_prediccion_con_contexto(
                            prediccion_base=yhat_base,
                            dia_semana=dia_semana,
                            usuario_id=usuario_id,
                            motivo_esperado=None
                        )
                        
                        if abs(yhat_ajustada - yhat_base) > 1.0:  # Solo log si hay cambio significativo
                            print(f"[CONTEXTO] {categoria}: {yhat_base:.0f} → {yhat_ajustada:.0f} min")
                        
                        yhat = yhat_ajustada
                    except Exception as e:
                        print(f"[CONTEXTO][ERROR] {categoria}: {e}")
                        yhat = yhat_base
                else:
                    yhat = yhat_base
            except Exception as e:
                print(f"[ERROR][MULTI] {categoria}: {e}")
                continue

            all_preds.append({
                "usuario_id": usuario_id,
                "fecha_pred": fecha_pred.date().isoformat(),
                "horizonte": f"T+{h}",
                "categoria": categoria,
                "yhat_minutos": yhat, 
                "modelo": modelo.__class__.__name__,
            })

    if all_preds:
        df_out = pd.DataFrame(all_preds)
        guardar_predicciones(df_out, usuario_id=usuario_id, tipo="multi") 
        return df_out
    else:
        print(f"[ML][MULTI] No se generaron predicciones para usuario={usuario_id}")
        return pd.DataFrame()

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
    p_multi = sub.add_parser("multi")
    p_multi.add_argument("--usuario", type=int, required=True)
    p_multi.add_argument("--fecha", type=str, default=None)
    p_multi.add_argument("--save-csv", action="store_true")

    args = parser.parse_args()

    if args.cmd == "train":
        print(f"[CMD] Entrenamiento por categoría para usuario {args.usuario}")
        train_por_categoria(args.usuario, hist_days=args.hist)
        print("[DONE] Entrenamiento por categoría completado.")

    elif args.cmd == "predict":
        f = date.fromisoformat(args.fecha) if args.fecha else None
        res = predict(args.usuario, fecha=f, save_csv=args.save_csv)
        print(json.dumps(res, ensure_ascii=False, indent=2))

    elif args.cmd == "train_cat":
        print(f"[CMD] Entrenamiento por categoría para usuario {args.usuario}")
        train_por_categoria(args.usuario, hist_days=args.hist)
        print("[DONE] Entrenamiento por categoría completado.")
    elif args.cmd == "multi":
        f = date.fromisoformat(args.fecha) if args.fecha else date.today()
        df = predict_multi_horizon(args.usuario, fecha_base=f)
        if df is None or getattr(df, "empty", False) or len(df) == 0:
            print("[WARN][MULTI] No se generaron predicciones (preds vacío).")
            sys.exit(1)
        print(json.dumps(df.to_dict(orient="records"), ensure_ascii=False, indent=2)) # <--- CAMBIO


SELECTOR_FILE = Path("ml/artifacts/model_selector.json")

if SELECTOR_FILE.exists():
    with open(SELECTOR_FILE, "r") as f:
        MODEL_SELECTOR = json.load(f)
else:
    MODEL_SELECTOR = {}

def get_model_for_categoria(usuario_id: int, categoria: str):
    """
    Carga modelo POR USUARIO.
    Busca en: ml/artifacts/usuario_X/<categoria>/rf_<categoria>.joblib
    """
    categoria_norm = categoria.lower().replace(" ", "_")
    base_dir = Path("ml/artifacts") / f"usuario_{usuario_id}" / categoria_norm
    
    if base_dir.exists() and base_dir.is_dir():
        for file in base_dir.glob(f"rf_{categoria_norm}.joblib"):
            try:
                print(f"[MODEL][user={usuario_id}][{categoria}] Cargando desde {file}")
                return joblib.load(file)
            except Exception as e:
                print(f"[MODEL][ERR] No se pudo cargar {file}: {e}")

    # Fallback a modelo global (solo para migración)
    global_path = Path("ml/artifacts") / categoria_norm / f"rf_{categoria_norm}.joblib"
    if global_path.exists():
        print(f"[MODEL][{categoria}] ⚠️ Usando modelo GLOBAL (migrar a por usuario)")
        return joblib.load(global_path)

    print(f"[MODEL][user={usuario_id}][{categoria}] Usando BaselineHybrid (fallback)")
    return BaselineHybrid()

def predict_categoria(usuario_id: int, categoria: str, features, df_hist=None) -> float:
    import numpy as np
    import pandas as pd

    modelo = get_model_for_categoria(usuario_id, categoria)

    if isinstance(features, (float, int, np.floating)):
        X = np.array([[float(features)]])
    elif isinstance(features, dict):
        if hasattr(modelo, "feature_names_in_"):
            cols = list(modelo.feature_names_in_)
            X = pd.DataFrame([{k: features.get(k, 0.0) for k in cols}])[cols].astype(float)
        else:
            X = np.array([list(features.values())], dtype=float)
    elif isinstance(features, pd.DataFrame):
        X = features
        if hasattr(modelo, "feature_names_in_"):
            X = X.reindex(columns=list(modelo.feature_names_in_), fill_value=0.0).astype(float)
    elif isinstance(features, pd.Series):
        X = pd.DataFrame([features.values], columns=list(features.index)).astype(float)
        if hasattr(modelo, "feature_names_in_"):
            X = X.reindex(columns=list(modelo.feature_names_in_), fill_value=0.0)
    else:
        X = np.array([[0.0]], dtype=float)

    if isinstance(modelo, BaselineHybrid):
        if df_hist is not None and len(df_hist) > 0:
            serie = pd.Series(df_hist).astype(float).tail(7)
            bh = BaselineHybrid().fit(serie)
            pred = bh.predict()
            print(f"[BASELINE] {categoria}: media={bh.mean_7d:.2f}, trend={bh.trend:.2f}, pred={pred:.2f}")
            return float(pred)
        else:
            print(f"[WARN] Sin histórico válido para {categoria}, devolviendo 0.0")
            return 0.0
        
    yhat = modelo.predict(X)

    if isinstance(yhat, (list, np.ndarray, pd.Series)) and len(yhat) > 1:
        return np.array(yhat, dtype=float)

    return float(yhat[0]) if hasattr(yhat, "__len__") else float(yhat)

def build_model_selector(usuario_id: int):
    """
    Construye model_selector.json POR USUARIO
    Escanea ml/artifacts/usuario_X/ y mapea categorías a sus modelos
    """
    base_dir = ARTIF_DIR / f"usuario_{usuario_id}"
    
    if not base_dir.exists():
        print(f"[WARN] No existe directorio de artefactos para usuario {usuario_id}")
        return
    
    selector = {}
    
    for cat_dir in base_dir.iterdir():
        if cat_dir.is_dir():
            categoria = cat_dir.name
            for model_file in cat_dir.glob("rf_*.joblib"):
                selector[categoria] = str(model_file.relative_to(ARTIF_DIR))
                break
    
    selector_path = base_dir / "model_selector.json"
    with open(selector_path, "w") as f:
        json.dump(selector, f, indent=2)
    
    print(f"[ML-005] model_selector.json creado para usuario {usuario_id}: {len(selector)} categorías")
    return selector

if __name__ == "__main__":
    main()