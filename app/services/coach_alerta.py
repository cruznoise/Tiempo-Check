# -*- coding: utf-8 -*-
from datetime import date
from sqlalchemy import and_
from app.extensions import db
from app.models import CoachAlerta, LimiteCategoria, FeatureDiaria, FeatureHoraria

def generar_alertas_exceso(usuario_id: int, dia: date) -> dict:
    """
    Genera alertas 'exceso_diario' comparando minutos del día (por categoría)
    vs el límite establecido en limite_categoria. Idempotente por UNIQUE.
    """
    # Fuente robusta: features_categoria_diaria del día
    usos = (
        db.session.query(
            FeaturesCategoriaDiaria.categoria,
            FeaturesCategoriaDiaria.minutos
        )
        .filter(
            FeaturesCategoriaDiaria.usuario_id == usuario_id,
            FeaturesCategoriaDiaria.fecha == dia
        ).all()
    )
    if not usos:
        return {"usuario_id": usuario_id, "fecha": str(dia), "generadas": 0, "detalle": []}

    # Mapear límites por categoría
    limites = {
        r.categoria: float(r.minutos_limite)
        for r in db.session.query(LimiteCategoria)
            .filter(LimiteCategoria.usuario_id == usuario_id).all()
            if r.minutos_limite is not None
    }

    generadas = 0
    detalle = []
    for cat, mins in usos:
        limite = limites.get(cat)
        if limite is None:
            continue
        if float(mins) > float(limite):
            # Upsert protegido por UNIQUE
            alerta = CoachAlerta(
                usuario_id=usuario_id,
                fecha=dia,
                categoria=cat,
                regla="exceso_diario",
                nivel="critical",
                detalle=f"Se registraron {mins:.2f} min, límite diario: {limite:.2f} min."
            )
            try:
                db.session.add(alerta)
                db.session.commit()
                generadas += 1
                detalle.append({"categoria": cat, "minutos": float(mins), "limite": float(limite)})
            except Exception:
                db.session.rollback()  # ya existía o colisión: mantener idempotencia
                continue

    return {"usuario_id": usuario_id, "fecha": str(dia), "generadas": generadas, "detalle": detalle}
