from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash, current_app, send_file
from io import BytesIO
from flask_login import login_required
from flask_cors import cross_origin
import csv
import json
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import text
from app.mysql_conn import get_mysql, close_mysql
from app.models.models import Registro, DominioCategoria, Categoria, LimiteCategoria, MetaCategoria, Usuario, FeatureDiaria, FeatureHoraria
from collections import defaultdict
from datetime import datetime
from app.utils import desbloquear_logro, verificar_logros_dinamicos, obtener_promedio_categoria, calcular_nivel_confianza, obtener_dias_uso, calcular_sugerencias_por_categoria, _qa_invariantes_dia
from ml.utils_ml import clasificar_dominio_automatico
from app.services.rachas_service import actualizar_rachas
from app.extensions import db 
from app.services.features_engine import calcular_persistir_features
from app.schedule.scheduler import get_scheduler
from app.models.models_coach import CoachAlerta, CoachAccionLog,    CoachEstadoRegla, CoachSugerencia
from app.schedule.coach_jobs import job_coach_alertas
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash, current_app, send_file


bp = Blueprint('admin_controller', __name__)

@bp.route('/categorias', methods=['GET'])
def vista_categorias():
    categorias = Categoria.query.all()
    dominios = DominioCategoria.query.all()
    return render_template('admin/categorias.html', categorias=categorias, dominios=dominios)

@bp.route('/configuracion')
def vista_configuracion():
    if 'usuario_id' not in session:
        return redirect('/login')
    return render_template('admin/configuracion.html')


@bp.route('/categorias', methods=['POST'])
def agregar_categoria():
    nombre = request.form.get('nombre')
    if nombre:
        nueva = Categoria(nombre=nombre)
        db.session.add(nueva)
        db.session.commit()
        flash('Categoría agregada correctamente')
    return redirect(url_for('admin_controller.vista_categorias'))

@bp.route('/dominios', methods=['POST'])
def agregar_dominio():
    dominio = request.form.get('dominio')
    categoria_id = request.form.get('categoria_id')
    if dominio and categoria_id:
        nuevo = DominioCategoria(dominio=dominio, categoria_id=int(categoria_id))
        db.session.add(nuevo)
        db.session.commit()
        flash('Dominio agregado correctamente')
    return redirect(url_for('admin_controller.vista_categorias'))

@bp.route('/categorias/eliminar/<int:id>', methods=['POST'])
def eliminar_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    db.session.delete(categoria)
    db.session.commit()
    flash('Categoría eliminada')
    return redirect(url_for('admin_controller.vista_categorias'))

@bp.route('/dominios/eliminar/<int:id>', methods=['POST'])
def eliminar_dominio(id):
    dominio = DominioCategoria.query.get_or_404(id)
    db.session.delete(dominio)
    db.session.commit()
    flash('Dominio eliminado')
    return redirect(url_for('admin_controller.vista_categorias'))

@bp.route('/categorias/editar/<int:id>', methods=['POST'])
def editar_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    nuevo_nombre = request.form.get('nuevo_nombre')
    if nuevo_nombre:
        categoria.nombre = nuevo_nombre
        db.session.commit()
        flash('Categoría actualizada')
    return redirect(url_for('admin_controller.vista_categorias'))

@bp.route('/dominios/editar/<int:id>', methods=['POST'])
def editar_dominio(id):
    dominio = DominioCategoria.query.get_or_404(id)
    nuevo_dominio = request.form.get('nuevo_dominio')
    nueva_categoria_id = request.form.get('nueva_categoria_id')
    if nuevo_dominio and nueva_categoria_id:
        dominio.dominio = nuevo_dominio
        dominio.categoria_id = int(nueva_categoria_id)
        db.session.commit()
        flash('Dominio actualizado')
    return redirect(url_for('admin_controller.vista_categorias'))


