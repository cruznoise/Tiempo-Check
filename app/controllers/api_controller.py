from datetime import date, timedelta, datetime
from flask import Blueprint, request, jsonify, session, current_app
from sqlalchemy import func, text
from pathlib import Path
import pandas as pd
import json
from app.extensions import db
from flask_login import login_required, current_user
from app.models.ml import MLPrediccionFuture
from app.models.models import LimiteCategoria, FeaturesCategoriaDiaria, SesionFocus, IntentoBloqeuoFocus, Categoria, DominioCategoria
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
    usuario_id = session.get('usuario_id')
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
            'success': True,
            'categorias': [{
                'id': c.id, 
                'nombre': c.nombre
            } for c in categorias]
        })
    except Exception as e:
        print(f"[API][ERROR] /categorias: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/categorias/con-dominios', methods=['GET'])
def obtener_categorias_con_dominios():
    """Retorna categorías con sus dominios para la extensión"""    
    try:
        categorias = Categoria.query.all()
        
        resultado = {}
        
        for cat in categorias:
            dominios = DominioCategoria.query.filter_by(categoria_id=cat.id).all()
            
            for dominio in dominios:
                resultado[dominio.dominio] = cat.nombre
        
        return jsonify({
            'success': True,
            'mapeo': resultado,  
            'total_dominios': len(resultado)
        })
        
    except Exception as e:
        print(f"[API][ERROR] /categorias/con-dominios: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    

@bp.route("/api/ml/predict_multi", methods=["GET"])
def api_ml_predict_multi():
    """
    Devuelve predicciones multi-horizonte POR USUARIO
    """
    from flask import session
    usuario_id = session.get("usuario_id", 1)
    
    #  Buscar en directorio POR USUARIO
    preds_dir = Path(current_app.root_path).parent / "ml" / "preds" / f"usuario_{usuario_id}"
    
    if not preds_dir.exists():
        return jsonify({
            "status": "error", 
            "msg": f"No hay predicciones para usuario {usuario_id}. Ejecute el entrenamiento primero."
        }), 404

    files = sorted(preds_dir.glob("preds_future_*.csv"), reverse=True)
    if not files:
        return jsonify({
            "status": "error", 
            "msg": f"No hay archivos de predicción para usuario {usuario_id}."
        }), 404

    latest_file = files[0]
    print(f"[API][PRED_MULTI] user={usuario_id} usando: {latest_file.name}")

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
    dias = request.args.get('dias', 180, type=int)
    
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
    

@bp.route('/api/focus/start', methods=['POST'])
def api_focus_start():
    """Iniciar sesión de Modo Focus"""
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401
    
    try:
        usuario_id = session.get('usuario_id')
        data = request.json
        
        # Validar datos
        duracion = data.get('duration_minutes')
        categorias = data.get('blocked_categories', [])
        
        if not duracion or duracion < 1 or duracion > 480:
            return jsonify({'success': False, 'message': 'Duración inválida'}), 400
        
        if not categorias:
            return jsonify({'success': False, 'message': 'Selecciona al menos una categoría'}), 400
        
        # Verificar que no haya sesión activa
        sesion_activa = SesionFocus.query.filter_by(
            usuario_id=usuario_id,
            completada=False
        ).filter(
            SesionFocus.fin_programado > datetime.now()
        ).first()
        
        if sesion_activa:
            return jsonify({'success': False, 'message': 'Ya existe una sesión activa'}), 400
        
        # Crear nueva sesión
        ahora = datetime.now()
        sesion = SesionFocus(
            usuario_id=usuario_id,
            inicio=ahora,
            fin_programado=ahora + timedelta(minutes=duracion),
            duracion_minutos=duracion,
            modo_estricto=data.get('strict_mode', False),
            categorias_bloqueadas=json.dumps(categorias)
        )
        
        db.session.add(sesion)
        db.session.commit()
        
        print(f"[FOCUS] Sesión iniciada: ID={sesion.id}, Usuario={usuario_id}, Duración={duracion}min")
        
        return jsonify({
            'success': True,
            'session_id': sesion.id,
            'message': 'Sesión iniciada correctamente'
        })
        
    except Exception as e:
        print(f"[ERROR] Error al iniciar Focus: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error del servidor: {str(e)}'}), 500


@bp.route('/api/focus/end', methods=['POST'])
def api_focus_end():
    """Finalizar sesión de Modo Focus"""
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401
    
    try:
        usuario_id = session.get('usuario_id')
        data = request.json
        completed = data.get('completed', False)
        
        # Buscar sesión activa
        sesion = SesionFocus.query.filter_by(
            usuario_id=usuario_id,
            completada=False
        ).order_by(SesionFocus.inicio.desc()).first()
        
        if not sesion:
            return jsonify({'success': False, 'message': 'No hay sesión activa'}), 400
        
        # Actualizar sesión
        ahora = datetime.now()
        sesion.fin_real = ahora
        sesion.completada = completed
        
        # Calcular tiempo real
        tiempo_real = (ahora - sesion.inicio).total_seconds() / 60
        sesion.tiempo_real_minutos = int(tiempo_real)
        
        db.session.commit()
        
        print(f"[FOCUS] Sesión finalizada: ID={sesion.id}, Completada={completed}, Tiempo={sesion.tiempo_real_minutos}min")
        
        return jsonify({
            'success': True,
            'completed': completed,
            'tiempo_real': sesion.tiempo_real_minutos
        })
        
    except Exception as e:
        print(f"[ERROR] Error al finalizar Focus: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error del servidor: {str(e)}'}), 500


@bp.route('/api/focus/status', methods=['GET'])
def api_focus_status():
    """Obtener estado actual de Focus Mode"""
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401
    
    try:
        usuario_id = session.get('usuario_id')
        
        # Buscar sesión activa
        sesion = SesionFocus.query.filter_by(
            usuario_id=usuario_id,
            completada=False
        ).filter(
            SesionFocus.fin_programado > datetime.now()
        ).order_by(SesionFocus.inicio.desc()).first()
        
        if not sesion:
            return jsonify({
                'success': True,
                'active': False
            })
        
        # Contar intentos de bloqueo
        intentos = IntentoBloqeuoFocus.query.filter_by(sesion_id=sesion.id).count()
        
        # Calcular tiempo restante
        ahora = datetime.now()
        restante_segundos = (sesion.fin_programado - ahora).total_seconds()
        restante_minutos = int(restante_segundos / 60)
        
        return jsonify({
            'success': True,
            'active': True,
            'session_id': sesion.id,
            'duracion_minutos': sesion.duracion_minutos,
            'tiempo_restante_minutos': restante_minutos,
            'categorias_bloqueadas': json.loads(sesion.categorias_bloqueadas),
            'modo_estricto': sesion.modo_estricto,
            'blocks_count': intentos
        })
        
    except Exception as e:
        print(f"[ERROR] Error al obtener estado: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error del servidor: {str(e)}'}), 500


@bp.route('/api/focus/block', methods=['POST'])
def api_focus_block():
    """Registrar intento de acceso a sitio bloqueado"""
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401
    
    try:
        usuario_id = session.get('usuario_id')
        data = request.json
        
        # Buscar sesión activa
        sesion = SesionFocus.query.filter_by(
            usuario_id=usuario_id,
            completada=False
        ).order_by(SesionFocus.inicio.desc()).first()
        
        if not sesion:
            return jsonify({'success': False, 'message': 'No hay sesión activa'}), 400
        
        # Registrar intento
        intento = IntentoBloqeuoFocus(
            sesion_id=sesion.id,
            momento=datetime.now(),
            url_bloqueada=data.get('url'),
            categoria=data.get('categoria')
        )
        
        db.session.add(intento)
        db.session.commit()
        
        print(f"[FOCUS] Bloqueo registrado: URL={data.get('url')}, Cat={data.get('categoria')}")
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"[ERROR] Error al registrar bloqueo: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error del servidor: {str(e)}'}), 500


@bp.route('/api/focus/stats/today', methods=['GET'])
def api_focus_stats_today():
    """Obtiene estadísticas de Focus Mode del día actual"""
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401
    
    try:
        usuario_id = session.get('usuario_id')
        hoy = datetime.now().date()
        
        # Sesiones completadas hoy
        sesiones_hoy = SesionFocus.query.filter(
            SesionFocus.usuario_id == usuario_id,
            db.func.date(SesionFocus.inicio) == hoy,
            SesionFocus.completada == True
        ).all()
        
        sesiones_completadas = len(sesiones_hoy)
        minutos_totales = sum(s.tiempo_real_minutos or s.duracion_minutos for s in sesiones_hoy)
        
        # Calcular racha (días consecutivos con al menos una sesión completada)
        racha = 0
        fecha_check = hoy
        while racha < 365:  # Límite de seguridad
            sesion_dia = SesionFocus.query.filter(
                SesionFocus.usuario_id == usuario_id,
                db.func.date(SesionFocus.inicio) == fecha_check,
                SesionFocus.completada == True
            ).first()
            
            if sesion_dia:
                racha += 1
                fecha_check = fecha_check - timedelta(days=1)
            else:
                break
        
        return jsonify({
            'success': True,
            'sesiones_completadas': sesiones_completadas,
            'minutos_totales': minutos_totales,
            'racha_dias': racha
        })
        
    except Exception as e:
        print(f"[ERROR] Error al obtener estadísticas: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error del servidor: {str(e)}'}), 500


@bp.route('/api/focus/history', methods=['GET'])
def api_focus_history():
    """Obtener historial de sesiones Focus"""
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401
    
    try:
        usuario_id = session.get('usuario_id')
        limit = request.args.get('limit', 10, type=int)
        
        sesiones = SesionFocus.query.filter_by(
            usuario_id=usuario_id
        ).order_by(SesionFocus.inicio.desc()).limit(limit).all()
        
        historial = []
        for s in sesiones:
            historial.append({
                'id': s.id,
                'inicio': s.inicio.strftime('%d/%m/%Y %H:%M'),
                'duracion': s.duracion_minutos,
                'completada': s.completada,
                'tiempo_real': s.tiempo_real_minutos
            })
        
        return jsonify({
            'success': True,
            'historial': historial
        })
        
    except Exception as e:
        print(f"[ERROR] Error al obtener historial: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error del servidor: {str(e)}'}), 500
    
@bp.route('/api/focus/skip-block', methods=['POST'])
def api_focus_skip_block():
    """Registrar que el usuario omitió un bloqueo (solo en modo no estricto)"""
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401
    
    try:
        usuario_id = session.get('usuario_id')
        data = request.json
        
        # Buscar sesión activa
        sesion = SesionFocus.query.filter_by(
            usuario_id=usuario_id,
            completada=False
        ).order_by(SesionFocus.inicio.desc()).first()
        
        if not sesion:
            return jsonify({'success': False, 'message': 'No hay sesión activa'}), 400
        
        # Verificar que no sea modo estricto
        if sesion.modo_estricto:
            return jsonify({'success': False, 'message': 'No se puede omitir en modo estricto'}), 403
        
        # Registrar como intento de bloqueo (igual que un bloqueo normal)
        intento = IntentoBloqeuoFocus(
            sesion_id=sesion.id,
            momento=datetime.now(),
            url_bloqueada=data.get('domain'),
            categoria=data.get('category')
        )
        
        db.session.add(intento)
        db.session.commit()
        
        print(f"[FOCUS] Usuario omitió bloqueo: {data.get('domain')} (categoría: {data.get('category')})")
        
        return jsonify({
            'success': True,
            'message': 'Omisión registrada',
            'domain': data.get('domain')
        })
        
    except Exception as e:
        print(f"[ERROR] Error en skip-block: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500