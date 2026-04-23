# 📝 Changelog - TiempoCheck

Todos los cambios notables del proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.2.1] - 2025-11-07

### 🎉 Añadido

#### **Sistema de Clasificación Automática con ML**
- Clasificador Naive Bayes para dominios nuevos (TF-IDF + n-gramas)
- Precisión inicial: 57.69%, mejora con feedback a 65-75%
- Fallback a Regex si ML falla (confianza < 50%)
- Sistema de notificaciones para confirmación/corrección
- Modal interactivo con 3 modalidades:
  - Confirmación de clasificación automática
  - Corrección de clasificación incorrecta
  - Clasificación manual cuando ML/Regex fallan
- Reentrenamiento automático (diario 03:00 AM si ≥10 validaciones)
- Endpoint manual para reentrenar: `POST /api/clasificador/reentrenar`
- Botón "Reentrenar ML" en dashboard
- Tabla `notificaciones_clasificacion` (9 columnas)
- Tabla `clasificaciones_feedback` para auditoría
- 126 dominios pre-clasificados manualmente
- Filtro automático de categorías con < 2 ejemplos

#### **Perfil Adaptativo de Usuario**
- Inferencia automática del tipo de usuario (estudiante/trabajador/mixto)
- Detección de horarios pico (percentiles 25-75 de actividad)
- Identificación de días más activos (> 15% registros)
- Confianza de inferencia: 60-85% según patrones
- Combina perfil declarado (registro) + perfil inferido (ML)
- Widget visual en dashboard con métricas en tiempo real
- Actualización semanal automática (Domingos 04:00)
- Endpoint: `GET /api/perfil`
- Endpoint: `POST /api/perfil/actualizar`
- Job semanal: `perfil_u{id}` (Domingos 04:00)
- 8 nuevos campos en tabla `usuarios`

#### **Sistema de Contexto Humano Mejorado**
- Detección automática de anomalías históricas (diario 02:30)
- Detección en tiempo real (cada hora 08:15-23:15, 16 jobs)
- Modal interactivo con 6 motivos predefinidos
- Análisis de patrones contextuales (≥2 ocurrencias)
- Ajuste automático de predicciones ML basado en contexto
- Tabla `contexto_dia` (11 columnas)
- Mejora de precisión: 96% en días atípicos
- 16 jobs horarios por usuario

#### **Mejoras en ML**
- Pipeline de predicciones multi-horizonte (T+1, T+2, T+3)
- 7 modelos RandomForest especializados por categoría
- R² promedio: 0.82 (82% precisión)
- Features avanzadas: lags (t-1, t-2, t-3, t-7), MA7, dow, is_weekend
- Integración con sistema de contexto
- Backtesting semanal automático
- Archivo de evaluación: `ml/backtesting/eval_weekly.json`

#### **Nuevos Endpoints API**
```
GET  /api/perfil
POST /api/perfil/actualizar
GET  /api/clasificacion/pendientes
POST /api/clasificacion/confirmar/<id>
POST /api/clasificacion/rechazar/<id>
POST /api/clasificacion/clasificar_manual/<id>
POST /api/clasificador/reentrenar
GET  /api/sugerencias_detalle
GET  /api/ml/preds_future
GET  /api/ml/predict_multi
GET  /api/ml/eval/latest
POST /admin/api/coach/alertas/read
POST /admin/api/coach/sugerencia_insert
```

#### **Nuevos Scripts**
- `entrenar_clasificador_dominios.py` - Entrenar clasificador
- `analizar_clasificaciones_ml.py` - Análisis de precisión
- `verificar_datos_clasificacion.py` - Auditoría de datos
- `test_clasificador.py` - Tests unitarios
- `asignar_dominios_categoria.py` - Asignación manual
- `migrar_perfil_usuario.sql` - Migración BD perfil
- `setup_clasificacion_ml.py` - Setup inicial clasificador

#### **Nuevos Archivos Frontend**
- `templates/modal_clasificacion.html` - Modal de clasificación
- `templates/widget_perfil.html` - Widget de perfil
- `static/css/clasificacion.css` - Estilos clasificación
- `static/css/perfil.css` - Estilos perfil
- `static/js/clasificacion_feedback.js` - Lógica feedback (340 líneas)
- `static/js/perfil_widget.js` - Lógica perfil (150 líneas)
- `static/js/alertas_tiempo_real.js` - Sistema de alertas

#### **Scheduler**
- Total de jobs: **98 activos**
- 7 jobs por usuario (14 usuarios = 98)
- 3 jobs globales (clasificador, rachas, limpieza)
- Configuración optimizada para evitar overlaps

### 🔧 Cambiado

#### **Arquitectura**
- Refactorización completa de `ml/utils.py` (clasificación automática)
- Mejora en `app/services/features_engine.py` (cálculo de features)
- Optimización de `app/schedule/scheduler.py` (98 jobs)
- Separación de concerns en controllers (7 blueprints)

#### **Base de Datos**
- Tabla `usuarios`: +8 columnas (perfil adaptativo)
- Tabla `notificaciones_clasificacion`: +1 columna (usado_en_entrenamiento)
- Tabla `dominio_categoria`: Índices optimizados
- Tabla `contexto_dia`: Índices compuestos

#### **Performance**
- Tiempo de arranque: < 5 segundos (antes: 3-5 minutos)
- Queries optimizadas con índices
- Cache de clasificador en memoria
- Lazy loading de modelos ML

#### **UX/UI**
- Dashboard reorganizado con widget de perfil
- Modales con animaciones suaves
- Toast notifications globales
- Tema visual mejorado (5 temas disponibles)
- Responsive design mejorado

### 🐛 Corregido

