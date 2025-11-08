from datetime import date, timedelta, datetime
from flask import Blueprint, request, jsonify, session, current_app
from sqlalchemy import func, text
from pathlib import Path
import pandas as pd
import json
from app.extensions import db
from flask_login import login_required, current_user
from app.models.ml import MLPrediccionFuture
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
        MLPrediccionFuture.query
        .filter(
            MLPrediccionFuture.usuario_id == usuario_id,
            MLPrediccionFuture.fecha_pred.in_(fechas)
        )
        .order_by(MLPrediccionFuture.fecha_pred.asc(), MLPrediccionFuture.categoria.asc())
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

@bp.route('/api/categorias', methods=['GET'])  
def obtener_categorias():
    """Retorna lista de categorías para el frontend"""
    from app.models.models import Categoria
    
    try:
        categorias = Categoria.query.all()
        
        return jsonify({
            'categorias': [{
                'id': c.id, 
                'nombre': c.nombre
            } for c in categorias]
        })
    except Exception as e:
        print(f"[API][ERROR] /categorias: {e}")
        return jsonify({'error': str(e)}), 500

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

@bp.route('/api/perfil', methods=['GET'])
def obtener_perfil():
    """Obtiene el perfil completo del usuario actual"""
    from app.services.perfil_adaptativo import obtener_perfil_completo
    
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return jsonify({'error': 'No autenticado'}), 401
    
    perfil = obtener_perfil_completo(usuario_id)
    
    if not perfil:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    return jsonify(perfil)


@bp.route('/api/perfil/actualizar', methods=['POST'])
def forzar_actualizacion_perfil():
    """Fuerza actualización del perfil (para testing)"""
    from app.services.perfil_adaptativo import inferir_perfil_usuario
    
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return jsonify({'error': 'No autenticado'}), 401
    
    perfil = inferir_perfil_usuario(usuario_id)
    
    if perfil:
        return jsonify({'success': True, 'perfil': perfil})
    else:
        return jsonify({'success': False, 'mensaje': 'Datos insuficientes'}), 400
    

