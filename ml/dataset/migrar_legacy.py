
# ml/dataset/migrar_legacy.py
from pathlib import Path
import argparse
import pandas as pd
import re

SCHEMA_VER = "0.6.0"

def _read_any(p: Path) -> pd.DataFrame:
    return pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_csv(p)

def _update_hist(df_new: pd.DataFrame, name: str, usuario_id: int, keys: list, processed_dir: Path, write_csv: bool = True):
    hist_parq = processed_dir / f"historico_{name}_usuario_{usuario_id}.parquet"
    if hist_parq.exists():
        df_old = pd.read_parquet(hist_parq)
        cols = sorted(set(df_old.columns) | set(df_new.columns))
        df_old = df_old.reindex(columns=cols)
        df_new = df_new.reindex(columns=cols)
        df_all = pd.concat([df_old, df_new], ignore_index=True)
        keep_last = "generated_at" in df_all.columns
        if keep_last:
            df_all = df_all.sort_values(["generated_at"]).drop_duplicates(subset=keys, keep="last")
        else:
            df_all = df_all.drop_duplicates(subset=keys, keep="last")
    else:
        df_all = df_new.drop_duplicates(subset=keys, keep="last")

    order = [c for c in ["fecha","hora","categoria"] if c in df_all.columns]
    if order:
        df_all = df_all.sort_values(order)

    hist_parq.parent.mkdir(parents=True, exist_ok=True)
    df_all.to_parquet(hist_parq, index=False)
    if write_csv:
        df_all.to_csv(hist_parq.with_suffix(".csv"), index=False)

    return hist_parq

def _normalize_legacy(df: pd.DataFrame, usuario_id: int) -> pd.DataFrame:
    df = df.copy()

    # Fecha/hora
    if "fecha_hora" in df.columns:
        dt = pd.to_datetime(df["fecha_hora"], errors="coerce")
        df["fecha"] = dt.dt.date.astype(str)
        df["hora"]  = dt.dt.hour
    else:
        df["fecha"] = pd.to_datetime(df.get("fecha"), errors="coerce").dt.date.astype(str)
        if "hora" in df.columns:
            h1 = pd.to_datetime(df["hora"], format="%H:%M", errors="coerce").dt.hour
            h2 = pd.to_numeric(df["hora"], errors="coerce")
            h = h1.where(h1.notna(), h2)
            df["hora"] = h.fillna(0).astype(int)
        else:
            df["hora"] = 0

    # Tiempos
    if "tiempo_segundos" in df.columns:
        df["tiempo_segundos"] = pd.to_numeric(df["tiempo_segundos"], errors="coerce").fillna(0).astype(int)
    elif "tiempo_minutos" in df.columns:
        df["tiempo_segundos"] = pd.to_numeric(df["tiempo_minutos"], errors="coerce").fillna(0).mul(60).astype(int)
    else:
        raise ValueError("El CSV legacy requiere 'tiempo_segundos' o 'tiempo_minutos'.")

    # Usuario
    if "usuario_id" in df.columns:
        df["usuario_id"] = pd.to_numeric(df["usuario_id"], errors="coerce").fillna(usuario_id).astype(int)
    else:
        df["usuario_id"] = int(usuario_id)

    # Categoría
    if "categoria" in df.columns:
        df["categoria"] = df["categoria"].astype(str)
    else:
        df["categoria"] = "Sin clasificar"

    return df

