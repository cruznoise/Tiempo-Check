"""
Jobs del scheduler para actualización automática de perfiles
"""
from app.services.perfil_adaptativo import inferir_perfil_usuario

def job_actualizar_perfil(app, usuario_id: int):
    """
    Job que actualiza el perfil del usuario automáticamente
    Se ejecuta los domingos a las 4:00 AM
    """
    with app.app_context():
        try:
            print(f" [JOB][PERFIL] Actualizando perfil usuario {usuario_id}...")
            
            perfil = inferir_perfil_usuario(usuario_id)
            
            if perfil:
                print(f" [JOB][PERFIL] Usuario {usuario_id}: {perfil['tipo_inferido']} ({perfil['confianza']:.0%})")
            else:
                print(f" [JOB][PERFIL] Usuario {usuario_id}: Sin suficientes datos")
                
        except Exception as e:
            print(f" [JOB][PERFIL] Error usuario {usuario_id}: {e}")
