from flask import Blueprint, request, jsonify
from datetime import datetime
from app.extensions import db
from app.models.models_coach import CoachAlerta, CoachSugerencia, CoachAccionLog


bp_coach = Blueprint('coach', __name__, url_prefix='/admin/api/coach')


@bp_coach.get('/alertas')
def list_alertas():
    usuario_id = int(request.args.get('usuario_id', 1))
    since = request.args.get('since') # ISO date opcional
    q = CoachAlerta.query.filter_by(usuario_id=usuario_id)
    if since:
        q = q.filter(CoachAlerta.creado_en >= since)
    items = q.order_by(CoachAlerta.creado_en.desc()).limit(100).all()
    return jsonify({"ok": True, "items": [
        {
            "id": a.id, "tipo": a.tipo, "categoria": a.categoria,
            "severidad": a.severidad, "titulo": a.titulo, "mensaje": a.mensaje,
            "contexto": a.contexto_json, "fecha_hasta": a.fecha_hasta.isoformat(),
            "leido": bool(a.leido)
        } for a in items
    ]})


@bp_coach.post('/alertas/read')
def mark_read():
    data = request.get_json(force=True)
    usuario_id = int(data.get('usuario_id', 1))
    ids = data.get('ids', [])
    CoachAlerta.query.filter(CoachAlerta.usuario_id==usuario_id, CoachAlerta.id.in_(ids)).update({"leido": True})
    db.session.add(CoachAccionLog(usuario_id=usuario_id, origen='alerta', origen_id=0, accion='read', payload={"ids":ids}))
    db.session.commit()
    return jsonify({"ok": True})


@bp_coach.get('/sugerencias')
def list_sugerencias():
    usuario_id = int(request.args.get('usuario_id', 1))
    items = (CoachSugerencia.query
        .filter_by(usuario_id=usuario_id, status='new')
        .order_by(CoachSugerencia.creado_en.desc()).limit(50).all())
    return jsonify({"ok": True, "items": [
        {"id": s.id, "tipo": s.tipo, "categoria": s.categoria, "titulo": s.titulo,
        "cuerpo": s.cuerpo, "action_type": s.action_type, "action_payload": s.action_payload}
        for s in items
    ]})


@bp_coach.post('/sugerencias/act')
def sugerencia_act():
    data = request.get_json(force=True)
    usuario_id = int(data.get('usuario_id', 1))
    sug_id = int(data['id'])
    action = data.get('action', 'accept') # 'accept' | 'dismiss'
    CoachAccionLog(usuario_id=usuario_id, origen='sugerencia', origen_id=sug_id, accion=action)
    # Cambia estado
    from app.models_coach import CoachSugerencia
    s = CoachSugerencia.query.get(sug_id)
    if s and s.usuario_id == usuario_id:
        s.status = 'acted' if action == 'accept' else 'dismissed'
        db.session.commit()
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "not_found"}), 404