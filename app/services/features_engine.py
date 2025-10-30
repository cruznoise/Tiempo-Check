from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Dict, List, Tuple
import unicodedata
import pandas as pd
from app.extensions import db
from sqlalchemy import and_, func
from app.models.models import Registro, FeatureDiaria, FeatureHoraria, DominioCategoria, Categoria, AggVentanaCategoria, AggEstadoDia, AggKpiRango, FeaturesCategoriaDiaria

VERSION = "fe-0.7-stable"
print(f"[ENG][LOAD] features_engine {VERSION} file={__file__}")

# --- Canonicalización de categorías ---
def _strip_accents(s: str) -> str:
    if not isinstance(s, str):
        return s
    nfkd = unicodedata.normalize('NFKD', s)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)])

_CANON_EQ = {
    "productivo": "Productividad",
    "sincategoria": "Sin categoría",
    "sin categoria": "Sin categoría",
    "sin categoria ": "Sin categoría",
    "sin categoria.": "Sin categoría",
    "sin categoria,": "Sin categoría",
    "sin categoría": "Sin categoría",
    "sin clasificar": "Sin categoría"
}

def _canon_cat(name: str) -> str:
    if not name:
        return "Sin categoría"
    key = _strip_accents(name).strip().lower()
    import re as _re
    key = _re.sub(r"[\s_\-]+", " ", key)
    key = key.strip()
    if key in _CANON_EQ:
        return _CANON_EQ[key]
    return name.strip()



_MULTI_TLDS: set[Tuple[str, str]] = {
    ("com", "mx"), ("org", "mx"), ("gob", "mx"),
    ("co", "uk"), ("com", "ar"), ("com", "br"),
    ("com", "co"), ("com", "pe"), ("com", "ve"),
}

def _solo_host(s: str) -> str:
    """Devuelve solo host: quita esquema, path, puerto, query, fragment y www."""
    if not s:
        return ""
    s = s.strip().lower()

    if "://" in s:
        s = s.split("://", 1)[1]

    for sep in ["/", "?", "#"]:
        if sep in s:
            s = s.split(sep, 1)[0]

    if ":" in s:
        s = s.split(":", 1)[0]

    if s.startswith("www."):
        s = s[4:]
    return s

def dominio_base(s: str) -> str:
    """Devuelve dominio base (eTLD+1) con heurística simple para TLDs compuestos."""
    host = _solo_host(s)
    if not host:
        return ""
    parts = host.split(".")
    if len(parts) >= 3 and (parts[-2], parts[-1]) in _MULTI_TLDS:
        return ".".join(parts[-3:])
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host



def _cargar_mapa_dominios() -> Dict[str, str]:
    """Carga dominio→categoria (texto). Incluye host y base para maximizar matches."""
    rows: List[Tuple[str, str]] = (
        db.session.query(DominioCategoria.dominio, Categoria.nombre)
        .join(Categoria, DominioCategoria.categoria_id == Categoria.id)
        .all()
    )
    mapa: Dict[str, str] = {}
    for dom, cat in rows:
        if not dom or not cat:
            continue
        host = _solo_host(dom)
        base = dominio_base(dom)

        mapa[base] = cat
        mapa[host] = cat
    return mapa

def _cargar_patrones() -> List[Tuple[re.Pattern, str]]:
    """Si existiera una tabla de patrones, compilar aquí; por ahora, vacío."""
    return []


def _categorizar(host_o_url: str, mapa: Dict[str, str], patrones: List[Tuple[re.Pattern, str]]) -> str:
    host = _solo_host(host_o_url)
    if not host:
        return "Sin categoría"
    base = dominio_base(host)

    cat = mapa.get(base)
    if cat:
        return _canon_cat(cat)

    cat = mapa.get(host)
    if cat:
        return _canon_cat(cat)

    for rex, nombre in patrones:
        if rex.search(host):
            return nombre
    return "Sin categoría"



