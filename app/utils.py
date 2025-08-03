import re
from sqlalchemy import func, text
from app.db import get_db, db  
from app.models.models import Registro, MetaCategoria, LimiteCategoria, UsuarioLogro, DominioCategoria, db
from datetime import datetime, date, timedelta

def generar_backup_completo(usuario_id):
    # Convierte cualquier consulta de modelos SQLAlchemy en listas de diccionarios
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
    conexion = get_db()
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

    # Limpiar registros previos (opcional, según política)
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
    from app.db import db

    db.session.query(Registro).filter_by(usuario_id=usuario_id).delete()
    db.session.query(MetaCategoria).filter_by(usuario_id=usuario_id).delete()
    db.session.query(LimiteCategoria).filter_by(usuario_id=usuario_id).delete()
    db.session.query(UsuarioLogro).filter_by(usuario_id=usuario_id).delete()

    # ⚠️ Elimina dominios asignados solo si son personalizados por ese usuario (ajusta si no)
    dominios = db.session.query(DominioCategoria).all()
    for d in dominios:
        db.session.delete(d)

    db.session.commit()

#definicion de desbloquear logros
def desbloquear_logro(usuario_id, logro_id):
    db = get_db()
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
        cursor.fetchall()  # Por si acaso quedó algo pendiente
        cursor.close()
   

