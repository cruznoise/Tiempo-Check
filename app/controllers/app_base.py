from flask import Flask, Blueprint, request, jsonify, render_template, Response, session, redirect
from flask_cors import CORS
from sqlalchemy import text, func
from datetime import datetime, timedelta, date
from collections import defaultdict
from app.models.models import db,Usuario, Registro, Categoria, DominioCategoria, FeatureDiaria, FeatureHoraria
from app.models import DominioCategoria, Categoria
from collections import defaultdict
import tldextract
from app.utils import clasificar_dominio_automatico, desbloquear_logro, verificar_logros_dinamicos, obtener_promedio_categoria, calcular_nivel_confianza, obtener_dias_uso, calcular_sugerencias_por_categoria, _qa_invariantes_dia
from app.services.rachas_service import actualizar_rachas

controlador = Blueprint('controlador', __name__)
bp = controlador 

@controlador.get('/')
def home():
    return redirect('/login')

@controlador.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    data = request.get_json(silent=True) or {}
    correo = data.get('correo') or request.form.get('correo')
    contrasena = data.get('contraseña') or request.form.get('contraseña')

    if not correo or not contrasena:
        return jsonify({'success': False, 'error': 'Faltan datos'}), 400

    usuario = Usuario.query.filter_by(correo=correo, contrasena=contrasena).first()

    if usuario:
        session['usuario_id'] = usuario.id
        return jsonify({'success': True})
    else:
        return jsonify({'success': False})

@controlador.get('/logout')
def logout():
    session.clear()
    return redirect('/login')


@controlador.route('/guardar', methods=['POST'])
def guardar():
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    return guardar_tiempo(request, session['usuario_id'])


def limpiar_dominio(url):

    ext = tldextract.extract(url)
    return f"{ext.domain}.{ext.suffix}" if ext.domain and ext.suffix else url

def guardar_tiempo(request, usuario_id):
    data = request.get_json()
    dominio = data.get('dominio')
    tiempo = data.get('tiempo')

    if tiempo is None or not isinstance(tiempo, int) or tiempo <= 0:
        return jsonify({'error': 'Tiempo inválido'}), 400
    if not dominio:
        return jsonify({'error': 'Faltan datos'}), 400

    dominio_limpio = limpiar_dominio(dominio)

    print(f"[✔] Petición recibida del dominio: {dominio_limpio} ({dominio}) con tiempo: {tiempo} para usuario: {usuario_id}")

    ahora = datetime.now()

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
def _parse_date(s: str):
    try:
        return datetime.strptime(str(s), "%Y-%m-%d").date()
    except Exception:
        return None

def _rango_fechas_desde_request():
    hoy = date.today()
    rango = request.args.get('rango','total')
    desde = request.args.get('desde')
    hasta = request.args.get('hasta')

    if rango == '7dias':
        return hoy - timedelta(days=6), hoy, '7dias'
    if rango == 'mes':
        return hoy - timedelta(days=29), hoy, 'mes'
    if rango == 'entre':
        d = _parse_date(desde)
        h = _parse_date(hasta)
        if d and h and h >= d:
            return d, h, 'entre'
        return hoy, hoy, 'hoy'
    if rango == 'total':

        return None, None, 'total'

    return hoy, hoy, 'hoy'

def _unificar_alias_sin_categoria(m: dict) -> dict:
    """Funde claves viejas hacia 'Sin categoría'."""
    if not m:
        return {}
    res = dict(m)
    aliases = ['SinCategoria', 'Sin categoria', 'sin categoria', 'sincategoria', None, '']
    carry = 0
    for k in aliases:
        if k in res:
            carry += int(res.pop(k) or 0)
    if carry:
        res['Sin categoría'] = int(res.get('Sin categoría', 0)) + carry
    return res

