#  TiempoCheck — “Tu asistente de hábitos digitales inteligentes”

**Versión actual:** `v3.2 Changes`  
**Fecha de lanzamiento:** 2025-11-06 
**Autores:** 
Luis Ángel Cruz Tenorio (`@cruznoise`)
Ana Maria Ambriz Gonzalez
**Licencia:** MIT  
**Stack:** Python · Flask · MySQL · APScheduler · scikit-learn · Chart.js

---

##  Descripción general

**TiempoCheck** es un asistente de productividad que analiza tus hábitos digitales y genera **recomendaciones automáticas** basadas en tus patrones de uso.  
El sistema monitorea tus actividades por categoría (Trabajo, Ocio, Estudio, etc.), genera **features horarios y diarios**, y usa modelos de **Machine Learning** para **predecir y sugerir metas personalizadas**.

---

## Pruebas funcionales en `v3.2 Changes`

Durante esta versión se validaron:
- Ejecución completa de jobs automáticos y boot_catchup.
- Predicción diaria sin errores en API `/api/ml/predict`.
- Persistencia correcta de features y métricas.
- Visualización dinámica en el dashboard.
- Integración funcional con la extensión del navegador.
- Integracion de clasificación inteligente de sitios en categorias.
- Rentrenamiento de clasificación y predicciones automáticos y manuales.
- 
---

##  Arquitectura general

```bash
TiempoCheck v3.2
├── Frontend (Extension Chrome)
│   ├── content_script.js
│   ├── background.js
│   └── popup.js/html/css
│
├── Backend (Flask App)
│   ├── Controllers (rutas y lógica web)
│   ├── Models (SQLAlchemy)
│   ├── Services (lógica de negocio)
│   ├── Schedule (jobs automáticos)
│   └── Coach (sistema de recomendaciones)
│
├── ML Pipeline (independiente pero acoplado)
│   ├── Dataset generation
│   ├── Feature engineering
│   ├── Model training
│   ├── Prediction service
│   └── Artifacts management
│
└── Database (MySQL)
    ├── usuarios
    ├── categorias
    ├── actividades
    ├── tiempos
    ├── metas
    └── features_*
```
##  Estructura de carpetas

```bash
TiempoCheck v3.2
├── Frontend (Extension Chrome)
│   ├── content_script.js
│   ├── background.js
│   └── popup.js/html/css
│
├── Backend (Flask App)
│   ├── Controllers (rutas y lógica web)
│   ├── Models (SQLAlchemy)
│   ├── Services (lógica de negocio)
│   ├── Schedule (jobs automáticos)
│   └── Coach (sistema de recomendaciones)
│
├── ML Pipeline (independiente pero acoplado)
│   ├── Dataset generation
│   ├── Feature engineering
│   ├── Model training
│   ├── Prediction service
│   └── Artifacts management
│
└── Database (MySQL)
    ├── usuarios
    ├── categorias
    ├── actividades
    ├── tiempos
    ├── metas
    └── features_*
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


#Estos jobs tambien se puededen ejecutar de manera manual mediante los botones incluidos en el dashboard.

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
| **v3.1** |  Cerrada | Selector automático y recomendaciones simples |
| **v3.2** |  Estable | Predicciones extendidas (T+1..T+3) + UI de adopción y coach Inteligente |
| **LaunchOf (v3.3)** |  En desarrollo | Correción de errores y version final |

---

##  Entorno recomendado
- **SO:** Ubuntu 22.04 (WSL2) o macOS  
- **Python:** 3.10+  
- **Base de datos:** MySQL 8.0  
- **Librerías clave:** Flask, SQLAlchemy, APScheduler, pandas, scikit-learn

---

##  Autoria

- Luis Ángel Cruz Tenorio — Estudiante de Ingeniería en Comunicaciones y Electrónica · IPN ESIME Zacatenco  
  GitHub: [@cruznoise](https://github.com/cruznoise)  
  Desarrollo backend · Arquitectura ML · Integración de datos

- Ana Maria Ambriz Gonzalez — Estudiante de Ingeniería en Comunicaciones y Electrónica · IPN ESIME Zacatenco
  Diseño de interfaz · UX/UI · Mejoras visuales y de experiencia de usuario · Documentación oficial 
  
