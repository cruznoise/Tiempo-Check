# app/coach/engine.py
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Callable, Dict, Optional
import hashlib

from app.extensions import db
# Mantengo tus rutas de import tal como las tienes:
from app.models.models import AggEstadoDia, AggVentanaCategoria, AggKpiRango
from app.models.models_coach import CoachAlerta, CoachSugerencia, CoachEstadoRegla


@dataclass
class RuleCtx:
    usuario_id: int
    hoy: date


RuleFn = Callable[[RuleCtx], None]
_REGISTRY: Dict[str, RuleFn] = {}

COOLDOWNS = {
    "exceso_diario": timedelta(days=1),
    "meta_cumplida": timedelta(days=1),
    "baja_productividad_7d": timedelta(days=2),
    "spike_distraccion": timedelta(days=2),
    "racha_equilibrio": timedelta(days=3),
}

# ----------------------
# Registro de reglas
# ----------------------
def rule(name: str):
    def deco(fn: RuleFn):
        _REGISTRY[name] = fn
        return fn
    return deco

# ----------------------
# Utilidades
# ----------------------
def _dedupe_key(usuario_id: int, tipo: str, categoria: Optional[str], ffin: date) -> str:
    raw = f"{usuario_id}|{tipo}|{(categoria or '')}|{ffin.isoformat()}"
    return hashlib.sha1(raw.encode()).hexdigest()

def _cooldown_ok(usuario_id: int, regla: str, categoria: Optional[str], now: datetime) -> bool:
    st = CoachEstadoRegla.query.get((usuario_id, regla, categoria or ""))
    return (st is None) or (st.cooldown_until is None) or (now >= st.cooldown_until)

def _touch_cooldown(usuario_id: int, regla: str, categoria: Optional[str], now: datetime):
    dur = COOLDOWNS.get(regla)
    cu = (now + dur) if dur else None
    st = CoachEstadoRegla.query.get((usuario_id, regla, categoria or ""))
    if st is None:
        st = CoachEstadoRegla(
            usuario_id=usuario_id, regla=regla, categoria=categoria or "",
            last_triggered=now, cooldown_until=cu, contador=1
        )
    else:
        st.last_triggered = now
        st.cooldown_until = cu
        st.contador = (st.contador or 0) + 1
    db.session.merge(st)

# ======================
# Reglas MVP
# ======================

@rule("exceso_diario")
def r_exceso_diario(ctx: RuleCtx):
    """Genera alerta si ayer excedió límite por categoría (idempotente, con cooldown y dedupe)."""
    ayer = ctx.hoy - timedelta(days=1)
    now = datetime.utcnow()

    q = (AggEstadoDia.query
         .filter_by(usuario_id=ctx.usuario_id, fecha=ayer, excedio_limite=True))

    for r in q:
        if not _cooldown_ok(ctx.usuario_id, "exceso_diario", r.categoria, now):
            continue

        key = _dedupe_key(ctx.usuario_id, "exceso_diario", r.categoria, ayer)

        # DEDUPE: si ya existe una alerta con la misma key, no la re-crees
        if db.session.query(CoachAlerta.id).filter_by(dedupe_key=key).first():
            continue

        alert = CoachAlerta(
            usuario_id=ctx.usuario_id,
            tipo="exceso_diario",
            categoria=r.categoria,
            severidad="high",
            titulo=f"Excediste el límite en {r.categoria}",
            mensaje=f"Ayer usaste {int(r.minutos)} min; revisa tu límite ({int(r.limite_min or 0)} min).",
            contexto_json={"minutos": float(r.minutos), "limite": float(r.limite_min or 0)},
            fecha_desde=ayer,
            fecha_hasta=ayer,
            dedupe_key=key,
        )
        db.session.add(alert)
        _touch_cooldown(ctx.usuario_id, "exceso_diario", r.categoria, now)

@rule('meta_cumplida')
def r_meta_cumplida(ctx: RuleCtx):
    """Crea sugerencia de celebración/ajuste cuando ayer se cumplió la meta."""
    ayer = ctx.hoy - timedelta(days=1)
    now = datetime.utcnow()

    q = (AggEstadoDia.query
         .filter_by(usuario_id=ctx.usuario_id, fecha=ayer, cumplio_meta=True))

    for r in q:
        if not _cooldown_ok(ctx.usuario_id, 'meta_cumplida', r.categoria, now):
            continue


        sug = CoachSugerencia(
            usuario_id=ctx.usuario_id, tipo='celebrar', categoria=r.categoria,
            titulo=f"¡Meta cumplida en {r.categoria}!",
            cuerpo="Bien ahí 👏 ¿Subimos la meta un 10% para seguir retando?",
            action_type='post_api',
            action_payload={"endpoint": "/admin/api/metas/adjust",
                            "body": {"categoria": r.categoria, "delta_pct": 10}}
        )
        db.session.add(sug)
        _touch_cooldown(ctx.usuario_id, 'meta_cumplida', r.categoria, now)

