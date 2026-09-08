#  TiempoCheck — “Tu asistente de hábitos digitales inteligentes”

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3-green.svg)](https://flask.palletsprojects.com/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3.0-orange.svg)](https://scikit-learn.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-success.svg)](https://github.com/cruznoise/Tiempo-Check)

**Versión actual:** `v3.2.1 Cambios en V 3.2`  
**Fecha de lanzamiento:** 2025-11-05  
**Autores:** 
- Luis Ángel Cruz Tenorio (`@cruznoise`).
- Ana Maria Ambriz Gonzalez.
**Licencia:** MIT  
**Stack:** Python · Flask · MySQL · APScheduler · scikit-learn · Chart.js

> *"Optimiza tu tiempo, potencia tu productividad"*
**Visualización de uso:** https://youtu.be/0mvdcTOqtyY
---

## 📖 Descripción

TiempoCheck es un **sistema integral de análisis y optimización del tiempo** que combina:

- 📊 **Tracking automático** de navegación web
- 🎯 **Modo concentración**
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
## Viusalización

### Interfaz de Inicio de Sesión y registro.
<img width="1274" height="663" alt="image" src="https://github.com/user-attachments/assets/1404ccc9-9b21-4ff3-aaa6-134f6cc734b5" />

### Dashboard y ventana principal.
<img width="1895" height="662" alt="image" src="https://github.com/user-attachments/assets/7b81bdf7-d229-4ca5-8f66-84dcb8ab058c" />
<img width="1403" height="588" alt="image" src="https://github.com/user-attachments/assets/ed3e1d76-3223-4cfc-b1ac-37807193a008" />

### Ventana de Logros y metas.
<img width="1913" height="747" alt="image" src="https://github.com/user-attachments/assets/8b3252a5-2fed-4781-94ec-c9e59a88ea76" />
<img width="1914" height="915" alt="image" src="https://github.com/user-attachments/assets/970707cd-6474-4aa1-877a-9eba8966ff52" />
<img width="1913" height="936" alt="image" src="https://github.com/user-attachments/assets/2206b574-dbd2-42b9-a98f-ef9a03562ada" />

### Panel de configuración de la cuenta.
<img width="323" height="771" alt="image" src="https://github.com/user-attachments/assets/ff50e4de-9411-40c6-ad6e-21a66ae6cc40" />

### Panel de información de la cuenta.
<img width="1014" height="378" alt="image" src="https://github.com/user-attachments/assets/0814d6d8-f879-42cc-ad06-4a4cb970f732" />


### Administración de sitios y categorias.
<img width="1907" height="938" alt="image" src="https://github.com/user-attachments/assets/fe2593ea-7746-4353-a9ca-13b72f049869" />

### Popup de monitoreo.
<img width="1915" height="985" alt="image" src="https://github.com/user-attachments/assets/d3b5a8f6-792e-409d-b765-9cc1277f7c29" />

### Interfaz de Modo concentración
![Imagen de WhatsApp 2025-11-28 a las 16 32 33_694de50c](https://github.com/user-attachments/assets/5931c4c8-96f1-40a2-b2e6-28162c5c9ead)
<img width="1898" height="896" alt="image" src="https://github.com/user-attachments/assets/339ab9f1-2b2c-43d0-a74c-57e71eca5c6c" />


### Popup de alerta de limite.
<img width="921" height="477" alt="image" src="https://github.com/user-attachments/assets/ea15b1fa-b243-4f2d-8294-4fb94c6b38a2" />

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
## USO
TiempoCheck es un prototipo de aplicacion el cual fue desarrollado como parte de proyecyo terminal para obtener el grado de Ingeniero en Comunicaciones y Electrónica, su uso esta establecido para probarse en entornos controlados, si deseas hacer uso de "TiempoCheck" puedes ponerte en contacto para indicarte los pasos a seguir para la instalacion en tu ordenador.
---

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE)

---

## 📞 Contacto

**Autor:** Angel Cruz  
**Email:** cruzlat3@gmail.com
**GitHub:** [@cruznoise](https://github.com/cruznoise)  

---

## 🙏 Agradecimientos

- scikit-learn
- Flask
- Comunidad Python
- Agradecimiento especiales a Ana María Ambriz Gonzalez por haber contribuido y confiado en el desarrollo de TiempoCheck

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

