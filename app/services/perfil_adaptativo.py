"""
Sistema de Inferencia Automática de Perfil de Usuario
Analiza patrones de uso para determinar tipo de usuario
"""
from datetime import date, timedelta, time
from app.models.models import Usuario, Registro
from app import db
from sqlalchemy import func
import numpy as np

def inferir_perfil_usuario(usuario_id: int, dias_minimos: int = 7):
    """
    Infiere automáticamente el perfil del usuario basado en sus patrones de uso
    
    Args:
        usuario_id: ID del usuario
        dias_minimos: Días mínimos de datos requeridos (default: 7)
    
    Returns:
        dict con perfil inferido o None si no hay suficientes datos
    """
    print(f" [PERFIL] Analizando usuario {usuario_id}...")
    
    # Obtener registros de últimos 30 días
    fecha_inicio = date.today() - timedelta(days=30)
    
    registros = Registro.query.filter(
        Registro.usuario_id == usuario_id,
        func.date(Registro.fecha_hora) >= fecha_inicio
    ).all()
    
    if len(registros) < dias_minimos:
        print(f" [PERFIL] Pocos datos: {len(registros)} registros < {dias_minimos} días mínimos")
        return None
    
    # Extraer patrones
    horas = [r.fecha_hora.hour for r in registros if r.fecha_hora]
    dias_semana = [r.fecha_hora.weekday() for r in registros if r.fecha_hora]  # 0=lun, 6=dom
    
    if not horas or not dias_semana:
        print(" [PERFIL] Sin datos de hora/día válidos")
        return None
    
    # ========================================================================
    # ANÁLISIS 1: Horario de Actividad
    # ========================================================================
    hora_pico_inicio = int(np.percentile(horas, 25))  # Cuartil inferior
    hora_pico_fin = int(np.percentile(horas, 75))    # Cuartil superior
    
    print(f" [PERFIL] Horario pico: {hora_pico_inicio}:00 - {hora_pico_fin}:00")

    # ========================================================================
    # ANÁLISIS 2: Días Activos
    # ========================================================================
    from collections import Counter
    dias_frecuentes = [dia for dia, count in Counter(dias_semana).items() 
                      if count > len(registros) * 0.15]  # >15% de registros
    dias_frecuentes.sort()
    
    es_laboral = set(dias_frecuentes).issubset({0, 1, 2, 3, 4})  # Solo lun-vie
    es_fin_semana = any(d in dias_frecuentes for d in [5, 6])
    
    print(f" [PERFIL] Días activos: {dias_frecuentes} (lun=0, dom=6)")
    
    # ========================================================================
    # ANÁLISIS 3: Inferir Tipo de Usuario
    # ========================================================================
    tipo_inferido = 'mixto'
    confianza = 0.6
    
    # Reglas de inferencia
    if es_laboral and not es_fin_semana:
        if 8 <= hora_pico_inicio <= 10 and 17 <= hora_pico_fin <= 20:
            # Horario de oficina típico
            tipo_inferido = 'trabajador'
            confianza = 0.85
        elif 14 <= hora_pico_inicio <= 17:
            # Horario de tarde típico de estudiantes
            tipo_inferido = 'estudiante'
            confianza = 0.75
    elif es_fin_semana or len(dias_frecuentes) == 7:
        # Trabaja todos los días o solo fines de semana
        tipo_inferido = 'mixto'
        confianza = 0.70
    
    print(f" [PERFIL] Tipo inferido: {tipo_inferido} (confianza: {confianza:.0%})")
    
    # ========================================================================
    # GUARDAR PERFIL
    # ========================================================================
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return None
    
    usuario.tipo_inferido = tipo_inferido
    usuario.confianza_inferencia = confianza
    usuario.hora_pico_inicio = hora_pico_inicio
    usuario.hora_pico_fin = hora_pico_fin
    usuario.dias_activos_patron = ','.join(map(str, dias_frecuentes))
    usuario.perfil_actualizado_en = func.now()
    
    db.session.commit()
    
    perfil = {
        'tipo_inferido': tipo_inferido,
        'confianza': confianza,
        'horario_pico': f"{hora_pico_inicio}:00 - {hora_pico_fin}:00",
        'dias_activos': dias_frecuentes,
        'total_registros': len(registros)
    }
    
    print(f" [PERFIL] Perfil actualizado para usuario {usuario_id}")
    
    return perfil


def obtener_perfil_completo(usuario_id: int):
    """
    Obtiene el perfil completo del usuario (manual + inferido)
    """
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return None
    
    return {
        # Datos básicos
        'nombre': usuario.nombre,
        'correo': usuario.correo,
        
        # Perfil manual (del registro)
        'dedicacion_declarada': usuario.dedicacion,
        'horario_preferido': usuario.horario_preferido,
        'dias_trabajo_declarados': usuario.dias_trabajo,
        
        # Perfil inferido (ML)
        'tipo_inferido': usuario.tipo_inferido,
        'confianza_inferencia': usuario.confianza_inferencia,
        'horario_pico': f"{usuario.hora_pico_inicio or '?'}:00 - {usuario.hora_pico_fin or '?'}:00",
        'dias_activos': usuario.dias_activos_patron,
        
        # Metadata
        'perfil_actualizado': usuario.perfil_actualizado_en.isoformat() if usuario.perfil_actualizado_en else None,
        'dias_desde_registro': (date.today() - usuario.creado_en.date()).days if usuario.creado_en else None
    }
