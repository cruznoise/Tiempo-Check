from flask import Blueprint, request, jsonify, render_template, Response, session
from sqlalchemy import text, and_, func
from datetime import datetime, timedelta, date
from collections import defaultdict
from app.models import db, Usuario, Registro, Categoria, DominioCategoria
from app.models.models import LimiteCategoria, Registro, DominioCategoria
from app.db import close_db
import tldextract



admin_base = Blueprint('admin_base', __name__)


controlador = Blueprint('controlador', __name__)
def limpiar_dominio(url):

    ext = tldextract.extract(url)
    return f"{ext.domain}.{ext.suffix}" if ext.domain and ext.suffix else url

def guardar_tiempo(request, usuario_id):
    data = request.get_json()
    dominio = data.get('dominio')
    tiempo = data.get('tiempo')

    # Validaciones básicas
    if tiempo is None or not isinstance(tiempo, int) or tiempo <= 0:
        return jsonify({'error': 'Tiempo inválido'}), 400
    if not dominio:
        return jsonify({'error': 'Faltan datos'}), 400

    # 🔹 Normalizar dominio antes de guardar
    dominio_limpio = limpiar_dominio(dominio)

    print(f"[✔] Petición recibida del dominio: {dominio_limpio} ({dominio}) con tiempo: {tiempo} para usuario: {usuario_id}")

    ahora = datetime.now()

    # Buscar si ya existe registro de hoy para ese dominio
    registro = Registro.query.filter(
        Registro.dominio == dominio_limpio,
        Registro.usuario_id == usuario_id,
        func.date(Registro.fecha) == ahora.date()
    ).first()

    if registro:
        registro.tiempo += tiempo
    else:
        registro = Registro(
            dominio=dominio_limpio,
            tiempo=tiempo,
            fecha=ahora,
            usuario_id=usuario_id
        )
        db.session.add(registro)

    db.session.commit()
    return jsonify({'mensaje': 'Tiempo actualizado'}), 200

@controlador.route('/dashboard')
def dashboard():
    try:
        if 'usuario_id' not in session:
            return jsonify({'error': 'No autenticado'}), 401

        usuario_id = session['usuario_id']
        rango = request.args.get('rango', 'total')
        desde = request.args.get('desde')
        hasta = request.args.get('hasta')

        if rango == 'hoy':
            fecha_inicio = datetime.now().date()
        elif rango == '7dias':
            fecha_inicio = datetime.now().date() - timedelta(days=7)
        elif rango == 'mes':
            fecha_inicio = datetime.now().date() - timedelta(days=30)
        elif rango == 'entre' and desde and hasta:
            fecha_inicio = desde
            fecha_fin = hasta
        else:
            fecha_inicio = None

        filtros_base = f"WHERE usuario_id = :usuario_id"
        params = {"usuario_id": usuario_id}

        if rango == 'entre' and desde and hasta:
            filtros_base += " AND DATE(fecha) BETWEEN :desde AND :hasta"
            params.update({"desde": desde, "hasta": hasta})
        elif fecha_inicio:
            filtros_base += " AND DATE(fecha) >= :fecha_inicio"
            params.update({"fecha_inicio": fecha_inicio})

        query = text(f"""
            SELECT dominio, SUM(tiempo) AS total
            FROM registro
            {filtros_base}
            GROUP BY dominio
            ORDER BY total DESC
        """)
        resultados = db.session.execute(query, params).fetchall()

        query_dias = text(f"""
            SELECT DATE(fecha) AS dia, SUM(tiempo) AS total
            FROM registro
            WHERE usuario_id = :usuario_id
            GROUP BY dia
            ORDER BY dia ASC
        """)
        por_dia = db.session.execute(query_dias, {"usuario_id": usuario_id}).fetchall()
        uso_diario = [{'dia': str(r[0]), 'total': round(r[1] / 60)} for r in por_dia]

        query_horas = text(f"""
            SELECT HOUR(fecha) AS hora, SUM(tiempo) AS total
            FROM registro
            WHERE usuario_id = :usuario_id
            GROUP BY hora
            ORDER BY hora
        """)
        por_hora = db.session.execute(query_horas, {"usuario_id": usuario_id}).fetchall()
        uso_horario = [{'hora': r[0], 'total': round(r[1] / 60)} for r in por_hora]

        datos = [{'dominio': r[0], 'total': round(r[1] / 60)} for r in resultados]

        from collections import defaultdict
        from app.models import DominioCategoria, Categoria

        # Obtener asociaciones dominio → categoría desde la BD
        asociaciones = db.session.query(DominioCategoria.dominio, Categoria.nombre) \
            .join(Categoria) \
            .all()

        mapa_dominios = {d: c for d, c in asociaciones}  # {'youtube.com': 'Ocio', ...}

        por_categoria = defaultdict(int)

        for dominio, total in [(r[0], r[1]) for r in resultados]:
            categoria = mapa_dominios.get(dominio, 'Otros')
            por_categoria[categoria] += round(total / 60)

                # Consultar metas del usuario
        metas = db.session.execute(text("""
            SELECT categoria_id, limite_minutos
            FROM metas_categoria
            WHERE usuario_id = :usuario_id
        """), {'usuario_id': usuario_id}).fetchall()

        # Mapa de id → nombre de categorías
        categorias = db.session.query(Categoria.id, Categoria.nombre).all()
        nombres_categoria = {c.id: c.nombre for c in categorias}

        # Comparar metas con el uso del día
        estado_metas = []

        for meta in metas:
            cat_id = meta.categoria_id
            nombre = nombres_categoria.get(cat_id, 'Desconocida')
            minutos_meta = meta.limite_minutos
            minutos_usados = por_categoria.get(nombre, 0)
            cumplida = minutos_usados >= minutos_meta

            estado_metas.append({
                'categoria': nombre,
                'meta': minutos_meta,
                'usado': minutos_usados,
                'cumplida': cumplida
            })

        return render_template(
            'dashboard.html',
            datos=datos,
            categorias=por_categoria,
            uso_diario=uso_diario,
            uso_horario=uso_horario,
        )


    except Exception as e:
        import traceback
        print("ERROR EN /dashboard")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@controlador.route('/resumen')
