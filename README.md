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
4. **Base de datos**
   ```bash
   -- Opcional: usa tu esquema
    -- USE tiempocheck;
    
    -- ===============================
    -- FEATURE STORE (grano hora/día)
    -- ===============================
    
    CREATE TABLE IF NOT EXISTS features_uso_hora (
      usuario_id   INT            NOT NULL,
      fecha        DATE           NOT NULL,
      hora         TINYINT UNSIGNED NOT NULL,          -- 0..23
      categoria    VARCHAR(64)    NOT NULL DEFAULT 'Sin categoría',
      minutos      DECIMAL(10,2)  NOT NULL DEFAULT 0.00,
      schema_ver   TINYINT UNSIGNED NOT NULL DEFAULT 1,
      created_at   TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at   TIMESTAMP      NULL ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (usuario_id, fecha, hora, categoria),
      KEY idx_fuho_usuario_fecha (usuario_id, fecha),
      KEY idx_fuho_fecha (fecha),
      CONSTRAINT fk_fuho_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    
    CREATE TABLE IF NOT EXISTS features_horarias (
      usuario_id   INT            NOT NULL,
      fecha        DATE           NOT NULL,
      hora         TINYINT UNSIGNED NOT NULL,          -- 0..23
      minutos      DECIMAL(10,2)  NOT NULL DEFAULT 0.00,
      schema_ver   TINYINT UNSIGNED NOT NULL DEFAULT 1,
      created_at   TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at   TIMESTAMP      NULL ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (usuario_id, fecha, hora),
      KEY idx_fhor_usuario_fecha (usuario_id, fecha),
      KEY idx_fhor_fecha (fecha),
      CONSTRAINT fk_fhor_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    
    CREATE TABLE IF NOT EXISTS features_categoria_diaria (
      usuario_id   INT            NOT NULL,
      fecha        DATE           NOT NULL,
      categoria    VARCHAR(64)    NOT NULL,
      minutos      DECIMAL(10,2)  NOT NULL DEFAULT 0.00,
      schema_ver   TINYINT UNSIGNED NOT NULL DEFAULT 1,
      created_at   TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at   TIMESTAMP      NULL ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (usuario_id, fecha, categoria),
      KEY idx_fcdi_usuario_fecha (usuario_id, fecha),
      KEY idx_fcdi_fecha (fecha),
      KEY idx_fcdi_categoria (categoria),
      CONSTRAINT fk_fcdi_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    
    CREATE TABLE IF NOT EXISTS features_diarias (
      usuario_id   INT            NOT NULL,
      fecha        DATE           NOT NULL,
      minutos_total DECIMAL(10,2) NOT NULL DEFAULT 0.00,
      schema_ver   TINYINT UNSIGNED NOT NULL DEFAULT 1,
      created_at   TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at   TIMESTAMP      NULL ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (usuario_id, fecha),
      KEY idx_fdia_fecha (fecha),
      CONSTRAINT fk_fdia_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    
    -- Alias de compatibilidad si alguna lógica espera el nombre en plural:
    -- CREATE OR REPLACE VIEW features_uso_horaS AS SELECT * FROM features_uso_hora;
    
    -- ===============================
    -- AGREGADOS / KPI
    -- ===============================
    
    CREATE TABLE IF NOT EXISTS agg_estado_dia (
      usuario_id   INT           NOT NULL,
      fecha        DATE          NOT NULL,
      ok           BOOLEAN       NOT NULL DEFAULT 0,     -- coherencia entre horas vs diario
      detalles     JSON          NOT NULL,               -- [{categoria, diaria, horas_sum, delta}, ...]
      created_at   TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (usuario_id, fecha),
      KEY idx_aed_fecha (fecha),
      CONSTRAINT fk_aed_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    
    CREATE TABLE IF NOT EXISTS agg_kpi_rango (
      id           BIGINT AUTO_INCREMENT PRIMARY KEY,
      usuario_id   INT           NOT NULL,
      fecha_inicio DATE          NOT NULL,
      fecha_fin    DATE          NOT NULL,
      kpis         JSON          NOT NULL,               -- totales, promedios, % productivo vs no, etc.
      created_at   TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
      UNIQUE KEY uniq_usuario_rango (usuario_id, fecha_inicio, fecha_fin),
      KEY idx_akr_usuario (usuario_id),
      CONSTRAINT fk_akr_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    
    CREATE TABLE IF NOT EXISTS agg_ventana_categoria (
      usuario_id       INT           NOT NULL,
      categoria        VARCHAR(64)   NOT NULL,
      fecha_fin        DATE          NOT NULL,           -- fin de la ventana móvil
      ventana_dias     SMALLINT      NOT NULL,          -- 7, 14, 30, etc.
      n_dias           SMALLINT      NOT NULL,          -- días efectivamente contados
      minutos_total    DECIMAL(10,2) NOT NULL,
      minutos_promedio DECIMAL(10,2) NOT NULL,
      minutos_min      DECIMAL(10,2) NULL,
      minutos_max      DECIMAL(10,2) NULL,
      minutos_mediana  DECIMAL(10,2) NULL,
      created_at       TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (usuario_id, categoria, fecha_fin, ventana_dias),
      KEY idx_avc_usuario_categoria (usuario_id, categoria),
      CONSTRAINT fk_avc_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    
    -- ===============================
    -- VISTAS
    -- ===============================
    
    -- Estado actual por usuario/categoría (hoy)
    CREATE OR REPLACE VIEW v_estado_actual_usuario AS
    SELECT
      f.usuario_id,
      f.fecha,
      f.categoria,
      f.minutos,
      t.minutos_total_dia
    FROM features_categoria_diaria AS f
    JOIN (
      SELECT usuario_id, fecha, SUM(minutos) AS minutos_total_dia
      FROM features_categoria_diaria
      GROUP BY usuario_id, fecha
    ) AS t
      ON t.usuario_id = f.usuario_id AND t.fecha = f.fecha
    WHERE f.fecha = CURRENT_DATE();
    
    -- Resumen de ventanas 7/14/30 días por usuario y categoría
    CREATE OR REPLACE VIEW v_resumen_ventanas AS
    SELECT usuario_id, categoria, '7d' AS ventana,
           MIN(fecha) AS desde, MAX(fecha) AS hasta,
           COUNT(*) AS n_dias, SUM(minutos) AS minutos_total, AVG(minutos) AS minutos_promedio
    FROM features_categoria_diaria
    WHERE fecha >= CURRENT_DATE() - INTERVAL 7 DAY
    GROUP BY usuario_id, categoria
    UNION ALL
    SELECT usuario_id, categoria, '14d' AS ventana,
           MIN(fecha) AS desde, MAX(fecha) AS hasta,
           COUNT(*) AS n_dias, SUM(minutos) AS minutos_total, AVG(minutos) AS minutos_promedio
    FROM features_categoria_diaria
    WHERE fecha >= CURRENT_DATE() - INTERVAL 14 DAY
    GROUP BY usuario_id, categoria
    UNION ALL
    SELECT usuario_id, categoria, '30d' AS ventana,
           MIN(fecha) AS desde, MAX(fecha) AS hasta,
           COUNT(*) AS n_dias, SUM(minutos) AS minutos_total, AVG(minutos) AS minutos_promedio
    FROM features_categoria_diaria
    WHERE fecha >= CURRENT_DATE() - INTERVAL 30 DAY
    GROUP BY usuario_id, categoria;
    ```


5. **Extensión Chrome**
   - Carga sin comprimir la carpeta `tiempocheck_extension/`.
   - Verifica envío de `fecha_hora` y que el backend lo persista.

6. **Datos & artefactos**
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
