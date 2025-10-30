from datetime import date, timedelta, datetime
from flask import Blueprint, request, jsonify, session, current_app
from sqlalchemy import func, text
from pathlib import Path
import pandas as pd
import json
from app.extensions import db
from flask_login import login_required, current_user
from app.models.ml import MlPrediccionFuture
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
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        usuario_id = request.args.get('usuario_id', type=int)
    if not usuario_id:
        return jsonify({'error': 'No autenticado'}), 401
    fecha = request.args.get('fecha')
    res = predict(
        usuario_id=usuario_id,
        fecha=None if not fecha else __import__('datetime').date.fromisoformat(fecha)
    )
    return jsonify(res)


print("[API] api_controller importado")  

@bp.route("/api/ml/preds_future", methods=["GET"])
#@login_required
def ml_preds_future():
    """Devuelve predicciones futuras desde la tabla ml_predicciones_future."""
    usuario_id = 1 #SE PONE 1 TEMPORALMENTE
    dias = request.args.get("dias", type=int)
    fecha_inicial = request.args.get("fecha_inicial", type=str)
    fecha_final = request.args.get("fecha_final", type=str)
    if dias:
        hoy = date.today()
        fechas = [hoy + timedelta(days=i) for i in range(1, dias + 1)]
    elif fecha_inicial and fecha_final:
        try:
            f_ini = datetime.strptime(fecha_inicial, "%Y-%m-%d").date()
            f_fin = datetime.strptime(fecha_final, "%Y-%m-%d").date()
            fechas = [f_ini + timedelta(days=i) for i in range((f_fin - f_ini).days + 1)]
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido, usa YYYY-MM-DD"}), 400
    else:
        return jsonify({"error": "Parámetros inválidos: usa ?dias=3 o ?fecha_inicial=...&fecha_final=..."}), 400

    registros = (
        MlPrediccionFuture.query
        .filter(
            MlPrediccionFuture.usuario_id == usuario_id,
            MlPrediccionFuture.fecha_pred.in_(fechas)
        )
        .order_by(MlPrediccionFuture.fecha_pred.asc(), MlPrediccionFuture.categoria.asc())
        .all()
    )
    if not registros:
        return jsonify({"mensaje": "No hay predicciones futuras registradas."}), 200
    data = [
        {
            "fecha_pred": r.fecha_pred.strftime("%Y-%m-%d"),
            "categoria": r.categoria,
            "yhat_minutos": r.yhat_minutos,
            "modelo": r.modelo,
            "version_modelo": r.version_modelo,
        }
        for r in registros
    ]
    return jsonify({
        "usuario_id": usuario_id,
        "rango": [str(fechas[0]), str(fechas[-1])],
        "predicciones": data
    }), 200

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

@bp.route("/api/ml/predict_multi", methods=["GET"])
def api_ml_predict_multi():
    """Devuelve predicciones multi-horizonte (T+1..T+3) y umbrales históricos por categoría."""
    usuario_id = request.args.get("usuario_id", type=int, default=1)
    preds_dir = Path(current_app.root_path).parent / "ml" / "preds"

    if not preds_dir.exists():
        return jsonify({"status": "error", "msg": "Directorio de predicciones no encontrado."}), 404

    files = sorted(preds_dir.glob("preds_future_*.csv"), reverse=True)
    if not files:
        return jsonify({"status": "error", "msg": "No hay archivos de predicción."}), 404

    latest_file = files[0]
    print(f"[API][PRED_MULTI] Usando archivo: {latest_file.name}")

    df = pd.read_csv(latest_file)
    required_cols = {"fecha_pred", "categoria", "yhat_minutos"}
    if not required_cols.issubset(df.columns):
        return jsonify({"status": "error", "msg": f"Archivo {latest_file.name} incompleto."}), 400

    if "usuario_id" in df.columns:
        df = df[df["usuario_id"] == usuario_id]

    preds_grouped = (
        df.groupby("categoria")[["fecha_pred", "yhat_minutos"]]
        .apply(lambda g: g.to_dict(orient="records"))
        .to_dict()
    )

    historicos = []
    for f in files[:10]: 
        try:
            tmp = pd.read_csv(f)
            if "usuario_id" in tmp.columns:
                tmp = tmp[tmp["usuario_id"] == usuario_id]
            historicos.append(tmp)
        except Exception:
            continue

    if historicos:
        df_hist = pd.concat(historicos, ignore_index=True)
        umbrales = (
            df_hist.groupby("categoria")["yhat_minutos"]
            .agg(media="mean", p80=lambda x: x.quantile(0.8))
            .to_dict(orient="index")
        )
    else:
        umbrales = {}

    return jsonify({
        "status": "ok",
        "usuario_id": usuario_id,
        "archivo": latest_file.name,
        "categorias": preds_grouped,
        "umbrales": umbrales
    })

@bp.route("/admin/api/jobs_status", methods=["GET"])
def api_jobs_status():
    """
    Devuelve el estado actual de los jobs del scheduler.
    Retorna: id, nombre, trigger, próxima ejecución y estado.
    """
    try:
        sched = current_app.extensions.get('scheduler')
        
        if sched is None:
            return jsonify({
                "status": "error",
                "msg": "Scheduler no inicializado o no disponible en esta instancia"
            }), 503

        if not getattr(sched, 'running', False):
            return jsonify({
                "status": "warning",
                "msg": "Scheduler existe pero no está corriendo",
                "running": False
            }), 200

        jobs = []
        for job in sched.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "trigger": str(job.trigger),
                "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                "func": f"{job.func_ref}"
            })

        return jsonify({
            "status": "ok",
            "running": True,
            "count": len(jobs),
            "jobs": jobs
        }), 200

    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "msg": str(e),
            "traceback": traceback.format_exc()
        }), 500
    
@bp.route("/api/ml/eval/latest", methods=["GET"])
def get_latest_eval():
    from ml.artifacts import EVAL_WEEKLY
    import json, os

    if not os.path.exists(EVAL_WEEKLY):
        return jsonify({"error": "No se encontró el archivo de evaluación"}), 404

    with open(EVAL_WEEKLY, "r") as f:
        data = json.load(f)

    ultima_semana = sorted(data.keys())[-1]
    return jsonify({"semana": ultima_semana, "data": data[ultima_semana]})
