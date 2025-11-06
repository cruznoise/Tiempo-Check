"""
Jobs para reentrenamiento automático del clasificador
"""
from app.services.clasificador_ml import entrenar_clasificador_desde_bd
from app.models.models_coach import NotificacionClasificacion
from app import db
from datetime import datetime, timedelta

def job_reentrenar_clasificador(app):
    """
    Re-entrena el clasificador si hay suficiente feedback nuevo
    Se ejecuta diariamente a las 3:00 AM
    """
    with app.app_context():
        try:
            print("🤖 [JOB][CLASIFICADOR] Verificando si es necesario reentrenar...")
            
            # Verificar cuánto feedback nuevo hay
            ultima_semana = datetime.now() - timedelta(days=7)
            
            feedback_nuevo = NotificacionClasificacion.query.filter(
                NotificacionClasificacion.status.in_(['confirmado', 'rechazado', 'clasificado_manual']),
                NotificacionClasificacion.respondido_en >= ultima_semana
            ).count()
            
            print(f"📊 [JOB][CLASIFICADOR] Feedback nuevo (última semana): {feedback_nuevo}")
            
            # Re-entrenar si hay al menos 10 nuevas validaciones
            UMBRAL_MINIMO = 10
            
            if feedback_nuevo >= UMBRAL_MINIMO:
                print(f"✅ [JOB][CLASIFICADOR] Suficiente feedback ({feedback_nuevo} >= {UMBRAL_MINIMO})")
                print("🔄 [JOB][CLASIFICADOR] Iniciando reentrenamiento...")
                
                clasificador = entrenar_clasificador_desde_bd()
                
                if clasificador:
                    print(f"✅ [JOB][CLASIFICADOR] Reentrenamiento exitoso")
                    print(f"📈 [JOB][CLASIFICADOR] Nueva precisión: {clasificador.metricas.get('accuracy', 0):.2%}")
                    
                    # Marcar feedback como "usado en entrenamiento"
                    NotificacionClasificacion.query.filter(
                        NotificacionClasificacion.status.in_(['confirmado', 'rechazado', 'clasificado_manual']),
                        NotificacionClasificacion.respondido_en >= ultima_semana
                    ).update({'usado_en_entrenamiento': True}, synchronize_session=False)
                    db.session.commit()
                    
                    # Recargar clasificador en memoria
                    from ml.utils import get_clasificador
                    get_clasificador().cargar()
                    print("🔄 [JOB][CLASIFICADOR] Modelo recargado en memoria")
                    
                else:
                    print("❌ [JOB][CLASIFICADOR] Fallo en reentrenamiento")
            else:
                print(f"⏳ [JOB][CLASIFICADOR] Insuficiente feedback ({feedback_nuevo} < {UMBRAL_MINIMO})")
                print(f"   Faltan {UMBRAL_MINIMO - feedback_nuevo} validaciones para reentrenar")
                
        except Exception as e:
            print(f"❌ [JOB][CLASIFICADOR] Error: {e}")
            import traceback
            traceback.print_exc()


def job_reentrenar_forzado(app):
    """
    Reentrenamiento forzado sin verificar umbral
    Útil para testing
    """
    with app.app_context():
        try:
            print("🔄 [JOB][CLASIFICADOR] Reentrenamiento FORZADO...")
            clasificador = entrenar_clasificador_desde_bd()
            
            if clasificador:
                print(f"✅ [JOB][CLASIFICADOR] Completado")
                from ml.utils import get_clasificador
                get_clasificador().cargar()
            else:
                print("❌ [JOB][CLASIFICADOR] Falló")
                
        except Exception as e:
            print(f"❌ [JOB][CLASIFICADOR] Error: {e}")