@bp.route('/metas')
def vista_metas():
    if 'usuario_id' not in session:
        return redirect(url_for('controlador.login'))

    usuario_id = session['usuario_id']

    categorias = db.session.query(Categoria).all()
    metas = db.session.query(MetaCategoria).filter_by(usuario_id=usuario_id).all()
    limites = db.session.query(LimiteCategoria).filter_by(usuario_id=usuario_id).all()

    hoy = date.today()
    registros = db.session.execute(text("""
        SELECT dc.categoria_id, SUM(r.tiempo) as total
        FROM registro r
        JOIN dominio_categoria dc ON r.dominio = dc.dominio
        WHERE r.usuario_id = :usuario_id AND DATE(r.fecha) = :hoy
        GROUP BY dc.categoria_id
    """), {"usuario_id": usuario_id, "hoy": hoy}).fetchall()

    uso_actual = defaultdict(int)
    for categoria_id, total in registros:
        uso_actual[categoria_id] = round(total / 60)  
    estado_metas = []
    for m in metas:
        nombre = next((c.nombre for c in categorias if c.id == m.categoria_id), 'Desconocida')
        usado = uso_actual.get(m.categoria_id, 0)
        cumplida = usado >= m.minutos_meta

        m.cumplida = bool(cumplida)

        estado_metas.append({
            'categoria': nombre,
            'meta': m.minutos_meta,
            'usado': usado,
            'cumplida': cumplida,
            'origen': getattr(m, 'origen', 'manual')  
        })

    # db.session.commit() # se comenta por que aun no se guardan estados de metas para analisis con ML

    verificar_logros_dinamicos(usuario_id)

    estado_limites = []
    for l in limites:
        usado = uso_actual.get(l.categoria_id, 0)
        excedido = usado >= l.limite_minutos
        estado_limites.append({
            'categoria': l.categoria.nombre,
            'limite': l.limite_minutos,
            'usado': usado,
            'excedido': excedido
        })

    from app.models import Usuario
    usuarios = Usuario.query.all()

    return render_template('admin/metas.html',
        usuarios=usuarios,
        categorias=categorias,
        metas=metas,
        limites=limites,
        uso_actual=uso_actual,
        estado_metas=estado_metas,
        estado_limites=estado_limites
    )



@bp.route('/metas', methods=['POST'])
def agregar_meta():
    usuario_id = request.form.get('usuario_id')
    categoria_id = request.form.get('categoria_id')
    limite_minutos = request.form.get('limite_minutos')

    if usuario_id and categoria_id and limite_minutos:
        nueva = MetaCategoria(
            usuario_id=int(usuario_id),
            categoria_id=int(categoria_id),
            limite_minutos=int(limite_minutos),
            fecha=datetime.now(),
            cumplida=0
        )
        db.session.add(nueva)
        db.session.commit()
        flash(' Meta agregada correctamente.')

        #Desbloquear logro "Establecer tu primera meta (ID: 11)"
        #desbloquear_logro(usuario_id, 11)
        verificar_logros_dinamicos(usuario_id)
    
    else:
        flash(" Todos los campos son obligatorios.")

    return redirect(url_for('admin_controller.vista_metas'))

@bp.route('/api/agregar_meta', methods=['POST'])
def agregar_meta_api():
    usuario_id = request.form.get('usuario_id')
    categoria_id = request.form.get('categoria_id')
    meta_minutos = request.form.get('meta_minutos')

    if not (usuario_id and categoria_id and meta_minutos):
        return jsonify({"error": "Faltan datos"}), 400

    nueva = MetaCategoria(
        usuario_id=int(usuario_id),
        categoria_id=int(categoria_id),
        limite_minutos=int(meta_minutos),
        fecha=datetime.now(),
        cumplida=0
    )
    db.session.add(nueva)
    db.session.commit()

    verificar_logros_dinamicos(usuario_id)
    return jsonify({"ok": True})


@bp.route('/metas/eliminar/<int:id>', methods=['POST'])
def eliminar_meta(id):
    meta = MetaCategoria.query.get_or_404(id)
    db.session.delete(meta)
    db.session.commit()
    flash('Meta eliminada')
    return redirect(url_for('admin_controller.vista_metas'))

@bp.route('/metas/editar/<int:id>', methods=['POST'])
def editar_meta(id):
    meta = MetaCategoria.query.get_or_404(id)
    nuevo_limite = request.form.get('limite_minutos')

    if nuevo_limite:
        meta.limite_minutos = int(nuevo_limite)
        db.session.commit()
        flash('Meta actualizada')

    return redirect(url_for('admin_controller.vista_metas'))

