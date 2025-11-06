"""
Controller para sistema de feedback de clasificaciones
"""
from flask import Blueprint, jsonify, request, session
from app.models.models_coach import NotificacionClasificacion
from app.models.models import Categoria
from app import db
from datetime import datetime

bp = Blueprint('clasificacion', __name__, url_prefix='/api/clasificacion')

@bp.route('/pendientes', methods=['GET'])
def obtener_pendientes():
    """Obtiene notificaciones pendientes de confirmación"""
    usuario_id = session.get('usuario_id', 1)
    
    pendientes = NotificacionClasificacion.query.filter_by(
        usuario_id=usuario_id,
        status='pendiente'
    ).order_by(NotificacionClasificacion.creado_en.desc()).limit(20).all()
    
    categorias = {c.id: c.nombre for c in Categoria.query.all()}
    
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
    usuario_id = session.get('usuario_id', 1)
    
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
    usuario_id = session.get('usuario_id', 1)
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
    
    notif.status = 'rechazado'
    notif.categoria_correcta_id = categoria_correcta_id
    notif.respondido_en = datetime.utcnow()
    
    # Actualizar en dominio_categoria
    from app.utils import get_mysql
    conexion = get_mysql()
    with conexion.cursor() as cursor:
        cursor.execute("""
            UPDATE dominio_categoria 
            SET categoria_id = %s
            WHERE dominio = %s
        """, (categoria_correcta_id, notif.dominio))
        conexion.commit()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'mensaje': 'Clasificación corregida'
    })
@bp.route('/clasificar_manual/<int:notif_id>', methods=['POST'])
def clasificar_manual(notif_id):
    """
    Usuario clasifica manualmente un sitio que el sistema no pudo clasificar
    Similar a rechazar, pero para sitios sin clasificación inicial
    """
    usuario_id = session.get('usuario_id', 1)
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
    
    # Marcar como clasificado manualmente
    notif.status = 'clasificado_manual'  # Nuevo status
    notif.categoria_correcta_id = categoria_correcta_id
    notif.respondido_en = datetime.utcnow()
    
    # Actualizar en dominio_categoria
    from app.utils import get_mysql
    try:
        conexion = get_mysql()
        with conexion.cursor() as cursor:
            cursor.execute("""
                UPDATE dominio_categoria 
                SET categoria_id = %s
                WHERE dominio = %s
            """, (categoria_correcta_id, notif.dominio))
            conexion.commit()
            print(f"[CLASIFICACIÓN MANUAL] {notif.dominio} → categoría {categoria_correcta_id}")
    except Exception as e:
        print(f"[CLASIFICACIÓN MANUAL][ERROR] {e}")
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'mensaje': 'Sitio clasificado correctamente. ¡Gracias por tu ayuda!'
    })