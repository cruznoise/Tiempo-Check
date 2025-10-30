from pathlib import Path
import re
from datetime import date, datetime

def canon_cat(cat: str) -> str:
    if not cat:
        return "Sin categoría"
    cat = cat.strip().lower()
    cat = re.sub(r'[\s_]+', ' ', cat)
    cat = cat.replace("sin categoria", "sin categoría")
    cat = cat.title()
    return cat

def canon_cat_filename(cat: str) -> str:
    """
    Normaliza el nombre de una categoría para usarlo en archivos.
    Convierte a minúsculas, reemplaza espacios y barras por guiones bajos.
    """
    if not cat:
        return "sin_categoria"
    return cat.strip().lower().replace(" ", "_").replace("/", "_")


def ensure_dir(path: str | Path):
    """
    Crea el directorio si no existe.
    """
    Path(path).mkdir(parents=True, exist_ok=True)

def guardar_predicciones(
        df,
        fecha_base=None,
        tipo: str = "multi",
        canonical: bool = True
            
):
    """ Se guaran las predicciones en ml/preds/ con nombre preds_future_xx_xx_xx.csv"""

    if fecha_base is None:
        fecha_str = date.today().isoformat()
    elif isinstance(fecha_base, str):
        try:
            date.fromisoformat(fecha_base)  
        except ValueError as e:
            raise ValueError(f"fecha_base inválida (YYYY-MM-DD): {fecha_base}") from e
        fecha_str = fecha_base
    elif isinstance(fecha_base, datetime):
        fecha_str = fecha_base.date().isoformat()
    elif isinstance(fecha_base, date):
        fecha_str = fecha_base.isoformat()
    else:
        raise TypeError(f"Tipo no soportado para fecha_base: {type(fecha_base)}")
    
    out_dir = Path(__file__).resolve().parent / "preds"
    out_dir.mkdir(parents=True, exist_ok=True)

    if canonical:
        fname = f"preds_future_{fecha_str}.csv"
    else:
        fname = f"{fecha_str}_{tipo}.csv"

    out_path = out_dir / fname
    df.to_csv(out_path, index=False)
    print(f"[ML][SAVE] Predicciones guardadas en: {out_path.as_posix()}")
    return out_path