@bp.route('/limites')
def vista_limites():
    if 'usuario_id' not in session:
        return redirect(url_for('controlador.login'))

    usuario_id = session['usuario_id']

    categorias = Categoria.query.all()
    limites = db.session.query(LimiteCategoria).all()


    hoy = date.today()
    registros = db.session.execute(text("""
        SELECT dc.categoria_id, SUM(r.tiempo) as total
        FROM registro r
        JOIN dominio_categoria dc ON r.dominio = dc.dominio
        WHERE r.usuario_id = :usuario_id AND DATE(r.fecha) = :hoy
        GROUP BY dc.categoria_id
    """), {"usuario_id": usuario_id, "hoy": hoy}).fetchall()

    uso_actual = defaultdict(int)
    for categoria_id, total in registros:
        uso_actual[categoria_id] = round(total / 60)  

    estado_limites = []
    for l in limites:
        usado = uso_actual.get(l.categoria_id, 0)
        excedido = usado >= l.limite_minutos

        estado_limites.append({
            'categoria': l.categoria.nombre,
            'limite': l.limite_minutos,
            'usado': usado,
            'excedido': excedido
        })

    return render_template('admin/metas.html',
                    categorias=categorias,
                    limites=limites,
                    uso_actual=uso_actual,
                    estado_limites=estado_limites
                )

@bp.route('/agregar_limite', methods=['POST'])
def agregar_limite():
    try:
        usuario_id = request.form.get('usuario_id')
        categoria_id = request.form['categoria_id']
        limite_minutos = int(request.form['limite_minutos'])

        nuevo = LimiteCategoria(
            usuario_id=usuario_id,
            categoria_id=categoria_id,
            limite_minutos=limite_minutos
        )
        db.session.add(nuevo)
        db.session.commit()
        flash("Límite agregado correctamente.")

        #Desbloquear logro "Establece tu primer límite" (ID: 10)
        #desbloquear_logro(usuario_id, 10)
        verificar_logros_dinamicos(usuario_id)


    except Exception as e:
        print("Error al agregar límite:", e)
        flash("Error al agregar límite.")

    return redirect(url_for('admin_controller.vista_metas'))


#ENDPOINT PARA AGREGAR LIMITES SUGERIDOS (EL DE ARRIBA ES MANUAL)

@bp.route('/api/agregar_limite', methods=['POST'])
def agregar_limite_api():
    usuario_id = request.form.get('usuario_id')
    categoria_id = request.form.get('categoria_id')
    limite_minutos = request.form.get('limite_minutos')

    if not (usuario_id and categoria_id and limite_minutos):
        return jsonify({"error": "Faltan datos"}), 400

    try:

        usuario_id = int(usuario_id)
        categoria_id = int(categoria_id)
        limite_minutos = int(limite_minutos)


        existente = LimiteCategoria.query.filter_by(
            usuario_id=usuario_id,
            categoria_id=categoria_id
        ).first()

        if existente:
            existente.limite_minutos = limite_minutos
            db.session.commit()
            mensaje = "Límite actualizado"
        else:
            nuevo = LimiteCategoria(
                usuario_id=usuario_id,
                categoria_id=categoria_id,
                limite_minutos=limite_minutos
            )
            db.session.add(nuevo)
            db.session.commit()
            mensaje = "Límite agregado"

        verificar_logros_dinamicos(usuario_id)

        return jsonify({"ok": True, "mensaje": mensaje})

    except Exception as e:
        db.session.rollback() 
        print(" ERROR en agregar_limite_api:", e)
        return jsonify({"error": str(e)}), 500



@bp.route('/editar_limite/<int:id>', methods=['POST'])
def editar_limite(id):
    try:
        nuevo_limite = int(request.form['limite_minutos'])
        limite = LimiteCategoria.query.get(id)
        if limite:
            limite.limite_minutos = nuevo_limite
            db.session.commit()
            flash(" Límite actualizado.")
        else:
            flash(" Límite no encontrado.")
    except Exception as e:
        print("Error al editar límite:", e)
        flash(" Error al editar límite.")

    return redirect(url_for('admin_controller.vista_metas'))

