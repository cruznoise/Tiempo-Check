# TiempoCheck — V3.0 (ML reproducible)

> **Objetivo:** generar predicciones diarias por categoría (T+1) comparadas contra baselines simples y un modelo base (RandomForest), con artefactos y métricas versionados en `ml/`, **sin** modificar el esquema de BD. Exponer un endpoint de **solo lectura** para que la UI muestre resultados.

---

## 1) Alcance de V3.0
- Predicciones **por categoría** a partir de `features_categoria_diaria` (solo lectura).
- Baselines: **Naive-1** y **Medias móviles** (MA-3/5/7).
- Modelo base: **RandomForestRegressor** con **lags** y **señales de calendario**.
- Métricas: **MAE** y **MAPE** por categoría y modelo.
- Artefactos versionados: CSVs en `ml/metrics/`, modelos `.joblib` en `ml/models/`.
- Endpoint **`/api/ml/predict`** (solo lectura) que devuelve el último archivo de predicciones T+1.
- **Reentrenamiento semanal** con APScheduler (configurable).
- **Sin cambios** de esquema en BD; no se escribe a BD desde ML.

---

## 2) Estructura de carpetas (ML)
ml/
baseline/
config.py # construye engine desde variables de entorno
loader.py # carga serie diaria por categoría
train_baseline.py # calcula Naive y MA(3/5/7) y guarda métricas
features/
ts_features.py # lags, medias móviles, calendario (one-hots del DOW)
models/
train_rf.py # RandomForest con TimeSeriesSplit y artefactos
metrics/ # CSVs de métricas (baselines, RF CV, etc.)
preds/ # CSVs de predicciones T+1..T+3 (opcional en 3.0)


> Nota: `ml/preds/` queda creado para 3.2; en 3.0 puedes dejar **T+1** dentro del CSV de RF (columna `yhat_next_day`) o generar un CSV de predicciones minimalista si prefieres.

---

## 3) Requisitos y entorno
- Python 3.9+ (mantener compatibilidad con tu entorno de Flask).
- Paquetes: `pandas`, `numpy`, `scikit-learn`, `SQLAlchemy`, `pymysql`, `joblib`.
- Base de datos MySQL/MariaDB con **feature store** ya operativo.
- Semillas fijas y ejecución determinista cuando sea posible.

### Variables de entorno (evitar credenciales en código)

export TC_DB_USER="root"
export TC_DB_PASS="root"
export TC_DB_HOST="localhost"
export TC_DB_NAME="tiempocheck"


---

## 4) Datos de entrada
Fuente única de verdad: tabla `features_categoria_diaria` con columnas al menos:
- `usuario_id`, `fecha`, `categoria`, `minutos`

> La calidad del dataset se monitorea con V2.5 (mini). Para V3.0 se asume que `features_*` están actualizadas y consistentes.

---

## 5) Baselines (Naive y MA)
Correr los baselines para tener referencia inmediata:

git checkout -b feat/v3.0-ml-baseline
python -m ml.baseline.train_baseline
# Salida -> ml/metrics/baseline_YYYY-MM-DD.csv


---
## 6) Modelo base (RandomForest con lags)

Entrenar RandomForest con lags y señales de calendario, validado con TimeSeriesSplit:
python -m ml.models.train_rf
# Salida ->
# - ml/metrics/rf_cv_YYYY-MM-DD.csv (métricas por categoría y CV)
# - ml/models/rf_usuario<id>_<categoria>.joblib (artefactos)

## 7) Endpoint de solo lectura /api/ml/predict
Idea

Exponer el último resultado de predicciones (T+1) sin tocar BD. Puedes:

Leer ml/preds/preds_*.csv y mapear a {categoria, yhat_next_day, modelo} (si ya generas predicciones dedicadas).

Fallback (V3.0): usar ml/metrics/rf_cv_*.csv y su yhat_next_day.