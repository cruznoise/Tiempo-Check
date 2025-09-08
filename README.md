# TiempoCheck v2.5 “mini” — Guardrails

## Objetivo
Esta versión consolida la salida de predicciones, añade barandales (guardrails) de magnitud, limpia categorías.

---

## Novedades clave en v2.5
- **Canonización y colapso de categorías** en `predict` (adiós duplicados “Sin categoría”, etc.).
- **Guardrails**: p95 por categoría (según día de semana) + re‑escalado si el total supera la mediana del mismo DOW; umbral mínimo (≥ 2.0 min); opción de **ocultar “Sin categoría”** con o sin redistribución.
- **Transparencia**: `meta` en el JSON (`dow`, `total_pred_raw`, `total_pred`, `med_total_dow`, `p95_aplicados`, `min_threshold`, `oculto_sin_categoria`, `redistribuido`).
- **Métricas robustas** en `train`: `smape_safe` con epsilon; promoción del modelo **solo** si RF vence a **MA7** en **MAE y RMSE**; `hist_requested`; baseline-only si días útiles < 75% de `--hist`.

---

## Requisitos
- **Usuario final**: Windows 10+ o macOS 12+. Navegador Chromium para la extensión.
- **Build**: Python 3.10+, `pip`, PyInstaller, Inno Setup (Windows) opcional.

---


## Modo Single‑User (resumen)
- **DB**: `~/.tiempocheck/tiempocheck.db` (SQLite).
- **Logs**: `~/.tiempocheck/tiempocheck.log`.
- **Puerto**: `127.0.0.1:5000`.
- **CORS**: `http://localhost:5000`, `http://127.0.0.1:5000`, `chrome-extension://*`.

Ejemplo `SingleUserConfig`:
```python
class SingleUserConfig(Config):
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DBFILE}"  # DBFILE = Path.home()/'.tiempocheck'/'tiempocheck.db'
    SCHED_SHOULD_START = True
    DEBUG = False
    CORS_ORIGINS = ["http://127.0.0.1:5000", "http://localhost:5000", "chrome-extension://*"]
```

---

## Variables de entorno (ejemplo)
```
TIEMPOCHECK_CONFIG=config.SingleUserConfig
PORT=5000
HOST=127.0.0.1
HIDE_SIN_CAT=true
REDISTRIBUIR_SIN_CAT=false
MIN_THRESHOLD_MIN=2.0
```

---

## Uso (CLI)
Entrenar:
```bash
python -m ml.pipeline train --usuario 1 --hist 60 --holdout 7
```
Predecir (mañana por defecto o fecha dada):
```bash
python -m ml.pipeline predict --usuario 1
python -m ml.pipeline predict --usuario 1 --fecha 2025-xx-xx
```

Salida ejemplo `predict`:
```json
{
  "usuario_id": 1,
  "fecha_pred": "2025-xx-xx",
  "predicciones": [
    {"categoria": "Productividad", "yhat_minutos": xx.xx},
    {"categoria": "Trabajo", "yhat_minutos": xx.xx}},
    {"categoria": "Ocio", "yhat_minutos": xx.xx}},
    {"categoria": "Estudio", "yhat_minutos": xx.xx}},
    {"categoria": "Redes Sociales", "yhat_minutos": xx.xx}},
    {"categoria": "Herramientas", "yhat_minutos": xx.xx}},
    {"categoria": "Comercio", "yhat_minutos": xx.xx}}
  ],
  "meta": {
    "dow": 1,
    "total_pred_raw": xx.xx},
    "total_pred": xx.xx},
    "med_total_dow": xx.xx},
    "p95_aplicados": {"categoria":xx.xx}},
    "min_threshold": 2.0,
    "oculto_sin_categoria": xx.xx},
    "redistribuido": false
  }
}
```

---

## Build del instalador (devs)

### PyInstaller — Windows
```bash
pyinstaller ^
  --name TiempoCheck ^
  --onefile ^
  --add-data "app/templates;app/templates" ^
  --add-data "app/static;app/static" ^
  --hidden-import "flask_cors" ^
  --hidden-import "apscheduler" ^
  app/app.py
```

### PyInstaller — macOS
```bash
pyinstaller   --name TiempoCheck   --onefile   --windowed   --add-data "app/templates:app/templates"   --add-data "app/static:app/static"   --hidden-import "flask_cors"   --hidden-import "apscheduler"   app/app.py
```

---

## QA de instalación
- Dashboard en `http://127.0.0.1:5000` tras instalar.
- APScheduler en marcha (recalcula features de ayer).
- Extensión conectada (CORS OK).
- `~/.tiempocheck/tiempocheck.db` creada/actualizada.
- Logs en `~/.tiempocheck/tiempocheck.log`.

---

## Changelog v2.5
- Canonización de categorías + colapso en salida.
- Guardrails: p95 por categoría + mediana total por DOW.
- `meta` en salida `predict`.
- Ocultar “Sin categoría” (opcional) y redistribución configurable.
- `smape_safe` y política de promoción RF vs MA7.
- CORS a localhost/127.0.0.1 y scheduler activo.

---

## Roadmap v2.5.x
- v2.5.1: constraints únicos en BD y upsert idempotente.
- v2.5.2: tabla `ml_metrics` + vista `/admin/qa_datos`.
- v3.0: baseline reproducible, reentrenos semanales, `/api/ml/predict`, Nuitka, opción de backend remoto, Instalador de programa single user en MacOS / Windows para pruebas, demos y usuarios betas.