def verificar_logros_dinamicos(usuario_id):
    conexion = get_db()
    with conexion.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT * FROM logros_dinamicos")
        logros = cursor.fetchall()

        for logro in logros:
            logro_id = logro['logro_id']
            tipo = logro['tipo_condicion']
            categoria_id = logro['categoria_id']
            valor = logro['valor_referencia']

            cursor.execute("""
                SELECT 1 FROM usuario_logro
                WHERE usuario_id = %s AND logro_id = %s
            """, (usuario_id, logro_id))
            if cursor.fetchone():
                continue
            else:
                cursor.fetchall()

            cumple = False

            if tipo == 'total_metas':
                cursor.execute("SELECT COUNT(*) AS total FROM metas_categoria WHERE usuario_id = %s", (usuario_id,))
                cumple = cursor.fetchone()['total'] >= valor

            elif tipo == 'total_limites':
                cursor.execute("SELECT COUNT(*) AS total FROM limite_categoria WHERE usuario_id = %s", (usuario_id,))
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
                    SELECT COUNT(*) AS total FROM metas_categoria
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
                        SELECT dc.categoria_id, SUM(r.tiempo) AS total_usado, MAX(l.limite_minutos) AS limite
                        FROM limite_categoria l
                        JOIN dominio_categoria dc ON l.categoria_id = dc.categoria_id
                        JOIN registro r ON r.dominio = dc.dominio AND r.usuario_id = l.usuario_id
                        WHERE l.usuario_id = %s AND DATE(r.fecha) = %s
                        GROUP BY dc.categoria_id
                        HAVING total_usado > limite
                    """, (usuario_id, dia))
                    if cursor.fetchone():
                        cursor.fetchall()
                        break
                    else:
                        cursor.fetchall()
                        racha += 1

                cumple = racha >= valor

            elif tipo == 'equilibrio_digital':
                racha = 0
                hoy = date.today()
                for i in range(valor):
                    dia = hoy - timedelta(days=i)

                    cursor.execute("""
                        SELECT 1 FROM metas_categoria
                        WHERE usuario_id = %s AND cumplida = 1 AND DATE(fecha) = %s
                    """, (usuario_id, dia))
                    meta_ok = cursor.fetchone() is not None

                    cursor.execute("""
                        SELECT dc.categoria_id, SUM(r.tiempo) AS total_usado, MAX(l.limite_minutos) AS limite
                        FROM limite_categoria l
                        JOIN dominio_categoria dc ON l.categoria_id = dc.categoria_id
                        JOIN registro r ON r.dominio = dc.dominio AND r.usuario_id = l.usuario_id
                        WHERE l.usuario_id = %s AND DATE(r.fecha) = %s
                        GROUP BY dc.categoria_id
                        HAVING total_usado > limite
                    """, (usuario_id, dia))
                    limites_ok = cursor.fetchone() is None
                    cursor.fetchall()

                    if meta_ok and limites_ok:
                        racha += 1
                    else:
                        break

                cumple = racha >= valor

            elif tipo == 'metas_categoria_cumplidas':
                cursor.execute("""
                    SELECT COUNT(*) AS total FROM metas_categoria
                    WHERE usuario_id = %s AND cumplida = 1 AND categoria_id = %s
                """, (usuario_id, categoria_id))
                cumple = cursor.fetchone()['total'] >= valor

            # 🔓 Si se cumple, desbloquear el logro
            if cumple:
                try:
                    cursor.execute("""
                        INSERT INTO usuario_logro (usuario_id, logro_id)
                        VALUES (%s, %s)
                    """, (usuario_id, logro_id))
                except Exception as e:
                    print(f"Error al insertar logro {logro_id}: {e}")

        conexion.commit()

#panel para rachas

def actualizar_rachas(usuario_id):
    conexion = get_db()
    with conexion.cursor(dictionary=True) as cursor:
        hoy = date.today()

        # --- Verificar si el usuario usó el navegador hoy ---
        cursor.execute("""
            SELECT COUNT(*) AS total FROM registro
            WHERE usuario_id = %s AND DATE(fecha) = %s
        """, (usuario_id, hoy))
        hubo_uso = cursor.fetchone()['total'] > 0

        if not hubo_uso:
            return  # No hacemos nada si no usó navegador hoy

        ### Racha de METAS
        cursor.execute("""
            SELECT COUNT(*) AS total FROM metas_categoria
            WHERE usuario_id = %s AND cumplida = 1 AND DATE(fecha) = %s
        """, (usuario_id, hoy))
        cumplio_meta = cursor.fetchone()['total'] > 0

        cursor.execute("""
            SELECT * FROM rachas_usuario
            WHERE usuario_id = %s AND tipo = 'metas'
        """, (usuario_id,))
        racha = cursor.fetchone()

        if racha:
            if cumplio_meta:
                nuevo_conteo = racha['dias_consecutivos'] + 1
                activar = nuevo_conteo >= 3
                cursor.execute("""
                    UPDATE rachas_usuario
                    SET dias_consecutivos = %s, activa = %s, ultima_fecha = %s
                    WHERE id = %s
                """, (nuevo_conteo, activar, hoy, racha['id']))
            else:
                # Si no cumplió meta, reiniciar racha
                cursor.execute("""
                    UPDATE rachas_usuario
                    SET dias_consecutivos = 0, activa = FALSE, ultima_fecha = %s
                    WHERE id = %s
                """, (hoy, racha['id']))
        else:
            # Crear la racha si no existe
            estado = cumplio_meta
            cursor.execute("""
                INSERT INTO rachas_usuario (usuario_id, tipo, dias_consecutivos, activa, ultima_fecha)
                VALUES (%s, 'metas', %s, %s, %s)
            """, (usuario_id, 1 if cumplio_meta else 0, False, hoy))

        ### Racha de LIMITES
        cursor.execute("""
            SELECT dc.categoria_id, SUM(r.tiempo) AS usado, MAX(l.limite_minutos) AS limite
            FROM limite_categoria l
            JOIN dominio_categoria dc ON l.categoria_id = dc.categoria_id
            JOIN registro r ON r.dominio = dc.dominio AND r.usuario_id = l.usuario_id
            WHERE l.usuario_id = %s AND DATE(r.fecha) = %s
            GROUP BY dc.categoria_id
            HAVING usado > limite
        """, (usuario_id, hoy))
        excedio_limite = cursor.fetchone() is not None

        cursor.execute("""
            SELECT * FROM rachas_usuario
            WHERE usuario_id = %s AND tipo = 'limites'
        """, (usuario_id,))
        racha = cursor.fetchone()

        if racha:
            if not excedio_limite:
                nuevo_conteo = racha['dias_consecutivos'] + 1
                activar = nuevo_conteo >= 3
                cursor.execute("""
                    UPDATE rachas_usuario
                    SET dias_consecutivos = %s, activa = %s, ultima_fecha = %s
                    WHERE id = %s
                """, (nuevo_conteo, activar, hoy, racha['id']))
            else:
                # Si excedió límite, reiniciar
                cursor.execute("""
                    UPDATE rachas_usuario
                    SET dias_consecutivos = 0, activa = FALSE, ultima_fecha = %s
                    WHERE id = %s
                """, (hoy, racha['id']))
        else:
            estado = not excedio_limite
            cursor.execute("""
                INSERT INTO rachas_usuario (usuario_id, tipo, dias_consecutivos, activa, ultima_fecha)
                VALUES (%s, 'limites', %s, %s, %s)
            """, (usuario_id, 1 if estado else 0, False, hoy))

        conexion.commit()

# ---------------------------
# FUNCIONES DE SUGERENCIAS
# ---------------------------

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

    # Extraer los valores diarios
    tiempos = [row.total for row in registros if row.total is not None]
    if not tiempos:
        return 0

    # Promedio en segundos
    promedio_segundos = float(sum(tiempos)) / len(tiempos)
    # Convertir a minutos para que coincida con tus sugerencias visibles
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

    # Tope por categoría
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

# ---------------------------
# FUNCIONES DE CONFIANZA
# ---------------------------

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