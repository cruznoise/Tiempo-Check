"""
Job para detectar anomalías diarias
"""
from app import db
import json
from datetime import date, timedelta, datetime
from app.services.detector_anomalias import detectar_anomalia_dia, guardar_anomalia

def job_detectar_anomalias(app, usuario_id: int = None):
    """
    Ejecuta detección de anomalías para el día anterior
    """
    with app.app_context():
        from app.models.models import Usuario
        
        # Si no se especifica usuario, detectar para todos
        if usuario_id is None:
            usuarios = Usuario.query.all()
            usuario_ids = [u.id for u in usuarios]
        else:
            usuario_ids = [usuario_id]
        
        ayer = date.today() - timedelta(days=1)
        
        for uid in usuario_ids:
            try:
                # Detectar
                deteccion = detectar_anomalia_dia(uid, ayer)
                
                # Guardar (sin motivo aún, el usuario lo dirá)
                guardar_anomalia(uid, ayer, deteccion)
                
                if deteccion['es_atipico']:
                    print(f"[ANOMALÍA] Usuario {uid} - {ayer}: "
                          f"{deteccion['uso_real']}min vs {deteccion['uso_esperado']}min esperados "
                          f"({deteccion['desviacion_pct']:+.0f}%)")
                
            except Exception as e:
                print(f"[ANOMALÍA][ERROR] Usuario {uid}: {e}")

def job_monitoreo_tiempo_real(app, usuario_id: int = None):
    """
    Monitorea el uso EN TIEMPO REAL y alerta si detecta anomalías en progreso
    """
    with app.app_context():
        from app.models.models import Usuario, Registro
        from app.models.models_coach import CoachSugerencia
        from sqlalchemy import func, text
        from datetime import date, time, datetime, timedelta
        from decimal import Decimal  # ← AGREGAR
        import json
        
        # Si no se especifica usuario, monitorear todos
        if usuario_id is None:
            usuarios = Usuario.query.all()
            usuario_ids = [u.id for u in usuarios]
        else:
            usuario_ids = [usuario_id]
        
        hoy = date.today()
        hora_actual = datetime.now().hour
        
        # Solo alertar durante horas activas (8 AM - 11 PM)
        if hora_actual < 8 or hora_actual > 23:
            print(f"[MONITOREO] Fuera de horario ({hora_actual}:00)")
            return
        
        for uid in usuario_ids:
            try:
                # Calcular uso hasta ahora HOY
                uso_hasta_ahora = db.session.query(
                    func.sum(Registro.tiempo) / 60.0
                ).filter(
                    Registro.usuario_id == uid,
                    func.date(Registro.fecha) == hoy
                ).scalar()
                
                # Convertir a float
                uso_hasta_ahora = float(uso_hasta_ahora) if uso_hasta_ahora else 0.0
                
                # Si no hay uso hoy, saltar
                if uso_hasta_ahora == 0:
                    print(f"[MONITOREO] Usuario {uid} - Sin uso hoy")
                    continue
                
                # Calcular promedio histórico usando query SQL directa
                fecha_inicio = hoy - timedelta(days=30)
                hora_corte = datetime.now().replace(minute=0, second=0, microsecond=0)
                
                # Query SQL directa para evitar problemas con AVG(SUM())
                query_promedio = text("""
                    SELECT AVG(uso_diario) as promedio
                    FROM (
                        SELECT DATE(fecha) as dia, SUM(tiempo)/60.0 as uso_diario
                        FROM registro
                        WHERE usuario_id = :usuario_id
                          AND DATE(fecha) >= :fecha_inicio
                          AND DATE(fecha) < :hoy
                          AND fecha <= :hora_corte
                        GROUP BY DATE(fecha)
                    ) as subq
                """)
                
                resultado = db.session.execute(query_promedio, {
                    'usuario_id': uid,
                    'fecha_inicio': fecha_inicio,
                    'hoy': hoy,
                    'hora_corte': hora_corte
                }).fetchone()
                
                # Convertir a float
                uso_promedio_hora = float(resultado[0]) if resultado and resultado[0] else 0.0
                
                # Si no hay suficiente historial, saltar
                if uso_promedio_hora == 0:
                    print(f"[MONITOREO] Usuario {uid} - Sin historial suficiente")
                    continue
                
                # Calcular desviación (ahora ambos son float)
                desviacion_pct = ((uso_hasta_ahora - uso_promedio_hora) / uso_promedio_hora) * 100
                
                # Umbral: ±80%
                UMBRAL = 80
                
                if abs(desviacion_pct) >= UMBRAL:
                    # Verificar si ya alertamos hoy
                    alerta_existente = CoachSugerencia.query.filter(
                        CoachSugerencia.usuario_id == uid,
                        CoachSugerencia.tipo == 'anomalia_tiempo_real',
                        func.date(CoachSugerencia.creado_en) == hoy
                    ).first()
                    
                    if not alerta_existente:
                        # Crear sugerencia
                        titulo = "🔍 Uso Atípico Detectado"
                        cuerpo = (
                            f"Llevas {uso_hasta_ahora:.0f} minutos de uso hoy "
                            f"cuando normalmente a esta hora llevas {uso_promedio_hora:.0f} min "
                            f"({desviacion_pct:+.0f}%)"
                        )
                        
                        sugerencia = CoachSugerencia(
                            usuario_id=uid,
                            tipo='anomalia_tiempo_real',
                            categoria='Sistema',
                            titulo=titulo,
                            cuerpo=cuerpo,
                            action_type='explicar_anomalia',
                            action_payload=json.dumps({
                                'uso_actual': float(uso_hasta_ahora),
                                'uso_esperado': float(uso_promedio_hora),
                                'desviacion': float(desviacion_pct),
                                'hora': hora_actual,
                                'fecha': hoy.isoformat()
                            }),
                            expires_at=datetime.now() + timedelta(hours=2),
                            status='new'
                        )
                        
                        db.session.add(sugerencia)
                        db.session.commit()
                        
                        print(f"[ANOMALÍA][TIEMPO REAL] ✅ Usuario {uid} - "
                              f"{uso_hasta_ahora:.0f} min vs {uso_promedio_hora:.0f} esperados "
                              f"({desviacion_pct:+.0f}%) a las {hora_actual}:00")
                    else:
                        print(f"[ANOMALÍA][TIEMPO REAL] ⏭️  Usuario {uid} - Ya alertado hoy")
                else:
                    print(f"[MONITOREO] ✅ Usuario {uid} - Uso normal: "
                          f"{uso_hasta_ahora:.0f} min vs {uso_promedio_hora:.0f} esperados "
                          f"({desviacion_pct:+.0f}%)")
                
            except Exception as e:
                import traceback
                print(f"[ANOMALÍA][TIEMPO REAL][ERROR] ❌ Usuario {uid}: {e}")
                traceback.print_exc()
                db.session.rollback()