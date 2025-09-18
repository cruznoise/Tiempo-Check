from flask import Blueprint, request, jsonify
from datetime import datetime, date
from app.extensions import db
from app.models.models_coach import CoachAlerta, CoachSugerencia, CoachAccionLog
from sqlalchemy import desc


bp = Blueprint("coach", __name__, url_prefix="/admin/api/coach")

@bp.get('/alertas')
def list_alertas():
    usuario_id = int(request.args.get('usuario_id', 1))
    since = request.args.get('since')  or request.args.get('fecha')
    if since and len(since) == 10:
        try:
            since = datetime.strptime(since, "%Y-%m-%d")
        except ValueError:
            since = None
    cols = (
        CoachAlerta.id,
        CoachAlerta.usuario_id,
        CoachAlerta.categoria,
        CoachAlerta.tipo,
        CoachAlerta.severidad,
        CoachAlerta.titulo,
        CoachAlerta.mensaje,
        CoachAlerta.contexto_json,
        CoachAlerta.fecha_hasta,
        CoachAlerta.leido,
        CoachAlerta.creado_en,
    )

    q = db.session.query(*cols).filter(CoachAlerta.usuario_id == usuario_id)
    if since:
        q = q.filter(CoachAlerta.creado_en >= since)

    rows = q.order_by(desc(CoachAlerta.creado_en)).limit(100).all()

    def _s(row):
        (
            id_, usuario_id_, categoria, tipo, severidad, titulo, mensaje,
            contexto_json, fecha_hasta, leido, creado_en
        ) = row
        return {
            "id": id_,
            "tipo": tipo,
            "categoria": categoria,
            "severidad": severidad,
            "titulo": titulo,
            "mensaje": mensaje,
            "contexto": contexto_json,
            "fecha_hasta": fecha_hasta.isoformat() if fecha_hasta else None,
            "leido": bool(leido),
            "creado_en": creado_en.isoformat() if creado_en else None,
        }

    return jsonify({"ok": True, "items": [_s(r) for r in rows]})
@bp.post('/alertas/read')
def mark_read():
    data = request.get_json(force=True)
    usuario_id = int(data.get('usuario_id', 1))
    ids = data.get('ids', [])
    CoachAlerta.query.filter(
        CoachAlerta.usuario_id == usuario_id,
        CoachAlerta.id.in_(ids)
    ).update({"leido": True}, synchronize_session=False)
    db.session.add(CoachAccionLog(usuario_id=usuario_id, origen='alerta', origen_id=0, accion='read', payload={"ids":ids}))
    db.session.commit()
    return jsonify({"ok": True})

@bp.get('/sugerencias')
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

@bp.post('/sugerencias/act')
def sugerencia_act():
    data = request.get_json(force=True)
    usuario_id = int(data.get('usuario_id', 1))
    sug_id = int(data['id'])
    action = data.get('action', 'accept') # 'accept' | 'dismiss'
    CoachAccionLog(usuario_id=usuario_id, origen='sugerencia', origen_id=sug_id, accion=action)
    from app.models.models_coach import CoachSugerencia
    s = CoachSugerencia.query.get(sug_id)
    if s and s.usuario_id == usuario_id:
        s.status = 'acted' if action == 'accept' else 'dismissed'
        db.session.commit()
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "not_found"}), 404