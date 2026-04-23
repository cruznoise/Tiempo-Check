import re
from sqlalchemy import func, text
from app.mysql_conn import get_mysql, close_mysql
from app.models.models import Registro, Categoria, MetaCategoria, LimiteCategoria, UsuarioLogro, DominioCategoria, ContextoDia, PatronCategoria, RachaUsuario, ConfiguracionLogro, AggEstadoDia, AggVentanaCategoria, AggKpiRango
from app.models.ml import MLModelo, MLPrediccionFuture, MlMetric
from app.models.features import FeatureDiaria, FeatureHoraria
from app.models.models_coach import CoachAlerta, CoachSugerencia, CoachAccionLog, NotificacionClasificacion, CoachEstadoRegla
from datetime import datetime, date, timedelta
from app.extensions import db 
from app.schedule.scheduler import get_scheduler
from flask import current_app, request, jsonify

def generar_backup_completo(usuario_id):
    """Genera backup completo con las clases correctas"""
    
    def serializar(queryset):
        resultado = []
        for obj in queryset:
            item = {}
            for column in obj.__table__.columns:
                try:
                    # Usar column.key en lugar de column.name para obtener el atributo Python
                    valor = getattr(obj, column.key)
                    if isinstance(valor, datetime):
                        valor = valor.strftime('%Y-%m-%d %H:%M:%S')
                    elif isinstance(valor, date):
                        valor = valor.strftime('%Y-%m-%d')
                    # Guardar con el nombre de la columna en BD
                    item[column.name] = valor
                except AttributeError:
                    # Si el atributo no existe, intentar con column.name
                    try:
                        valor = getattr(obj, column.name)
                        if isinstance(valor, datetime):
                            valor = valor.strftime('%Y-%m-%d %H:%M:%S')
                        elif isinstance(valor, date):
                            valor = valor.strftime('%Y-%m-%d')
                        item[column.name] = valor
                    except AttributeError:
                        # Si aún no funciona, skip este campo
                        continue
            resultado.append(item)
        return resultado
    from app.models.models import (
        Registro, MetaCategoria, LimiteCategoria, UsuarioLogro,
        DominioCategoria, Categoria, ContextoDia,
        AggEstadoDia, AggVentanaCategoria, AggKpiRango,
        PatronCategoria, RachaUsuario 
    )
    from app.models.features import FeatureDiaria, FeatureHoraria
    from app.models.ml import MLModelo, MlMetric, MLPrediccionFuture
    from app.models.models_coach import (
        CoachAlerta, CoachSugerencia, CoachAccionLog, 
        CoachEstadoRegla, NotificacionClasificacion
    )
    
    # DATOS PRINCIPALES
    registros = serializar(Registro.query.filter_by(usuario_id=usuario_id).all())
    
    # CONFIGURACIÓN Y GAMIFICACIÓN
    metas = serializar(MetaCategoria.query.filter_by(usuario_id=usuario_id).all())
    limites = serializar(LimiteCategoria.query.filter_by(usuario_id=usuario_id).all())
    logros = serializar(UsuarioLogro.query.filter_by(usuario_id=usuario_id).all())
    
    # Rachas (con try/catch por si no existe)
    try:
        rachas = serializar(RachaUsuario.query.filter_by(usuario_id=usuario_id).all())
    except:
        rachas = []
    
    # MACHINE LEARNING
    contexto_dia = serializar(ContextoDia.query.filter_by(usuario_id=usuario_id).all())
    ml_predicciones = serializar(MLPrediccionFuture.query.filter_by(usuario_id=usuario_id).all())
    ml_metrics = serializar(MlMetric.query.filter_by(usuario_id=usuario_id).all())
    ml_modelos = serializar(MLModelo.query.filter_by(usuario_id=usuario_id).all())
    features_diarias = serializar(FeatureDiaria.query.filter_by(usuario_id=usuario_id).all())
    features_horarias = serializar(FeatureHoraria.query.filter_by(usuario_id=usuario_id).all())
    
    # COACHING
    coach_sugerencias = serializar(CoachSugerencia.query.filter_by(usuario_id=usuario_id).all())
    coach_alertas = serializar(CoachAlerta.query.filter_by(usuario_id=usuario_id).all())
    coach_acciones = serializar(CoachAccionLog.query.filter_by(usuario_id=usuario_id).all())
    coach_estado_reglas = serializar(CoachEstadoRegla.query.filter_by(usuario_id=usuario_id).all())
    
    # ANÁLISIS Y PATRONES
    patrones = serializar(PatronCategoria.query.filter_by(usuario_id=usuario_id).all())  
    agg_estado_dia = serializar(AggEstadoDia.query.filter_by(usuario_id=usuario_id).all())
    agg_ventana = serializar(AggVentanaCategoria.query.filter_by(usuario_id=usuario_id).all())
    agg_kpi = serializar(AggKpiRango.query.filter_by(usuario_id=usuario_id).all())
    notificaciones = serializar(NotificacionClasificacion.query.filter_by(usuario_id=usuario_id).all())
    
    # DATOS UNICOS POR USUARIO!!!!! NO SE COMPARTE NADA
    dominios = serializar(DominioCategoria.query.filter_by(usuario_id=usuario_id).all())
    categorias = serializar(Categoria.query.filter_by(usuario_id=usuario_id).all())

    return {
        # Datos principales
        "registro": registros,
        
        # Configuración y gamificación
        "metas": metas,
        "limites": limites,
        "logros": logros,
        "rachas": rachas,
        
        # Machine Learning
        "contexto_dia": contexto_dia,
        "ml_predicciones": ml_predicciones,
        "ml_metrics": ml_metrics,
        "ml_modelos": ml_modelos,
        "features_diarias": features_diarias,
        "features_horarias": features_horarias,
        
        # Coaching
        "coach_sugerencias": coach_sugerencias,
        "coach_alertas": coach_alertas,
        "coach_acciones": coach_acciones,
        "coach_estado_reglas": coach_estado_reglas,
        
        # Análisis
        "patrones": patrones,  
        "agg_estado_dia": agg_estado_dia,
        "agg_ventana": agg_ventana,
        "agg_kpi": agg_kpi,
        "notificaciones_clasificacion": notificaciones,
        
        # Datos compartidos (solo referencia, no se restauran)
        "dominios": dominios,
        "categorias": categorias,
        
        # Metadata
        "fecha_backup": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "usuario_id": usuario_id,
        "version_backup": "3.2"
    }

