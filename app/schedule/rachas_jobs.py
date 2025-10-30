from datetime import date
from flask import current_app
from app.services.rachas_service import actualizar_rachas

from datetime import date
from flask import current_app
from app.services.rachas_service import actualizar_rachas

def job_rachas(app=None, usuario_id: int = 1, fecha: date = None):
    """
    Job diario: actualiza las rachas del usuario para una fecha específica.
    Compatible con boot_catchup y scheduler.
    """
    app = app or current_app
    with app.app_context():
        if fecha is None:
            fecha = date.today()

        print(f"[SCHED][rachas] user={usuario_id} fecha={fecha}")

        try:
            res = actualizar_rachas(usuario_id=usuario_id, fecha=fecha)
            if isinstance(res, dict):
                total = res.get("total", "?")
                nuevas = res.get("nuevas", "?")
                print(f"[SCHED][OK][rachas] {fecha} → total={total}, nuevas={nuevas}")
            else:
                print(f"[SCHED][OK][rachas] {fecha} procesada correctamente")
            return res
        except Exception as e:
            print(f"[SCHED][ERR][rachas] user={usuario_id} fecha={fecha} → {e}")
            return None