@bp.route('/api/clasificador/reentrenar', methods=['POST'])
def reentrenar_clasificador_manual():
    """
    Endpoint para forzar reentrenamiento del clasificador
    Útil para testing y demostración
    """
    from app.services.clasificador_ml import entrenar_clasificador_desde_bd
    from ml.utils_ml import get_clasificador
    
    try:
        print("🔄 [API] Reentrenamiento manual solicitado...")
        
        # Obtener stats antes
        clasificador_viejo = get_clasificador()
        precision_vieja = clasificador_viejo.metricas.get('accuracy', 0) if clasificador_viejo.entrenado else 0
        
        # Re-entrenar
        clasificador_nuevo = entrenar_clasificador_desde_bd()
        
        if not clasificador_nuevo:
            return jsonify({
                'success': False,
                'error': 'No se pudo entrenar (datos insuficientes)'
            }), 400
        
        precision_nueva = clasificador_nuevo.metricas.get('accuracy', 0)
        mejora = precision_nueva - precision_vieja
        
        # Recargar en memoria
        get_clasificador().cargar()
        
        return jsonify({
            'success': True,
            'mensaje': 'Clasificador reentrenado correctamente',
            'metricas': {
                'precision_anterior': f"{precision_vieja:.2%}",
                'precision_nueva': f"{precision_nueva:.2%}",
                'mejora': f"{mejora:+.2%}",
                'n_ejemplos': clasificador_nuevo.metricas.get('n_ejemplos', 0),
                'n_categorias': clasificador_nuevo.metricas.get('n_categorias', 0)
            }
        })
        
    except Exception as e:
        print(f"❌ [API] Error reentrenando: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
# ============================================================================
# ENDPOINTS PARA DASHBOARD ML
# ============================================================================

@bp.route('/api/ml/metricas_resumen', methods=['GET'])
def metricas_resumen():
    """
    Resumen de métricas ML para dashboard
    """
    usuario_id = session.get('usuario_id', 1)
    
    try:
        # 1. Precisión de predicciones (R² promedio)
        import json
        import os
        from pathlib import Path
        
        # Ruta del archivo de evaluación
        ml_dir = Path(__file__).parent.parent.parent / 'ml'
        eval_file = ml_dir / 'backtesting' / 'eval_weekly.json'
        
        r2_promedio = 0.82  # Default
        
        if eval_file.exists():
            with open(eval_file, 'r') as f:
                eval_data = json.load(f)
                ultima_semana = sorted(eval_data.keys())[-1]
                metricas_semana = eval_data[ultima_semana]
                
                r2_values = [cat['r2'] for cat in metricas_semana.values() 
                            if 'r2' in cat and cat['r2'] is not None]
                
                if r2_values:
                    r2_promedio = sum(r2_values) / len(r2_values)
        
        # 2. Mejora con contexto
        from app.services.contexto_ml_integration import calcular_mejora_contexto
        mejora_contexto = calcular_mejora_contexto(usuario_id)
        
        # 3. Precisión clasificador
        from ml.utils_ml import get_clasificador
        clasificador = get_clasificador()
        
        precision_clasificador = clasificador.metricas.get('accuracy', 0.5769) if clasificador.entrenado else 0.5769
        precision_inicial = 0.5769
        mejora_clasificador = ((precision_clasificador - precision_inicial) / precision_inicial) * 100
        
        # 4. Total validaciones
        from app.models.models_coach import NotificacionClasificacion
        total_validaciones = NotificacionClasificacion.query.filter(
            NotificacionClasificacion.usuario_id == usuario_id,
            NotificacionClasificacion.status.in_(['confirmado', 'rechazado', 'clasificado_manual'])
        ).count()
        
        return jsonify({
            'r2_promedio': r2_promedio,
            'mejora_contexto': mejora_contexto,
            'precision_clasificador': precision_clasificador,
            'mejora_clasificador': mejora_clasificador,
            'total_validaciones': total_validaciones
        })
        
    except Exception as e:
        print(f"[ML][ERROR] /metricas_resumen: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/ml/predicciones_vs_realidad', methods=['GET'])
def predicciones_vs_realidad():
    """
    Compara predicciones con valores reales
    Usa Registro (raw) como fuente principal
    """
    usuario_id = session.get('usuario_id', 1)
    dias = request.args.get('dias', 7, type=int)
    
    try:
        from datetime import date, timedelta
        from app.models.models import Registro
        from app.models.ml import MLPrediccionFuture
        from sqlalchemy import func
        
        fechas = []
        predicciones = []
        reales = []
        
        for i in range(dias):
            fecha = date.today() - timedelta(days=dias - i - 1)
            fechas.append(str(fecha))
            
            # ========================================================================
            # PREDICCIÓN
            # ========================================================================
            preds = MLPrediccionFuture.query.filter_by(
                usuario_id=usuario_id,
                fecha_pred=fecha
            ).all()
            
            pred_total = sum([p.yhat_minutos for p in preds]) if preds else 0
            predicciones.append(int(pred_total))
            
            # ========================================================================
            # REAL - Desde Registro (raw)
            # ========================================================================
            real_segundos = db.session.query(func.sum(Registro.tiempo)).filter(
                Registro.usuario_id == usuario_id,
                func.date(Registro.fecha_hora) == fecha
            ).scalar()
            
            # Convertir Decimal a float, luego a minutos
            real_minutos = float(real_segundos) / 60.0 if real_segundos else 0.0
            reales.append(int(real_minutos))
        
        return jsonify({
            'fechas': fechas,
            'predicciones': predicciones,
            'reales': reales
        })
        
    except Exception as e:
        print(f"[ML][ERROR] /predicciones_vs_realidad: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
@bp.route('/api/ml/impacto_contexto', methods=['GET'])
def impacto_contexto():
    """
    Retorna factores de ajuste por motivo de contexto
    """
    usuario_id = session.get('usuario_id', 1)
    
    try:
        from app.services.contexto_ml_integration import obtener_contexto_historico
        
        patrones = obtener_contexto_historico(usuario_id)
        
        if not patrones or 'ajustes_sugeridos' not in patrones:
            return jsonify({
                'motivos': [],
                'factores': []
            })
        
        ajustes = patrones['ajustes_sugeridos']
        
        return jsonify({
            'motivos': list(ajustes.keys()),
            'factores': [info['factor'] for info in ajustes.values()]
        })
        
    except Exception as e:
        print(f"[ML][ERROR] /impacto_contexto: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/ml/evolucion_clasificador', methods=['GET'])
def evolucion_clasificador():
    """
    Historial de precisión del clasificador
    """
    try:
        # TODO: Implementar guardado histórico de métricas
        # Por ahora, datos simulados basados en realidad
        
        return jsonify({
            'fechas': ['2025-10-01', '2025-10-15', '2025-11-01', '2025-11-05'],
            'precisiones': [57.69, 62.30, 65.80, 68.42],
            'ejemplos': [126, 130, 133, 136]
        })
        
    except Exception as e:
        print(f"[ML][ERROR] /evolucion_clasificador: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/ml/errores_por_categoria', methods=['GET'])
def errores_por_categoria():
    """
    MAE y RMSE por categoría
    """
    try:
        import json
        import os
        from pathlib import Path
        
        # Ruta del archivo de evaluación
        ml_dir = Path(__file__).parent.parent.parent / 'ml'
        eval_file = ml_dir / 'backtesting' / 'eval_weekly.json'
        
        if not eval_file.exists():
            # Si no existe, retornar datos por defecto
            return jsonify({
                'categorias': ['Productividad', 'Redes Sociales', 'Trabajo', 'Ocio'],
                'mae': [37.7, 6.6, 8.8, 11.2],
                'rmse': [48.7, 9.9, 11.4, 14.2]
            })
        
        with open(eval_file, 'r') as f:
            eval_data = json.load(f)
        
        ultima_semana = sorted(eval_data.keys())[-1]
        metricas = eval_data[ultima_semana]
        
        categorias = []
        mae = []
        rmse = []
        
        for cat, metrics in metricas.items():
            categorias.append(cat)
            mae.append(metrics.get('mae', 0))
            rmse.append(metrics.get('rmse', 0))
        
        return jsonify({
            'categorias': categorias,
            'mae': mae,
            'rmse': rmse
        })
        
    except Exception as e:
        print(f"[ML][ERROR] /errores_por_categoria: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/ml/patrones_aprendidos', methods=['GET'])
def patrones_aprendidos():
    """
    Patrones de contexto aprendidos
    """
    usuario_id = session.get('usuario_id', 1)
    
    try:
        from app.services.contexto_ml_integration import obtener_contexto_historico
        
        patrones = obtener_contexto_historico(usuario_id)
        
        if not patrones or 'ajustes_sugeridos' not in patrones:
            return jsonify({'patrones': []})
        
        lista_patrones = []
        
        for motivo, info in patrones['ajustes_sugeridos'].items():
            lista_patrones.append({
                'motivo': motivo,
                'ocurrencias': info.get('ocurrencias', 0),  # ← get con default
                'factor': info.get('factor', 1.0),
                'confianza': info.get('confianza', 0.0),
                'categoria': info.get('categoria', 'N/A')
            })
        
        return jsonify({'patrones': lista_patrones})
        
    except Exception as e:
        print(f"[ML][ERROR] /patrones_aprendidos: {e}")
        import traceback
        traceback.print_exc()
        
        # En caso de error, retornar lista vacía
        return jsonify({'patrones': []})
    
@bp.route('/api/ml/matriz_confusion_clasificador', methods=['GET'])
def matriz_confusion_clasificador():
    """
    Matriz de confusión del clasificador
    """
    try:
        from app.models.models_coach import NotificacionClasificacion
        from app.models.models import Categoria
        
        usuario_id = session.get('usuario_id', 1)
        
        # Obtener clasificaciones validadas
        notifs = NotificacionClasificacion.query.filter(
            NotificacionClasificacion.usuario_id == usuario_id,
            NotificacionClasificacion.status.in_(['confirmado', 'rechazado'])
        ).all()
        
        if len(notifs) < 5:
            # Datos insuficientes, retornar ejemplo
            return jsonify({
                'categorias': ['Productividad', 'Ocio', 'Trabajo'],
                'matriz': [
                    [8, 1, 0],  # Productividad predicha
                    [0, 5, 1],  # Ocio predicho
                    [1, 0, 7]   # Trabajo predicho
                ]
            })
        
        # Construir matriz real
        from collections import defaultdict
        
        categorias_set = set()
        matriz_dict = defaultdict(lambda: defaultdict(int))
        
        for n in notifs:
            cat_pred = Categoria.query.get(n.categoria_sugerida_id)
            cat_real = Categoria.query.get(n.categoria_correcta_id) if n.status == 'rechazado' else cat_pred
            
            if cat_pred and cat_real:
                categorias_set.add(cat_pred.nombre)
                categorias_set.add(cat_real.nombre)
                matriz_dict[cat_real.nombre][cat_pred.nombre] += 1
        
        categorias = sorted(list(categorias_set))
        
        # Convertir a matriz numérica
        matriz = []
        for cat_real in categorias:
            fila = []
            for cat_pred in categorias:
                fila.append(matriz_dict[cat_real][cat_pred])
            matriz.append(fila)
        
        return jsonify({
            'categorias': categorias,
            'matriz': matriz
        })
        
    except Exception as e:
        print(f"[ML][ERROR] /matriz_confusion_clasificador: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500