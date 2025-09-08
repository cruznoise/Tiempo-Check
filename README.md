#  TiempoCheck — **V2.4 (Pre‑release)**

> Preparación para IA: *feature store*, scheduler en background, panel de estado y cimientos para análisis histórico y ML.

**Estado:** Pre‑release  
**Última actualización:** 2025‑08‑18 (TZ: America/Mexico_City)

---

##  Resumen de esta pre‑release

Esta versión sienta los cimientos para el análisis avanzado y la futura integración de IA. Se introducen tablas de **agregados oficiales** (feature store), un **scheduler** robusto que calcula y persiste los agregados en segundo plano, y **endpoints de salud/QA** para observabilidad. El dashboard y los notebooks ahora consumen los datos **desde el feature store**, no desde CSV.

---

##  Bloques completados

###  Bloque 0 — *Feature store* y dataset industrializado  **(CERRADO: 2025‑08‑14)**
- Tablas de agregados: `features_horarias` y `features_diarias` como **fuente única** para dashboard, notebooks y ML.
- Pipeline con estructura **raw/processed/logs**, limpieza automática (dominios inválidos, tiempos negativos), **versionado de esquema** (`schema_ver`) y **validaciones previas** al guardar.
- Consolidación del histórico y **exportación** a `CSV.gz` (paralelo a BD).
- Notebooks parcheados para carga histórica y **modo DB por defecto** (no CSV).
- Normalización de dominios a base y “Sin categoría”.

###  Bloque 1 — Scheduler y panel de estado  **(CERRADO: 2025‑08‑14)**
- Scheduler APS con `coalesce=True`, `max_instances=1`, `replace_existing=True`, protegido contra doble arranque con `WERKZEUG_RUN_MAIN`.
- **Jobs activos**:
  - `features_horarias`: cada *N* minutos (UPSERT incremental desde `registro` con *lookback*).
  - `features_diarias`: cierre diario **00:05**.
  - `features_catchup`: *catch‑up* cada *N* horas.
- **Endpoints** integrados en el panel de administración:
  - `GET /admin/api/features_estado` — estado por usuario/día y deltas QA.
  - `GET /features_health` — salud del scheduler y últimas ejecuciones.
  - `GET /features_qa` — chequeos de consistencia entre horas↔día.
  - `POST /admin/api/features_rebuild?dia=YYYY‑MM‑DD` — reconstrucción puntual.
- Dashboard preparado para leer de `features_*` y seguir inyectando datasets vía `data-*`.
- Extensión: envío de `fecha_hora` (ISO) y persistencia en backend.

---

##  Bloques en curso / próximos

> **Leyenda:** 🟢 Listo · 🟡 En progreso · ⚪ Pendiente

- **Bloque 2 — Motor de agregados en segundo plano**: 🟡 *(planificación/afinamiento)*  
  - Endurecer *catch‑up*, ventanas de re‑cálculo y control de idempotencia.  
  - Endpoint de ejecución manual (ya existe `features_rebuild`) y CLI utilitaria.  
  - Métricas de latencia/recencia para cada job en `/features_health` (ampliación).

- **Bloque 3 — Transparencia de sugerencias**: 🟡  
  - Endpoint `/api/sugerencias_detalle` y **tooltip** explicativo en UI (cálculo, días de respaldo y nivel de confianza).

- **Bloque 4 — Servicio de alertas en background robusto**: 🟡  
  - Daemon consolidado, canalización en tiempo real (**SSE/WebSocket**).  
  - Fix del botón **“Aceptar y cerrar”** de la extensión para cierre de pestaña.

- **Bloque 5 — Evaluador offline de políticas**: ⚪  
  - Simulador con histórico, métricas y ajuste de multiplicadores/topes para metas/límites.

- **Bloque 6 — Andamiaje ML (sin entrenar aún)**: ⚪  
  - `pipeline.py`, `TimeSeriesSplit`, métricas base, baseline sin ML y *stubs* de modelos.

- **Bloque 7 — Monitoreo de calidad de datos**: ⚪  
  - Checks automáticos, vista `/admin/qa_datos`, reglas de alerta y semáforos.

---

##  Cambios técnicos relevantes (V2.4)

- **Refactor de inicialización** de DB a `app/extensions.py` (se remove `app/db.py`).  
- **Servicios** en `app/services/` (`features_engine.py`) y **jobs** en `app/schedule/`.  
- Dashboard lee **directo** desde `features_*` (uso horario/diario y categorías).  
- **Análisis por defecto: DB** (no CSV). RANGO por defecto: **`total`**.  
- Endpoints de estado/QA y reconstrucción puntual.  
- `.gitignore` actualizado para **excluir datasets/artefactos** (`ml/dataset/raw/`, `processed/`, `*.csv`, `*.parquet`, `*.csv.gz`) y `config.py`. Se incluye `config.example.py`.

---

##  Estructura relevante

```
app/
 ├─ extensions.py                 # Init de DB (SQLAlchemy)
 ├─ schedule/
 │   ├─ scheduler.py              # Setup de jobs (APScheduler)
 │   └─ features_jobs.py          # Jobs horarias/diarias/catchup
 └─ services/
     └─ features_engine.py        # Cálculo y persistencia de agregados

ml/
 ├─ dataset/                      # raw/processed, validaciones y utilidades
 ├─ modelos/                      # Andamiaje ML (baseline)
 └─ notebooks/                    # Análisis histórico (DB‑first)

tiempocheck_extension/
 └─ background.js                 # Envía fecha_hora (ISO) y eventos
```

---

##  Guía de actualización desde V2.3

1. **Pull + dependencias**
   ```bash
   git pull
   python -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Config**
   ```bash
   cp config.example.py config.py
   # Edita credenciales/DSN de MySQL y variables necesarias
   ```

3. **Arranque**
   ```bash
   python -m app.app
   # Verifica salud en: /features_health  y QA en: /features_qa
   ```

4. **Extensión Chrome**
   - Carga sin comprimir la carpeta `tiempocheck_extension/`.
   - Verifica envío de `fecha_hora` y que el backend lo persista.

5. **Datos & artefactos**
   - Los datasets locales quedan fuera del repo por `.gitignore`.
   - Export/backup/restauración siguen disponibles desde el panel (si aplica).

> **Importante:** El scheduler está protegido contra doble arranque con `WERKZEUG_RUN_MAIN`. No lances múltiples procesos del servidor en paralelo.

---

##  Endpoints de estado / operación

- `GET /admin/api/features_estado?usuario_id=...&dia=YYYY‑MM‑DD`  
- `GET /features_health`  
- `GET /features_qa`  
- `POST /admin/api/features_rebuild?dia=YYYY‑MM‑DD&usuario_id=...`

---

##  Pendientes conocidos (pre‑release)

- Consolidar el **nivel de confianza de sugerencias** por días de uso (0‑2 oculta, 3‑6 inicial, 7‑14 confiable, 14+ consolidado) y el **tooltip** de transparencia.  
- Servicio de alertas en **tiempo real** (SSE/WebSocket) y **fix** del cierre de pestaña en la extensión.

---

##  Roadmap post‑pre‑release

- Cerrar Bloque 2 y estabilizar recálculos/catch‑up.  
- Entregar Bloques 3–4 (transparencia y alertas robustas).  
- Comenzar Bloque 6 (andamiaje ML) y Bloque 7 (monitoreo de calidad).

---

##  Autor

**Luis Ángel Cruz** — ESIME Zacatenco (IPN)  
Proyecto de titulación — *TiempoCheck*  
Pre‑release V2.4 · 2025‑08‑18