@bp.route('/eliminar_limite/<int:id>', methods=['POST'])
def eliminar_limite(id):
    try:
        limite = LimiteCategoria.query.get(id)
        if limite:
            db.session.delete(limite)
            db.session.commit()
            flash("🗑️ Límite eliminado.")
        else:
            flash(" Límite no encontrado.")
    except Exception as e:
        print("Error al eliminar límite:", e)
        flash("Error al eliminar límite.")

    return redirect(url_for('admin_controller.vista_metas'))

@bp.route('/api/categorias_usuario')
def categorias_usuario():
    if 'usuario_id' not in session:
        return jsonify([])
    usuario_id = session['usuario_id']
    categorias = db.session.query(Categoria.id, Categoria.nombre).all()
    return jsonify([{'id': c.id, 'nombre': c.nombre} for c in categorias])

@bp.route('/api/alerta_categoria', methods=['POST', 'OPTIONS'])
@cross_origin(origins='*', methods=['POST', 'OPTIONS'], allow_headers='Content-Type')
def verificar_alerta_categoria():
    print(" SESSION:", session)
    if 'usuario_id' not in session:
        print(" No hay usuario en sesión")
        return jsonify({'alerta': False})


    data = request.get_json()
    categoria_id = data.get('categoria_id')

    if not categoria_id:
        return jsonify({'alerta': False})

    usuario_id = session['usuario_id']
    hoy = date.today()

    resultado = db.session.execute(text("""
        SELECT SUM(r.tiempo)
        FROM registro r
        JOIN dominio_categoria dc ON r.dominio = dc.dominio
        WHERE r.usuario_id = :usuario_id
        AND dc.categoria_id = :categoria_id
        AND DATE(r.fecha) = :hoy
    """), {
        "usuario_id": usuario_id,
        "categoria_id": categoria_id,
        "hoy": hoy
    }).scalar() or 0

    minutos_usados = resultado / 60

    limite = db.session.query(LimiteCategoria).filter_by(
        usuario_id=usuario_id,
        categoria_id=categoria_id
    ).first()

    print(" CATEGORIA:", categoria_id)
    print(" USUARIO:", usuario_id)
    print(" MINUTOS USADOS:", minutos_usados)
    print(" LIMITE:", limite.limite_minutos if limite else "no hay límite")

    if not limite:
        return jsonify({'alerta': False})


    if minutos_usados >= limite.limite_minutos:
        return jsonify({'alerta': True, 'mensaje': f' Has excedido tu límite diario para {limite.categoria.nombre}.'})

    elif minutos_usados >= 0.8 * limite.limite_minutos:
        return jsonify({'alerta': True, 'mensaje': f' Estás cerca de tu límite diario para {limite.categoria.nombre}.'})

    return jsonify({'alerta': False})

@bp.route('/api/alerta_dominio', methods=['POST', 'OPTIONS'])
@cross_origin(origins='*', methods=['POST', 'OPTIONS'], allow_headers='Content-Type')
def alerta_por_dominio():
    if request.method == 'OPTIONS':
        response = jsonify({'ok': True})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response


    data = request.get_json()
    dominio = data.get('dominio')
    usuario_id = 1 

    if not dominio or not usuario_id:
        return jsonify({"alerta": False, "error": "Faltan datos"}), 400

    categoria_result = db.session.execute(text("""
        SELECT categoria_id 
        FROM dominio_categoria 
        WHERE dominio = :dominio
    """), {"dominio": dominio}).fetchone()

    if not categoria_result:
        return jsonify({"alerta": False, "error": "Dominio sin categoría asociada"}), 404

    categoria_id = categoria_result.categoria_id

    resultado = db.session.execute(text("""
        SELECT 
            c.nombre AS categoria_nombre,
            SUM(r.tiempo) AS total, 
            lc.limite_minutos
        FROM registro r
        JOIN dominio_categoria dc ON r.dominio = dc.dominio
        JOIN categorias c ON dc.categoria_id = c.id
        LEFT JOIN limite_categoria lc 
            ON lc.categoria_id = c.id AND lc.usuario_id = :usuario_id
        WHERE r.usuario_id = :usuario_id 
          AND dc.categoria_id = :categoria_id
          AND DATE(r.fecha) = CURDATE()
        GROUP BY c.id, lc.limite_minutos
    """), {
        "usuario_id": usuario_id,
        "categoria_id": categoria_id
    }).fetchone()

    if resultado and resultado.total and resultado.limite_minutos is not None:
        minutos_usados = resultado.total / 60
        limite = resultado.limite_minutos
        categoria_nombre = resultado.categoria_nombre

        if minutos_usados >= limite:
            return jsonify({
                "alerta": True,
                "tipo": "exceso",
                "mensaje": f" Has superado tu límite diario de {limite} minutos en {categoria_nombre}.",
                "categoria_nombre": categoria_nombre
            })

        elif minutos_usados >= 0.8 * limite:
            return jsonify({
                "alerta": True,
                "tipo": "proximidad",
                "mensaje": f"Estás cerca de tu límite diario para {categoria_nombre}. Llevas {int(minutos_usados)} minutos.",
                "categoria_nombre": categoria_nombre
            })

    return jsonify({"alerta": False})


