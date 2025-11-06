"""
Controlador para sistema de anomalías
"""
from flask import Blueprint, request, jsonify, session
from datetime import date, timedelta, datetime
from app.extensions import db
from app.models.models import ContextoDia
from app.services.detector_anomalias import detectar_anomalia_dia, guardar_anomalia

bp = Blueprint('anomalias', __name__, url_prefix='/api/anomalias')

@bp.route('/detectar', methods=['GET'])
def detectar():
    """Detecta anomalías de días recientes para el usuario actual"""
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return jsonify({'error': 'No autenticado'}), 401
    
    # Detectar últimos 7 días
    anomalias = []
    for i in range(1, 8):
        fecha = date.today() - timedelta(days=i)
        deteccion = detectar_anomalia_dia(usuario_id, fecha)
        
        if deteccion['es_atipico']:
            # Verificar si ya tiene motivo guardado
            contexto = ContextoDia.query.filter_by(
                usuario_id=usuario_id,
                fecha=fecha
            ).first()
            
            anomalias.append({
                'fecha': fecha.isoformat(),
                'uso_real': deteccion['uso_real'],
                'uso_esperado': deteccion['uso_esperado'],
                'desviacion_pct': deteccion['desviacion_pct'],
                'tiene_motivo': bool(contexto and contexto.motivo)
            })
    
    return jsonify({
        'anomalias': anomalias,
        'total': len(anomalias)
    })


@bp.route('/guardar-motivo', methods=['POST'])
def guardar_motivo():
    """Guarda el motivo explicado por el usuario para una anomalía"""
    try:
        usuario_id = session.get('usuario_id')
        if not usuario_id:
            return jsonify({'error': 'No autenticado'}), 401
        
        data = request.json
        fecha_str = data.get('fecha')
        motivo = data.get('motivo')
        detalle = data.get('detalle', '')
        
        if not fecha_str or not motivo:
            return jsonify({'error': 'Faltan datos requeridos'}), 400
        
        # Convertir fecha
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Formato de fecha inválido'}), 400
        
        # Buscar contexto existente
        contexto = ContextoDia.query.filter_by(
            usuario_id=usuario_id,
            fecha=fecha
        ).first()
        
        if not contexto:
            return jsonify({'error': 'Anomalía no encontrada'}), 404
        
        # Actualizar motivo
        contexto.motivo = motivo
        contexto.motivo_detalle = detalle if detalle else None
        
        db.session.commit()
        
        print(f"[ANOMALÍA] Motivo guardado: usuario={usuario_id}, fecha={fecha}, motivo={motivo}")
        
        return jsonify({
            'success': True,
            'mensaje': 'Motivo guardado correctamente'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"[ANOMALÍA][ERROR] al guardar motivo: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
@bp.route('/pendientes', methods=['GET'])
def pendientes():
    """Obtiene anomalías sin motivo explicado"""
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return jsonify({'error': 'No autenticado'}), 401
    
    # Buscar anomalías sin motivo de los últimos 7 días
    fecha_limite = date.today() - timedelta(days=7)
    
    pendientes = ContextoDia.query.filter(
        ContextoDia.usuario_id == usuario_id,
        ContextoDia.es_atipico == True,
        ContextoDia.motivo == None,
        ContextoDia.fecha >= fecha_limite
    ).order_by(
        ContextoDia.fecha.desc()
    ).all()
    
    return jsonify({
        'pendientes': [{
            'fecha': c.fecha.isoformat(),
            'uso_real': c.uso_real_min,
            'uso_esperado': c.uso_esperado_min,
            'desviacion_pct': c.desviacion_pct
        } for c in pendientes],
        'total': len(pendientes)
    })
