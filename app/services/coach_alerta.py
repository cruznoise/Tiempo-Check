from datetime import date, datetime
import hashlib, json
from app.extensions import db
from app.models.models import Registro, Categoria, MetaCategoria, LimiteCategoria, UsuarioLogro, DominioCategoria, ContextoDia, PatronCategoria, RachaUsuario, ConfiguracionLogro, AggEstadoDia, AggVentanaCategoria, AggKpiRango
from app.models.ml import MLModelo, MLPrediccionFuture, MlMetric
from app.models.features import FeatureDiaria, FeatureHoraria
from app.models.models_coach import CoachAlerta, CoachSugerencia, CoachAccionLog, NotificacionClasificacion, CoachEstadoRegla

def generar_alertas_exceso(usuario_id: int, dia: date) -> dict:
    """
    Genera alertas 'exceso_diario' comparando minutos del día (por categoría)
    vs el límite establecido en limite_categoria. Inserta en coach_alerta
    con la estructura real de la tabla (tipo, severidad, titulo, mensaje, etc.).
    """
    usos = (
        db.session.query(
            FeatureDiaria.categoria,
            FeatureDiaria.minutos
        )
        .filter(
            FeatureDiaria.usuario_id == usuario_id,
            FeatureDiaria.fecha == dia
        ).all()
    )
    if not usos:
        return {"usuario_id": usuario_id, "fecha": str(dia), "generadas": 0, "detalle": []}
    limites_q = (
        db.session.query(
            Categoria.nombre,
            LimiteCategoria.limite_minutos
        )
        .join(Categoria, Categoria.id == LimiteCategoria.categoria_id)
        .filter(LimiteCategoria.usuario_id == usuario_id)
        .all()
    )
    limites = {
        nombre: float(limite)
        for nombre, limite in limites_q
        if limite is not None
    }

    generadas = 0
    detalle = []

    for cat, mins in usos:
        limite = limites.get(cat)
        if limite is None:
            continue
        if float(mins) > float(limite):
            dedupe = hashlib.sha1(
                f"{usuario_id}-{cat}-{dia}-exceso".encode("utf-8")
            ).hexdigest()

            alerta = CoachAlerta(
                usuario_id=usuario_id,
                categoria=cat,
                tipo="exceso_diario",
                severidad="high",
                titulo=f"Exceso en {cat}",
                mensaje=f"Se registraron {mins:.2f} min, límite diario: {limite:.2f} min.",
                fecha_desde=dia,
                fecha_hasta=dia,
                contexto_json=json.dumps({"minutos": float(mins), "limite": float(limite)}),
                dedupe_key=dedupe,
                creado_en=datetime.utcnow(),
                leido=0
            )

            try:
                db.session.add(alerta)
                db.session.commit()
                generadas += 1
                detalle.append({"categoria": cat, "minutos": float(mins), "limite": float(limite)})
            except Exception:
                db.session.rollback()
                continue

    return {"usuario_id": usuario_id, "fecha": str(dia), "generadas": generadas, "detalle": detalle}
