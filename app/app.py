from flask import Flask, render_template, request, session, redirect, jsonify
from flask_cors import CORS
from datetime import datetime
from app.models.models import db, Usuario, Registro
from app.controllers.app_base import guardar_tiempo, resumen, exportar_csv
from app.controllers.app_base import controlador as app_base_controller
from app.controllers.admin_controller import admin_controller

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

if __name__ == '__main__':
    app.run(debug=True)