@bp.route('/exportar/datos', methods=['GET'])
def exportar_datos():
    if 'usuario_id' not in session:
        return jsonify({"error": "No autenticado"}), 401

    usuario_id = session['usuario_id']
    formato = request.args.get('formato', 'csv')  
    rango = request.args.get('rango', 'todo')      

    hoy = datetime.now().date()

    if rango == '3dias':
        fecha_min = hoy - timedelta(days=3)
    elif rango == '15dias':
        fecha_min = hoy - timedelta(days=15)
    elif rango == 'mes':
        fecha_min = hoy - timedelta(days=30)
    elif rango == '3meses':
        fecha_min = hoy - timedelta(days=90)
    else:
        fecha_min = None  

    query = Registro.query.filter_by(usuario_id=usuario_id)
    if fecha_min:
        query = query.filter(Registro.fecha >= fecha_min)

    registros = query.order_by(Registro.fecha.desc()).all()

    if formato == 'json':
        datos = [
            {
                "fecha": str(r.fecha),
                "dominio": r.dominio,
                "tiempo_min": r.tiempo
            }
            for r in registros
        ]
        return jsonify({
            "usuario_id": usuario_id,
            "rango": rango,
            "datos": datos
        })

    elif formato == 'csv':

            from io import StringIO
            salida_texto = StringIO()
            writer = csv.writer(salida_texto)
            writer.writerow(['Fecha', 'Dominio', 'Tiempo (min)'])
            for r in registros:
                writer.writerow([r.fecha, r.dominio, r.tiempo])

            salida_bytes = BytesIO()
            salida_bytes.write(salida_texto.getvalue().encode('utf-8'))
            salida_bytes.seek(0)

            nombre_archivo = f"registro_{rango}_{datetime.now().strftime('%Y%m%d')}.csv"
            return send_file(
            salida_bytes,
            mimetype='text/csv',
            as_attachment=True,
            download_name=nombre_archivo
        )

    else:
        return jsonify({"error": "Formato no válido"}), 400

@bp.route('/api/logros')
def obtener_logros_usuario():
    if 'usuario_id' not in session:
        print(" Sesión no activa para /admin/api/logros")
        return jsonify([])

    usuario_id = session['usuario_id']
    conexion = get_mysql()
    with conexion.cursor(dictionary=True) as cursor:
        cursor.execute("""
            SELECT l.id, l.nombre, l.descripcion, l.nivel, l.imagen_url,
            (ul.id IS NOT NULL) AS desbloqueado

            FROM logros l
            LEFT JOIN usuario_logro ul ON l.id = ul.logro_id AND ul.usuario_id = %s
        """, (usuario_id,))
        logros = cursor.fetchall()

    for logro in logros:
        logro["imagen_url"] = url_for('static', filename='icons/logro.png')
    

    return jsonify(logros)