def restaurar_backup_completo(data, usuario_id):
    """
    Restaura un backup completo del usuario.
    ADVERTENCIA: Esto borrará todos los datos existentes del usuario antes de restaurar.
    """
    from app.models.models import (
        Registro, MetaCategoria, LimiteCategoria, UsuarioLogro,
        DominioCategoria, ContextoDia, AggEstadoDia, 
        AggVentanaCategoria, AggKpiRango, PatronCategoria, RachaUsuario
    )
    from app.models.features import FeatureDiaria, FeatureHoraria
    from app.models.ml import MLModelo, MlMetric, MLPrediccionFuture
    from app.models.models_coach import (
        CoachAlerta, CoachSugerencia, CoachAccionLog,
        CoachEstadoRegla, NotificacionClasificacion
    )
    from app.extensions import db
    from datetime import datetime, date
    
    try:
        # PASO 1: Eliminar datos existentes del usuario (usar la función que ya tienes)
        print(f"[DEBUG] Eliminando datos existentes del usuario {usuario_id}")
        resultado_limpieza = resetear_datos_usuario(usuario_id)
        
        if not resultado_limpieza.get("success"):
            return {"success": False, "error": "No se pudieron limpiar los datos existentes"}
        
        # PASO 2: Restaurar datos principales
        print(f"[DEBUG] Restaurando registros...")
        for entry in data.get('registro', []):
            nuevo = Registro(
                usuario_id=usuario_id,
                dominio=entry['dominio'],
                tiempo=entry['tiempo'],
                fecha=datetime.strptime(entry['fecha'], '%Y-%m-%d %H:%M:%S') if isinstance(entry['fecha'], str) else entry['fecha']
            )
            db.session.add(nuevo)
        
        # PASO 3: Restaurar configuración
        print(f"[DEBUG] Restaurando metas...")
        for entry in data.get('metas', []):
            nuevo = MetaCategoria(
                usuario_id=usuario_id,
                categoria_id=entry['categoria_id'],
                minutos_meta=entry.get('minutos_meta', entry.get('limite_minutos')),
                fecha=datetime.strptime(entry['fecha'], '%Y-%m-%d').date() if isinstance(entry['fecha'], str) else entry['fecha'],
                cumplida=entry.get('cumplida', False),
                origen=entry.get('origen', 'manual')
            )
            db.session.add(nuevo)
        
        print(f"[DEBUG] Restaurando límites...")
        for entry in data.get('limites', []):
            nuevo = LimiteCategoria(
                usuario_id=usuario_id,
                categoria_id=entry['categoria_id'],
                limite_minutos=entry['limite_minutos']
            )
            db.session.add(nuevo)
        
        print(f"[DEBUG] Restaurando logros...")
        for entry in data.get('logros', []):
            nuevo = UsuarioLogro(
                usuario_id=usuario_id,
                logro_id=entry['logro_id']
            )
            db.session.add(nuevo)
        
        # PASO 4: Restaurar ML y contexto
        print(f"[DEBUG] Restaurando contexto de días...")
        for entry in data.get('contexto_dia', []):
            nuevo = ContextoDia(
                usuario_id=usuario_id,
                fecha=datetime.strptime(entry['fecha'], '%Y-%m-%d').date() if isinstance(entry['fecha'], str) else entry['fecha'],
                es_atipico=entry.get('es_atipico', False),
                motivo=entry.get('motivo'),
                motivo_detalle=entry.get('motivo_detalle'),
                uso_esperado_min=entry.get('uso_esperado_min'),
                uso_real_min=entry.get('uso_real_min'),
                desviacion_pct=entry.get('desviacion_pct')
            )
            db.session.add(nuevo)
        
        # ✅ NUEVO: Restaurar anomalías
        print(f"[DEBUG] Restaurando anomalías...")
        for entry in data.get('anomalias', []):
            fecha_anomalia = datetime.strptime(entry['fecha'], '%Y-%m-%d').date() if isinstance(entry['fecha'], str) else entry['fecha']
            
            # Buscar si ya existe contexto para ese día
            contexto = ContextoDia.query.filter_by(
                usuario_id=usuario_id,
                fecha=fecha_anomalia
            ).first()
            
            if contexto:
                # Actualizar existente
                contexto.es_atipico = True
                contexto.motivo = entry.get('motivo')
                contexto.motivo_detalle = entry.get('detalle')  # ✅ Nota: en anomalias es 'detalle', no 'motivo_detalle'
                print(f"[DEBUG]   Actualizado contexto existente para {fecha_anomalia}: {entry.get('motivo')}")
            else:
                # Crear nuevo
                nuevo_contexto = ContextoDia(
                    usuario_id=usuario_id,
                    fecha=fecha_anomalia,
                    es_atipico=True,
                    motivo=entry.get('motivo'),
                    motivo_detalle=entry.get('detalle')
                )
                db.session.add(nuevo_contexto)
                print(f"[DEBUG]   Creado nuevo contexto para {fecha_anomalia}: {entry.get('motivo')}")
        
        print(f"[DEBUG] {len(data.get('anomalias', []))} anomalías procesadas")
        
        print(f"[DEBUG] Restaurando predicciones ML...")
        for entry in data.get('ml_predicciones', []):
            nuevo = MLPrediccionFuture(
                usuario_id=usuario_id,
                fecha_pred=datetime.strptime(entry['fecha_pred'], '%Y-%m-%d').date() if isinstance(entry['fecha_pred'], str) else entry['fecha_pred'],
                categoria=entry.get('categoria'),
                yhat_minutos=entry.get('yhat_minutos'),
                modelo=entry.get('modelo', 'RandomForest'),
                version_modelo=entry.get('version_modelo', 'v3.2')
            )
            db.session.add(nuevo)
        
        print(f"[DEBUG] Restaurando métricas ML...")
        for entry in data.get('ml_metrics', []):
            nuevo = MlMetric(
                fecha=datetime.strptime(entry['fecha'], '%Y-%m-%d').date() if isinstance(entry['fecha'], str) else entry['fecha'],
                usuario_id=usuario_id,
                modelo=entry.get('modelo'),
                categoria=entry.get('categoria'),
                hist_days=entry.get('hist_days'),
                rows_train=entry.get('rows_train'),
                rows_test=entry.get('rows_test'),
                metric_mae=entry.get('metric_mae'),
                metric_rmse=entry.get('metric_rmse')
            )
            db.session.add(nuevo)
        
        print(f"[DEBUG] Restaurando features diarias...")
        for entry in data.get('features_diarias', []):
            nuevo = FeatureDiaria(
                usuario_id=usuario_id,
                fecha=datetime.strptime(entry['fecha'], '%Y-%m-%d').date() if isinstance(entry['fecha'], str) else entry['fecha'],
                categoria=entry.get('categoria'),
                minutos=entry.get('minutos', 0)
            )
            db.session.add(nuevo)
        
        # PASO 5: Restaurar coaching
        print(f"[DEBUG] Restaurando patrones personalizados...")
        for entry in data.get('patrones', []):
            nuevo = PatronCategoria(
                usuario_id=usuario_id,
                categoria_id=entry['categoria_id'],
                patron=entry['patron'],
                activo=entry.get('activo', True),  
            )
            db.session.add(nuevo)
        
        # PASO 6: Commit final
        db.session.commit()
        print(f"[DEBUG] ✅ Backup restaurado exitosamente")
        
        return {"success": True, "mensaje": "Backup restaurado exitosamente"}
        
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Error al restaurar backup: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}
    
