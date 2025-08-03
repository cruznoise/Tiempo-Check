# TiempoCheck 

**TiempoCheck** es una herramienta de análisis de hábitos digitales desarrollada como proyecto de titulación. A través de una extensión para Google Chrome y un backend en Flask, permite monitorear el tiempo que pasas en cada sitio web, clasificarlos por categoría, definir metas y límites, y recibir alertas cuando te excedes.

---

##  Funcionalidades principales

- Registro automático del tiempo por dominio en tiempo real
- Dashboard interactivo con visualización diaria por categoría
- Sistema de metas diarias configurables por el usuario
- Límites de tiempo con alertas emergentes al superarlos
- Alertas preventivas al alcanzar el 80% del límite
- Clasificación automática de dominios por categoría
- Envío de datos periódicos cada 30 segundos desde la extensión
- Exportación de datos a CSV y JSON (a partir de v2.2)
- Autenticación de usuario y manejo de sesiones

---

## Tecnologías utilizadas

- **Frontend:** HTML5, CSS3, JavaScript, Chart.js, jQuery
- **Backend:** Python (Flask), MySQL
- **Extensión de navegador:** Chrome Extensions API
- **Estilo visual:** Dashboard moderno con tarjetas, tablas y formularios interactivos
- **Otros:** AJAX, JSON, Git

---

## Instalación (modo desarrollador)

1. Clona este repositorio:

```
git clone https://github.com/cruznoise/Tiempo-Check.git
```

2. Instala los paquetes de Python necesarios:

```
cd Tiempo-Check
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Corre el backend:

```
python -m app.app
```

4. Carga la extensión manualmente en Chrome:
    - Ve a `chrome://extensions/`
    - Activa "Modo desarrollador"
    - Click en “Cargar descomprimida” y selecciona la carpeta `tiempocheck_extension/`

---

## Historial de versiones

| Versión   | Fecha         | Cambios principales                                                                 |
|-----------|---------------|--------------------------------------------------------------------------------------|
| `v1.0`    | 2025-21-05    | Registro básico de tiempo por dominio desde extensión. Flask + MySQL inicial.       |
| `v2.0`    | 2025-01-06    | Dashboard funcional, integración con base de datos, sesiones, visualización con Chart.js |
| `v2.1`    | 2025-07-07    | Clasificación automática de dominios, sistema de metas y límites diarios, alertas emergentes |
| `v2.1.2`  | 2025-08-07    | Alertas emergentes al llegar al 80% del límite. Envío de datos cada 30 segundos.   |

---

## Releases

- [Versión 1.0](https://github.com/cruznoise/Tiempo-Check/releases/tag/v1.0)
- [Versión 2.0](https://github.com/cruznoise/Tiempo-Check/releases/tag/v2.0)
- [Versión 2.1](https://github.com/cruznoise/Tiempo-Check/releases/tag/v2.1)
- [Versión 2.1.2](https://github.com/cruznoise/Tiempo-Check/releases/tag/v2.1.2)

---

## Autor

Desarrollado por **Luis Ángel Cruz** – Estudiante de Ingeniería en Comunicaciones y Electrónica, ESIME Zacatenco – IPN  
[LinkedIn](https://www.linkedin.com/in/luisact/) | [GitHub](https://github.com/cruznoise)

---
