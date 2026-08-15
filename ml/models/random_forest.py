import joblib
from pathlib import Path
from ml.utils_ml import canon_cat_filename, ensure_dir 

ARTIFACTS_DIR = Path("ml/artifacts")

class RandomForestWrapper:
    def __init__(self, categoria):
        self.categoria = categoria
        self.model = None

    @classmethod
    def load(cls, categoria: str):
        """
        Carga el modelo RandomForest entrenado para una categoría.
        Corrige ML-003: usa nombre canonizado sin espacios.
        """
        cat_name = canon_cat_filename(categoria)
        path = ARTIFACTS_DIR / cat_name / f"rf_{cat_name}.joblib"
        if not path.exists():
            raise FileNotFoundError(f"No existe modelo RF para {categoria}: {path}")
        wrapper = cls(categoria)
        wrapper.model = joblib.load(path)
        return wrapper

    @staticmethod
    def save(model, categoria: str):
        """
        Guarda el modelo RandomForest en la carpeta de artefactos.
        Corrige ML-003: crea subcarpeta por categoría y usa nombre limpio.
        """
        cat_name = canon_cat_filename(categoria)
        outdir = ARTIFACTS_DIR / cat_name
        ensure_dir(outdir)
        path = outdir / f"rf_{cat_name}.joblib"
        joblib.dump(model, path)
        print(f"[RF][SAVE] {path}")
        return path

    def predict(self, features):
        """
        Realiza una predicción con el modelo cargado.
        """
        if self.model is None:
            raise ValueError("Modelo RF no cargado")
        return float(self.model.predict([features])[0])
