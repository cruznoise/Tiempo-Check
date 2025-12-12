"""
Controller para sistema de feedback de clasificaciones
"""
from flask import Blueprint, jsonify, request, session
from app.models.models_coach import NotificacionClasificacion
from app.models.models import Categoria, DominioCategoria
from app import db
from datetime import datetime

bp = Blueprint('clasificacion', __name__, url_prefix='/api/clasificacion')

def get_usuario_id():
    """
    Obtiene usuario_id desde session o header X-Usuario-ID
    Útil para requests desde extensión Chrome
    """
    # Prioridad 1: Session (dashboard web)
    usuario_id = session.get('usuario_id')
    
    # Prioridad 2: Header (extensión Chrome)
    if not usuario_id:
        usuario_id = request.headers.get('X-Usuario-ID')
        if usuario_id:
            try:
                usuario_id = int(usuario_id)
            except (ValueError, TypeError):
                return None
    
    return usuario_id

@bp.route('/pendientes', methods=['GET'])
def obtener_pendientes():
    """Obtiene notificaciones pendientes de confirmación"""
    usuario_id = get_usuario_id()
    if not usuario_id:
        return jsonify({'error': 'No autenticado'}), 401
    
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
    usuario_id = get_usuario_id()
    if not usuario_id:
        return jsonify({'error': 'No autenticado'}), 401
    
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
    usuario_id = get_usuario_id()
    if not usuario_id:
        return jsonify({'error': 'No autenticado'}), 401
    
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
    
    try:
        dominio_cat = DominioCategoria.query.filter_by(
            dominio=notif.dominio,
            usuario_id=usuario_id
        ).first()
        
        if dominio_cat:
            dominio_cat.categoria_id = categoria_correcta_id
        else:
            dominio_cat = DominioCategoria(
                dominio=notif.dominio,
                usuario_id=usuario_id,
                categoria_id=categoria_correcta_id,
                categoria='Sin categoría'
            )
            db.session.add(dominio_cat)
        
        db.session.commit()
        print(f"[CLASIFICACIÓN]  {notif.dominio} → categoría {categoria_correcta_id} (usuario {usuario_id})")
        
    except Exception as e:
        print(f"[CLASIFICACIÓN][ERROR] {e}")
        db.session.rollback()
    
    return jsonify({
        'success': True,
        'mensaje': 'Clasificación corregida'
    })


@bp.route('/clasificar_manual/<int:notif_id>', methods=['POST'])
def clasificar_manual(notif_id):
    """
    Usuario clasifica manualmente un sitio que el sistema no pudo clasificar
    """
    usuario_id = get_usuario_id()
    if not usuario_id:
        return jsonify({'error': 'No autenticado'}), 401
    
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
    
    notif.status = 'clasificado_manual'
    notif.categoria_correcta_id = categoria_correcta_id
    notif.respondido_en = datetime.utcnow()
    
    try:
        dominio_cat = DominioCategoria.query.filter_by(
            dominio=notif.dominio,
            usuario_id=usuario_id
        ).first()
        
        if dominio_cat:
            dominio_cat.categoria_id = categoria_correcta_id
        else:
            dominio_cat = DominioCategoria(
                dominio=notif.dominio,
                usuario_id=usuario_id,
                categoria_id=categoria_correcta_id,
                categoria='Sin categoría'
            )
            db.session.add(dominio_cat)
        
        db.session.commit()
        print(f"[CLASIFICACIÓN MANUAL] {notif.dominio} → categoría {categoria_correcta_id} (usuario {usuario_id})")
        
    except Exception as e:
        print(f"[CLASIFICACIÓN MANUAL][ERROR] {e}")
        db.session.rollback()
    
    return jsonify({
        'success': True,
        'mensaje': 'Sitio clasificado correctamente. ¡Gracias por tu ayuda!'
    })


@bp.route('/verificar-dominio', methods=['POST'])
def verificar_dominio_clasificacion():
    """
    Verifica si un dominio específico tiene notificación pendiente
    Usado por content_script.js para mostrar modal en el sitio
    """
    try:
        usuario_id = get_usuario_id()
        if not usuario_id:
            return jsonify({'error': 'No autenticado'}), 401
        
        data = request.get_json()
        dominio = data.get('dominio', '').strip()
        
        if not dominio:
            return jsonify({'necesita_clasificacion': False})
        
        notif = NotificacionClasificacion.query.filter_by(
            usuario_id=usuario_id,
            dominio=dominio,
            status='pendiente'
        ).first()
        
        if not notif:
            return jsonify({'necesita_clasificacion': False})
        
        categoria_sugerida = None
        if notif.categoria_sugerida_id:
            cat = Categoria.query.get(notif.categoria_sugerida_id)
            if cat:
                categoria_sugerida = cat.nombre
        
        return jsonify({
            'necesita_clasificacion': True,
            'notificacion_id': notif.id,
            'dominio': notif.dominio,
            'metodo': notif.metodo,
            'categoria_sugerida': categoria_sugerida,
            'confianza': notif.confianza if notif.confianza else 0,
            'creado_en': notif.creado_en.isoformat() if notif.creado_en else None
        })
        
    except Exception as e:
        print(f"[CLASIFICACIÓN][ERROR] verificar-dominio: {str(e)}")
        return jsonify({'error': str(e)}), 500


@bp.route('/categorias', methods=['GET'])
def listar_categorias_usuario():
    """
    Lista todas las categorías del usuario actual
    Usado para llenar selectores en modales
    """
    try:
        usuario_id = get_usuario_id()
        if not usuario_id:
            return jsonify({'error': 'No autenticado'}), 401
        
        categorias = Categoria.query.filter_by(usuario_id=usuario_id).all()
        
        return jsonify({
            'success': True,
            'categorias': [{
                'id': c.id,
                'nombre': c.nombre
            } for c in categorias]
        })
        
    except Exception as e:
        print(f"[CLASIFICACIÓN][ERROR] /categorias: {str(e)}")
        return jsonify({'error': str(e)}), 500