def resetear_datos_usuario(usuario_id):
    """Borra TODOS los datos del usuario excepto su cuenta."""
    from app.models.models import (
        Registro, MetaCategoria, LimiteCategoria, UsuarioLogro,
        ContextoDia, AggEstadoDia, AggVentanaCategoria, AggKpiRango,
        PatronCategoria, RachaUsuario  # ✅
    )
    from app.models.features import FeatureDiaria, FeatureHoraria
    from app.models.ml import MLModelo, MlMetric, MLPrediccionFuture
    from app.models.models_coach import (
        CoachAlerta, CoachSugerencia, CoachAccionLog,
        CoachEstadoRegla, NotificacionClasificacion
    )
    from app.extensions import db
    
    try:
        # Limpiar todas las tablas POR USUARIO
        db.session.query(Registro).filter_by(usuario_id=usuario_id).delete()
        db.session.query(MetaCategoria).filter_by(usuario_id=usuario_id).delete()
        db.session.query(LimiteCategoria).filter_by(usuario_id=usuario_id).delete()
        db.session.query(UsuarioLogro).filter_by(usuario_id=usuario_id).delete()
        
        db.session.query(PatronCategoria).filter_by(usuario_id=usuario_id).delete()  # ✅
        
        try:
            db.session.query(RachaUsuario).filter_by(usuario_id=usuario_id).delete()
        except:
            pass
        
        db.session.query(ContextoDia).filter_by(usuario_id=usuario_id).delete()
        db.session.query(MLPrediccionFuture).filter_by(usuario_id=usuario_id).delete()
        db.session.query(MlMetric).filter_by(usuario_id=usuario_id).delete()
        db.session.query(MLModelo).filter_by(usuario_id=usuario_id).delete()
        db.session.query(FeatureDiaria).filter_by(usuario_id=usuario_id).delete()
        db.session.query(FeatureHoraria).filter_by(usuario_id=usuario_id).delete()
        
        db.session.query(CoachSugerencia).filter_by(usuario_id=usuario_id).delete()
        db.session.query(CoachAlerta).filter_by(usuario_id=usuario_id).delete()
        db.session.query(CoachAccionLog).filter_by(usuario_id=usuario_id).delete()
        db.session.query(CoachEstadoRegla).filter_by(usuario_id=usuario_id).delete()
        
        db.session.query(AggEstadoDia).filter_by(usuario_id=usuario_id).delete()
        db.session.query(AggVentanaCategoria).filter_by(usuario_id=usuario_id).delete()
        db.session.query(AggKpiRango).filter_by(usuario_id=usuario_id).delete()
        db.session.query(NotificacionClasificacion).filter_by(usuario_id=usuario_id).delete()
        
        # NO tocamos: logros_dinamicos, dominio_categoria, categorias (son globales)
        
        db.session.commit()
        return {"success": True, "mensaje": "Todos los datos del usuario han sido eliminados"}
        
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Error al resetear usuario: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

