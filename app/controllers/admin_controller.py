from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash, current_app
from flask_login import login_required
from flask_cors import cross_origin
from datetime import date
from sqlalchemy import text
from app.db import db
from app.models.models import Registro, DominioCategoria, Categoria, LimiteCategoria, MetaCategoria, Usuario
from collections import defaultdict


admin_controller = Blueprint('admin_controller', __name__, url_prefix='/admin')

@admin_controller.route('/categorias', methods=['GET'])
def vista_categorias():
    categorias = Categoria.query.all()
    dominios = DominioCategoria.query.all()
    return render_template('admin/categorias.html', categorias=categorias, dominios=dominios)

@admin_controller.route('/categorias', methods=['POST'])
def agregar_categoria():
    nombre = request.form.get('nombre')
    if nombre:
        nueva = Categoria(nombre=nombre)
        db.session.add(nueva)
        db.session.commit()
        flash('Categoría agregada correctamente')
    return redirect(url_for('admin_controller.vista_categorias'))

@admin_controller.route('/dominios', methods=['POST'])
def agregar_dominio():
    dominio = request.form.get('dominio')
    categoria_id = request.form.get('categoria_id')
    if dominio and categoria_id:
        nuevo = DominioCategoria(dominio=dominio, categoria_id=int(categoria_id))
        db.session.add(nuevo)
        db.session.commit()
        flash('Dominio agregado correctamente')
    return redirect(url_for('admin_controller.vista_categorias'))

@admin_controller.route('/categorias/eliminar/<int:id>', methods=['POST'])
def eliminar_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    db.session.delete(categoria)
    db.session.commit()
    flash('Categoría eliminada')
    return redirect(url_for('admin_controller.vista_categorias'))

@admin_controller.route('/dominios/eliminar/<int:id>', methods=['POST'])
def eliminar_dominio(id):
    dominio = DominioCategoria.query.get_or_404(id)
    db.session.delete(dominio)
    db.session.commit()
    flash('Dominio eliminado')
    return redirect(url_for('admin_controller.vista_categorias'))

@admin_controller.route('/categorias/editar/<int:id>', methods=['POST'])
def editar_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    nuevo_nombre = request.form.get('nuevo_nombre')
    if nuevo_nombre:
        categoria.nombre = nuevo_nombre
        db.session.commit()
        flash('Categoría actualizada')
    return redirect(url_for('admin_controller.vista_categorias'))

@admin_controller.route('/dominios/editar/<int:id>', methods=['POST'])
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


@admin_controller.route('/metas')
def vista_metas():
    if 'usuario_id' not in session:
        return redirect(url_for('controlador.login'))

    usuario_id = session['usuario_id']

    # Traer categorías
    categorias = db.session.query(Categoria).all()

    # Traer metas establecidas
    metas = db.session.query(MetaCategoria).filter_by(usuario_id=usuario_id).all()

    # Traer límites establecidos
    limites = db.session.query(LimiteCategoria).filter_by(usuario_id=usuario_id).all()

    # Calcular uso actual por categoría (hoy)
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
        uso_actual[categoria_id] = round(total / 60)  # en minutos

    # Estado de metas
    estado_metas = []
    for m in metas:
        nombre = next((c.nombre for c in categorias if c.id == m.categoria_id), 'Desconocida')
        usado = uso_actual.get(m.categoria_id, 0)
        cumplida = usado >= m.limite_minutos
        estado_metas.append({
            'categoria': nombre,
            'meta': m.limite_minutos,
            'usado': usado,
            'cumplida': cumplida
        })

    # Estado de límites
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


@admin_controller.route('/metas', methods=['POST'])
def agregar_meta():
    usuario_id = request.form.get('usuario_id')
    categoria_id = request.form.get('categoria_id')
    limite_minutos = request.form.get('limite_minutos')

    if usuario_id and categoria_id and limite_minutos:
        nueva = MetaCategoria(
            usuario_id=int(usuario_id),
            categoria_id=int(categoria_id),
            limite_minutos=int(limite_minutos)
        )
        db.session.add(nueva)
        db.session.commit()
        flash('Meta agregada correctamente')
    
    return redirect(url_for('admin_controller.vista_metas'))

@admin_controller.route('/metas/eliminar/<int:id>', methods=['POST'])
def eliminar_meta(id):
    meta = MetaCategoria.query.get_or_404(id)
    db.session.delete(meta)
    db.session.commit()
    flash('Meta eliminada')
    return redirect(url_for('admin_controller.vista_metas'))

