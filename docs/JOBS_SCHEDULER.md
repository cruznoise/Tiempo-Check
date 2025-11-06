# 📅 Jobs del Scheduler - TiempoCheck

## Jobs Activos (Ejecutados Automáticamente)

### Por Usuario (9 jobs × 9 usuarios = 54 jobs)

| Job | Horario | Frecuencia | Descripción |
|-----|---------|------------|-------------|
| `job_agg_close_day` | 00:05 | Diario | Cierre de día, agrega estadísticas |
| `job_features_diarias` | 00:30 | Diario | Calcula features ML del día |
| `job_ml_predict_multi` | 01:00 | Diario | Genera predicciones multi-horizonte |
| `job_coach_alertas` | 01:30 | Diario | Genera alertas del coach |
| `job_ml_eval_daily` | 02:00 | Diario | Evalúa precisión del modelo |
| `job_detectar_anomalias` | 02:30 | Diario | Detecta días atípicos |
| `job_ml_train_daily` | 02:00 Dom | Semanal | Re-entrena modelo ML |
| `job_rachas` | 23:55 | Diario | Calcula rachas de cumplimiento |

### Globales (1 job)

| Job | Horario | Frecuencia | Descripción |
|-----|---------|------------|-------------|
| `job_ml_eval_weekly` | 03:00 Dom | Semanal | Resumen semanal de precisión |

**Total: 55 jobs activos**

---

## Jobs Disponibles (No en Scheduler)

Estos jobs existen pero no se ejecutan automáticamente. Se pueden usar manualmente:

| Job | Archivo | Uso Manual |
|-----|---------|-----------|
| `job_catchup` | features_jobs.py | `python scripts/run_jobs_manually.py features --catchup` |
| `job_ml_catchup` | ml_jobs.py | Sincronizar predicciones históricas |
| `job_agg_catchup` | agg_jobs.py | Recalcular agregaciones históricas |

---

## Jobs Obsoletos (Para Eliminar)

| Job | Archivo | Razón |
|-----|---------|-------|
| `job_agg_short` | agg_jobs.py | No se usa, redundante |
| `job_features_horarias` | features_jobs.py | Ya incluido en job_features_diarias |

---

## Próximas Mejoras

- [ ] Job de limpieza de datos antiguos (>6 meses)
- [ ] Job de backup de BD
- [ ] Job de notificaciones push (futuro)
```

---

## 🎯 Backend - Lo que Falta

Basado en la auditoría, este es el estado real:

### ✅ **Completado (90%)**
- ✅ Todos los controladores registrados
- ✅ Modelos de BD completos (14 modelos)
- ✅ 11 jobs funcionando
- ✅ Sistema de anomalías implementado
- ✅ Código limpio sin basura

### 🔨 **Pendiente (10%)**

1. **Agregar job de anomalías** (5 min) ← HACER YA
2. **Revisar job_coach_autometas** (5 min)
3. **Integrar contexto con ML** (1 hora) ← LO MÁS IMPORTANTE
4. **Eliminar 2-3 jobs obsoletos** (5 min)
5. **Optimizar queries BD** (30 min)

---

## 💡 Recomendación

**Orden de ejecución:**
```
1. Agregar job_detectar_anomalias al scheduler (5 min)
2. Revisar job_coach_autometas (decidir) (5 min)
3. Integrar contexto con ML (1 hora) ← FEATURE DIFERENCIADOR
4. Crear documento RESUMEN_FINAL.md (30 min)
5. Testing completo (1 hora)