def desbloquear_logro(usuario_id, logro_id):
    conn = get_mysql()
    cursor = db.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM usuario_logro 
            WHERE usuario_id = %s AND logro_id = %s
        """, (usuario_id, logro_id))
        ya_lo_tiene = cursor.fetchone()[0]

        if not ya_lo_tiene:
            cursor.execute("""
                INSERT INTO usuario_logro (usuario_id, logro_id)
                VALUES (%s, %s)
            """, (usuario_id, logro_id))
            db.commit()
    finally:
        cursor.fetchall()  
        cursor.close()
   

def verificar_logros_dinamicos(usuario_id: int):
    cnx = get_mysql()
    try:

        with cnx.cursor(dictionary=True, buffered=True) as cursor:

            cursor.execute("SELECT * FROM logros_dinamicos")
            logros = cursor.fetchall()  

            for logro in logros:
                logro_id     = logro['logro_id']
                tipo         = logro['tipo_condicion']
                categoria_id = logro['categoria_id']
                valor        = logro['valor_referencia']

                cursor.execute("""
                    SELECT COUNT(*) AS c
                    FROM usuario_logro
                    WHERE usuario_id = %s AND logro_id = %s
                """, (usuario_id, logro_id))
                if cursor.fetchone()['c'] > 0:
                    continue  
                cumple = False

                if tipo == 'total_metas':
                    cursor.execute("""
                        SELECT COUNT(*) AS total
                        FROM metas_categoria
                        WHERE usuario_id = %s
                    """, (usuario_id,))
                    cumple = cursor.fetchone()['total'] >= valor

                elif tipo == 'total_limites':
                    cursor.execute("""
                        SELECT COUNT(*) AS total
                        FROM limite_categoria
                        WHERE usuario_id = %s
                    """, (usuario_id,))
                    cumple = cursor.fetchone()['total'] >= valor

                elif tipo == 'minutos_categoria_total':
                    cursor.execute("""
                        SELECT SUM(r.tiempo) AS total
                        FROM registro r
                        JOIN dominio_categoria dc ON r.dominio = dc.dominio
                        WHERE r.usuario_id = %s AND dc.categoria_id = %s
                    """, (usuario_id, categoria_id))
                    minutos = cursor.fetchone()['total'] or 0
                    cumple = minutos >= valor if valor >= 0 else minutos <= abs(valor)

                elif tipo == 'metas_cumplidas':
                    cursor.execute("""
                        SELECT COUNT(*) AS total
                        FROM metas_categoria
                        WHERE usuario_id = %s AND cumplida = 1
                    """, (usuario_id,))
                    cumple = cursor.fetchone()['total'] >= valor

                elif tipo == 'minutos_categoria_dia':
                    hoy = date.today()
                    cursor.execute("""
                        SELECT SUM(r.tiempo) AS total
                        FROM registro r
                        JOIN dominio_categoria dc ON r.dominio = dc.dominio
                        WHERE r.usuario_id = %s AND dc.categoria_id = %s AND DATE(r.fecha) = %s
                    """, (usuario_id, categoria_id, hoy))
                    minutos = cursor.fetchone()['total'] or 0
                    cumple = minutos >= valor if valor >= 0 else minutos <= abs(valor)

                elif tipo == 'metas_dias_consecutivos':
                    cursor.execute("""
                        SELECT DATE(fecha) AS dia
                        FROM metas_categoria
                        WHERE usuario_id = %s AND cumplida = 1
                        GROUP BY DATE(fecha)
                        ORDER BY dia DESC
                    """, (usuario_id,))
                    dias_cumplidos = [row['dia'] for row in cursor.fetchall()]
                    racha = 0
                    hoy = date.today()
                    for i in range(valor):
                        dia_revisado = hoy - timedelta(days=i)
                        if dia_revisado in dias_cumplidos:
                            racha += 1
                        else:
                            break
                    cumple = racha >= valor

                elif tipo == 'dias_sin_exceder_limites':
                    racha = 0
                    hoy = date.today()
                    for i in range(valor):
                        dia = hoy - timedelta(days=i)

                        cursor.execute("""
                            SELECT COUNT(*) AS total
                            FROM registro
                            WHERE usuario_id = %s AND DATE(fecha) = %s
                        """, (usuario_id, dia))
                        hubo_uso = cursor.fetchone()['total'] > 0
                        if not hubo_uso:
                            break

                        cursor.execute("""
                            SELECT 1
                            FROM limite_categoria l
                            JOIN dominio_categoria dc ON l.categoria_id = dc.categoria_id
                            JOIN registro r ON r.dominio = dc.dominio AND r.usuario_id = l.usuario_id
                            WHERE l.usuario_id = %s AND DATE(r.fecha) = %s
                            GROUP BY dc.categoria_id
                            HAVING SUM(r.tiempo) > MAX(l.limite_minutos)
                            LIMIT 1
                        """, (usuario_id, dia))
                        excedio = cursor.fetchone() is not None

                        if excedio:
                            break
                        racha += 1

                    cumple = racha >= valor

                elif tipo == 'equilibrio_digital':
                    racha = 0
                    hoy = date.today()
                    for i in range(valor):
                        dia = hoy - timedelta(days=i)

                        cursor.execute("""
                            SELECT 1
                            FROM metas_categoria
                            WHERE usuario_id = %s AND cumplida = 1 AND DATE(fecha) = %s
                            LIMIT 1
                        """, (usuario_id, dia))
                        meta_ok = cursor.fetchone() is not None

                        cursor.execute("""
                            SELECT 1
                            FROM limite_categoria l
                            JOIN dominio_categoria dc ON l.categoria_id = dc.categoria_id
                            JOIN registro r ON r.dominio = dc.dominio AND r.usuario_id = l.usuario_id
                            WHERE l.usuario_id = %s AND DATE(r.fecha) = %s
                            GROUP BY dc.categoria_id
                            HAVING SUM(r.tiempo) > MAX(l.limite_minutos)
                            LIMIT 1
                        """, (usuario_id, dia))
                        limites_ok = cursor.fetchone() is None

                        if meta_ok and limites_ok:
                            racha += 1
                        else:
                            break

                    cumple = racha >= valor

                elif tipo == 'metas_categoria_cumplidas':
                    cursor.execute("""
                        SELECT COUNT(*) AS total
                        FROM metas_categoria
                        WHERE usuario_id = %s AND cumplida = 1 AND categoria_id = %s
                    """, (usuario_id, categoria_id))
                    cumple = cursor.fetchone()['total'] >= valor


                if cumple:
                    try:
                        cursor.execute("""
                            INSERT INTO usuario_logro (usuario_id, logro_id)
                            VALUES (%s, %s)
                        """, (usuario_id, logro_id))
                    except Exception as e:

                        print(f"[logros] Error al insertar logro {logro_id}: {e}")

        cnx.commit()
    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()

def obtener_promedio_categoria(usuario_id, categoria_id, dias=5):
    """
    Calcula el promedio diario de uso (en MINUTOS) para una categoría en los últimos N días.
    Convierte automáticamente los tiempos de segundos a minutos para que las sugerencias sean realistas.
    """
    hoy = date.today()
    fecha_inicio = hoy - timedelta(days=dias)

    registros = db.session.execute(text("""
        SELECT SUM(r.tiempo) as total
        FROM registro r
        JOIN dominio_categoria dc ON r.dominio = dc.dominio
        WHERE r.usuario_id = :usuario_id
          AND dc.categoria_id = :categoria_id
          AND DATE(r.fecha) BETWEEN :inicio AND :hoy
        GROUP BY DATE(r.fecha)
    """), {
        "usuario_id": usuario_id,
        "categoria_id": categoria_id,
        "inicio": fecha_inicio,
        "hoy": hoy
    }).fetchall()

    tiempos = [row.total for row in registros if row.total is not None]
    if not tiempos:
        return 0

    promedio_segundos = float(sum(tiempos)) / len(tiempos)

    promedio_minutos = promedio_segundos / 60.0

    return promedio_minutos


def calcular_sugerencias_por_categoria(categoria, promedio):
    """
    Aplica el porcentaje según categoría y devuelve (meta, límite).
    """
    nombre = categoria.nombre.lower()
    if nombre in ['productividad', 'estudio', 'trabajo', 'herramientas']:
        meta_sugerida = int(promedio * 1.30)
        limite_sugerido = int(promedio * 0.90)
    elif nombre in ['ocio', 'redes sociales', 'comercio']:
        meta_sugerida = int(promedio * 0.70)
        limite_sugerido = int(promedio * 0.50)
    else:
        meta_sugerida = int(promedio)
        limite_sugerido = int(promedio * 0.80)

    MAX_POR_CATEGORIA = {
        'productividad': 600,
        'estudio': 480,
        'redes sociales': 180,
        'ocio': 120,
        'comercio': 240
    }

    maximo = MAX_POR_CATEGORIA.get(nombre)
    if maximo:
        meta_sugerida = min(meta_sugerida, maximo)
        limite_sugerido = min(limite_sugerido, maximo)

    return meta_sugerida, limite_sugerido


def calcular_nivel_confianza(dias_con_datos: int) -> str:
    """
    Determina el nivel de confianza basado en días de uso efectivos.
    """
    if dias_con_datos <= 2:
        return "insuficiente"
    elif 3 <= dias_con_datos <= 6:
        return "baja"
    elif 7 <= dias_con_datos <= 14:
        return "media"
    else:
        return "alta"


def obtener_dias_uso(usuario_id: int) -> int:
    """
    Cuenta los días distintos en los que el usuario tuvo registros.
    """
    dias_uso = db.session.query(
        func.count(func.distinct(func.date(Registro.fecha)))
    ).filter(
        Registro.usuario_id == usuario_id
    ).scalar()

    return dias_uso or 0


from urllib.parse import urlparse

MULTI_TLDS = {
    ("com", "mx"), ("org", "mx"), ("gob", "mx"),
    ("co", "uk"), ("com", "ar"), ("com", "br")
}

def _solo_host(s: str) -> str:
    if not s:
        return ""
    s = s.strip().lower()
    if "://" in s:
        s = urlparse(s).netloc or s
    s = s.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0].split(":", 1)[0]
    if s.startswith("www."):
        s = s[4:]
    return s

def dominio_base(s: str) -> str:
    host = _solo_host(s)
    if not host:
        return ""
    parts = host.split(".")
    if len(parts) >= 3:

        if (parts[-2], parts[-1]) in MULTI_TLDS:
            return ".".join(parts[-3:])
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host  
def _qa_invariantes_dia(usuario_id: int, d: date):
    """
    Invariante: para cada categoría, sum(minutos por hora) == minutos diarios.
    """

    diarias = {
        r.categoria: r.minutos
        for r in FeatureDiaria.query.filter_by(usuario_id=usuario_id, fecha=d).all()
    }

    horarias_sum = {}
    for r in FeatureHoraria.query.filter_by(usuario_id=usuario_id, fecha=d).all():
        horarias_sum[r.categoria] = horarias_sum.get(r.categoria, 0) + int(r.minutos)

    ok = True
    detalles = []
    cats = set(diarias.keys()) | set(horarias_sum.keys())
    for c in cats:
        vd = int(diarias.get(c, 0))
        vh = int(horarias_sum.get(c, 0))
        if vd != vh:
            ok = False
            detalles.append({"categoria": c, "diaria": vd, "horas_sum": vh, "delta": vh - vd})

    return {"usuario_id": usuario_id, "dia": d.isoformat(), "ok": ok, "detalles": detalles}
