"""
Motor de agregados para TiempoCheck V2.4 - Bloque 2
Calcula ventanas móviles, estado diario y KPIs por rango.
Alineado a modelos: AggVentanaCategoria, AggEstadoDia, AggKpiRango.
Fuente de verdad: features_diarias (usuario_id, fecha, categoria, minutos).
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, Iterable, Tuple
from collections import defaultdict
from app.models.models import Registro, FeatureDiaria, FeatureHoraria, DominioCategoria, Categoria, AggVentanaCategoria, AggEstadoDia, AggKpiRango, MetaCategoria, LimiteCategoria
from app.extensions import db
from sqlalchemy import func, and_, text

logger = logging.getLogger(__name__)

PRODUCTIVAS = {"productividad", "estudio", "herramientas", "trabajo"}  # ajusta según tus categorías

def _categoria_id_por_nombre(nombre: str):
    row = db.session.execute(
        text("SELECT id FROM categorias WHERE nombre = :n LIMIT 1"),
        {"n": nombre}
    ).fetchone()
    return row[0] if row else None

def _rango(fecha_fin: date, dias: int) -> Tuple[date, date]:
    return (fecha_fin - timedelta(days=dias - 1), fecha_fin)


def _minutos_por_categoria(usuario_id: int, f_ini: date, f_fin: date) -> Dict[str, float]:
    """
    Retorna minutos totales por categoría en el rango [f_ini, f_fin]
    """
    rows = (
        db.session.query(FeatureDiaria.categoria, func.sum(FeatureDiaria.minutos))
        .filter(
            FeatureDiaria.usuario_id == usuario_id,
            FeatureDiaria.fecha >= f_ini,
            FeatureDiaria.fecha <= f_fin,
        )
        .group_by(FeatureDiaria.categoria)
        .all()
    )
    return {cat: float(mins or 0.0) for cat, mins in rows}


def _dias_con_datos_por_categoria(usuario_id: int, f_ini: date, f_fin: date) -> Dict[str, int]:
    """
    Cuenta cuántos días (fechas) tuvieron minutos > 0 por categoría en el rango.
    """
    rows = (
        db.session.query(FeatureDiaria.categoria, FeatureDiaria.fecha, func.sum(FeatureDiaria.minutos))
        .filter(
            FeatureDiaria.usuario_id == usuario_id,
            FeatureDiaria.fecha >= f_ini,
            FeatureDiaria.fecha <= f_fin,
        )
        .group_by(FeatureDiaria.categoria, FeatureDiaria.fecha)
        .having(func.sum(FeatureDiaria.minutos) > 0)
        .all()
    )
    cont = defaultdict(int)
    for cat, _fecha, _mins in rows:
        cont[cat] += 1
    return dict(cont)


def _total_global(usuario_id: int, f_ini: date, f_fin: date) -> float:
    total = (
        db.session.query(func.sum(FeatureDiaria.minutos))
        .filter(
            FeatureDiaria.usuario_id == usuario_id,
            FeatureDiaria.fecha >= f_ini,
            FeatureDiaria.fecha <= f_fin,
        )
        .scalar()
    )
    return float(total or 0.0)


def _meta_limite_en_fecha(usuario_id: int, categoria: str, f):
    """
    Lee meta y límite desde tus tablas:
      - metas_categoria: meta_minutos (o minutos_meta)
      - limite_categoria: limite_minutos
    Usa categoria_id (resolviendo por nombre en 'categorias'). Si no existe, intenta por nombre directo.
    Devuelve (meta_min, limite_min) como float o None.
    """
    meta = None
    limite = None


    cat_id = _categoria_id_por_nombre(categoria)

    if cat_id is not None:

        for col in ("meta_minutos", "minutos_meta"):
            try:
                row = db.session.execute(
                    text(f"""
                        SELECT {col} AS m
                        FROM metas_categoria
                        WHERE usuario_id = :u AND categoria_id = :c
                        ORDER BY fecha DESC, id DESC
                        LIMIT 1
                    """),
                    {"u": usuario_id, "c": cat_id},
                ).fetchone()
                if row and row[0] is not None:
                    meta = float(row[0])
                    break
            except Exception:
                continue


        try:
            row = db.session.execute(
                text("""
                    SELECT limite_minutos
                    FROM limite_categoria
                    WHERE usuario_id = :u AND categoria_id = :c
                    ORDER BY updated_at DESC, id DESC
                    LIMIT 1
                """),
                {"u": usuario_id, "c": cat_id},
            ).fetchone()
            if row and row[0] is not None:
                limite = float(row[0])
        except Exception:
            pass

        return meta, limite


    for col in ("meta_minutos", "minutos_meta"):
        try:
            row = db.session.execute(
                text(f"""
                    SELECT {col} AS m
                    FROM metas_categoria
                    WHERE usuario_id = :u AND (categoria = :cat OR categoria_nombre = :cat)
                    ORDER BY fecha DESC, id DESC
                    LIMIT 1
                """),
                {"u": usuario_id, "cat": categoria},
            ).fetchone()
            if row and row[0] is not None:
                meta = float(row[0])
                break
        except Exception:
            continue


    try:
        row = db.session.execute(
            text("""
                SELECT limite_minutos
                FROM limite_categoria
                WHERE usuario_id = :u AND (categoria = :cat OR categoria_nombre = :cat)
                ORDER BY updated_at DESC, id DESC
                LIMIT 1
            """),
            {"u": usuario_id, "cat": categoria},
        ).fetchone()
        if row and row[0] is not None:
            limite = float(row[0])
    except Exception:
        pass

    return meta, limite

class AgregadosEngine:
    """
    Motor principal de cálculo de agregados.
    Cada método hace un commit por lote, no por renglón.
    """

    VENTANAS = (7, 14, 30)

    def calcular_ventanas_usuario(self, usuario_id: int, fecha_fin: date) -> Dict[str, int]:
        logger.info(f"[AGG] Ventanas user={usuario_id} fecha_fin={fecha_fin}")
        cont = {"ventanas": 0, "categorias": 0}

        for dias in self.VENTANAS:
            f_ini, f_fin = _rango(fecha_fin, dias)
            por_cat = _minutos_por_categoria(usuario_id, f_ini, f_fin)
            dias_cat = _dias_con_datos_por_categoria(usuario_id, f_ini, f_fin)
            total = _total_global(usuario_id, f_ini, f_fin) or 1.0

            for cat, mins in por_cat.items():
                dias_con = int(dias_cat.get(cat, 0)) or 1
                obj = AggVentanaCategoria(
                    usuario_id=usuario_id,
                    categoria=cat,
                    ventana=f"{dias}d",
                    fecha_fin=fecha_fin,
                    minutos_sum=mins,
                    minutos_promedio=mins / dias_con,
                    dias_con_datos=dias_con,
                    pct_del_total=(mins / total),
                )
                db.session.merge(obj)
                cont["ventanas"] += 1

            cont["categorias"] = max(cont["categorias"], len(por_cat))

        db.session.commit()
        return cont


    def calcular_estado_dia_usuario(self, usuario_id: int, f: date) -> Dict[str, int]:
        logger.info(f"[AGG] Estado día user={usuario_id} fecha={f}")

        por_cat = _minutos_por_categoria(usuario_id, f, f)
        cont = {"procesadas": 0, "con_meta": 0, "con_limite": 0, "excesos": 0}

        for cat, mins in por_cat.items():
            m, l = _meta_limite_en_fecha(usuario_id, cat, f)

            cumplio = (m is not None) and (mins >= m)
            excedio = (l is not None) and (mins > l)

            if m is not None:
                cont["con_meta"] += 1
            if l is not None:
                cont["con_limite"] += 1
            if excedio:
                cont["excesos"] += 1

            db.session.merge(
                AggEstadoDia(
                    usuario_id=usuario_id,
                    fecha=f,
                    categoria=cat,
                    minutos=mins,
                    meta_min=m,
                    limite_min=l,
                    cumplio_meta=cumplio,
                    excedio_limite=excedio,
                )
            )
            cont["procesadas"] += 1

        db.session.commit()
        return cont


    def calcular_kpis_usuario(self, usuario_id: int, fecha_ref: date) -> Dict[str, int]:
        logger.info(f"[AGG] KPIs user={usuario_id} fecha_ref={fecha_ref}")

        def _guarda(rango: str, ini: date, fin: date):
            por_cat = _minutos_por_categoria(usuario_id, ini, fin)
            prod = sum(v for c, v in por_cat.items() if c and c.lower() in PRODUCTIVAS)
            nprod = sum(v for c, v in por_cat.items() if not c or c.lower() not in PRODUCTIVAS)
            total = prod + nprod

            db.session.merge(
                AggKpiRango(
                    usuario_id=usuario_id,
                    rango=rango,
                    fecha_ref=fecha_ref,
                    min_total=total,
                    min_productivo=prod,
                    min_no_productivo=nprod,
                    pct_productivo=(prod / (total or 1.0)),
                )
            )

        
        _guarda("hoy", fecha_ref, fecha_ref)

        
        ini7, fin7 = _rango(fecha_ref, 7)
        _guarda("7dias", ini7, fin7)

    
        mes_ini = date(fecha_ref.year, fecha_ref.month, 1)
        _guarda("mes", mes_ini, fecha_ref)

    
        first = (
            db.session.query(FeatureDiaria.fecha)
            .filter(FeatureDiaria.usuario_id == usuario_id)
            .order_by(FeatureDiaria.fecha.asc())
            .first()
        )
        tot_ini = first[0] if first else fecha_ref
        _guarda("total", tot_ini, fecha_ref)

        db.session.commit()
        return {"rangos_procesados": 4}
