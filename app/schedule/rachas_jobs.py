from app.services.rachas_service import actualizar_rachas

def job_rachas(app, usuario_id: int):
    with app.app_context():
        try:
            actualizar_rachas(usuario_id)
            print(f"[SCHED][RACHAS] Rachas actualizadas para user={usuario_id}")
        except Exception as e:
            print(f"[SCHED][RACHAS][ERROR] user={usuario_id} -> {e}")
