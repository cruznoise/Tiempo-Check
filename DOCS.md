# 📖 Documentación Técnica - TiempoCheck v3.2

Documentación técnica completa del sistema.

---

## 📑 Tabla de Contenidos

1. [Arquitectura del Sistema](#arquitectura-del-sistema)
2. [Modelos de Base de Datos](#modelos-de-base-de-datos)
3. [Sistema de Machine Learning](#sistema-de-machine-learning)
4. [API Endpoints](#api-endpoints)
5. [Scheduler y Jobs](#scheduler-y-jobs)
6. [Sistema de Contexto Humano](#sistema-de-contexto-humano)
7. [Clasificación Automática](#clasificación-automática)
8. [Perfil Adaptativo](#perfil-adaptativo)
9. [Frontend](#frontend)
10. [Seguridad](#seguridad)
11. [Performance](#performance)
12. [Testing](#testing)

---

## 🏗️ Arquitectura del Sistema

### Diagrama General
```
┌─────────────────────────────────────────────────────────────────┐
│                        CAPA DE PRESENTACIÓN                      │
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  Extensión  │  │  Dashboard  │  │   Admin     │            │
│  │   Chrome    │  │    Web      │  │   Panel     │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│         │                 │                 │                    │
│         └─────────────────┴─────────────────┘                   │
│                           │                                      │
└───────────────────────────┼──────────────────────────────────────┘
                            │ HTTP/JSON
┌───────────────────────────┼──────────────────────────────────────┐
│                           ▼                                       │
│                    CAPA DE APLICACIÓN                            │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │               FLASK APPLICATION                           │  │
│  │                                                            │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │  │
│  │  │Controllers │  │  Services  │  │   Utils    │         │  │
│  │  │  (7 BPs)   │  │ (Business) │  │ (Helpers)  │         │  │
│  │  └────────────┘  └────────────┘  └────────────┘         │  │
│  │         │                │                │                │  │
│  │         └────────────────┴────────────────┘                │  │
│  └──────────────────────────┬───────────────────────────────┘  │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │
┌──────────────────────────────┼───────────────────────────────────┐
│                              ▼                                    │
│                    CAPA DE MACHINE LEARNING                      │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Predicciones │  │ Clasificador │  │   Contexto   │          │
│  │              │  │              │  │              │          │
│  │ RF x 7       │  │ Naive Bayes  │  │ Integration  │          │
│  │ R²=0.82      │  │ Prec=68%     │  │ +96% mejora  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                 │                 │                    │
│         └─────────────────┴─────────────────┘                   │
│                           │                                      │
└───────────────────────────┼──────────────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────────────┐
│                           ▼                                       │
│                    CAPA DE SCHEDULER                             │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              APScheduler (98 Jobs Activos)             │    │
│  │                                                          │    │
│  │  Por Usuario (7 jobs × 14 usuarios = 98):              │    │
│  │    • features_diarias      (01:30)                     │    │
│  │    • features_horarias     (01:45)                     │    │
│  │    • predicciones          (02:00)                     │    │
│  │    • anomalias_historico   (02:30)                     │    │
│  │    • anomalias_tiempo_real (cada hora 08:15-23:15)     │    │
│  │    • perfil                (Dom 04:00)                 │    │
│  │    • evaluacion_semanal    (Dom 05:00)                 │    │
│  │                                                          │    │
│  │  Globales (3 jobs):                                     │    │
│  │    • reentrenar_clasificador (03:00)                   │    │
│  │    • actualizar_rachas       (23:55)                   │    │
│  │    • limpiar_logs            (Dom 06:00)               │    │
│  └────────────────────────────────────────────────────────┘    │
│                           │                                      │
└───────────────────────────┼──────────────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────────────┐
│                           ▼                                       │
│                    CAPA DE DATOS                                 │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                    MySQL 8.0 (InnoDB)                  │    │
│  │                                                          │    │
│  │  Tablas Principales (14):                              │    │
│  │    • usuarios                (5,234 rows)              │    │
│  │    • registro                (17,683 rows)             │    │
│  │    • dominio_categoria       (126 rows)                │    │
│  │    • categorias              (7 rows)                  │    │
│  │    • features_diarias        (8,901 rows)              │    │
│  │    • features_horarias       (12,345 rows)             │    │
│  │    • contexto_dia            (11 rows)                 │    │
│  │    • notificaciones_clasif   (15 rows)                 │    │
│  │    • ml_predicciones_future  (4,567 rows)              │    │
│  │    • coach_alertas           (234 rows)                │    │
│  │    • coach_sugerencias       (89 rows)                 │    │
│  │    • rachas                  (456 rows)                │    │
│  │    • metas_categoria         (78 rows)                 │    │
│  │    • limites_categoria       (92 rows)                 │    │
│  │                                                          │    │
│  │  Total: ~50,000 registros                              │    │
│  └────────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Modelos de Base de Datos

### 1. Tabla `usuarios`
```sql
CREATE TABLE usuarios (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    correo VARCHAR(100) UNIQUE NOT NULL,
    contrasena VARCHAR(255) NOT NULL,
    
    -- Perfil Manual (del registro)
    dedicacion VARCHAR(50),              -- estudiante, trabajador, etc.
    horario_preferido VARCHAR(50),       -- manana, tarde, noche
    dias_trabajo VARCHAR(50),            -- lun_vie, toda_semana, etc.
    
    -- Perfil Inferido (ML)
    tipo_inferido VARCHAR(50),           -- estudiante, trabajador, mixto
    confianza_inferencia FLOAT DEFAULT 0.0,
    hora_pico_inicio INT,                -- 0-23
    hora_pico_fin INT,                   -- 0-23
    dias_activos_patron VARCHAR(50),     -- "0,1,2,3,4"
    
    -- Metadata
    perfil_actualizado_en DATETIME,
    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_tipo_inferido (tipo_inferido),
    INDEX idx_dedicacion (dedicacion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Relaciones:**
- 1:N con `registro`
- 1:N con `contexto_dia`
- 1:N con `notificaciones_clasificacion`

---

### 2. Tabla `registro`
```sql
CREATE TABLE registro (
    id INT PRIMARY KEY AUTO_INCREMENT,
    dominio VARCHAR(255) NOT NULL,
    tiempo INT NOT NULL,                 -- Segundos
    fecha DATETIME NOT NULL,             -- DEPRECATED
    fecha_hora DATETIME NOT NULL,        -- Timestamp preciso
    usuario_id INT NOT NULL,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    
    INDEX idx_usuario_fecha (usuario_id, fecha_hora),
    INDEX idx_dominio (dominio)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Uso:**
- Captura de tiempo por dominio
- Fuente de datos para features
- 17,683 registros en demo

---

### 3. Tabla `dominio_categoria`
```sql
CREATE TABLE dominio_categoria (
    id INT PRIMARY KEY AUTO_INCREMENT,
    dominio VARCHAR(255) UNIQUE NOT NULL,
    categoria_id INT NOT NULL,
    
    -- Metadata clasificación
    clasificado_por VARCHAR(50) DEFAULT 'manual',  -- manual, ml, regex
    confianza FLOAT,
    clasificado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (categoria_id) REFERENCES categorias(id),
    
    INDEX idx_dominio (dominio),
    INDEX idx_categoria (categoria_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Uso:**
- Mapeo dominio → categoría
- Entrenamiento de clasificador ML
- 126 dominios clasificados

---

### 4. Tabla `contexto_dia`
```sql
CREATE TABLE contexto_dia (
    id INT PRIMARY KEY AUTO_INCREMENT,
    usuario_id INT NOT NULL,
    fecha DATE NOT NULL,
    categoria VARCHAR(100),
    
    -- Métricas
    uso_real_min INT,
    uso_esperado_min INT,
    desviacion_pct FLOAT,
    es_atipico BOOLEAN DEFAULT FALSE,
    
    -- Contexto del usuario
    motivo VARCHAR(50),                  -- deadline, sin_clases, etc.
    notas TEXT,
    explicacion_completa TEXT,
    
    -- Metadata
    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    
    UNIQUE KEY uk_usuario_fecha_cat (usuario_id, fecha, categoria),
    INDEX idx_motivo (motivo),
    INDEX idx_es_atipico (es_atipico)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Uso:**
- Sistema de contexto humano
- Ajuste de predicciones ML
- 11 anomalías explicadas

---

### 5. Tabla `notificaciones_clasificacion`
```sql
CREATE TABLE notificaciones_clasificacion (
    id INT PRIMARY KEY AUTO_INCREMENT,
    usuario_id INT NOT NULL,
    dominio VARCHAR(255) NOT NULL,
    
    -- Clasificación sugerida
    categoria_sugerida_id INT NULL,
    confianza FLOAT DEFAULT 0.0,
    metodo VARCHAR(50),                  -- ml, regex, manual_required
    
    -- Estado
    status VARCHAR(50) DEFAULT 'pendiente',  -- pendiente, confirmado, rechazado, clasificado_manual
    
    -- Feedback del usuario
    categoria_correcta_id INT NULL,
    
    -- Metadata
    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
    respondido_en DATETIME NULL,
    usado_en_entrenamiento BOOLEAN DEFAULT FALSE,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (categoria_sugerida_id) REFERENCES categorias(id),
    FOREIGN KEY (categoria_correcta_id) REFERENCES categorias(id),
    
    INDEX idx_status (status),
    INDEX idx_usado_entrenamiento (usado_en_entrenamiento, respondido_en),
    INDEX idx_usuario_status (usuario_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Uso:**
- Sistema de feedback clasificación
- Human-in-the-loop learning
- Reentrenamiento automático

---

### 6. Tabla `features_diarias`
```sql
CREATE TABLE features_diarias (
    id INT PRIMARY KEY AUTO_INCREMENT,
    usuario_id INT NOT NULL,
    fecha DATE NOT NULL,
    categoria VARCHAR(100),
    minutos INT DEFAULT 0,
    
    -- Features para ML
    min_t_minus_1 INT,
    min_t_minus_2 INT,
    min_t_minus_3 INT,
    min_t_minus_7 INT,
    MA7 FLOAT,                           -- Media móvil 7 días
    dow INT,                             -- Día de semana (0-6)
    is_weekend BOOLEAN,
    day INT,                             -- Día del mes (1-31)
    days_to_eom INT,                     -- Días hasta fin de mes
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    
    UNIQUE KEY uk_usuario_fecha_cat (usuario_id, fecha, categoria),
    INDEX idx_fecha (fecha),
    INDEX idx_categoria (categoria)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Uso:**
- Features para predicciones ML
- Calculadas diariamente (01:30)

---

### Diagrama ER Simplificado
```
┌─────────────┐
│  usuarios   │
└──────┬──────┘
       │ 1:N
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌─────────────┐   ┌─────────────┐
│  registro   │   │contexto_dia │
└─────────────┘   └─────────────┘
       │
       │ N:1
       ▼
┌─────────────────────┐
│ dominio_categoria   │
└──────────┬──────────┘
           │ N:1
           ▼
    ┌────────────┐
    │categorias  │
    └────────────┘
           ▲
           │ 1:N
           │
┌──────────┴────────────────────┐
│notificaciones_clasificacion   │
└───────────────────────────────┘
```

---

## 🤖 Sistema de Machine Learning

### Pipeline Completo
```python
# ml/pipeline.py

def predict(usuario_id: int, fecha: date = None):
    """
    Pipeline completo de predicción
    
    Pasos:
    1. Cargar features del día (features_diarias)
    2. Para cada categoría:
       a. Cargar modelo entrenado
       b. Hacer predicción base
       c. Verificar contexto histórico
       d. Ajustar predicción si hay patrón
    3. Retornar predicciones ajustadas
    """
    
    if fecha is None:
        fecha = date.today() + timedelta(days=1)  # T+1
    
    # 1. Cargar features
    features = cargar_features_dia(usuario_id, fecha)
    
    predicciones = {}
    contexto_aplicado = False
    
    # 2. Predicción por categoría
    for categoria in CATEGORIAS_DISPONIBLES:
        # a. Cargar modelo
        modelo = cargar_modelo(categoria)
        
        if not modelo:
            continue
        
        # b. Predicción base
        X = preparar_features(features, categoria)
        pred_base = modelo.predict(X)[0]
        
        # c. Verificar contexto
        from app.services.contexto_ml_integration import ajustar_prediccion_con_contexto
        
        pred_ajustada = ajustar_prediccion_con_contexto(
            prediccion_base=pred_base,
            dia_semana=fecha.weekday(),
            usuario_id=usuario_id,
            categoria=categoria
        )
        
        if pred_ajustada != pred_base:
            contexto_aplicado = True
        
        predicciones[categoria] = int(pred_ajustada)
    
    return {
        'fecha': str(fecha),
        'predicciones': predicciones,
        'contexto_aplicado': contexto_aplicado
    }
```

---

### Sistema de Contexto
```python
# app/services/contexto_ml_integration.py

def ajustar_prediccion_con_contexto(
    prediccion_base: float,
    dia_semana: int,
    usuario_id: int,
    categoria: str
):
    """
    Ajusta predicción ML con contexto aprendido
    
    Lógica:
    1. Obtener patrones históricos del usuario
    2. Si hay patrón para este día/categoría:
       - Calcular factor de ajuste
       - Aplicar a predicción base
    3. Si no hay patrón: retornar predicción base
    """
    
    # 1. Obtener contexto histórico
    patrones = obtener_contexto_historico(usuario_id)
    
    if not patrones or 'ajustes_sugeridos' not in patrones:
        return prediccion_base
    
    ajustes = patrones['ajustes_sugeridos']
    
    # 2. Buscar patrón aplicable
    for motivo, info in ajustes.items():
        # Verificar si es relevante para este día
        if info.get('dias_aplicables') and dia_semana not in info['dias_aplicables']:
            continue
        
        if info.get('categoria') and info['categoria'] != categoria:
            continue
        
        # 3. Aplicar ajuste
        factor = info.get('factor', 1.0)
        prediccion_ajustada = prediccion_base * factor
        
        print(f"[CONTEXTO] Ajuste aplicado: {prediccion_base} × {factor} = {prediccion_ajustada}")
        
        return prediccion_ajustada
    
    return prediccion_base


def obtener_contexto_historico(usuario_id: int):
    """
    Analiza contexto_dia para encontrar patrones
    
    Retorna:
    {
        'ajustes_sugeridos': {
            'deadline': {
                'factor': 1.45,
                'confianza': 0.85,
                'ocurrencias': 3,
                'categoria': 'Productividad',
                'dias_aplicables': [0, 1, 2, 3, 4]
            }
        }
    }
    """
    
    from collections import defaultdict
    
    # Obtener anomalías explicadas
    contextos = ContextoDia.query.filter_by(
        usuario_id=usuario_id,
        es_atipico=True
    ).all()
    
    if not contextos:
        return {}
    
    # Agrupar por motivo
    por_motivo = defaultdict(list)
    
    for ctx in contextos:
        if ctx.motivo:
            por_motivo[ctx.motivo].append({
                'desviacion_pct': ctx.desviacion_pct,
                'uso_real': ctx.uso_real_min,
                'uso_esperado': ctx.uso_esperado_min,
                'categoria': ctx.categoria,
                'dia_semana': ctx.fecha.weekday()
            })
    
    ajustes = {}
    
    # Calcular factor de ajuste por motivo
    for motivo, eventos in por_motivo.items():
        if len(eventos) < 2:  # Mínimo 2 ocurrencias
            continue
        
        # Calcular factor promedio
        factores = [e['uso_real'] / e['uso_esperado'] 
                   for e in eventos if e['uso_esperado'] > 0]
        
        if not factores:
            continue
        
        factor_promedio = sum(factores) / len(factores)
        
        ajustes[motivo] = {
            'factor': factor_promedio,
            'confianza': min(len(eventos) / 5.0, 1.0),  # Max confianza con 5+ eventos
            'ocurrencias': len(eventos),
            'categoria': eventos[0]['categoria'],
            'dias_aplicables': list(set(e['dia_semana'] for e in eventos))
        }
    
    return {'ajustes_sugeridos': ajustes}
```

---

### Clasificador de Dominios
```python
# app/services/clasificador_ml.py

class ClasificadorDominios:
    """
    Clasificador Naive Bayes para dominios
    
    Features:
    - TF-IDF con n-gramas de caracteres (2-4)
    - MultinomialNB con alpha=0.1
    - Filtrado de categorías con < 2 ejemplos
    """
    
    def entrenar(self, dominios: List[str], categorias: List[str]):
        """
        Entrena el clasificador
        
        Args:
            dominios: Lista de dominios (ej: ['github.com', 'facebook.com'])
            categorias: Lista de categorías correspondientes
        
        Returns:
            True si éxito, False si error
        """
        
        if len(dominios) < 10:
            print("[CLASIFICADOR] Muy pocos datos (< 10)")
            return False
        
        # Vectorizar
        X = self.vectorizador.fit_transform(dominios)
        y = categorias
        
        # Split (sin stratify si hay categorías con 1 ejemplo)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Entrenar
        self.modelo.fit(X_train, y_train)
        
        # Evaluar
        y_pred = self.modelo.predict(X_test)
        
        self.metricas = {
            'accuracy': accuracy_score(y_test, y_pred),
            'n_ejemplos': len(dominios),
            'n_categorias': len(set(categorias))
        }
        
        self.entrenado = True
        
        # Guardar
        self.guardar()
        
        return True
    
    def predecir(self, dominio: str):
        """
        Clasifica un dominio
        
        Returns:
            (categoria, confianza)
        """
        
        if not self.entrenado:
            return None, 0.0
        
        X = self.vectorizador.transform([dominio])
        
        # Predicción
        categoria = self.modelo.predict(X)[0]
        
        # Probabilidades
        probas = self.modelo.predict_proba(X)[0]
        confianza = max(probas)
        
        return categoria, confianza
```

---

## 🌐 API Endpoints

### Autenticación
```http
POST /login
Content-Type: application/json

{
    "correo": "usuario@ejemplo.com",
    "contraseña": "password123"
}

Response 200:
{
    "success": true
}

Response 401:
{
    "success": false,
    "error": "Credenciales inválidas"
}
```

---

### Tracking
```http
POST /guardar
Content-Type: application/json

{
    "dominio": "github.com",
    "tiempo": 60
}

Response 200:
{
    "mensaje": "Tiempo actualizado"
}
```

---

### Predicciones
```http
GET /api/ml/predict?fecha=2025-11-06

Response 200:
{
    "fecha": "2025-11-06",
    "predicciones": {
        "Productividad": 180,
        "Redes Sociales": 30,
        "Trabajo": 120
    },
    "contexto_aplicado": true
}
```

---

### Clasificación
```http
GET /api/clasificacion/pendientes

Response 200:
{
    "pendientes": [
        {
            "id": 1,
            "dominio": "example.com",
            "categoria_sugerida": "Trabajo",
            "confianza": 0.85,
            "metodo": "ml"
        }
    ],
    "total": 1
}
```
```http
POST /api/clasificacion/confirmar/1

Response 200:
{
    "success": true,
    "mensaje": "Clasificación confirmada"
}
```
```http
POST /api/clasificacion/rechazar/1
Content-Type: application/json

{
    "categoria_correcta_id": 3
}

Response 200:
{
    "success": true,
    "mensaje": "Corrección guardada"
}
```

---

### Perfil
```http
GET /api/perfil

Response 200:
{
    "nombre": "Usuario Demo",
    "dedicacion_declarada": "trabajador",
    "tipo_inferido": "trabajador",
    "confianza_inferencia": 0.85,
    "horario_pico": "9:00 - 18:00",
    "dias_activos": "0,1,2,3,4",
    "perfil_actualizado": "2025-11-03T04:00:00"
}
```
```http
POST /api/perfil/actualizar

Response 200:
{
    "success": true,
    "perfil": {
        "tipo_inferido": "trabajador",
        "confianza": 0.85,
        "horario_pico": "9:00 - 18:00"
    }
}
```

---

### Reentrenamiento
```http
POST /api/clasificador/reentrenar

Response 200:
{
    "success": true,
    "mensaje": "Clasificador reentrenado correctamente",
    "metricas": {
        "precision_anterior": "57.69%",
        "precision_nueva": "68.42%",
        "mejora": "+10.73%",
        "n_ejemplos": 136,
        "n_categorias": 6
    }
}
```

---
