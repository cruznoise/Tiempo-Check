import json
import pandas as pd
from .utils import SCHEMA_DIR

def load_schema():
    with open(SCHEMA_DIR / "features_schema.json", "r", encoding="utf-8") as f:
        return json.load(f)

def require_columns(df: pd.DataFrame, cols):
    faltan = [c for c in cols if c not in df.columns]
    if faltan:
        raise ValueError(f"Faltan columnas: {faltan}")

def validar_rangos_tiempo(df: pd.DataFrame, min_v: int, max_v: int):
    if (df["tiempo_segundos"] < min_v).any():
        raise ValueError("Tiempos negativos detectados tras limpieza.")
    if (df["tiempo_segundos"] > max_v).any():
        raise ValueError(f"Tiempos fuera de rango (> {max_v}s)")

def validar_unicidad_diarias(df: pd.DataFrame):
    dups = df.duplicated(subset=["usuario_id", "fecha", "categoria"], keep=False)
    if dups.any():
        raise ValueError("Duplicados en llave diarias (usuario_id, fecha, categoria).")

def validar_unicidad_horarias(df: pd.DataFrame):
    dups = df.duplicated(subset=["usuario_id", "fecha", "hora", "categoria"], keep=False)
    if dups.any():
        raise ValueError("Duplicados en llave horarias (usuario_id, fecha, hora, categoria).")
