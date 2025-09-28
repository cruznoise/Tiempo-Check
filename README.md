# TiempoCheck

Plataforma de hábitos digitales y productividad con integración de extensiones de navegador, backend en Flask, base de datos MySQL y motor de Machine Learning.

---

## 🚀 Novedades v3.0 (Baseline reproducible)
- **Pipeline ML reproducible** con RandomForest y baseline híbrido.
- Artefactos versionados en `ml/artifacts/`.
- Registro de métricas + hiperparámetros en JSON (`ml/metrics/`).
- Endpoint `/api/ml/predict` estable (solo lectura).
- Jobs automáticos con APScheduler:
  - Entrenamiento semanal.
  - Predicción diaria.
  - Catchup diario (rellena días faltantes).
  - Rachas automáticas (metas y límites).
- Validación de duplicados en features (`horarias`, `diarias`, `categoria_diaria`).

---

## ⚙️ Instalación

### 🔹 Requisitos
- Python 3.10+
- MySQL 8+
- Navegador Chrome/Edge para extensión

### 🔹 Windows
```bash
git clone https://github.com/cruznoise/Tiempo-Check.git
cd Tiempo-Check
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 🔹 Mac/Linux
```bash
git clone https://github.com/cruznoise/Tiempo-Check.git
cd Tiempo-Check
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Configura las variables de entorno en `.env`:

```
DB_URL=mysql+pymysql://root:tu_password@localhost/tiempocheck_db
ENABLE_SCHEDULER=1
TZ=America/Mexico_City
```

### 🔹 Ejecutar servidor
```bash
python -m app.app
```

---

## 📊 Machine Learning
- Artefactos: `ml/artifacts/`
- Métricas: `ml/metrics/`
- Dataset procesado: `ml/dataset/`
- Entrenamiento reproducible con:
  ```bash
  python -m ml.pipeline train --usuario 1 --hist 45 --holdout 7
  ```

---

## 🗓️ Jobs Automáticos
- `job_ml_train`: semanal (domingo 00:10).
- `job_ml_predict`: diario (00:15).
- `job_ml_catchup`: diario (01:00).
- `job_rachas`: diario (23:59).
- `job_features_*` y `job_agg_*` según config.

---
