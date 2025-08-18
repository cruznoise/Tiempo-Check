
import sys
import os
import json
from datetime import datetime, date
import argparse
import zoneinfo
import re
import pandas as pd

# Permite imports relativos si se ejecuta como módulo
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

RAW_DIR = os.path.join(os.path.dirname(__file__), 'raw')
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), 'processed')
LOG_DIR = os.path.join(PROCESSED_DIR, 'logs')

# ===== Config: CSV histórico =====
HIST_WRITE_CSV = True           # Pon en False si no quieres CSV histórico
HIST_CSV_COMPRESS = None     # "gzip" -> .csv.gz ; None -> .csv plano

# -------- Config / Reglas
MAP_CATEGORIAS = {
    'rrss': 'Redes Sociales',
    'social': 'Redes Sociales',
    'redes': 'Redes Sociales',
    'productividad': 'Productividad',
    'productiva': 'Productividad',
    'ocio': 'Ocio',
    'entretenimiento': 'Ocio',
    'comercio': 'Comercio',
}
CATEGORIA_DEFECTO = "Sin clasificar"
SCHEMA_VER = "0.6.0"
MAX_SEG_ROW = 4 * 3600       # 4 horas por registro
MAX_SEG_DIA = 24 * 3600      # 24 horas por agregado (sanity)
DOM_RE = re.compile(r'^(localhost|(\w[\w-]{0,61}\.)+[A-Za-z]{2,})$')

# -------- Utilidades
def _resolver_infile(usuario_id: int, dia: date, raw_dir: str = RAW_DIR) -> str:
    fname = f"{dia.isoformat()}_usuario_{usuario_id}.csv"
    path = os.path.join(raw_dir, fname)
    if not os.path.exists(path):
        raise FileNotFoundError(f"No existe RAW: {path}")
    return path

def _normalizar_categoria(x: str) -> str:
    if x is None or str(x).strip() == "":
        return CATEGORIA_DEFECTO
    key = str(x).strip().lower()
    return MAP_CATEGORIAS.get(key, x)

def _validar_cols(df: pd.DataFrame, cols):
    faltan = [c for c in cols if c not in df.columns]
    if faltan:
        raise ValueError(f"Columnas faltantes: {faltan}")

def _validar_unicidad(df: pd.DataFrame, subset, nombre):
    dups = df.duplicated(subset=subset, keep=False)
    if dups.any():
        raise ValueError(f"Duplicados en llave {nombre}: {subset}")

def _validar_rangos(df: pd.DataFrame, col: str, max_v: int, nombre: str):
    if (df[col] < 0).any():
        raise ValueError(f"{nombre}: tiempos negativos tras limpieza")
    if (df[col] > max_v).any():
        raise ValueError(f"{nombre}: tiempos fuera de rango (> {max_v}s)")

def _write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

# -------- Limpieza + rechazos
def _limpiar(df: pd.DataFrame):
    df = df.copy()

    # tipos base
    df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
    df["hora"] = pd.to_numeric(df["hora"], errors="coerce").fillna(0).astype(int).clip(0, 23)
    df["tiempo_segundos"] = pd.to_numeric(df["tiempo_segundos"], errors="coerce").fillna(0).astype(int)
    df["usuario_id"] = pd.to_numeric(df["usuario_id"], errors="coerce").astype("Int64")

    # normalización de dominio
    df["dominio"] = df["dominio"].astype(str).str.strip().str.lower()

    # rechazos: dominios inválidos
    mask_dom_ok = df["dominio"].fillna("").str.match(DOM_RE)
    rej_dom = df.loc[~mask_dom_ok].copy()
    rej_dom["motivo_rechazo"] = "dominio inválido"

    # rechazos: tiempos negativos
    mask_neg = df["tiempo_segundos"] < 0
    rej_neg = df.loc[mask_neg].copy()
    rej_neg["motivo_rechazo"] = "tiempo negativo"

    # dataframe limpio (sin inválidos)
    df = df.loc[mask_dom_ok & ~mask_neg].copy()

    # normalización de categorías
    df["categoria"] = df["categoria"].astype(str).apply(_normalizar_categoria)
    df.loc[df["categoria"].isna() | (df["categoria"].str.strip() == ""), "categoria"] = CATEGORIA_DEFECTO

    # cap por registro
    df["tiempo_segundos"] = df["tiempo_segundos"].clip(lower=0, upper=MAX_SEG_ROW)

    # nulos críticos fuera
    df = df.dropna(subset=["usuario_id", "fecha", "categoria"])

    # duplicados exactos fuera
    df = df.drop_duplicates()

    rechazados = pd.concat([rej_dom, rej_neg], ignore_index=True) if (len(rej_dom) or len(rej_neg)) else pd.DataFrame()
    return df, rechazados

