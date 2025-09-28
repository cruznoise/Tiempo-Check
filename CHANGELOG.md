## [3.0.0] - 2025-09-27
### Added
- Pipeline ML reproducible (RandomForest + baseline híbrido).
- Artefactos versionados en `ml/artifacts/`.
- Métricas e hiperparámetros en JSON (`ml/metrics/`).
- Endpoint `/api/ml/predict` (solo lectura).
- Jobs APScheduler:
  - Entrenamiento semanal.
  - Predicción diaria.
  - Catchup (rellena gaps).
  - Rachas automáticas (metas y límites).
- Validación de duplicados en tablas de features.

### Changed
- Consola más limpia: logs de features ahora muestran solo resúmenes.
- `actualizar_rachas` movido a `services/rachas_service.py`.

### Fixed
- Bug de imports circulares en utils/rachas.
- Error `Unread result found` en cálculo de rachas.
