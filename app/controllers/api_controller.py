from datetime import date, timedelta
from flask import Blueprint, request, jsonify, session
from sqlalchemy import func
from app.extensions import db
from app.models import FeaturesCategoriaDiaria, LimiteCategoria  

api = Blueprint("api_controller", __name__)

def _nivel_confianza(dias):
    if dias < 3: return "insuficiente"
    if dias < 7: return "inicial"
    if dias < 15: return "confiable"
    return "consolidado"

@api.route("/api/sugerencias_detalle")
def sugerencias_detalle():
    if "usuario_id" not in session:
        return jsonify({"error": "No autenticado"}), 401
    usuario_id = session["usuario_id"]

    hoy = date.today()
    desde = hoy - timedelta(days=14)  # ventana de respaldo para explicar

    rows = (
        db.session.query(
            FeaturesCategoriaDiaria.categoria.label("categoria"),
            func.count(FeaturesCategoriaDiaria.minutos).label("dias"),
            func.avg(FeaturesCategoriaDiaria.minutos).label("promedio_14d"),
        )
        .filter(
            FeaturesCategoriaDiaria.usuario_id == usuario_id,
            FeaturesCategoriaDiaria.fecha >= desde,
            FeaturesCategoriaDiaria.fecha < hoy,
        )
        .group_by(FeaturesCategoriaDiaria.categoria)
        .all()
    )

    # Regla de negocio vigente (ya la usas): 10% productivas, 20% no productivas
    # Si tienes un campo "tipo" en categorias, úsalo; si no, heurística por nombre:
    def _multiplicador(categoria):
        nombre = (categoria or "").lower()
        no_productivas = ["ocio", "redes", "comercio", "entretenimiento"]
        return 1.10 if not any(x in nombre for x in no_productivas) else 1.20

    out = []
    for r in rows:
        dias = int(r.dias or 0)
        if dias < 3:
            # No mostramos sugerencia si hay <3 días (como ya definiste)
            continue
        prom = float(r.promedio_14d or 0.0)
        mult = _multiplicador(r.categoria)
        sugerido = round(prom * mult, 2)
        out.append({
            "categoria": r.categoria,
            "dias_respaldo": dias,
            "promedio_14d": prom,
            "multiplicador": mult,
            "sugerencia_minutos": sugerido,
            "nivel_confianza": _nivel_confianza(dias),
            "formula": f"sugerencia = promedio_14d ({prom:.2f}) × multiplicador ({mult:.2f})",
        })

    return jsonify({"usuario_id": usuario_id, "detalle": out, "ventana": {"desde": str(desde), "hasta": str(hoy)}})
