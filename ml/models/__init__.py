from ml.models.baseline import BaselineHybrid
from ml.models.random_forest import RandomForestWrapper

import joblib
import json
from pathlib import Path

ARTIFACTS_DIR = Path("ml/artifacts")
MODELOS_JSON = ARTIFACTS_DIR / "model_selector.json"

def load_model_for_categoria(categoria: str):
    """Carga el modelo correspondiente a la categoría según model_selector.json o usa fallback BaselineHybrid."""
    if not MODELOS_JSON.exists():
        raise FileNotFoundError(f"No se encontró {MODELOS_JSON}")
    modelos = json.loads(MODELOS_JSON.read_text())
    entry = modelos.get(categoria)
    if entry:
        modelo_path = ARTIFACTS_DIR / entry
        if modelo_path.exists():
            return joblib.load(modelo_path)

    cat_path = ARTIFACTS_DIR / categoria.lower().replace(" ", "_")
    rf_path = cat_path / f"rf_{categoria.lower().replace(' ', '_')}.joblib"
    if rf_path.exists():
        return joblib.load(rf_path)

    print(f"[WARN][MODEL] No se encontró modelo para {categoria}, usando BaselineHybrid()")
    return BaselineHybrid()