@bp.route('/api/estado_rachas')
def estado_rachas():
    if 'usuario_id' not in session:
        return jsonify({"error": "No autenticado"}), 401

    usuario_id = session['usuario_id']
    conexion = get_mysql()
    with conexion.cursor(dictionary=True) as cursor:
        cursor.execute("""
            SELECT tipo, dias_consecutivos, activa FROM rachas_usuario
            WHERE usuario_id = %s
        """, (usuario_id,))
        rachas = cursor.fetchall()

    return jsonify({r['tipo']: {"activa": r['activa'], "dias": r['dias_consecutivos']} for r in rachas})

@bp.route('/guardar', methods=['POST'])
@cross_origin(origins='*', methods=['POST'])
def guardar_dominio():
    try:
        dominio = (request.form.get('dominio') or '').strip()
        tiempo  = int(request.form.get('tiempo') or 0)
        usuario_id = request.form.get('usuario_id') or session.get('usuario_id')

        if not dominio or not tiempo or not usuario_id:
            return jsonify({"error": "Faltan datos"}), 400

        fh_raw = request.form.get('fecha_hora')  
        fh = None
        if fh_raw:
            try:

                fh = datetime.fromisoformat(fh_raw.replace('Z', '+00:00'))
                if fh.tzinfo:
                    fh = fh.astimezone().replace(tzinfo=None)
            except Exception:
                fh = None
        if fh is None:
            fh = datetime.now()  

        conexion = get_mysql()
        with conexion.cursor() as cursor:

            cursor.execute("SELECT categoria_id FROM dominio_categoria WHERE dominio = %s", (dominio,))
            row = cursor.fetchone()

            if row:
                categoria_id = row[0]
            else:
                categoria_id = clasificar_dominio_automatico(dominio)


            cursor.execute("""
                INSERT INTO registro (usuario_id, dominio, tiempo, fecha, fecha_hora)
                VALUES (%s, %s, %s, %s, %s)
            """, (usuario_id, dominio, tiempo, fh.date(), fh))
            conexion.commit()

        print(f"[✔] /guardar dominio={dominio} tiempo={tiempo}s usuario={usuario_id} fecha_hora={fh}")
        return jsonify({"ok": True})

    except Exception as e:
        try:
            conexion.rollback()
        except Exception:
            pass
        print("Error en /guardar:", e)
        return jsonify({"error": "Error al guardar"}), 500

import traceback

@bp.route('/dashboard_ml')
def dashboard_ml():
    """Dashboard de métricas ML"""
    if 'usuario_id' not in session:
        return redirect('/login')
    
    return render_template('dashboard_ml.html')

@bp.route("/registro", methods=["POST"])
def registro():
    """
    Registro de usuario con perfil inicial
    Guarda datos manuales + hace inferencia inicial
    """
    try:
        data = request.get_json() or {}
        print(" [REGISTRO] DATA RECIBIDA:", data)

        nombre = data.get("nombre")
        correo = data.get("correo")
        contrasena = data.get("contrasena")
        dedicacion = data.get("dedicacion")
        horario = data.get("horario")
        dias_trabajo = data.get("dias_trabajo")

        if not nombre or not correo or not contrasena:
            print(" [REGISTRO] Faltan campos obligatorios")
            return jsonify(success=False, message="Nombre, correo y contraseña son obligatorios."), 400

        from app.models.models import Usuario
        existente = Usuario.query.filter_by(correo=correo).first()
        if existente:
            print(f" [REGISTRO] Ya existe usuario: {correo}")
            return jsonify(success=False, message="Ya existe un usuario con ese correo."), 400

        nuevo_usuario = Usuario(
            nombre=nombre,
            correo=correo,
            dedicacion=dedicacion,
            horario_preferido=horario,
            dias_trabajo=dias_trabajo
        )
        nuevo_usuario.set_password(contrasena)
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        print(f" [REGISTRO] Usuario creado: {correo} (ID: {nuevo_usuario.id})")
        
        # Inferir tipo inicial basado en dedicación manual
        if dedicacion:
            tipo_inicial = _inferir_tipo_desde_dedicacion(dedicacion)
            nuevo_usuario.tipo_inferido = tipo_inicial
            nuevo_usuario.confianza_inferencia = 0.5  # Baja confianza inicial
            db.session.commit()
            print(f" [PERFIL] Tipo inicial inferido: {tipo_inicial}")

        return jsonify(success=True, message="Registro exitoso.", usuario_id=nuevo_usuario.id), 201

    except Exception as e:
        print(f" [REGISTRO] ERROR:", e)
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify(success=False, message=f"Error interno: {str(e)}"), 500


