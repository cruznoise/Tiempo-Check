from ml.models.baseline import BaselineHybrid
from ml.models.random_forest import RandomForestWrapper

import joblib
import json
from pathlib import Path

ARTIFACTS_DIR = Path("ml/artifacts")
MODELOS_JSON = ARTIFACTS_DIR / "model_selector.json"

def load_model_for_categoria(usuario_id: int, categoria: str):
    """Carga el modelo correspondiente a la categoría POR USUARIO"""
    if not MODELOS_JSON.exists():
        raise FileNotFoundError(f"No se encontró {MODELOS_JSON}")
    
    # Buscar model_selector del usuario
    user_selector = ARTIFACTS_DIR / f"usuario_{usuario_id}" / "model_selector.json"
    
    if user_selector.exists():
        modelos = json.loads(user_selector.read_text())
    elif MODELOS_JSON.exists():
        # Fallback a global (para migración)
        modelos = json.loads(MODELOS_JSON.read_text())
        print(f"[WARN] Usando model_selector global para usuario {usuario_id}")
    else:
        modelos = {}
    
    entry = modelos.get(categoria)
    if entry:
        modelo_path = ARTIFACTS_DIR / f"usuario_{usuario_id}" / entry
        if modelo_path.exists():
            return joblib.load(modelo_path)

    # Buscar en directorio del usuario
    cat_path = ARTIFACTS_DIR / f"usuario_{usuario_id}" / categoria.lower().replace(" ", "_")
    rf_path = cat_path / f"rf_{categoria.lower().replace(' ', '_')}.joblib"
    if rf_path.exists():
        return joblib.load(rf_path)

    print(f"[WARN][MODEL] No se encontró modelo para usuario {usuario_id}, {categoria}, usando BaselineHybrid()")
    return BaselineHybrid()