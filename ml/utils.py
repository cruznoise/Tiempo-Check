from pathlib import Path
import re

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