def calcular_persistir_features(usuario_id: int, dia: date) -> dict:
    """
    Calcula agregados por categoría (y por hora) para el día `dia` y hace UPSERT.
    Usa Registro.fecha_hora si existe; si no, cae a Registro.fecha.
    """
    print(f"[ENG][RUN] calcular_persistir_features usuario={usuario_id} dia={dia}")

    mapa = _cargar_mapa_dominios()
    patrones = _cargar_patrones()

    if hasattr(Registro, 'fecha_hora'):
        day_filter = func.date(Registro.fecha_hora) == dia
    else:
        day_filter = Registro.fecha == dia

    registros = (
        db.session.query(Registro)
        .filter(Registro.usuario_id == usuario_id)
        .filter(day_filter)
        .all()
    )
    print(f"[DEBUG] {dia} → registros={len(registros)}")
    acc_diario: Dict[str, int] = {}
    acc_hora: Dict[tuple, int] = {}

    for r in registros:
        cat = _canon_cat(_categorizar(getattr(r, "dominio", "") or "", mapa, patrones))
        seg = max(0, int(getattr(r, "tiempo", 0) or 0))
        #print(f"[DEBUG] {dia} → cat={cat}, seg={seg}, dominio={getattr(r, 'dominio', '')}") #DESCOMENTAR SOLO EN CASO DE PRUEBAS O VERIFICAR QUE FUNCIONA CON NORMALIDAD
        h = r.fecha_hora.hour if getattr(r, 'fecha_hora', None) else 0

        acc_diario[cat] = acc_diario.get(cat, 0) + seg
        acc_hora[(h, cat)] = acc_hora.get((h, cat), 0) + seg

    # --- FeatureDiaria ---
    for cat, seg in acc_diario.items():
        mins = seg // 60
        obj = (
            FeatureDiaria.query
            .filter_by(usuario_id=usuario_id, fecha=dia, categoria=cat)
            .first()
        )
        if obj:
            obj.minutos = mins
        else:
            db.session.add(FeatureDiaria(
                usuario_id=usuario_id, fecha=dia, categoria=cat, minutos=mins
            ))

    # --- FeaturesCategoriaDiaria ---
    for cat, seg in acc_diario.items():
        mins = seg // 60
        objfc = (
            FeaturesCategoriaDiaria.query
            .filter_by(usuario_id=usuario_id, fecha=dia, categoria=cat)
            .first()
        )
        if objfc:
            objfc.minutos = mins
        else:
            db.session.add(FeaturesCategoriaDiaria(
                usuario_id=usuario_id,
                fecha=dia,
                categoria=cat,
                minutos=mins
            ))
            
    for (h, cat), seg in acc_hora.items():
        mins = seg // 60
        objh = (
            FeatureHoraria.query
            .filter_by(usuario_id=usuario_id, fecha=dia, hora=int(h), categoria=cat)
            .first()
        )
        if objh:
            objh.minutos = mins
        else:
            db.session.add(FeatureHoraria(
                usuario_id=usuario_id, fecha=dia, hora=int(h), categoria=cat, minutos=mins
            ))

    print(f"[DEBUG][COMMIT] {dia} → diarias={len(acc_diario)}, horarias={len(acc_hora)}, new={len(db.session.new)}, dirty={len(db.session.dirty)}")
    try:
        db.session.commit()
    except Exception as e:
        print(f"[ERROR][COMMIT] {dia} → {e}")
        db.session.rollback()

    rows = FeatureDiaria.query.filter_by(usuario_id=usuario_id, fecha=dia).all()
    print(f"[DEBUG][POST-COMMIT] {dia} → rows_in_db={len(rows)}")

    dias_hist = 30
    fecha_inicio = dia - timedelta(days=dias_hist)
    rows_hist = (
        FeaturesCategoriaDiaria.query
        .filter(FeaturesCategoriaDiaria.usuario_id == usuario_id)
        .filter(FeaturesCategoriaDiaria.fecha >= fecha_inicio)
        .filter(FeaturesCategoriaDiaria.fecha <= dia)
        .all()
    )

    if rows_hist:
        df_hist = pd.DataFrame([
            {
                "fecha": r.fecha,
                "categoria": r.categoria,
                "minutos": r.minutos,
            }
            for r in rows_hist
        ])
    else:
        df_hist = pd.DataFrame()

    return {
        "ok": 1,
        "diarias": len(acc_diario),
        "horarias": len(acc_hora),
        "hist": df_hist
    }

def recalcular_rango(usuario_id: int, desde: date, hasta: date) -> Dict[str, int]:
    print(f"[DEBUG] Entrando a recalcular_rango {desde} → {hasta}")

    """Recalcula features para el rango [desde, hasta] (ambos inclusive)."""
    if hasta < desde:
        desde, hasta = hasta, desde
    d = desde
    tot_diarias = tot_horarias = 0
    while d <= hasta:
        print(f"[DEBUG] Día en loop: {d}")
        res = calcular_persistir_features(usuario_id=usuario_id, dia=d)
        tot_diarias += res.get("diarias", 0)
        tot_horarias += res.get("horarias", 0)
        d += timedelta(days=1)
    return {"ok": 1, "diarias": tot_diarias, "horarias": tot_horarias}
    
def load_fc_diaria(usuario_id: int, start: date | None = None, end: date | None = None) -> pd.DataFrame:
    """
    Carga las features diarias por categoría del usuario desde la tabla FeaturesCategoriaDiaria.
    Si se dan fechas, filtra por rango.
    """
    q = db.session.query(FeaturesCategoriaDiaria).filter_by(usuario_id=usuario_id)
    if start:
        q = q.filter(FeaturesCategoriaDiaria.fecha >= start)
    if end:
        q = q.filter(FeaturesCategoriaDiaria.fecha <= end)

    rows = q.order_by(FeaturesCategoriaDiaria.fecha).all()
    if not rows:
        print("[WARN] No se encontraron registros en FeaturesCategoriaDiaria")
        return pd.DataFrame()

    df = pd.DataFrame([
        {
            "usuario_id": r.usuario_id,
            "fecha": r.fecha,
            "categoria": r.categoria,
            "minutos": r.minutos,
        }
        for r in rows
    ])
    return df