@controlador.route('/dashboard')
def dashboard():
    try:
        if 'usuario_id' not in session:
            return jsonify({'error': 'No autenticado'}), 401

        usuario_id = session['usuario_id']
        fecha_inicio, fecha_fin, etiqueta_rango = _rango_fechas_desde_request()

        cutover = (
            db.session.query(func.min(func.date(Registro.fecha_hora)))
            .filter(func.date(Registro.fecha_hora).isnot(None))
            .filter(func.hour(Registro.fecha_hora) != 0)
            .scalar()
        )
        from datetime import date
        cutover = cutover or date.today()

        q_hora = db.session.query(
            FeatureHoraria.hora.label('hora'),
            func.sum(FeatureHoraria.minutos).label('total')
        ).filter(
            FeatureHoraria.usuario_id == usuario_id
        )

        cutover = (
            db.session.query(func.min(func.date(Registro.fecha_hora)))
            .filter(func.date(Registro.fecha_hora).isnot(None))
            .filter(func.hour(Registro.fecha_hora) != 0)
            .scalar()
        )
        from datetime import date
        cutover = cutover or date.today()

        todo_historico = request.args.get('todo_historico', '1') == '1'

        if etiqueta_rango == 'total':
            if not todo_historico:
                q_hora = q_hora.filter(FeatureHoraria.fecha >= cutover)
        else:

            q_hora = q_hora.filter(
                FeatureHoraria.fecha >= fecha_inicio,
                FeatureHoraria.fecha <= fecha_fin
            )

        q_hora = q_hora.group_by(FeatureHoraria.hora).order_by(FeatureHoraria.hora)

        uso_horario = [
            {'hora': int(r.hora), 'total': int(r.total or 0)}
            for r in q_hora.all()
        ]

        q_dia = db.session.query(
            FeatureDiaria.fecha.label('dia'),
            func.sum(FeatureDiaria.minutos).label('total')
        ).filter(
            FeatureDiaria.usuario_id == usuario_id
        )
        if etiqueta_rango != 'total':
            q_dia = q_dia.filter(
                FeatureDiaria.fecha >= fecha_inicio,
                FeatureDiaria.fecha <= fecha_fin
            )
        q_dia = q_dia.group_by(FeatureDiaria.fecha).order_by(FeatureDiaria.fecha.asc())

        uso_diario = [
            {'dia': str(r.dia), 'total': int(r.total or 0)}
            for r in q_dia.all()
        ]

        q_cat = db.session.query(
            FeatureDiaria.categoria,
            func.sum(FeatureDiaria.minutos).label('total')
        ).filter(
            FeatureDiaria.usuario_id == usuario_id
        )
        if etiqueta_rango != 'total':
            q_cat = q_cat.filter(
                FeatureDiaria.fecha >= fecha_inicio,
                FeatureDiaria.fecha <= fecha_fin
            )
        q_cat = q_cat.group_by(FeatureDiaria.categoria)\
                     .order_by(func.sum(FeatureDiaria.minutos).desc())

        por_categoria = {}
        for cat, total in q_cat.all():
            key = cat or 'Sin categoría'
            por_categoria[key] = int(total or 0)
        por_categoria = _unificar_alias_sin_categoria(por_categoria)

        q_dom = db.session.query(
            Registro.dominio,
            (func.sum(Registro.tiempo) / 60.0).label('total_min')
        ).filter(
            Registro.usuario_id == usuario_id
        )
        if etiqueta_rango != 'total':
            q_dom = q_dom.filter(
                func.date(Registro.fecha) >= (fecha_inicio or func.date(Registro.fecha)),
                func.date(Registro.fecha) <= (fecha_fin or func.date(Registro.fecha))
            )
        q_dom = q_dom.group_by(Registro.dominio)\
                     .order_by(func.sum(Registro.tiempo).desc())

        datos = [
            {'dominio': r.dominio, 'total': int(round(float(r.total_min or 0)))}
            for r in q_dom.all()
        ]

        estado_metas = []
        try:
            metas_rows = db.session.execute(text("""
                SELECT categoria_id, limite_minutos
                FROM metas_categoria
                WHERE usuario_id = :uid
            """), {'uid': usuario_id}).fetchall()
            nombres_categoria = dict(db.session.query(Categoria.id, Categoria.nombre).all())

            for row in metas_rows:
                cat_id = row[0]
                meta_min = int(row[1] or 0)
                nombre = nombres_categoria.get(cat_id, 'Desconocida')
                usado = int(por_categoria.get(nombre, 0))
                estado_metas.append({
                    'categoria': nombre,
                    'meta': meta_min,
                    'usado': usado,
                    'cumplida': usado >= meta_min
                })
        except Exception:

            estado_metas = []
        estado_limites = []
        try:
            limites_rows = db.session.execute(text("""
                SELECT categoria_id, limite_minutos
                FROM limites_categoria
                WHERE usuario_id = :uid
            """), {'uid': usuario_id}).fetchall()
            nombres_categoria = dict(db.session.query(Categoria.id, Categoria.nombre).all())

            for row in limites_rows:
                cat_id = row[0]
                lim_min = int(row[1] or 0)
                nombre = nombres_categoria.get(cat_id, 'Desconocida')
                usado = int(por_categoria.get(nombre, 0))
                estado_limites.append({
                    'categoria': nombre,
                    'limite': lim_min,
                    'usado': usado,
                    'excedido': usado > lim_min if lim_min > 0 else False
                })
        except Exception:
            estado_limites = []

        fi = str(fecha_inicio) if fecha_inicio else ''
        ff = str(fecha_fin) if fecha_fin else ''

        return render_template(
            'dashboard.html',
            datos=datos,                  
            categorias=por_categoria,        
            uso_horario=uso_horario,        
            uso_diario=uso_diario,        
            estado_metas=estado_metas,
            estado_limites=estado_limites,
            rango=etiqueta_rango,
            fecha_inicio=fi,
            fecha_fin=ff,
            mostrar_nota_hora=(etiqueta_rango == 'total' and not todo_historico),
            cutover=str(cutover)
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

        asociaciones = db.session.query(DominioCategoria.dominio, Categoria.nombre) \
            .join(Categoria) \
            .all()

        mapa_dominios = {dominio: categoria for dominio, categoria in asociaciones}

        registros = db.session.execute(text("""
            SELECT dominio, SUM(tiempo) AS total
            FROM registro
            WHERE usuario_id = :usuario_id
            GROUP BY dominio
        """), {'usuario_id': usuario_id}).fetchall()

        por_categoria = defaultdict(int)
        for dominio, total in registros:
            categoria = mapa_dominios.get(dominio, 'Otros')
            por_categoria[categoria] += total

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

@controlador.route('/alertas', methods=['POST'])
def alertas():
    if 'usuario_id' not in session:
        return jsonify({'alerta': False})
    return jsonify({'alerta': False})