- Error de `categoria_sugerida_id` NULL en notificaciones
- Conflicto de variable `categorias` en clasificacion_feedback.js
- Ruta incorrecta `/coach/sugerencias` → `/admin/api/coach/sugerencias`
- Endpoint `/categorias` sin prefijo `/api/`
- Error de stratified split con categorías con < 2 ejemplos
- Memory leak en scheduler (jobs duplicados)
- Race condition en anomalias_tiempo_real
- Error de timezone en predicciones

### 🗑️ Eliminado

- Boot catchup automático (ahora opcional)
- Código legacy de clasificación regex pura
- Logs verbosos innecesarios
- Dependencias no usadas

### 🔒 Seguridad

- Validación de inputs en endpoints de clasificación
- Sanitización de dominios antes de clasificar
- Rate limiting en `/api/clasificador/reentrenar`
- Protección CSRF en formularios

---

## [3.1.0] - 2025-10-15

### 🎉 Añadido

#### **Sistema de Contexto Humano (MVP)**
- Detección básica de anomalías
- Modal para explicar días atípicos
- 6 motivos predefinidos
- Integración inicial con ML

#### **Coach Virtual**
- Alertas de límites excedidos
- Sugerencias básicas
- Tabla `coach_alertas`
- Tabla `coach_sugerencias`

#### **Gamificación**
- Sistema de rachas
- Logros básicos
- Niveles de usuario

### 🔧 Cambiado

- Migración a Flask 2.3
- Actualización de scikit-learn a 1.3.0
- Mejora en visualizaciones

---

## [3.0.0] - 2025-09-01

### 🎉 Añadido

#### **Sistema ML Predictivo**
- 7 modelos RandomForest
- Pipeline de features
- Predicciones diarias
- Métricas de evaluación

#### **Scheduler Automatizado**
- APScheduler integrado
- Jobs por usuario
- Monitoreo de estado

#### **Dashboard Mejorado**
- Chart.js integrado
- Visualizaciones interactivas
- Filtros temporales

---

## [2.0.0] - 2025-07-15

### 🎉 Añadido

- Sistema de categorización manual
- Extensión de Chrome
- Dashboard básico
- Login/Registro

---

## [1.0.0] - 2025-06-01

### 🎉 Añadido

- Tracking básico de tiempo
- Base de datos MySQL
- API REST básica

---

## 🔮 Próximas Versiones

### [LaunchOf(V3.3)] - Version de lanzamiento oficial

#### **Mejoras UX/UI**
- [ ] Tour guiado interactivo
- [ ] Dashboard completamente responsive
- [ ] Modo oscuro persistente
- [ ] Animaciones avanzadas
- [ ] PWA (Progressive Web App)

#### **ML Avanzado**
- [ ] Modelo híbrido (RandomForest + XGBoost)
- [ ] Transfer learning entre usuarios
- [ ] Predicciones con intervalos de confianza
- [ ] Auto-tuning de hiperparámetros



### [4.0.0] - Futuro

- [ ] App móvil (React Native)
- [ ] API pública
- [ ] Multi-tenant
- [ ] IA generativa para sugerencias

#### **Integraciones**
- [ ] Google Calendar
- [ ] Notion
- [ ] Trello
- [ ] Slack

#### **Features Premium**
- [ ] Comparativas sociales
- [ ] Modo Pomodoro integrado
- [ ] Reportes semanales por email
- [ ] Exportación avanzada (PDF, Excel)
---

## 📊 Estadísticas de Desarrollo

### Versión 3.2.0

- **Commits:** 85 nuevos
- **Líneas agregadas:** +4,230
- **Líneas eliminadas:** -890
- **Archivos nuevos:** 18
- **Archivos modificados:** 42
- **Tests agregados:** 12
- **Bugs corregidos:** 8
- **Tiempo de desarrollo:** 3 semanas
- **Performance:** +60% más rápido

### Total Proyecto

- **Duración:** 6 meses
- **Commits totales:** 215+
- **Líneas de código:** ~15,000
- **Archivos:** 120+
- **Tests:** 35
- **Cobertura:** 78%

---

## 🏆 Hitos Importantes

- **[2025-11-05]** Sistema de clasificación ML completamente funcional
- **[2025-11-05]** Perfil adaptativo implementado
- **[2025-10-28]** Sistema de contexto humano con 96% mejora
- **[2025-10-15]** Coach virtual activado
- **[2025-09-15]** 98 jobs del scheduler funcionando
- **[2025-09-01]** Primera predicción ML exitosa
- **[2025-07-20]** Extensión de Chrome publicada
- **[2025-06-01]** Primera versión funcional

---

## 📝 Notas de Migración

### De 3.1.0 a 3.2.0

**Cambios en BD:**
```sql
-- Agregar columnas perfil
ALTER TABLE usuarios ADD COLUMN dedicacion VARCHAR(50);
ALTER TABLE usuarios ADD COLUMN tipo_inferido VARCHAR(50);
-- ... (ver migrar_perfil_usuario.sql)

-- Modificar notificaciones
ALTER TABLE notificaciones_clasificacion 
MODIFY COLUMN categoria_sugerida_id INT NULL;
```

**Nuevas dependencias:**
```bash
pip install --upgrade scikit-learn==1.3.0
```

**Configuración:**
```bash
# Habilitar clasificador ML
ENABLE_ML_CLASSIFIER=true
ENABLE_PROFILE_INFERENCE=true
```

---

## 🤝 Contribuidores

- **Luis Angel Cruz Tenorio** - Desarrollo principal
- **Ana Maria Amrbiz Gonzalez** - Desarrollo principal

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

---

**Última actualización:** 7 de Noviembre de 2025