# -------- Métricas de resumen del processed base
def _resumen_processed(df: pd.DataFrame):
    total = len(df)
    sin_clasificar = (df['categoria'] == CATEGORIA_DEFECTO).sum() if total else 0
    pct_sin_clasificar = round((sin_clasificar / total) * 100, 2) if total else 0.0
    max_tiempo = int(df['tiempo_segundos'].max()) if total else 0
    min_tiempo = int(df['tiempo_segundos'].min()) if total else 0
    status = "OK" if total > 0 else "EMPTY"
    warnings = []
    if pct_sin_clasificar > 15:
        warnings.append("Porcentaje de 'Sin clasificar' > 15%")
    if max_tiempo > 8 * 3600:
        warnings.append("Se detectaron tiempos > 8h por registro")

    return {
        "schema_ver": SCHEMA_VER,
        "filas": total,
        "porcentaje_sin_clasificar": pct_sin_clasificar,
        "min_tiempo_segundos": min_tiempo,
        "max_tiempo_segundos": max_tiempo,
        "status": status,
        "warnings": warnings,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }

# -------- Construcción de features
def _build_features(df: pd.DataFrame):
    diarias = (
        df.groupby(["usuario_id", "fecha", "categoria"], as_index=False)["tiempo_segundos"]
          .sum()
          .sort_values(["usuario_id", "fecha", "categoria"])
    )
    horarias = (
        df.groupby(["usuario_id", "fecha", "hora", "categoria"], as_index=False)["tiempo_segundos"]
          .sum()
          .sort_values(["usuario_id", "fecha", "hora", "categoria"])
    )

    now_iso = datetime.now().isoformat(timespec="seconds")
    diarias["schema_ver"] = SCHEMA_VER
    diarias["generated_at"] = now_iso
    horarias["schema_ver"] = SCHEMA_VER
    horarias["generated_at"] = now_iso
    return diarias, horarias

# -------- Persistencia (archivos del día)
def _persist_df(df: pd.DataFrame, out_base: str):
    out_parquet = os.path.join(PROCESSED_DIR, f"{out_base}.parquet")
    out_csv = os.path.join(PROCESSED_DIR, f"{out_base}.csv")
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    df.to_parquet(out_parquet, index=False)
    df.to_csv(out_csv, index=False)
    return out_parquet, out_csv

# -------- Consolidado histórico
def _align_columns(df_a: pd.DataFrame, df_b: pd.DataFrame):
    cols = sorted(set(df_a.columns) | set(df_b.columns))
    return df_a.reindex(columns=cols), df_b.reindex(columns=cols)