@admin_controller.route('/metas/editar/<int:id>', methods=['POST'])
def editar_meta(id):
    meta = MetaCategoria.query.get_or_404(id)
    nuevo_limite = request.form.get('limite_minutos')

    if nuevo_limite:
        meta.limite_minutos = int(nuevo_limite)
        db.session.commit()
        flash('Meta actualizada')

    return redirect(url_for('admin_controller.vista_metas'))

@admin_controller.route('/limites')
def vista_limites():
    if 'usuario_id' not in session:
        return redirect(url_for('controlador.login'))

    usuario_id = session['usuario_id']

    categorias = Categoria.query.all()
    limites = db.session.query(LimiteCategoria).all()


    # Uso actual por categoría (solo hoy)
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
        uso_actual[categoria_id] = round(total / 60)  # minutos

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

@admin_controller.route('/agregar_limite', methods=['POST'])
def agregar_limite():
    try:
        usuario_id = request.form.get('usuario_id')  # <- CAMBIO AQUÍ
        categoria_id = request.form['categoria_id']
        limite_minutos = int(request.form['limite_minutos'])

        nuevo = LimiteCategoria(
            usuario_id=usuario_id,
            categoria_id=categoria_id,
            limite_minutos=limite_minutos
        )
        db.session.add(nuevo)
        db.session.commit()
        flash("✅ Límite agregado correctamente.")
    except Exception as e:
        print("Error al agregar límite:", e)
        flash("❌ Error al agregar límite.")

    return redirect(url_for('admin_controller.vista_metas'))


@admin_controller.route('/editar_limite/<int:id>', methods=['POST'])
def editar_limite(id):
    try:
        nuevo_limite = int(request.form['limite_minutos'])
        limite = LimiteCategoria.query.get(id)
        if limite:
            limite.limite_minutos = nuevo_limite
            db.session.commit()
            flash("✏️ Límite actualizado.")
        else:
            flash("❌ Límite no encontrado.")
    except Exception as e:
        print("Error al editar límite:", e)
        flash("❌ Error al editar límite.")

    return redirect(url_for('admin_controller.vista_metas'))
@admin_controller.route('/eliminar_limite/<int:id>', methods=['POST'])
def eliminar_limite(id):
    try:
        limite = LimiteCategoria.query.get(id)
        if limite:
            db.session.delete(limite)
            db.session.commit()
            flash("🗑️ Límite eliminado.")
        else:
            flash("❌ Límite no encontrado.")
    except Exception as e:
        print("Error al eliminar límite:", e)
        flash("❌ Error al eliminar límite.")

    return redirect(url_for('admin_controller.vista_metas'))

@admin_controller.route('/api/categorias_usuario')
def categorias_usuario():
    if 'usuario_id' not in session:
        return jsonify([])
    usuario_id = session['usuario_id']
    categorias = db.session.query(Categoria.id, Categoria.nombre).all()
    return jsonify([{'id': c.id, 'nombre': c.nombre} for c in categorias])

@admin_controller.route('/api/alerta_categoria', methods=['POST', 'OPTIONS'])
@cross_origin(origins='*', methods=['POST', 'OPTIONS'], allow_headers='Content-Type')
def verificar_alerta_categoria():
    print("⚠️ SESSION:", session)
    if 'usuario_id' not in session:
        print("❌ No hay usuario en sesión")
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

    print("🧪 CATEGORIA:", categoria_id)
    print("🧪 USUARIO:", usuario_id)
    print("🧪 MINUTOS USADOS:", minutos_usados)
    print("🧪 LIMITE:", limite.limite_minutos if limite else "no hay límite")

    if not limite:
        return jsonify({'alerta': False})


    if minutos_usados >= limite.limite_minutos:
        return jsonify({'alerta': True, 'mensaje': f'🚨 Has excedido tu límite diario para {limite.categoria.nombre}.'})

    elif minutos_usados >= 0.8 * limite.limite_minutos:
        return jsonify({'alerta': True, 'mensaje': f'⚠️ Estás cerca de tu límite diario para {limite.categoria.nombre}.'})

    return jsonify({'alerta': False})

@admin_controller.route('/api/alerta_dominio', methods=['POST', 'OPTIONS'])
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
    usuario_id = 1  # session.get('usuario_id')

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
                "mensaje": f"🚨 Has superado tu límite diario de {limite} minutos en {categoria_nombre}.",
                "categoria_nombre": categoria_nombre
            })

        elif minutos_usados >= 0.8 * limite:
            return jsonify({
                "alerta": True,
                "tipo": "proximidad",
                "mensaje": f"⚠️ Estás cerca de tu límite diario para {categoria_nombre}. Llevas {int(minutos_usados)} minutos.",
                "categoria_nombre": categoria_nombre
            })

    return jsonify({"alerta": False})