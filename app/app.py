from flask import Flask, render_template, request, session, redirect, jsonify, Response
from flask_cors import CORS
from datetime import datetime, date
from app.models.models import db, Usuario, Registro
from app.controllers.app_base import guardar_tiempo, resumen, exportar_csv
from app.controllers.app_base import controlador as app_base_controller
from app.controllers.admin_controller import admin_controller
from app.utils import generar_backup_completo, restaurar_backup_completo
from app.mysql_conn import get_mysql, close_mysql


import json

app = Flask(__name__)
app.secret_key = 'tiempocheck_key'
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)


# Configuración de base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:base@localhost/tiempocheck_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Registro de blueprints
app.register_blueprint(app_base_controller)
app.register_blueprint(admin_controller)


# Redirección principal
@app.route('/')
def home():
    return redirect('/login')

# Ruta de Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        correo = data.get('correo')
        contraseña = data.get('contraseña')

        usuario = Usuario.query.filter_by(correo=correo, contraseña=contraseña).first()
        if usuario:
            session['usuario_id'] = usuario.id
            return jsonify({'success': True})
        else:
            return jsonify({'success': False})
    return render_template('login.html')


# API para guardar tiempo
@app.route('/guardar', methods=['POST'])
def guardar():
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    return guardar_tiempo(request, session['usuario_id'])

# API para exportar CSV
@app.route('/exportar')
def exportar():
    return exportar_csv()

# API para resumen de uso
@app.route('/resumen')
def resumen_actividad():
    if 'usuario_id' not in session:
        return jsonify({})
    return resumen(session['usuario_id'])

# API de alertas
@app.route('/alertas', methods=['POST'])
def alerta_categoria():
    if 'usuario_id' not in session:
        return jsonify({'alerta': False})
    return alertas(request, session['usuario_id'])

# API para obtener tiempo por dominio (usado con AJAX)
@app.route('/api/tiempo', methods=['POST'])
def tiempo():
    if 'usuario_id' not in session:
        return jsonify([])
    registros = Registro.query.filter_by(usuario_id=session['usuario_id']).all()
    return jsonify([
        {
            'dominio': r.dominio,
            'tiempo': r.tiempo,
            'fecha': r.fecha.strftime('%Y-%m-%d %H:%M:%S')
        } for r in registros
    ])

# Logout de sesión
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

#Backup de cuenta
@app.route('/backup_completo')
def backup_completo():
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401

    backup = generar_backup_completo(session['usuario_id'])  # <- asegúrate de importar esta
    json_data = json.dumps(backup, indent=2)

    return Response(
        json_data,
        mimetype='application/json',
        headers={'Content-Disposition': 'attachment;filename=backup_completo.json'}
    )


@app.route('/restaurar_backup', methods=['POST'])
def restaurar_backup():
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401

    archivo = request.files.get('backup')
    if not archivo:
        return jsonify({'error': 'Archivo no encontrado'}), 400

    try:
        contenido = json.load(archivo)
        restaurar_backup_completo(contenido, session['usuario_id'])
        return jsonify({'mensaje': 'Backup restaurado exitosamente ✅'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error al restaurar backup: {str(e)}'}), 500


@app.route('/reseteo_total', methods=['POST'])
def reseteo_total():
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401

    try:
        from app.utils import resetear_datos_usuario
        resetear_datos_usuario(session['usuario_id'])
        return jsonify({'mensaje': 'Cuenta reiniciada correctamente ✅'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error al resetear la cuenta: {str(e)}'}), 500



import os
import atexit
from app.schedule.scheduler import start_scheduler


_scheduler = None

def _start_scheduler_once():
    global _scheduler
    if _scheduler is None:
        _scheduler = start_scheduler(app, usuario_id=1)


# Evita doble arranque con el reloader de Flask
if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
    _start_scheduler_once()

# Apagar limpio al salir del proceso (NO en teardown de app_context)
@atexit.register
def _shutdown_scheduler_on_exit():
    global _scheduler
    if _scheduler:
        try:
            _scheduler.shutdown(wait=False)
            print("[SCHED] Scheduler detenido (atexit)")
        except Exception as e:
            print(f"[SCHED] Error al detener scheduler en atexit: {e}")
        _scheduler = None

if __name__ == '__main__':
    app.run(debug=True)