def resumen():
    try:
        if 'usuario_id' not in session:
            return jsonify({'error': 'No autenticado'}), 401

        usuario_id = session['usuario_id']

        total_tiempo = db.session.execute(text("""
            SELECT SUM(tiempo) FROM registro WHERE usuario_id = :usuario_id
        """), {'usuario_id': usuario_id}).scalar() or 0

        sitio_top = db.session.execute(text("""
            SELECT dominio, SUM(tiempo) AS total
            FROM registro
            WHERE usuario_id = :usuario_id
            GROUP BY dominio
            ORDER BY total DESC
            LIMIT 1
        """), {'usuario_id': usuario_id}).fetchone()

        dia_top = db.session.execute(text("""
            SELECT DATE(fecha) as dia, SUM(tiempo) AS total
            FROM registro
            WHERE usuario_id = :usuario_id
            GROUP BY dia
            ORDER BY total DESC
            LIMIT 1
        """), {'usuario_id': usuario_id}).fetchone()

        promedio_diario = db.session.execute(text("""
            SELECT AVG(t.total) FROM (
                SELECT DATE(fecha) AS dia, SUM(tiempo) AS total
                FROM registro
                WHERE usuario_id = :usuario_id
                GROUP BY dia
            ) AS t
        """), {'usuario_id': usuario_id}).scalar() or 0

        from app.models import DominioCategoria, Categoria
        from collections import defaultdict

        # Obtener dominios con su categoría desde la BD
        asociaciones = db.session.query(DominioCategoria.dominio, Categoria.nombre) \
            .join(Categoria) \
            .all()

        # Creamos un mapa: dominio → categoría
        mapa_dominios = {dominio: categoria for dominio, categoria in asociaciones}

        # Consulta de dominios y tiempo total por dominio
        registros = db.session.execute(text("""
            SELECT dominio, SUM(tiempo) AS total
            FROM registro
            WHERE usuario_id = :usuario_id
            GROUP BY dominio
        """), {'usuario_id': usuario_id}).fetchall()

        # Agrupar tiempos por categoría
        por_categoria = defaultdict(int)
        for dominio, total in registros:
            categoria = mapa_dominios.get(dominio, 'Otros')
            por_categoria[categoria] += total

        # Determinar la categoría con más tiempo
        categoria_top = max(por_categoria.items(), key=lambda x: x[1]) if por_categoria else ('N/A', 0)


        return jsonify({
            'tiempo_total': int(round(total_tiempo / 60)),
            'sitio_mas_visitado': sitio_top[0] if sitio_top else 'N/A',
            'tiempo_sitio_top': int(round(sitio_top[1] / 60)) if sitio_top else 0,
            'dia_mas_activo': str(dia_top[0]) if dia_top else 'N/A',
            'tiempo_dia_top': int(round(dia_top[1] / 60)) if dia_top else 0,
            'promedio_diario': int(round(promedio_diario / 60)),
            'categoria_dominante': categoria_top[0],
            'tiempo_categoria_top': int(round(categoria_top[1] / 60))
        })

    except Exception as e:
        import traceback
        print(" ERROR EN /resumen")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@controlador.route('/exportar')
def exportar_csv():
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401

    usuario_id = session['usuario_id']
    registros = Registro.query.filter_by(usuario_id=usuario_id).order_by(Registro.fecha.asc()).all()

    def generar_csv():
        yield 'Dominio,Tiempo (segundos),Fecha\n'
        for r in registros:
            yield f'{r.dominio},{r.tiempo},{r.fecha.strftime("%Y-%m-%d %H:%M:%S")}\n'

    return Response(generar_csv(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=historial_navegacion.csv'})


if __name__ == '__main__':
    app.run(debug=True)