def _update_hist(df_new: pd.DataFrame, name: str, usuario_id: int, keys: list, processed_dir: str = PROCESSED_DIR):
    hist_path = os.path.join(processed_dir, f"historico_{name}_usuario_{usuario_id}.parquet")
    if os.path.exists(hist_path):
        df_old = pd.read_parquet(hist_path)
        df_old, df_new = _align_columns(df_old, df_new)
        df_all = pd.concat([df_old, df_new], ignore_index=True)
        # Mantener el último registro por generated_at si existe (reprocesos del mismo día)
        if "generated_at" in df_all.columns:
            df_all = (
                df_all.sort_values(["generated_at"])
                      .drop_duplicates(subset=keys, keep="last")
            )
        else:
            df_all = df_all.drop_duplicates(subset=keys, keep="last")
    else:
        df_all = df_new.copy()

    # Orden humano
    if "fecha" in df_all.columns:
        order = ["fecha"]
        if "hora" in df_all.columns:
            order.append("hora")
        order.append("categoria")
        df_all = df_all.sort_values(order)

    # Guardar Parquet
    df_all.to_parquet(hist_path, index=False)

    # CSV histórico opcional
    if HIST_WRITE_CSV:
        csv_ext = ".csv.gz" if HIST_CSV_COMPRESS == "gzip" else ".csv"
        hist_csv_path = hist_path.replace(".parquet", csv_ext)
        df_all.to_csv(
            hist_csv_path,
            index=False,
            encoding="utf-8",
            compression=(HIST_CSV_COMPRESS if HIST_CSV_COMPRESS else None)
        )

    return hist_path

# -------- Pipeline principal
def procesar_raw(
    usuario_id: int,
    dia: date,
    infile: str = None,
    raw_dir: str = RAW_DIR,
    processed_dir: str = PROCESSED_DIR,
    log_dir: str = LOG_DIR,
):
    """
    RAW -> limpieza -> processed base -> features_diarias / features_horarias
    - Se rechazan dominios inválidos y tiempos negativos (se registran en logs).
    - Se capean outliers por registro a 4h.
    - Se validan unicidades y rangos antes de persistir.
    - Se versiona con schema_ver y generated_at.
    - Se actualiza el consolidado histórico idempotente (+ CSV opcional).
    """
    if infile is None:
        infile = _resolver_infile(usuario_id, dia, raw_dir)

    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    # 1) Leer RAW y validar columnas mínimas
    df = pd.read_csv(infile)
    _validar_cols(df, ["fecha", "hora", "dominio", "categoria", "tiempo_segundos", "usuario_id"])

    # 2) Limpieza + rechazos
    df_clean, rechazados = _limpiar(df)

    # 3) Persist processed base (para auditoría y depuración)
    base_name = f"{dia.isoformat()}_usuario_{usuario_id}"
    out_parquet_base = os.path.join(processed_dir, f"{base_name}.parquet")
    df_clean.to_parquet(out_parquet_base, index=False)

    # 4) Features
    diarias, horarias = _build_features(df_clean)

    # 5) Validaciones previas de features
    _validar_cols(diarias, ["usuario_id", "fecha", "categoria", "tiempo_segundos", "schema_ver", "generated_at"])
    _validar_cols(horarias, ["usuario_id", "fecha", "hora", "categoria", "tiempo_segundos", "schema_ver", "generated_at"])
    _validar_unicidad(diarias, ["usuario_id", "fecha", "categoria"], "features_diarias")
    _validar_unicidad(horarias, ["usuario_id", "fecha", "hora", "categoria"], "features_horarias")
    _validar_rangos(diarias, "tiempo_segundos", MAX_SEG_DIA, "features_diarias")
    _validar_rangos(horarias, "tiempo_segundos", MAX_SEG_DIA, "features_horarias")

    # 6) Persistir features (csv + parquet) del día
    fd_base = f"features_diarias_{dia.isoformat()}_usuario_{usuario_id}"
    fh_base = f"features_horarias_{dia.isoformat()}_usuario_{usuario_id}"
    fd_parq, fd_csv = _persist_df(diarias, fd_base)
    fh_parq, fh_csv = _persist_df(horarias, fh_base)

    # 7) Consolidado histórico (idempotente + CSV)
    hist_d = _update_hist(
        diarias, name="features_diarias", usuario_id=usuario_id,
        keys=["usuario_id", "fecha", "categoria"], processed_dir=processed_dir
    )
    hist_h = _update_hist(
        horarias, name="features_horarias", usuario_id=usuario_id,
        keys=["usuario_id", "fecha", "hora", "categoria"], processed_dir=processed_dir
    )

    # 8) Logs (resumen + rechazos + meta)
    resumen = _resumen_processed(df_clean)
    resumen.update({
        "usuario_id": usuario_id,
        "fecha": dia.isoformat(),
        "raw_file": os.path.relpath(infile, start=os.path.dirname(__file__)),
        "processed_base": os.path.relpath(out_parquet_base, start=os.path.dirname(__file__)),
        "features_diarias": {
            "parquet": os.path.relpath(fd_parq, start=os.path.dirname(__file__)),
            "csv": os.path.relpath(fd_csv, start=os.path.dirname(__file__)),
            "filas": int(len(diarias))
        },
        "features_horarias": {
            "parquet": os.path.relpath(fh_parq, start=os.path.dirname(__file__)),
            "csv": os.path.relpath(fh_csv, start=os.path.dirname(__file__)),
            "filas": int(len(horarias))
        },
        "historico": {
            "features_diarias": os.path.relpath(hist_d, start=os.path.dirname(__file__)),
            "features_horarias": os.path.relpath(hist_h, start=os.path.dirname(__file__))
        },
        "rechazados": int(len(rechazados))
    })
    out_log = os.path.join(log_dir, f"{dia.isoformat()}_usuario_{usuario_id}.json")
    _write_json(out_log, resumen)

    if len(rechazados):
        out_rej = os.path.join(log_dir, f"rechazos_{dia.isoformat()}_usuario_{usuario_id}.csv")
        rechazados.to_csv(out_rej, index=False)

    print(f"[PROCESSED] Base: {out_parquet_base}")
    print(f"[PROCESSED] Diarias: {fd_parq} | {fd_csv}")
    print(f"[PROCESSED] Horarias: {fh_parq} | {fh_csv}")
    print(f"[HIST] Actualizado: {hist_d}")
    if HIST_WRITE_CSV:
        csv_ext = '.csv.gz' if HIST_CSV_COMPRESS == 'gzip' else '.csv'
        print(f"[HIST] CSV: {hist_d.replace('.parquet', csv_ext)}")
    print(f"[HIST] Actualizado: {hist_h}")
    if HIST_WRITE_CSV:
        csv_ext = '.csv.gz' if HIST_CSV_COMPRESS == 'gzip' else '.csv'
        print(f"[HIST] CSV: {hist_h.replace('.parquet', csv_ext)}")
    print(f"[PROCESSED] Log: {out_log}")
    if len(rechazados):
        print(f"[PROCESSED] Rechazados: {len(rechazados)} filas")

    # Para compatibilidad con llamadas previas, devolvemos el log principal.
    return out_log

