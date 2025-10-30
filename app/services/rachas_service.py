from app.mysql_conn import get_mysql
from datetime import date

def actualizar_rachas(usuario_id: int, fecha: date = None):
    """
    Actualiza las rachas del usuario para una fecha específica.
    Si no se proporciona fecha, usa hoy.
    Compatible con boot_catchup para procesar fechas históricas.
    """
    conexion = get_mysql()
    with conexion.cursor(dictionary=True, buffered=True) as cursor:
        dia = fecha if fecha is not None else date.today()

        cursor.execute("""
            SELECT COUNT(*) AS total FROM registro
            WHERE usuario_id = %s AND DATE(fecha) = %s
        """, (usuario_id, dia))
        hubo_uso = cursor.fetchone()['total'] > 0
        cursor.fetchall()

        if not hubo_uso:
            return 

        cursor.execute("""
            SELECT COUNT(*) AS total FROM metas_categoria
            WHERE usuario_id = %s AND cumplida = 1 AND DATE(fecha) = %s
        """, (usuario_id, dia))
        cumplio_meta = cursor.fetchone()['total'] > 0
        cursor.fetchall()

        cursor.execute("""
            SELECT * FROM rachas_usuario
            WHERE usuario_id = %s AND tipo = 'metas'
            LIMIT 1
        """, (usuario_id,))
        racha = cursor.fetchone()
        cursor.fetchall()

        if racha:
            if cumplio_meta:
                nuevo_conteo = racha['dias_consecutivos'] + 1
                activar = nuevo_conteo >= 3
                cursor.execute("""
                    UPDATE rachas_usuario
                    SET dias_consecutivos = %s, activa = %s, ultima_fecha = %s
                    WHERE id = %s
                """, (nuevo_conteo, activar, dia, racha['id']))
            else:
                cursor.execute("""
                    UPDATE rachas_usuario
                    SET dias_consecutivos = 0, activa = FALSE, ultima_fecha = %s
                    WHERE id = %s
                """, (dia, racha['id']))
        else:
            cursor.execute("""
                INSERT INTO rachas_usuario (usuario_id, tipo, dias_consecutivos, activa, ultima_fecha)
                VALUES (%s, 'metas', %s, %s, %s)
            """, (usuario_id, 1 if cumplio_meta else 0, False, dia))

        cursor.execute("""
            SELECT dc.categoria_id, SUM(r.tiempo) AS usado, MAX(l.limite_minutos) AS limite
            FROM limite_categoria l
            JOIN dominio_categoria dc ON l.categoria_id = dc.categoria_id
            JOIN registro r ON r.dominio = dc.dominio AND r.usuario_id = l.usuario_id
            WHERE l.usuario_id = %s AND DATE(r.fecha) = %s
            GROUP BY dc.categoria_id
            HAVING usado > limite
        """, (usuario_id, dia))
        excedio_limite = cursor.fetchone() is not None
        cursor.fetchall()

        cursor.execute("""
            SELECT * FROM rachas_usuario
            WHERE usuario_id = %s AND tipo = 'limites'
            LIMIT 1
        """, (usuario_id,))
        racha = cursor.fetchone()
        cursor.fetchall()

        if racha:
            if not excedio_limite:
                nuevo_conteo = racha['dias_consecutivos'] + 1
                activar = nuevo_conteo >= 3
                cursor.execute("""
                    UPDATE rachas_usuario
                    SET dias_consecutivos = %s, activa = %s, ultima_fecha = %s
                    WHERE id = %s
                """, (nuevo_conteo, activar, dia, racha['id']))
            else:
                cursor.execute("""
                    UPDATE rachas_usuario
                    SET dias_consecutivos = 0, activa = FALSE, ultima_fecha = %s
                    WHERE id = %s
                """, (dia, racha['id']))
        else:
            estado = not excedio_limite
            cursor.execute("""
                INSERT INTO rachas_usuario (usuario_id, tipo, dias_consecutivos, activa, ultima_fecha)
                VALUES (%s, 'limites', %s, %s, %s)
            """, (usuario_id, 1 if estado else 0, False, dia))

        conexion.commit()
        
        return {
            "fecha": dia,
            "hubo_uso": hubo_uso,
            "cumplio_meta": cumplio_meta,
            "excedio_limite": excedio_limite
        }