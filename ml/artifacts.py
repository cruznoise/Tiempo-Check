"""
Rutas de artefactos ML
"""
from pathlib import Path

# Directorio base
ML_DIR = Path(__file__).parent
ARTIFACTS_DIR = ML_DIR / 'artifacts'
PREDS_DIR = ML_DIR / 'preds'
BACKTESTING_DIR = ML_DIR / 'backtesting'

# Archivos específicos
EVAL_WEEKLY = BACKTESTING_DIR / 'eval_weekly.json'

# Crear directorios si no existen
ARTIFACTS_DIR.mkdir(exist_ok=True)
PREDS_DIR.mkdir(exist_ok=True)
BACKTESTING_DIR.mkdir(exist_ok=True)

print(f"[ARTIFACTS] Configurado: {ML_DIR}")