# -------- CLI
def _parse_args():
    parser = argparse.ArgumentParser(description="Procesar RAW a PROCESSED (limpieza + features + validaciones + histórico + CSV)")
    parser.add_argument("--usuario", type=int, default=1, help="ID de usuario")
    parser.add_argument("--fecha", type=str, help="YYYY-MM-DD")
    parser.add_argument("--hoy-mx", action="store_true", help="Usa la fecha actual en America/Mexico_City")
    parser.add_argument("--infile", type=str, help="Ruta explícita al RAW .csv (si no, se resuelve por convención)")
    parser.add_argument("--rawdir", type=str, default=RAW_DIR, help="Directorio RAW")
    parser.add_argument("--outdir", type=str, default=PROCESSED_DIR, help="Directorio PROCESSED")
    parser.add_argument("--logdir", type=str, default=LOG_DIR, help="Directorio de logs JSON")
    return parser.parse_args()

if __name__ == "__main__":
    args = _parse_args()
    if args.hoy_mx:
        tz = zoneinfo.ZoneInfo("America/Mexico_City")
        d = datetime.now(tz).date()
    elif args.fecha:
        d = datetime.strptime(args.fecha, "%Y-%m-%d").date()
    else:
        d = date.today()

    procesar_raw(
        usuario_id=args.usuario,
        dia=d,
        infile=args.infile,
        raw_dir=args.rawdir,
        processed_dir=args.outdir,
        log_dir=args.logdir,
    )
