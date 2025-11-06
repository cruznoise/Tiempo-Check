import json
from flask import Blueprint, request, jsonify
from datetime import datetime, date, timedelta
from app.extensions import db
from app.models.models_coach import CoachAlerta, CoachSugerencia, CoachAccionLog
from sqlalchemy import desc, text


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

@bp.route('/sugerencias', methods=['GET'])
def obtener_sugerencias():
    """Obtiene sugerencias del coach para el usuario"""
    usuario_id = request.args.get('usuario_id', 1, type=int)
    
    try:
        # Obtener sugerencias activas
        from app.models.models_coach import CoachSugerencia
        from datetime import date

        sugerencias = CoachSugerencia.query.filter(
            CoachSugerencia.usuario_id == usuario_id,
            CoachSugerencia.status == 'new'  
        ).order_by(
            CoachSugerencia.id.desc()  
        ).limit(5).all()
        
        return jsonify({
            'sugerencias': [{
                'id': s.id,
                'tipo': s.tipo,
                'cuerpo': s.cuerpo,
                'creado_en': s.creado_en.isoformat() if s.creado_en else None
            } for s in sugerencias]
        })
    except Exception as e:
        print(f"[COACH][ERROR] /sugerencias: {e}")
        return jsonify({'error': str(e)}), 500

@bp.post('/sugerencias/act')
def sugerencia_act():
    data = request.get_json(force=True)
    usuario_id = int(data.get('usuario_id', 1))
    sug_id = int(data['id'])
    action = data.get('action', 'accept')
    db.session.add(CoachAccionLog(
        usuario_id=usuario_id,
        origen='sugerencia',
        origen_id=sug_id,
        accion=action,
        payload={}
    ))
    from app.models.models_coach import CoachSugerencia
    s = CoachSugerencia.query.get(sug_id)
    if s and s.usuario_id == usuario_id:
        s.status = 'acted' if action == 'accept' else 'dismissed'
        db.session.commit()
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "not_found"}), 404


@bp.post("/accion_log")
def registrar_accion():
    """Registra una acción del usuario en coach_accion_log (desde UI Coach)."""
    data = request.get_json() or {}
    usuario_id = data.get("usuario_id", 1)
    origen = data.get("origen", "dashboard")
    origen_id = data.get("origen_id")
    accion = data.get("accion")
    payload = data.get("payload", {})

    if not accion:
        return jsonify({"status": "error", "msg": "Falta parámetro 'accion'"}), 400

    try:
        log = CoachAccionLog(
            usuario_id=usuario_id,
            origen=origen,
            origen_id=origen_id or 0,
            accion=accion,
            payload=json.dumps(payload) if isinstance(payload, (dict, list)) else payload,
        )
        db.session.add(log)
        db.session.commit()
        print(f"[COACH][OK] Acción '{accion}' registrada (user={usuario_id})")
        return jsonify({"status": "ok", "msg": f"Acción '{accion}' registrada."})
    except Exception as e:
        db.session.rollback()
        print(f"[COACH][ERR] No se pudo registrar acción: {e}")
        return jsonify({"status": "error", "msg": str(e)}), 500


@bp.post("/sugerencia_insert")
def sugerencia_insert():
    data = request.get_json() or {}
    usuario_id = data.get("usuario_id", 1)
    tipo = data.get("tipo")
    categoria = data.get("categoria")
    titulo = data.get("titulo", "")
    cuerpo = data.get("cuerpo", "")
    action_type = data.get("action_type", "")
    action_payload = data.get("action_payload", {})
    expires_at = datetime.now() + timedelta(days=7)
    status = "new"

    if not tipo or not categoria:
        return jsonify({"status": "error", "msg": "Faltan campos requeridos"}), 400

    try:
        sug = CoachSugerencia(
            usuario_id=usuario_id,
            tipo=tipo,
            categoria=categoria,
            titulo=titulo,
            cuerpo=cuerpo,
            action_type=action_type,
            action_payload=json.dumps(action_payload, ensure_ascii=False),
            expires_at=expires_at,
            status=status,
        )
        db.session.add(sug)

        if tipo == "meta_personalizada":
            try:
                minutos = float(action_payload.get("minutos_predichos", 0))
                registrar_meta_coach(usuario_id, categoria, minutos, action_payload.get("fecha"))
            except Exception as e:
                print(f"[COACH][WARN] No se pudo registrar la meta del Coach: {e}")

        db.session.commit()
        print(f"[COACH][OK] Sugerencia '{tipo}' registrada (user={usuario_id})")
        return jsonify({"status": "ok", "msg": "Sugerencia registrada"})
    except Exception as e:
        db.session.rollback()
        print(f"[COACH][ERR] Error insertando sugerencia: {e}")
        return jsonify({"status": "error", "msg": str(e)}), 500


def registrar_meta_coach(usuario_id, categoria, minutos_meta, fecha):
    """Inserta o actualiza una meta establecida por el Coach en la tabla metas_categoria."""
    try:
        query = text("""
            INSERT INTO metas_categoria (usuario_id, categoria_id, minutos_meta, fecha, origen, creado_en)
            SELECT :usuario_id, c.id, :minutos_meta, :fecha, 'coach', NOW()
            FROM categorias c
            WHERE c.nombre = :categoria
            ON DUPLICATE KEY UPDATE
                minutos_meta = VALUES(minutos_meta),
                origen = 'coach',
                creado_en = NOW();
        """)
        db.session.execute(query, {
            "usuario_id": usuario_id,
            "categoria": categoria,
            "minutos_meta": int(minutos_meta),
            "fecha": fecha
        })
        db.session.commit()
        print(f"[COACH][META] Meta registrada en metas_categoria (user={usuario_id}, cat={categoria})")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"[COACH][ERR] No se pudo registrar meta del Coach: {e}")
        return False
