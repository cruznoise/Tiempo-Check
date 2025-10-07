from app import create_app
from app.schedule.coach_jobs import job_coach_alertas

def run_test(usuario_id=1):
    app = create_app()
    with app.app_context():
        print(f"[TEST] Ejecutando job_coach_alertas para usuario_id={usuario_id}")
        job_coach_alertas(app, usuario_id=usuario_id)
        print("[TEST] Job ejecutado. Revisa las tablas coach_alerta/coach_sugerencia.")

if __name__ == "__main__":
    run_test()
