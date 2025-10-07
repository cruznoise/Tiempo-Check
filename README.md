#  TiempoCheck — “Tu asistente de hábitos digitales inteligentes”

**Versión actual:** `v3.1-stable`  
**Fecha de lanzamiento:** 2025-10-07  
**Autor:** Luis Ángel Cruz Tenorio (`@cruznoise`)  en colaboracion con Ana Maria Ambriz Gonzalez
**Licencia:** MIT  
**Stack:** Python · Flask · MySQL · APScheduler · scikit-learn · Chart.js

---

##  Descripción general

**TiempoCheck** es un asistente de productividad que analiza tus hábitos digitales y genera **recomendaciones automáticas** basadas en tus patrones de uso.  
El sistema monitorea tus actividades por categoría (Trabajo, Ocio, Estudio, etc.), genera **features horarios y diarios**, y usa modelos de **Machine Learning** para **predecir y sugerir metas personalizadas**.

---

##  Novedades en `v3.1-stable`

- **Selector automático de modelo por categoría** (`ml/artifacts/model_selector.json`).
- **Entrenamiento modular**: cada categoría entrena su propio modelo RF (`train_por_categoria()`).
- **Fallback inteligente con `BaselineHybrid`** cuando no hay modelo entrenado.
- **Predicciones diarias limpias y reproducibles**, servidas por el endpoint `/api/ml/predict`.
- **Interfaz mejorada**: botón *“Predicción de mañana (por categoría)”* en el Dashboard.
- **Nuevo `.gitignore`** optimizado y estructura ML consolidada (`ml/models/`, `ml/scripts/`, `ml/artifacts/`).

---

##  Arquitectura general

```bash
TiempoCheck/
├── app/                     # Backend Flask (rutas, controladores, jobs APScheduler)
│   ├── routes/
│   ├── schedule/
│   ├── services/
│   ├── static/
│   └── templates/
│
├── ml/                      # Módulo de Machine Learning
│   ├── models/              # Modelos BaselineHybrid y RandomForest
│   ├── scripts/             # Scripts auxiliares de mantenimiento y validación
│   ├── artifacts/           # Artefactos entrenados y selector de modelos
│   ├── preds/               # Predicciones generadas por usuario/fecha
│   ├── data.py              # Carga de features
│   ├── pipeline.py          # Entrenamiento / predicción principal
│   └── utils.py             # Funciones auxiliares (canon_cat, paths, etc.)
│
├── docs/                    # Documentación y reportes técnicos
├── backup_tiempocheck.sql   # Dump SQL de respaldo (estructura DB)
├── CHANGELOG_v3.1-stable.md # Registro de cambios actual
└── README.md
```

---

##  Instalación y ejecución

```bash
# 1. Clonar el repositorio
git clone https://github.com/cruznoise/Tiempo-Check.git
cd Tiempo-Check

# 2. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate   # (Linux/Mac)
venv\Scripts\activate    # (Windows)

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar base de datos MySQL
# Edita config.py (o usa config.example.py)
# DB: tiempocheck_db

# 5. Ejecutar el servidor Flask
python3 -m app.app
```

---

## Entrenamiento y predicción ML

```bash
# Entrenar modelos por categoría
python3 -m ml.pipeline train --usuario 1

# Generar selector de modelo
python3 -m ml.scripts.build_model_selector

# Generar predicción para hoy
python3 -m ml.pipeline predict --usuario 1
```

---

##  Resultados

Los artefactos y resultados se guardan automáticamente en:
```
ml/artifacts/      → modelos y métricas entrenadas
ml/preds/<id>/     → predicciones diarias
```

---

##  Roadmap de versiones

| Versión | Estado | Enfoque principal |
|----------|---------|------------------|
| **v3.0** |  Cerrada | Baseline reproducible (RandomForest + BaselineHybrid) |
| **v3.1** |  Estable | Selector automático y recomendaciones simples |
| **v3.2** |  En desarrollo | Predicciones extendidas (T+1..T+3) + UI de adopción |
| **v3.3** |  Planeada | Coach inteligente con metas dinámicas |

---

##  Entorno recomendado
- **SO:** Ubuntu 22.04 (WSL2) o macOS  
- **Python:** 3.10+  
- **Base de datos:** MySQL 8.0  
- **Librerías clave:** Flask, SQLAlchemy, APScheduler, pandas, scikit-learn

---

##  Autoria
**Autor principal**
-Luis Ángel Cruz Tenorio — Estudiante de Ingeniería en Comunicaciones y Electrónica · IPN ESIME Zacatenco  
GitHub: [@cruznoise](https://github.com/cruznoise)  
Desarrollo backend · Arquitectura ML · Integración de datos

- Ana Maria Ambriz Gonzalez — Estudiante de Ingeniería en Comunicaciones y Electrónica · IPN ESIME Zacatenco
  Diseño de interfaz · UX/UI · Mejoras visuales y de experiencia de usuario
