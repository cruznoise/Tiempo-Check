import re
from sqlalchemy import func, text
from app.mysql_conn import get_mysql, close_mysql
from app.models.models import Registro, MetaCategoria, LimiteCategoria, UsuarioLogro, DominioCategoria, FeatureDiaria, FeatureHoraria
from datetime import datetime, date, timedelta
from app.extensions import db 
from app.schedule.scheduler import get_scheduler
from flask import current_app, request, jsonify

def generar_backup_completo(usuario_id):

    def serializar(queryset):
        resultado = []
        for obj in queryset:
            item = {}
            for column in obj.__table__.columns:
                valor = getattr(obj, column.name)
                if isinstance(valor, datetime):
                    valor = valor.strftime('%Y-%m-%d %H:%M:%S')
                item[column.name] = valor
            resultado.append(item)
        return resultado


    registros = serializar(Registro.query.filter_by(usuario_id=usuario_id).all())
    metas = serializar(MetaCategoria.query.filter_by(usuario_id=usuario_id).all())
    limites = serializar(LimiteCategoria.query.filter_by(usuario_id=usuario_id).all())
    logros = serializar(UsuarioLogro.query.filter_by(usuario_id=usuario_id).all())
    dominios = serializar(DominioCategoria.query.all())  

    return {
        "registro": registros,
        "metas": metas,
        "limites": limites,
        "logros": logros,
        "dominios": dominios
    }


def clasificar_dominio_automatico(dominio):
    conexion = get_mysql()
    print(f"[DEBUG] Intentando clasificar dominio: {dominio}")
    
    with conexion.cursor() as cursor:
        cursor.execute("SELECT patron, categoria_id FROM patrones_categoria")
        patrones = cursor.fetchall()

        for patron, categoria_id in patrones:
            if re.search(patron, dominio, re.IGNORECASE):
                print(f"[DEBUG] Match encontrado: {patron} → categoría {categoria_id}")
                cursor.execute("""
                    INSERT INTO dominio_categoria (dominio, categoria_id) VALUES (%s, %s)
                """, (dominio, categoria_id))
                conexion.commit()
                return categoria_id
    
    print("[DEBUG] No se encontró ningún patrón que haga match.")
    return None

def restaurar_backup_completo(data, usuario_id):

    db.session.query(Registro).filter_by(usuario_id=usuario_id).delete()

    for entry in data.get('registro', []):
        nuevo = Registro(
            usuario_id=usuario_id,
            dominio=entry['dominio'],
            tiempo=entry['tiempo'],
            fecha = datetime.strptime(entry['fecha'], '%Y-%m-%d %H:%M:%S')

        )
        db.session.add(nuevo)

    for entry in data.get('metas', []):
        nuevo = MetaCategoria(
            usuario_id=usuario_id,
            categoria_id=entry['categoria_id'],
            limite_minutos=entry['limite_minutos'],
            fecha=datetime.strptime(entry['fecha'], '%Y-%m-%d %H:%M:%S'),
            cumplida=entry.get('cumplida', False)
        )
        db.session.add(nuevo)

    for entry in data.get('limites', []):
        nuevo = LimiteCategoria(
            usuario_id=usuario_id,
            categoria_id=entry['categoria_id'],
            limite_minutos=entry['limite_minutos']
        )
        db.session.add(nuevo)

    for entry in data.get('logros', []):
        nuevo = UsuarioLogro(
            usuario_id=usuario_id,
            logro_id=entry['logro_id']
        )
        db.session.add(nuevo)

    for entry in data.get('dominios', []):
        nuevo = DominioCategoria(
            dominio=entry['dominio'],
            categoria_id=entry['categoria_id']
        )
        db.session.add(nuevo)

    db.session.commit()

def resetear_datos_usuario(usuario_id):
    from app.models.models import Registro, MetaCategoria, LimiteCategoria, UsuarioLogro, DominioCategoria
    from app.mysql_conn import db

    db.session.query(Registro).filter_by(usuario_id=usuario_id).delete()
    db.session.query(MetaCategoria).filter_by(usuario_id=usuario_id).delete()
    db.session.query(LimiteCategoria).filter_by(usuario_id=usuario_id).delete()
    db.session.query(UsuarioLogro).filter_by(usuario_id=usuario_id).delete()

    dominios = db.session.query(DominioCategoria).all()
    for d in dominios:
        db.session.delete(d)

    db.session.commit()

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
