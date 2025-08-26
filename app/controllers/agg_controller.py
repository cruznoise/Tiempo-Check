# app/controllers/agg_controller.py
from flask import Blueprint, request, jsonify
from datetime import datetime, date
from app.extensions import db
from app.models_agg import AggVentanaCategoria, AggEstadoDia, AggKpiRango

bp_agg = Blueprint("agg", __name__, url_prefix="/admin/api/agg")

def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()

@bp_agg.get("/ventanas")
def api_ventanas():
    usuario_id = int(request.args.get("usuario_id", 1))
    categoria = request.args.get("categoria")
    ventanas = request.args.get("ventanas", "7d,14d,30d").split(",")

    sub = (db.session.query(
                AggVentanaCategoria.ventana,
                db.func.max(AggVentanaCategoria.fecha_fin).label("max_fecha"))
           .filter(AggVentanaCategoria.usuario_id == usuario_id,
                   AggVentanaCategoria.ventana.in_(ventanas))
           .group_by(AggVentanaCategoria.ventana)
           ).subquery()

    q = (db.session.query(AggVentanaCategoria)
         .join(sub, db.and_(AggVentanaCategoria.ventana == sub.c.ventana,
                            AggVentanaCategoria.fecha_fin == sub.c.max_fecha))
         .filter(AggVentanaCategoria.usuario_id == usuario_id))
    if categoria:
        q = q.filter(AggVentanaCategoria.categoria == categoria)

    rows = q.all()
    return jsonify({"ok": True, "items": [{
        "usuario_id": r.usuario_id,
        "categoria": r.categoria,
        "ventana": r.ventana,
        "fecha_fin": r.fecha_fin.isoformat(),
        "minutos_sum": r.minutos_sum,
        "minutos_promedio": r.minutos_promedio,
        "dias_con_datos": r.dias_con_datos,
        "pct_del_total": r.pct_del_total,
    } for r in rows]})

@bp_agg.get("/estado")
def api_estado():
    usuario_id = int(request.args.get("usuario_id", 1))
    fecha = request.args.get("fecha")
    f = _parse_date(fecha) if fecha else date.today()
    rows = (AggEstadoDia.query
            .filter_by(usuario_id=usuario_id, fecha=f)
            .order_by(AggEstadoDia.categoria.asc())
            .all())
    return jsonify({"ok": True, "fecha": f.isoformat(), "items": [{
        "usuario_id": r.usuario_id,
        "fecha": r.fecha.isoformat(),
        "categoria": r.categoria,
        "minutos": r.minutos,
        "meta_min": r.meta_min,
        "limite_min": r.limite_min,
        "cumplio_meta": r.cumplio_meta,
        "excedio_limite": r.excedio_limite,
    } for r in rows]})

@bp_agg.get("/dashboard")
def api_dashboard():
    usuario_id = int(request.args.get("usuario_id", 1))
    rango = request.args.get("rango", "7dias")
    row = (db.session.query(AggKpiRango)
           .filter_by(usuario_id=usuario_id, rango=rango)
           .order_by(AggKpiRango.fecha_ref.desc())
           .first())
    if not row:
        return jsonify({"ok": False, "error": "sin_datos"}), 404
    return jsonify({
        "ok": True,
        "rango": rango,
        "fecha_ref": row.fecha_ref.isoformat(),
        "min_total": row.min_total,
        "min_productivo": row.min_productivo,
        "min_no_productivo": row.min_no_productivo,
        "pct_productivo": row.pct_productivo,
    })
