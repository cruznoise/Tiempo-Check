from pathlib import Path
from datetime import datetime
import hashlib, json, re
import pandas as pd
import numpy as np
from sqlalchemy import text
from flask import current_app
from app.extensions import db
from ml.features import build_features_for_day
from ml.pipeline import get_model_for_categoria

BASE = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE / "dataset"
RAW_DIR = DATASET_DIR / "raw"
PROCESSED_DIR = DATASET_DIR / "processed"
LOGS_DIR = PROCESSED_DIR / "logs"
SCHEMA_DIR = BASE / "schema"

DOM_RE = re.compile(r'^(localhost|(\w[\w-]{0,61}\.)+[A-Za-z]{2,})$')

def ensure_dirs():
    for d in [RAW_DIR, PROCESSED_DIR, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def todaystamp():
    return datetime.now().strftime("%Y%m%d")

def now_iso():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

def log_line(msg: str):
    ensure_dirs()
    p = LOGS_DIR / f"pipeline_{todaystamp()}.log"
    p.write_text((p.read_text() if p.exists() else "") + f"[{now_iso()}] {msg}\n", encoding="utf-8")

def write_meta(df, tabla: str, schema_ver: str):
    ensure_dirs()
    csv_bytes = df.to_csv(index=False).encode()
    meta = {
        "tabla": tabla,
        "schema_ver": schema_ver,
        "generated_at": now_iso(),
        "rowcount": int(len(df)),
        "sha256": hashlib.sha256(csv_bytes).hexdigest()
    }
    (LOGS_DIR / f"meta_{tabla}_{todaystamp()}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")



def _audit_df_features(df: pd.DataFrame, tag: str = "base"):
    print(f"\n[AUDIT][{tag}] shape={df.shape}")
    print(f"[AUDIT][{tag}] columnas={list(df.columns)}")
    print(f"[AUDIT][{tag}] head(3)=\n{df.head(3)}")
    print(f"[AUDIT][{tag}] dtypes=\n{df.dtypes}")
    na = df.isna().sum()
    bad = na[na > 0]
    if not bad.empty:
        print(f"[AUDIT][{tag}] NaN por columna:\n{bad.sort_values(ascending=False)}")

def _audit_X(X: pd.DataFrame | np.ndarray, feature_cols: list[str] | None = None, tag: str = "X"):
    import numpy as np, pandas as pd
    if isinstance(X, pd.DataFrame):
        print(f"\n[AUDIT][{tag}] DF shape={X.shape}")
        print(f"[AUDIT][{tag}] cols={list(X.columns)}")
        print(f"[AUDIT][{tag}] head(3)=\n{X.head(3)}")

def trace_one_pred(app, usuario_id: int, fecha_str: str, categoria: str):
    from datetime import date
    import pandas as pd
    from pathlib import Path
    from flask import current_app

    fecha_base = pd.to_datetime(fecha_str)

    df_features = build_features_for_day(usuario_id, fecha_base)
    if df_features.empty:
        print(f"[TRACE] Sin features para {fecha_str}.")
        return

    row = df_features[df_features["categoria"] == categoria].copy()
    if row.empty:
        print(f"[TRACE] No hay fila de features para la categoría '{categoria}' en {fecha_str}.")
        return

    X = row.drop(columns=["categoria"])
    print(f"[AUDIT][{fecha_str}_{categoria}] X columns = {list(X.columns)}")

    modelo = get_model_for_categoria(categoria)
    if hasattr(modelo, "feature_names_in_"):
        X = X.reindex(columns=list(modelo.feature_names_in_), fill_value=0.0).astype(float)

    pred = modelo.predict(X)
    yhat = float(pred[0]) if hasattr(pred, "__len__") else float(pred)
    print(f"[TRACE][{fecha_str}][{categoria}] yhat={yhat:.2f}")

    outdir = Path(current_app.root_path).parent / "ml" / "debug_traces"
    outdir.mkdir(parents=True, exist_ok=True)
    X.to_csv(outdir / f"X_{fecha_str}_{categoria}.csv", index=False)

    return yhat