def _inferir_tipo_desde_dedicacion(dedicacion: str) -> str:
    """
    Convierte la dedicación manual a tipo inferido
    """
    mapping = {
        'estudiante': 'estudiante',
        'trabajador': 'trabajador',
        'freelancer': 'mixto',
        'emprendedor': 'mixto',
        'otro': 'mixto'
    }
    return mapping.get(dedicacion, 'mixto')

@bp.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for("app_base.login"))

"""
"ATENCION, ESTE ENDPOINT FUNCIONA, SIN EMBARGO POR MEJORAS EN EL SISTEMA, SE ENCUENTRA SUSPENDIDO
EN CASO DE QUE EL ENDPOINT API/ML/PREDICT_MULTI NO FUNCIONE, USAR ESTE ENDPOINT, AMBOS CUMPLEN CON
LA FUNCION DE SUGRERIR METAS, SIN EMBARGO EL COACH TRABAJA DE FORMA 'INTELIGENTE'POR LO QUE SU IMPLEMENTACION
PRETENDE SER MAS EFECTIVA Y PERSONALIZADA"


@bp.route('/api/sugerencias', methods=['GET'])
def sugerencias():

    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return jsonify({"error": "Usuario no autenticado"}), 401

    dias_uso = obtener_dias_uso(usuario_id)
    nivel_confianza = calcular_nivel_confianza(dias_uso)

    if nivel_confianza == "insuficiente":
        return jsonify({
            "mensaje": "Aún no hay datos suficientes para sugerencias.",
            "nivel_confianza": nivel_confianza
        })

    sugerencias_resultado = []
    categorias = Categoria.query.all()

    for cat in categorias:
        promedio = obtener_promedio_categoria(usuario_id, cat.id)
        if promedio == 0:
            continue

        sugerencia_meta, sugerencia_limite = calcular_sugerencias_por_categoria(cat, promedio)

        sugerencias_resultado.append({
            "categoria_id": cat.id,
            "categoria_nombre": cat.nombre,
            "sugerencia_meta": sugerencia_meta,
            "sugerencia_limite": sugerencia_limite,
            "nivel_confianza": nivel_confianza
        })

    LIMITE_DIARIO = 1440
    total_sugerido = sum(s["sugerencia_meta"] for s in sugerencias_resultado)
    if total_sugerido > LIMITE_DIARIO:
        for s in sugerencias_resultado:
            proporcion = s["sugerencia_meta"] / total_sugerido
            s["sugerencia_meta"] = int(proporcion * LIMITE_DIARIO)

    return jsonify(sugerencias_resultado)"""

@bp.route("/admin/api/features_hoy", methods=["GET"])
def api_features_hoy():
    """
    Devuelve features diarias y horarias para un usuario y fecha.
    Parámetros:
      - usuario_id (opcional): si no viene, toma session['usuario_id']
      - fecha (opcional): YYYY-MM-DD, default = hoy MX
      - recalcular=1 (opcional): ejecuta calcular_persistir_features antes de leer
    """
    tz = ZoneInfo("America/Mexico_City")
    hoy_mx = datetime.now(tz).date()

    usuario_id = request.args.get("usuario_id", type=int) or session.get("usuario_id", 1)
    fecha_str = request.args.get("fecha")
    recalcular = request.args.get("recalcular", "0") == "1"

    try:
        f = date.fromisoformat(fecha_str) if fecha_str else hoy_mx
    except Exception:
        return jsonify({"ok": False, "error": "fecha inválida (usa YYYY-MM-DD)"}), 400

    if recalcular:
        try:
            calcular_persistir_features(usuario_id=usuario_id, dia=f)
        except Exception as e:
            return jsonify({"ok": False, "error": f"error recalculando features: {e}"}), 500


    diarias_q = (FeatureDiaria.query
                 .filter_by(usuario_id=usuario_id, fecha=f)
                 .order_by(FeatureDiaria.categoria.asc()))
    diarias = [{"categoria": x.categoria, "minutos": int(x.minutos)} for x in diarias_q.all()]


    horarias_q = (FeatureHoraria.query
                  .filter_by(usuario_id=usuario_id, fecha=f)
                  .order_by(FeatureHoraria.hora.asc(), FeatureHoraria.categoria.asc()))
    horarias = [{"categoria": x.categoria, "hora": int(x.hora), "minutos": int(x.minutos)} for x in horarias_q.all()]

    total_minutos = sum(d["minutos"] for d in diarias)


    categorias = sorted({d["categoria"] for d in diarias})
    horas = list(range(24))

    mapa_h = {(h["categoria"], h["hora"]): h["minutos"] for h in horarias}
    series_horarias = [
        {
            "categoria": cat,
            "datos": [mapa_h.get((cat, h), 0) for h in horas]
        }
        for cat in categorias
    ]

    return jsonify({
        "ok": True,
        "usuario_id": usuario_id,
        "fecha": f.isoformat(),
        "diarias": diarias,
        "horarias": horarias,
        "total_minutos": int(total_minutos),
        "categorias": categorias,
        "horas": horas,
        "series_horarias": series_horarias
    })