@rule("baja_productividad_7d")
def r_baja_productividad(ctx: RuleCtx):
    """Alerta si productividad 7d < 40% y menor que 30d; sugiere bloques de foco."""
    kpi7 = (AggKpiRango.query
            .filter_by(usuario_id=ctx.usuario_id, rango="7d")
            .order_by(AggKpiRango.fecha_ref.desc()).first())
    kpi30 = (AggKpiRango.query
             .filter_by(usuario_id=ctx.usuario_id, rango="30d")
             .order_by(AggKpiRango.fecha_ref.desc()).first())
    if not kpi7 or not kpi30:
        return

    p7 = float(kpi7.pct_productivo or 0.0)
    p30 = float(kpi30.pct_productivo or 0.0)

    if p7 < 0.40 and p7 < p30:
        now = datetime.utcnow()
        if not _cooldown_ok(ctx.usuario_id, "baja_productividad_7d", None, now):
            return

        key = _dedupe_key(ctx.usuario_id, "baja_productividad_7d", None, kpi7.fecha_ref)
        if not db.session.query(CoachAlerta.id).filter_by(dedupe_key=key).first():
            alert = CoachAlerta(
                usuario_id=ctx.usuario_id,
                tipo="baja_productividad_7d",
                categoria=None,
                severidad="mid",
                titulo="Tu productividad cayó en 7 días",
                mensaje=f"{round(p7*100)}% vs {round(p30*100)}% del mes.",
                contexto_json={"pct7": p7, "pct30": p30},
                fecha_desde=ctx.hoy - timedelta(days=6),
                fecha_hasta=ctx.hoy,
                dedupe_key=key,
            )
            db.session.add(alert)

        # Sugerencia para focus block
        sug = CoachSugerencia(
            usuario_id=ctx.usuario_id,
            tipo="programar_focus",
            categoria=None,
            titulo="Agendemos 2 bloques de enfoque hoy",
            cuerpo="Propuesta: 2×45min con descanso de 10min. ¿Lo agendamos?",
            action_type="local_ui",
            action_payload={"dialog": "focus_plan", "blocks": [45, 45]},
        )
        db.session.add(sug)
        _touch_cooldown(ctx.usuario_id, "baja_productividad_7d", None, now)

@rule("spike_distraccion")
def r_spike(ctx: RuleCtx):
    """Alerta si la media 7d de una categoría no productiva > 1.5× su media 14d."""
    hoy = ctx.hoy

    # 7d en fecha exacta
    v7 = (AggVentanaCategoria.query
          .filter_by(usuario_id=ctx.usuario_id, ventana="7d", fecha_fin=hoy)
          .all())

    # última 14d disponible
    v14f = (db.session.query(db.func.max(AggVentanaCategoria.fecha_fin))
            .filter_by(usuario_id=ctx.usuario_id, ventana="14d").scalar())
    if not v14f:
        return

    v14 = (AggVentanaCategoria.query
           .filter_by(usuario_id=ctx.usuario_id, ventana="14d", fecha_fin=v14f)
           .all())
    by14 = {r.categoria: float(r.minutos_promedio) for r in v14}

    now = datetime.utcnow()
    for r in v7:
        # considera no productivas las que no sean productividad/estudio (ajusta a tu taxonomía)
        if (r.categoria or "").lower() in ("productividad", "estudio"):
            continue

        base = by14.get(r.categoria)
        if not base or base == 0:
            continue

        if float(r.minutos_promedio) > base * 1.5 and _cooldown_ok(ctx.usuario_id, "spike_distraccion", r.categoria, now):
            key = _dedupe_key(ctx.usuario_id, "spike_distraccion", r.categoria, hoy)
            if db.session.query(CoachAlerta.id).filter_by(dedupe_key=key).first():
                continue

            alert = CoachAlerta(
                usuario_id=ctx.usuario_id,
                tipo="spike_distraccion",
                categoria=r.categoria,
                severidad="mid",
                titulo=f"Subiste {r.categoria} un 50%+ vs 14d",
                mensaje=f"Promedio 7d: {int(r.minutos_promedio)} min/día vs {int(base)} 14d.",
                contexto_json={"m7": float(r.minutos_promedio), "m14": base},
                fecha_desde=hoy - timedelta(days=6),
                fecha_hasta=hoy,
                dedupe_key=key,
            )
            db.session.add(alert)
            _touch_cooldown(ctx.usuario_id, "spike_distraccion", r.categoria, now)

@rule("racha_equilibrio")
def r_racha(ctx: RuleCtx):
    """Sugerencia si hubo N días seguidos con meta OK y sin exceder límites."""
    N = 3
    ok = 0
    for i in range(N):
        d = ctx.hoy - timedelta(days=i + 1)  # días cerrados
        rows = AggEstadoDia.query.filter_by(usuario_id=ctx.usuario_id, fecha=d).all()
        if not rows:
            break
        meta_ok = any(r.cumplio_meta for r in rows)
        exc_no = not any(r.excedio_limite for r in rows)
        if meta_ok and exc_no:
            ok += 1
        else:
            break

    if ok >= N:
        now = datetime.utcnow()
        if not _cooldown_ok(ctx.usuario_id, "racha_equilibrio", None, now):
            return

        sug = CoachSugerencia(
            usuario_id=ctx.usuario_id,
            tipo="celebrar",
            categoria=None,
            titulo=f"¡{N} días de equilibrio!",
            cuerpo="Te ganaste un descanso planificado hoy. ¿Agendamos 30min libres?",
            action_type="local_ui",
            action_payload={"dialog": "schedule_break", "minutes": 30},
        )
        db.session.add(sug)
        _touch_cooldown(ctx.usuario_id, "racha_equilibrio", None, now)

# ----------------------
# Motor principal
# ----------------------
def run_coach(usuario_id: int, hoy: date):
    """Ejecuta TODAS las reglas registradas para ese usuario/fecha."""
    ctx = RuleCtx(usuario_id=usuario_id, hoy=hoy)
    for _, fn in _REGISTRY.items():
        fn(ctx)
    db.session.commit()

# ----------------------
# Wrapper útil para pruebas manuales
# ----------------------
def run_regla_exceso_diario(usuario_id: int, fecha: date):
    """Ejecuta SOLO la regla de exceso, recibiendo (usuario, fecha)."""
    ctx = RuleCtx(usuario_id=usuario_id, hoy=fecha)
    r_exceso_diario(ctx)
    db.session.commit()
