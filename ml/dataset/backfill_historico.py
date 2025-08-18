# ml/dataset/backfill_historico.py
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent / "processed"
USUARIO_ID = 1  # cambia si aplica

def _read_any(p: Path) -> pd.DataFrame:
    return pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_csv(p)

def _normalize(df: pd.DataFrame, has_hour: bool) -> pd.DataFrame:
    df = df.copy()
    # fecha -> ISO string YYYY-MM-DD
    if "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.date.astype("string")
    # hora -> int [0..23] si aplica
    if has_hour:
        if "hora" not in df.columns:
            df["hora"] = 0
        df["hora"] = pd.to_numeric(df["hora"], errors="coerce").fillna(0).astype(int)
    # tiempos / usuario / categoria
    if "tiempo_segundos" in df.columns:
        df["tiempo_segundos"] = pd.to_numeric(df["tiempo_segundos"], errors="coerce").fillna(0).astype(int)
    if "usuario_id" in df.columns:
        df["usuario_id"] = pd.to_numeric(df["usuario_id"], errors="coerce").astype("Int64")
    if "categoria" in df.columns:
        df["categoria"] = df["categoria"].astype("string")
    if "schema_ver" in df.columns:
        df["schema_ver"] = df["schema_ver"].astype("string")
    if "generated_at" in df.columns:
        df["generated_at"] = df["generated_at"].astype("string")
    return df

def _stitch(prefix: str, keys: list, has_hour: bool):
    files = sorted(BASE.glob(f"{prefix}_*_usuario_{USUARIO_ID}.parquet")) \
          + sorted(BASE.glob(f"{prefix}_*_usuario_{USUARIO_ID}.csv"))
    if not files:
        print(f"[WARN] No hay diarios para {prefix}")
        return
    dfs = [ _read_any(p) for p in files ]
    df = pd.concat(dfs, ignore_index=True)
    df = _normalize(df, has_hour=has_hour)
    df = df.drop_duplicates(subset=keys, keep="last")

    # Orden humano
    order = ["fecha"] + (["hora"] if has_hour else []) + ["categoria"]
    order = [c for c in order if c in df.columns]
    if order:
        df = df.sort_values(order)

    out_parq = BASE / f"historico_{prefix}_usuario_{USUARIO_ID}.parquet"
    df.to_parquet(out_parq, index=False)
    out_csv = out_parq.with_suffix(".csv")
    df.to_csv(out_csv, index=False)
    print(f"[OK] {prefix}: {out_parq.name} y {out_csv.name} ({len(df)} filas)")

if __name__ == "__main__":
    _stitch("features_diarias",  ["usuario_id","fecha","categoria"], has_hour=False)
    _stitch("features_horarias", ["usuario_id","fecha","hora","categoria"], has_hour=True)
