"""
Detector de Días Atípicos
Identifica cuándo el uso del usuario se desvía significativamente de su patrón normal
"""
from datetime import date, timedelta
from sqlalchemy import func
from app import db
from app.models.models import Registro, ContextoDia

def detectar_anomalia_dia(usuario_id: int, fecha: date = None) -> dict:
    """
    Detecta si un día fue atípico comparando con el promedio del mismo día de semana
    
    Returns:
        {
            'es_atipico': bool,
            'uso_real': float (minutos),
            'uso_esperado': float (minutos),
            'desviacion_pct': float,
            'umbral': float
        }
    """
    if fecha is None:
        fecha = date.today()
    
    # Obtener uso del día en cuestión
    uso_dia = db.session.query(
        func.sum(Registro.tiempo) / 60.0
    ).filter(
        Registro.usuario_id == usuario_id,
        func.date(Registro.fecha) == fecha
    ).scalar() or 0.0
    
    # Obtener día de la semana (0=lunes, 6=domingo)
    dia_semana = fecha.weekday()
    
    # Calcular promedio histórico para este día de semana
    # (últimos 30 días, excluyendo el día actual)
    fecha_inicio = fecha - timedelta(days=30)
    
    uso_promedio = db.session.query(
        func.avg(func.sum(Registro.tiempo) / 60.0)
    ).filter(
        Registro.usuario_id == usuario_id,
        func.date(Registro.fecha) >= fecha_inicio,
        func.date(Registro.fecha) < fecha,
        func.dayofweek(Registro.fecha) == (dia_semana + 2) % 7 + 1  # MySQL DAYOFWEEK
    ).group_by(
        func.date(Registro.fecha)
    ).scalar() or 0.0
    
    # Si no hay suficiente historial, no es atípico
    if uso_promedio == 0:
        return {
            'es_atipico': False,
            'uso_real': uso_dia,
            'uso_esperado': 0,
            'desviacion_pct': 0,
            'umbral': 2.0
        }
    
    # Calcular desviación
    desviacion_pct = ((uso_dia - uso_promedio) / uso_promedio) * 100
    
    # Umbral: ±100% (el doble o la mitad)
    UMBRAL_PCT = 100
    
    es_atipico = abs(desviacion_pct) >= UMBRAL_PCT
    
    return {
        'es_atipico': es_atipico,
        'uso_real': round(uso_dia, 1),
        'uso_esperado': round(uso_promedio, 1),
        'desviacion_pct': round(desviacion_pct, 1),
        'umbral': UMBRAL_PCT
    }


def guardar_anomalia(usuario_id: int, fecha: date, deteccion: dict, motivo: str = None, detalle: str = None):
    """Guarda la detección de anomalía en la BD"""
    
    # Buscar si ya existe
    contexto = ContextoDia.query.filter_by(
        usuario_id=usuario_id,
        fecha=fecha
    ).first()
    
    if contexto:
        # Actualizar
        contexto.es_atipico = deteccion['es_atipico']
        contexto.uso_real_min = deteccion['uso_real']
        contexto.uso_esperado_min = deteccion['uso_esperado']
        contexto.desviacion_pct = deteccion['desviacion_pct']
        if motivo:
            contexto.motivo = motivo
        if detalle:
            contexto.motivo_detalle = detalle
    else:
        # Crear nuevo
        contexto = ContextoDia(
            usuario_id=usuario_id,
            fecha=fecha,
            es_atipico=deteccion['es_atipico'],
            uso_real_min=deteccion['uso_real'],
            uso_esperado_min=deteccion['uso_esperado'],
            desviacion_pct=deteccion['desviacion_pct'],
            motivo=motivo,
            motivo_detalle=detalle
        )
        db.session.add(contexto)
    
    db.session.commit()
    
    return contexto


def obtener_dias_atipicos(usuario_id: int, limit: int = 10):
    """Obtiene los últimos días atípicos del usuario"""
    return ContextoDia.query.filter_by(
        usuario_id=usuario_id,
        es_atipico=True
    ).order_by(
        ContextoDia.fecha.desc()
    ).limit(limit).all()