def _features_from_base(df_base: pd.DataFrame):
    df = df_base.copy()
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.date.astype(str)
    if "hora" not in df.columns:
        if "fecha_hora" in df.columns:
            df["hora"] = pd.to_datetime(df["fecha_hora"], errors="coerce").dt.hour
        else:
            df["hora"] = 0
    df["hora"] = pd.to_numeric(df["hora"], errors="coerce").fillna(0).astype(int)
    df["tiempo_segundos"] = pd.to_numeric(df["tiempo_segundos"], errors="coerce").fillna(0).astype(int)
    df["usuario_id"] = pd.to_numeric(df["usuario_id"], errors="coerce").astype(int)
    df["categoria"] = df["categoria"].astype(str)

    diarias = df.groupby(["usuario_id","fecha","categoria"], as_index=False)["tiempo_segundos"].sum()
    horarias = df.groupby(["usuario_id","fecha","hora","categoria"], as_index=False)["tiempo_segundos"].sum()

    now_iso = pd.Timestamp.utcnow().isoformat()
    diarias["schema_ver"] = "0.6.0"; diarias["generated_at"] = now_iso
    horarias["schema_ver"] = "0.6.0"; horarias["generated_at"] = now_iso

    return diarias, horarias

def main():
    ap = argparse.ArgumentParser(description="Migrar CSV legacy y backfill desde bases procesadas al histórico.")
    ap.add_argument("--usuario", type=int, default=1)
    ap.add_argument("--legacy", type=str, default="ml/dataset/dataset_usuario_1.csv", help="Ruta al CSV legacy (hasta 4 de agosto)")
    ap.add_argument("--processed-dir", type=str, default="ml/dataset/processed")
    args = ap.parse_args()

    usuario_id = args.usuario
    processed_dir = Path(args.processed_dir)

    # 1) Migrar LEGACY CSV si existe
    legacy_path = Path(args.legacy)
    if legacy_path.exists():
        print(f"[LEGACY] Leyendo {legacy_path}")
        df = pd.read_csv(legacy_path)
        df = _normalize_legacy(df, usuario_id=usuario_id)
        diarias = df.groupby(["usuario_id","fecha","categoria"], as_index=False)["tiempo_segundos"].sum()
        horarias = df.groupby(["usuario_id","fecha","hora","categoria"], as_index=False)["tiempo_segundos"].sum()
        now_iso = pd.Timestamp.utcnow().isoformat()
        diarias["schema_ver"] = "0.6.0"; diarias["generated_at"] = now_iso
        horarias["schema_ver"] = "0.6.0"; horarias["generated_at"] = now_iso

        _update_hist(diarias,  "features_diarias",  usuario_id, ["usuario_id","fecha","categoria"], processed_dir)
        _update_hist(horarias, "features_horarias", usuario_id, ["usuario_id","fecha","hora","categoria"], processed_dir)
        print(f"[LEGACY] Migración desde CSV completada (usuario={usuario_id})")
    else:
        print(f"[LEGACY] No encontrado: {legacy_path} (se omite)")

    # 2) Backfill desde bases procesadas (YYYY-MM-DD_usuario_<id>.parquet)
    #   Usamos f-string + llaves dobles en la regex para evitar .format() con {2} etc.
    patt = re.compile(rf'^\d{{4}}-\d{{2}}-\d{{2}}_usuario_{usuario_id}\.parquet$')
    base_files = [p for p in processed_dir.glob("*.parquet") if patt.match(p.name)]
    base_files.sort()
    if base_files:
        print(f"[BASE] Detectadas {len(base_files)} bases procesadas para usuario {usuario_id}")
        dfs = []
        for p in base_files:
            try:
                dfs.append(pd.read_parquet(p))
            except Exception as e:
                print("[WARN] No se pudo leer", p, "->", e)
        if dfs:
            df_base_all = pd.concat(dfs, ignore_index=True)
            diarias_b, horarias_b = _features_from_base(df_base_all)
            _update_hist(diarias_b,  "features_diarias",  usuario_id, ["usuario_id","fecha","categoria"], processed_dir)
            _update_hist(horarias_b, "features_horarias", usuario_id, ["usuario_id","fecha","hora","categoria"], processed_dir)
            print(f"[BASE] Backfill desde bases procesadas completado.")
    else:
        print("[BASE] No se encontraron bases procesadas tipo YYYY-MM-DD_usuario_<id>.parquet (se omite)")

    print("[DONE] Histórico actualizado.")

if __name__ == "__main__":
    main()
