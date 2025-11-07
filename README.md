#  TiempoCheck — “Tu asistente de hábitos digitales inteligentes”

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3-green.svg)](https://flask.palletsprojects.com/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3.0-orange.svg)](https://scikit-learn.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-success.svg)](https://github.com/cruznoise/tiempocheck)

**Versión actual:** `v3.2.1 Cambios en V 3.2`  
**Fecha de lanzamiento:** 2025-11-05  
**Autores:** 
Luis Ángel Cruz Tenorio (`@cruznoise`)
Ana Maria Ambriz Gonzalez
**Licencia:** MIT  
**Stack:** Python · Flask · MySQL · APScheduler · scikit-learn · Chart.js

> *"Optimiza tu tiempo, potencia tu productividad"*

---

## 📖 Descripción

TiempoCheck es un **sistema integral de análisis y optimización del tiempo** que combina:

- 📊 **Tracking automático** de navegación web
- 🤖 **Machine Learning predictivo** con 7 modelos especializados
- 🧠 **Sistema de contexto humano** que aprende de tus explicaciones
- 🎯 **Clasificación automática** con mejora continua
- 👤 **Perfil adaptativo** que se ajusta a tu comportamiento
- 📈 **Visualizaciones interactivas** y alertas inteligentes

### 🌟 Diferenciador Clave

**Sistema único de contexto humano:** A diferencia de RescueTime, Toggl o WakaTime, TiempoCheck aprende de tus explicaciones sobre días atípicos y ajusta automáticamente las predicciones futuras.

**Resultado:** 96% de mejora en precisión para días atípicos.

---

## ✨ Características Principales

### 🎯 Core Features

| Feature | Descripción | Estado |
|---------|-------------|--------|
| **Tracking Automático** | Extensión Chrome que captura tiempo por dominio | ✅ 100% |
| **ML Predictivo** | 7 modelos RandomForest (R²=0.82) | ✅ 100% |
| **Contexto Humano** | Aprende de explicaciones (96% mejora) | ✅ 100% |
| **Clasificación ML** | Naive Bayes + feedback loop (57→75%) | ✅ 100% |
| **Perfil Adaptativo** | Infiere tipo de usuario automáticamente | ✅ 100% |
| **Coach Virtual** | Alertas y sugerencias inteligentes | ✅ 80% |
| **Gamificación** | Rachas, logros, niveles | ✅ 70% |
| **Dashboard** | Visualizaciones interactivas | ✅ 90% |

---

## 🏗️ Arquitectura
```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND LAYER                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Extensión│  │ Dashboard│  │ Modales  │             │
│  │  Chrome  │  │   Web    │  │Interactive│            │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
                         ↕ HTTP/JSON
┌─────────────────────────────────────────────────────────┐
│                   BACKEND LAYER (Flask)                  │
│  ┌────────────────┐  ┌────────────────┐                │
│  │  Controllers   │  │    Services    │                │
│  │   (7 BPs)      │  │  (Business)    │                │
│  └────────────────┘  └────────────────┘                │
└─────────────────────────────────────────────────────────┘
                         ↕
┌─────────────────────────────────────────────────────────┐
│                   ML LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Predicciones │  │ Clasificador │  │   Contexto   │ │
│  │   (RF x7)    │  │     (NB)     │  │ Integration  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                         ↕
┌─────────────────────────────────────────────────────────┐
│              SCHEDULER (APScheduler - 98 jobs)           │
└─────────────────────────────────────────────────────────┘
                         ↕
┌─────────────────────────────────────────────────────────┐
│                 DATABASE (MySQL - 14 tablas)             │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ Stack Tecnológico

### Backend
- **Python 3.10+** - Lenguaje principal
- **Flask 2.3** - Framework web
- **SQLAlchemy** - ORM
- **APScheduler** - Jobs automatizados (98 activos)
- **PyMySQL** - Conector MySQL

### Machine Learning
- **scikit-learn 1.3.0**
  - RandomForestRegressor (predicciones)
  - MultinomialNB (clasificación)
- **pandas 2.0.3** - Manipulación de datos
- **numpy 1.24.3** - Operaciones numéricas

### Frontend
- **HTML5/CSS3/JavaScript (ES6+)**
- **jQuery 3.7**
- **Bootstrap 5.3**
- **Chart.js** - Visualizaciones
- **Font Awesome** - Iconos

### Database
- **MySQL 8.0** (InnoDB)
- **14 tablas principales**
- **17,683+ registros** (datos de prueba)

---

## 📦 Instalación Rápida

### Requisitos Previos
```bash
Python 3.10+
MySQL 8.0+
Node.js 16+ (opcional, para extensión)
```

### Paso 1: Clonar Repositorio
```bash
git clone https://github.com/tu-usuario/TiempoCheck.git
cd TiempoCheck
```

### Paso 2: Entorno Virtual
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

### Paso 3: Dependencias
```bash
pip install -r requirements.txt
```

### Paso 4: Base de Datos
```bash
# Crear BD
mysql -u root -p -e "CREATE DATABASE tiempocheck_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Importar esquema
mysql -u root -p tiempocheck_db < database/schema.sql

# Datos iniciales
mysql -u root -p tiempocheck_db < database/seed_data.sql
```

### Paso 5: Configuración
```bash
cp .env.example .env
nano .env
```
```bash
DATABASE_URL=mysql+pymysql://root:TU_PASSWORD@localhost/tiempocheck_db
SECRET_KEY=tu-secret-key-cambiar-en-produccion
ENABLE_SCHEDULER=true
ENABLE_ML=true
TZ=America/Mexico_City
```

### Paso 6: Iniciar
```bash
python3 -m app.app
# Servidor en: http://localhost:5000
```

### Paso 7: Extensión
```bash
# Chrome: chrome://extensions/
# Activar "Modo desarrollador"
# Cargar extension/ como "extensión sin empaquetar"
```

---

## 🚀 Uso

### Primera Ejecución
```bash
# Crear usuario
python3 scripts/crear_usuario.py

# Entrenar modelos
python3 scripts/setup_ml_completo.py

# (Opcional) Datos de demo
python3 scripts/generar_datos_demo.py
```

### Acceso
```
URL: http://localhost:5000
Email: demo@tiempocheck.com
Password: demo123
```

---

## 🤖 Machine Learning

### Modelos Implementados

#### 1. RandomForest Regressor (Predicciones)

**7 modelos especializados:**
- Productividad (R²=0.82, MAE=37.7)
- Redes Sociales (R²=0.84, MAE=6.6)
- Trabajo (R²=0.85, MAE=8.8)
- Ocio (R²=0.85, MAE=11.2)
- Herramientas (R²=0.79, MAE=4.6)
- Estudio (R²=0.78, MAE=9.2)
- Sin categoría (R²=0.70, MAE=15.3)

**Features:**
```python
features = [
    'min_t-1', 'min_t-2', 'min_t-3', 'min_t-7',  # Lags
    'MA7',                                         # Media móvil 7 días
    'dow',                                         # Día de la semana
    'is_weekend',                                  # Fin de semana
    'day',                                         # Día del mes
    'days_to_eom'                                  # Días hasta fin de mes
]
```

#### 2. Naive Bayes (Clasificación de Dominios)

**Configuración:**
```python
MultinomialNB(alpha=0.1)
TfidfVectorizer(analyzer='char', ngram_range=(2,4))
```

**Precisión:**
- Inicial: 57.69%
- Con feedback (50+ validaciones): 68-75%
- Mejora continua con uso

#### 3. Sistema de Contexto

**Ajuste de predicciones:**
```python
if motivo in patrones_aprendidos:
    factor = patrones['ajustes_sugeridos'][motivo]['factor']
    prediccion_ajustada = prediccion_base * factor
```

**Mejora:** 96% en días atípicos

---

## 📊 Resultados

### Métricas Generales

| Métrica | Valor |
|---------|-------|
| **Precisión ML** | 82% (R²=0.82) |
| **Mejora con contexto** | 96% en días atípicos |
| **Clasificador inicial** | 57.69% |
| **Clasificador mejorado** | 68-75% |
| **Jobs activos** | 98 |
| **Tiempo arranque** | < 5 segundos |

### Evaluación por Categoría
```
Categoría         MAE    RMSE    R²     Ejemplos
───────────────────────────────────────────────────
Productividad    37.7   48.7   0.82     2,450
Redes Sociales    6.6    9.9   0.84     1,823
Trabajo           8.8   11.4   0.85     3,102
Ocio             11.2   14.2   0.85     1,567
Herramientas      4.6    6.1   0.79       892
Estudio           9.2   14.0   0.78     1,234
Sin categoría    15.3   22.1   0.70       615
```

---

## 📚 Documentación

- **[CHANGELOG.md](CHANGELOG.md)** - Historial de cambios detallado
- **[DOCS.md](DOCS.md)** - Documentación técnica completa
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Estado actual del proyecto
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Guía de despliegue
- **[API.md](API.md)** - Documentación de endpoints
- **[ML.md](ML.md)** - Detalles de modelos ML

---

## 🗺️ Roadmap

### ✅ Completado (v3.2.1)
- [x] Sistema de tracking
- [x] ML predictivo
- [x] Contexto humano
- [x] Clasificación automática
- [x] Perfil adaptativo

### 🔄 En Progreso (v3.3.0)
- [ ] Dashboard responsive
- [ ] Tour guiado
- [ ] PWA

### 📅 Planificado (v4.0.0)
- [ ] App móvil
- [ ] Integraciones (Calendar, Notion)
- [ ] API pública
- [ ] Multi-tenant

---

## 🧪 Testing
```bash
# Tests unitarios
pytest tests/ -v

# Test de integración
python3 scripts/test_integracion_ml_contexto.py

# Análisis ML
python3 scripts/analizar_clasificaciones_ml.py
```

---

## 📁 Estructura
```
TiempoCheck/
├── app/                    # Backend Flask
│   ├── controllers/        # 7 blueprints
│   ├── services/           # Lógica de negocio
│   ├── models/             # Modelos SQLAlchemy
│   └── schedule/           # 98 jobs
├── ml/                     # Machine Learning
│   ├── pipeline.py         # Pipeline principal
│   ├── artifacts/          # Modelos entrenados
│   └── preds/              # Predicciones
├── templates/              # HTML
├── static/                 # CSS/JS/Images
├── extension/              # Chrome Extension
├── scripts/                # Scripts utilidad
├── database/               # SQL schemas
└── tests/                  # Tests
```

---

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE)

---

## 📞 Contacto

**Autor:** Angel Cruz  
**Email:** contacto@tiempocheck.com  
**GitHub:** [@cruznoise](https://github.com/tu-usuario)  

---

## 🙏 Agradecimientos

- scikit-learn
- Flask
- Comunidad Python
- [Más agradecimientos]

---

## 📊 Estadísticas
```
📦 Líneas de código: ~15,000
📝 Commits: 215+
⏱️  Desarrollo: 6 meses
🤖 Modelos ML: 8
🎯 Precisión: 82%
⚙️  Jobs: 98
🔌 Endpoints: 35+
🗄️  Tablas: 14
```

---

**Última actualización:** 5 de Noviembre de 2025  
**Versión:** 3.2.1  
**Estado:** ✅ Estable

---

# 🚀 ¡Comienza a optimizar tu tiempo ahora!
