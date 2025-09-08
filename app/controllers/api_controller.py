from datetime import date, timedelta
from flask import Blueprint, request, jsonify, session
from sqlalchemy import func
from app.extensions import db
from app.models.models import LimiteCategoria, FeaturesCategoriaDiaria
from ml.pipeline import predict as ml_predict_fn
from ml.pipeline import predict


bp = Blueprint("api_controller", __name__)

def _nivel_confianza(dias):
    if dias < 3: return "insuficiente"
    if dias < 7: return "inicial"
    if dias < 15: return "confiable"
    return "consolidado"

@bp.route("/api/sugerencias_detalle")
def sugerencias_detalle():
    if "usuario_id" not in session:
        return jsonify({"error": "No autenticado"}), 401
    usuario_id = session["usuario_id"]

    hoy = date.today()
    desde = hoy - timedelta(days=14) 

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


    def _multiplicador(categoria):
        nombre = (categoria or "").lower()
        no_productivas = ["ocio", "redes", "comercio", "entretenimiento"]
        return 1.10 if not any(x in nombre for x in no_productivas) else 1.20

    out = []
    for r in rows:
        dias = int(r.dias or 0)
        if dias < 3:
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


@bp.route('/api/ml/predict')
def ml_predict():
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    usuario_id = session['usuario_id']
    fecha = request.args.get('fecha')  
    res = predict(usuario_id=usuario_id, fecha=None if not fecha else __import__('datetime').date.fromisoformat(fecha))
    return jsonify(res)


print("[API] api_controller importado")  

@bp.route("/api/ping", methods=["GET"])
def api_ping():
    return jsonify({"ok": True, "ns": "api"})

@bp.route("/api/ml/predict", methods=["GET"])
def api_ml_predict():
    usuario_id = session.get("usuario_id", 1)
    f = request.args.get("fecha")
    fecha = date.fromisoformat(f) if f else None
    res = ml_predict_fn(usuario_id=usuario_id, fecha=fecha)
    return jsonify(res)