@bp.route('/api/features_estado', methods=['GET'])
def features_estado():
    usuario_id = int(request.args.get("usuario_id", 1))
    d = date.fromisoformat(request.args.get("dia", date.today().isoformat()))
    fd = FeatureDiaria.query.filter_by(usuario_id=usuario_id, fecha=d).count()
    fh = FeatureHoraria.query.filter_by(usuario_id=usuario_id, fecha=d).count()
    return jsonify({
        "usuario_id": usuario_id,
        "dia": d.isoformat(),
        "diarias_count": fd,
        "horarias_count": fh
    })

@bp.route('/api/features_health', methods=['GET'])
def features_health():
    try:
        sched = get_scheduler()
        jobs = []
        for j in sched.get_jobs():
            jobs.append({
                "id": j.id,
                "next_run_time": j.next_run_time.isoformat() if j.next_run_time else None,
                "trigger": str(j.trigger)
            })
        tz = current_app.config.get("TZ", "America/Mexico_City")
        return jsonify({"jobs": jobs, "tz": tz})
    except Exception as e:
        return jsonify({"jobs": [], "tz": current_app.config.get("TZ", "America/Mexico_City"),
                        "warning": f"scheduler no disponible: {type(e).__name__}"}), 200

@bp.route('/api/features_qa', methods=['GET'])
def features_qa():
    usuario_id = int(request.args.get("usuario_id", 1))
    d = date.fromisoformat(request.args.get("dia", date.today().isoformat()))
    res = _qa_invariantes_dia(usuario_id, d)
    return jsonify(res)

@bp.route("/admin/api/coach/alertas")
def coach_alertas_list():
    if "usuario_id" not in session:
        return jsonify({"error": "No autenticado"}), 401
    usuario_id = session["usuario_id"]
    fecha = request.args.get("fecha")
    desde = request.args.get("desde")
    hasta = request.args.get("hasta")
    q = CoachAlerta.query.filter_by(usuario_id=usuario_id)
    if fecha:
        q = q.filter(CoachAlerta.fecha == fecha)
    elif desde and hasta:
        q = q.filter(CoachAlerta.fecha >= desde, CoachAlerta.fecha <= hasta)
    q = q.order_by(CoachAlerta.fecha.desc(), CoachAlerta.creado_en.desc())
    data = [{
        "fecha": str(r.fecha),
        "categoria": r.categoria,
        "regla": r.regla,
        "nivel": r.nivel,
        "detalle": r.detalle,
        "creado_en": r.creado_en.isoformat()
    } for r in q.limit(200).all()]

    return jsonify({"usuario_id": usuario_id, "alertas": data})

@bp.route("/admin/api/coach/generar_alertas", methods=["POST"])
def coach_alertas_run():
    if "usuario_id" not in session:
        return jsonify({"error": "No autenticado"}), 401
    usuario_id = session["usuario_id"]
    job_coach_alertas(current_app, usuario_id)
    return jsonify({"ok": True})

