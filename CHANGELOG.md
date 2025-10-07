##  Versión v3.1-stable — “Recomendaciones simples y selector de modelo por categoría”
**Fecha:** 2025-10-07  
**Estado:**  Estable  
**Tag:** `v3.1-stable`  
**Commit base:** `f78742b`

###  Novedades principales
- **Selector automático de modelo por categoría (`model_selector.json`)**  
  Implementación del proceso `build_model_selector()` que analiza métricas históricas (`backtesting_summary.json`) y selecciona automáticamente el mejor modelo entre `RandomForest` y `BaselineHybrid` para cada categoría.
- **Predicciones reproducibles y transparentes**  
  El endpoint `/api/ml/predict` ahora usa el selector actualizado y genera predicciones diarias limpias, con fallback robusto a `BaselineHybrid` cuando no hay modelo RF entrenado.
- **Entrenamiento modular (`train_por_categoria`)**  
  Nuevo flujo de entrenamiento independiente por categoría. Cada modelo RF se guarda en su carpeta bajo `ml/artifacts/<categoria>/`, con actualización automática del selector al finalizar.
- **Script de mantenimiento:**  
  `ml/scripts/build_model_selector.py` → Genera o actualiza el selector desde los resultados de backtesting.  
  `ml/scripts/test_selector.py` → Valida la integridad del selector generado.

###  Correcciones (ML-001 → ML-005)
| ID | Descripción | Estado |
|----|--------------|---------|
| **ML-001** | Error al cargar modelos RF inexistentes. |  Corregido — Fallback controlado a `BaselineHybrid`. |
| **ML-002** | Normalización inconsistente de categorías (`Sin categoría` / `SinCategoria`). |  Corregido — nueva función `canon_cat()` en `ml/utils.py`. |
| **ML-003** | Joblib no se guardaba con nombre estandarizado. |  Corregido — convención `rf_<categoria>.joblib` + `canon_cat_filename`. |
| **ML-004** | `BaselineHybrid` devolvía siempre 0.0. |  Corregido — ahora entrena con últimos 7 valores y calcula tendencia (`mean_7d`, `trend`). |
| **ML-005** | `model_selector.json` no se actualizaba automáticamente. |  Corregido — `train_por_categoria()` llama a `build_model_selector()` al cierre. |

###  Mejoras de interfaz (UI-002)
- Botón “**Predicción de mañana (por categoría)**” activo en dashboard.  
  Carga predicciones desde `/api/ml/predict` y las muestra en lista con total estimado.

###  Notas técnicas
- Consolidación de estructura `ml/` (datasets, models, scripts, artifacts).  
- Validado desde entorno **WSL2 Ubuntu 22.04 + Python 3.10**, compatible con **MacOS**.  
- Logs limpios y predicciones reproducibles (sin warnings ni fallos en jobs APScheduler).  

### Archivos relevantes
```
ml/
 ├─ models/
 │   ├─ baseline.py
 │   └─ random_forest.py
 ├─ scripts/
 │   ├─ build_model_selector.py
 │   └─ test_selector.py
 ├─ artifacts/
 │   ├─ backtesting_summary.json
 │   └─ model_selector.json
 └─ pipeline.py  ← Entrenamiento, predicción y selector integrados
```

###  Próxima versión (v3.2)
> **“Predicciones extendidas y adopción”**  
> - Servicio de inferencia offline (T+1…T+3) guardado en `ml/preds/`  
> - UI de adopción para mostrar próximos días y sugerir metas.  
> - Integración con coach para metas dinámicas.


### Autor
**Luis Angel Cruz Tenorio**
En colaboración con **Ana Maria Ambriz Gonzalez**
Proyecto de titulación - 9no semestre
Ingenieria en Comunicaciones y Electrónica
GitHub: [@cruznoise ](#)   
Fecha de actualización: Octubre 2025
