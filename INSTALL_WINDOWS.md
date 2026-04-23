# Instalación en Windows

1. Instala **Python 3.10+** y **MySQL 8+**.
2. Clona el repo:
   ```bash
   git clone https://github.com/cruznoise/Tiempo-Check.git
   cd Tiempo-Check
   ```
3. Crea entorno virtual:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
4. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
5. Crea la base de datos:
   ```sql
   CREATE DATABASE tiempocheck_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
   Importa el schema:
   ```bash
   mysql -u root -p tiempocheck_db < dump_schema.sql
   ```
6. Configura `.env`:
   ```
   DB_URL=mysql+pymysql://root:tu_password@localhost/tiempocheck_db
   ENABLE_SCHEDULER=1
   TZ=America/Mexico_City
   ```
7. Ejecuta servidor:
   ```bash
   python -m app.app
   ```
