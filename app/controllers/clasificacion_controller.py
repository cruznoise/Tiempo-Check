"""
Controller para sistema de feedback de clasificaciones
"""
from flask import Blueprint, jsonify, request, session
from app.models.models_coach import NotificacionClasificacion
from app.models.models import Categoria, DominioCategoria
from app import db
from datetime import datetime

bp = Blueprint('clasificacion', __name__, url_prefix='/api/clasificacion')

@bp.route('/pendientes', methods=['GET'])
def obtener_pendientes():
    """Obtiene notificaciones pendientes de confirmación - SOLO del usuario actual"""
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autenticado', 'pendientes': [], 'total': 0}), 401
    
    usuario_id = session['usuario_id']
    
    pendientes = NotificacionClasificacion.query.filter_by(
        usuario_id=usuario_id,
        status='pendiente'
    ).order_by(NotificacionClasificacion.creado_en.desc()).limit(20).all()
    
    categorias = {c.id: c.nombre for c in Categoria.query.filter_by(usuario_id=usuario_id).all()}
    
    return jsonify({
        'pendientes': [{
            'id': p.id,
            'dominio': p.dominio,
            'categoria_sugerida': categorias.get(p.categoria_sugerida_id, 'Desconocida'),
            'categoria_sugerida_id': p.categoria_sugerida_id,
            'confianza': p.confianza,
            'metodo': p.metodo,
            'creado_en': p.creado_en.isoformat()
        } for p in pendientes],
        'total': len(pendientes)
    })


@bp.route('/confirmar/<int:notif_id>', methods=['POST'])
def confirmar_clasificacion(notif_id):
    """Usuario confirma que la clasificación es correcta"""
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    
    usuario_id = session['usuario_id']
    notif = NotificacionClasificacion.query.filter_by(
        id=notif_id,
        usuario_id=usuario_id
    ).first()
    
    if not notif:
        return jsonify({'error': 'No encontrada'}), 404
    
    notif.status = 'confirmado'
    notif.respondido_en = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'mensaje': 'Clasificación confirmada'
    })


@bp.route('/rechazar/<int:notif_id>', methods=['POST'])
def rechazar_clasificacion(notif_id):
    """Usuario rechaza y corrige la clasificación"""
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    
    usuario_id = session['usuario_id']
    data = request.json
    categoria_correcta_id = data.get('categoria_correcta_id')
    
    if not categoria_correcta_id:
        return jsonify({'error': 'Falta categoria_correcta_id'}), 400
    
    notif = NotificacionClasificacion.query.filter_by(
        id=notif_id,
        usuario_id=usuario_id
    ).first()
    
    if not notif:
        return jsonify({'error': 'No encontrada'}), 404
    
    categoria = Categoria.query.filter_by(
        id=categoria_correcta_id,
        usuario_id=usuario_id
    ).first()
    
    if not categoria:
        return jsonify({'error': 'Categoría no válida'}), 400
    
    notif.status = 'rechazado'
    notif.categoria_correcta_id = categoria_correcta_id
    notif.respondido_en = datetime.utcnow()
    
    dominio_cat = DominioCategoria.query.filter_by(
        dominio=notif.dominio,
        usuario_id=usuario_id
    ).first()
    
    if dominio_cat:
        dominio_cat.categoria_id = categoria_correcta_id
        dominio_cat.categoria = categoria.nombre
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'mensaje': 'Clasificación corregida'
    })


@bp.route('/clasificar_manual/<int:notif_id>', methods=['POST'])
def clasificar_manual(notif_id):
    """
    Usuario clasifica manualmente un sitio que el sistema no pudo clasificar
    """
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    
    usuario_id = session['usuario_id']
    data = request.json
    categoria_correcta_id = data.get('categoria_correcta_id')
    
    if not categoria_correcta_id:
        return jsonify({'error': 'Falta categoria_correcta_id'}), 400
    
    notif = NotificacionClasificacion.query.filter_by(
        id=notif_id,
        usuario_id=usuario_id
    ).first()
    
    if not notif:
        return jsonify({'error': 'No encontrada'}), 404
    
    categoria = Categoria.query.filter_by(
        id=categoria_correcta_id,
        usuario_id=usuario_id
    ).first()
    
    if not categoria:
        return jsonify({'error': 'Categoría no válida'}), 400
    
    notif.status = 'clasificado_manual'
    notif.categoria_correcta_id = categoria_correcta_id
    notif.respondido_en = datetime.utcnow()
    
    dominio_cat = DominioCategoria.query.filter_by(
        dominio=notif.dominio,
        usuario_id=usuario_id
    ).first()
    
    if dominio_cat:
        dominio_cat.categoria_id = categoria_correcta_id
        dominio_cat.categoria = categoria.nombre
        print(f"[CLASIFICACIÓN MANUAL]  {notif.dominio} → {categoria.nombre} (usuario {usuario_id})")
    else:
        print(f"[CLASIFICACIÓN MANUAL]  Dominio no encontrado: {notif.dominio} (usuario {usuario_id})")
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'mensaje': 'Sitio clasificado correctamente. ¡Gracias por tu ayuda!'
    })