import pandas as pd
import numpy as np
import json
from pathlib import Path
from app.models.models import FeaturesCategoriaDiaria
from app.models import ContextoDia  # Para anomalías
from app.extensions import db

def _calendar_feats(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    dt = pd.to_datetime(d["fecha"])
    d["dow"] = dt.dt.weekday
    d["is_weekend"] = (d["dow"] >= 5).astype(int)
    d["day"] = dt.dt.day
    d["days_to_eom"] = dt.dt.daysinmonth - d["day"]
    return d

def make_lagged(df: pd.DataFrame, lags=(1,2,3,7,14,21), ma_windows=(7,14,30)) -> pd.DataFrame:
    """
    Construye features por usuario-categoría con índice alineado (sin MultiIndex).
    
    MEJORAS IMPLEMENTADAS:
    - Lags extendidos: 1,2,3,7,14,21 días (antes solo 1,2,3,7)
    - Ventanas móviles: MA7, MA14, MA30 (antes solo MA7)
    - Requiere al menos min_t-1; MA se calcula como rolling del shift(1)
    """
    d = df.sort_values(["usuario_id","categoria","fecha"]).copy()
    d = _calendar_feats(d)
    g = d.groupby(["usuario_id","categoria"], group_keys=False)

    # Lags extendidos (hasta 21 días atrás)
    for L in lags:
        d[f"min_t-{L}"] = g["minutos"].shift(L)

    # Ventanas móviles extendidas (7, 14, 30 días)
    for W in ma_windows:
        d[f"MA{W}"] = g["minutos"].transform(lambda s: s.shift(1).rolling(W, min_periods=1).mean())

    d = d.dropna(subset=["min_t-1"])
    return d

def make_lagged_with_context(df: pd.DataFrame, usuario_id: int, 
                             lags=(1,2,3,7,14,21), ma_windows=(7,14,30)) -> pd.DataFrame:
    """
    Añade contexto de anomalías estacionales (ej. Jueves vs Jueves pasados)
    calculado individualmente por categoría.
    """
    # 1. Llamada a la base
    d = make_lagged(df, lags=lags, ma_windows=ma_windows)
    
    # 2. Grupo estacional: Usuario + Categoría + Día de la Semana (dow)
    g_estacional = d.groupby(["usuario_id", "categoria", "dow"], group_keys=False)
    
    # 3. Cálculo de Z-Score Estacional (Compara hoy contra los últimos 4 mismos días)
    # Ejemplo: Este jueves contra los 4 jueves anteriores.
    ma_est = g_estacional["minutos"].transform(lambda s: s.shift(1).rolling(4, min_periods=1).mean())
    std_est = g_estacional["minutos"].transform(lambda s: s.shift(1).rolling(4, min_periods=1).std()).fillna(1.0).replace(0, 1.0)
    
    d["Z_score_estacional"] = (d["min_t-1"] - ma_est) / std_est
    
    # 4. Definición de anomalía estacional
    umbral_z = 2.5
    d["es_anomalia"] = (abs(d["Z_score_estacional"]) > umbral_z).astype(int)
    
    # Función interna para etiquetar el motivo
    def determinar_motivo(z):
        if z > umbral_z: return 'pico_alto'
        if z < -umbral_z: return 'caida_atipica'
        return 'normal'
    
    d["motivo_estacional"] = d["Z_score_estacional"].apply(determinar_motivo)
    
    # 5. Features para el modelo (Contexto de ayer)
    g_cat = d.groupby(["usuario_id", "categoria"], group_keys=False)
    
    # ¿Ayer fue un día raro para esta categoría específicamente?
    d['fue_anomalia_lag1'] = g_cat['es_anomalia'].shift(1).fillna(0).astype(int)
    
    # Días desde el último comportamiento anómalo en esta categoría
    def calcular_dias_desde_anomalia(serie_es_anom):
        dias_desde = []
        contador = 30
        for es_anom in serie_es_anom:
            contador = 0 if es_anom else min(contador + 1, 30)
            dias_desde.append(contador)
        return pd.Series(dias_desde, index=serie_es_anom.index)
    
    d['dias_desde_anomalia'] = g_cat['es_anomalia'].transform(calcular_dias_desde_anomalia)
    
    # One-hot encoding de los motivos (Picos o Caídas)
    d['motivo_lag1'] = g_cat['motivo_estacional'].shift(1).fillna('normal')
    for m in ['pico_alto', 'caida_atipica']:
        d[f'motivo_{m}'] = (d['motivo_lag1'] == m).astype(int)
        
    # Limpieza de columnas de cálculo
    d = d.drop(columns=['motivo_estacional', 'motivo_lag1'], errors='ignore')
    
    print(f"[FEATURES] Contexto estacional calculado (Día vs Día pasados) por categoría.")
    return d

def detectar_y_exportar_anomalias_cat(df, usuario_id, umbral_z=2.5):
    """
    Toma un DataFrame con ['fecha', 'categoria', 'minutos_reales']
    y exporta un JSON de anomalías basado en el Z-Score Estacional
    (comparando cada día contra los mismos días de las 4 semanas anteriores).
    """
    # 1. Preparar datos y asegurar formato de fecha
    df = df.copy()
    df['fecha_dt'] = pd.to_datetime(df['fecha'])
    df['dow'] = df['fecha_dt'].dt.weekday
    df = df.sort_values(['categoria', 'fecha'])

    # 2. Cálculo Estacional (Mismo día de la semana)
    g_est = df.groupby(['categoria', 'dow'])
    
    # Media y Desviación estándar de los últimos 4 días iguales
    ma_est = g_est['minutos_reales'].transform(lambda x: x.shift(1).rolling(4, min_periods=1).mean())
    std_est = g_est['minutos_reales'].transform(lambda x: x.shift(1).rolling(4, min_periods=1).std()).fillna(1.0).replace(0, 1.0)
    
    # Calcular Z-Score
    df['z_score'] = (df['minutos_reales'] - ma_est) / std_est
    
    # 3. Filtrar anomalías
    df_anomalo = df[abs(df['z_score']) > umbral_z].copy()
    anomalias_list = []
    
    for _, row in df_anomalo.iterrows():
        tipo = "pico_alto" if row['z_score'] > 0 else "caida_atipica"
        
        # Generar descripción amigable
        if tipo == "pico_alto":
            desc = f"Uso excepcionalmente alto: {row['z_score']:.1f} desv. estándar sobre su media de los últimos {row['fecha_dt'].strftime('%A')}s"
        else:
            desc = f"Uso inusualmente bajo para ser {row['fecha_dt'].strftime('%A')}."
            
        anomalias_list.append({
            "fecha": str(row['fecha']),
            "categoria": row['categoria'],
            "minutos_reales": round(float(row['minutos_reales']), 2),
            "media_estacional": round(float(ma_est.loc[row.name]), 2),
            "z_score": round(float(row['z_score']), 2),
            "tipo_anomalia": tipo,
            "contexto_humano": desc
        })
        
    # 4. Guardar en la ruta de backups
    ruta_salida = Path(f"backups/usuarios_realistas/usuario_{usuario_id}_anomalias_cat.json")
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    
    with open(ruta_salida, 'w', encoding='utf-8') as f:
        json.dump(anomalias_list, f, indent=4, ensure_ascii=False)
    
    return df

def get_feature_cols(d: pd.DataFrame):
    """
    Devuelve la lista de columnas que el modelo usará para aprender.
    Incluye las variables base y el nuevo contexto de anomalías estacionales.
    """
    # 1. Variables de retardo (lags) y medias móviles (MA)
    base_features = [c for c in d.columns if c.startswith("min_t-") or c.startswith("MA")]
    
    # 2. Variables de calendario
    calendar_features = ["dow", "is_weekend", "day", "days_to_eom"]
    
    # 3. NUEVO: Variables de contexto de anomalías por categoría
    # Incluimos el Z-Score estacional y los indicadores de anomalía previa
    context_features = [
        "Z_score_estacional", 
        "fue_anomalia_lag1", 
        "dias_desde_anomalia",
        "motivo_pico_alto", 
        "motivo_caida_atipica"
    ]
    
    # Solo devolvemos las columnas que realmente existan en el DataFrame
    final_cols = base_features + calendar_features + context_features
    return [c for c in final_cols if c in d.columns]

def split_train_holdout(d: pd.DataFrame, holdout_days=7):
    d = d.sort_values(["usuario_id","categoria","fecha"]).copy()
    max_date = pd.to_datetime(d["fecha"]).max().normalize()
    mask = pd.to_datetime(d["fecha"]).dt.normalize() > (max_date - pd.Timedelta(days=holdout_days))
    return d.loc[~mask].copy(), d.loc[mask].copy()

def latest_X_per_categoria(d: pd.DataFrame):
    """
    Devuelve el registro más reciente por usuario y categoría.
    Corrige duplicados o categorías vacías ('Sin categoría').
    """
    d = d.copy()
    d["categoria"] = d["categoria"].astype(str).fillna("Sin categoría")
    d = d.sort_values(["usuario_id", "categoria", "fecha"], ascending=True)
    d = d.drop_duplicates(subset=["usuario_id", "categoria", "fecha"], keep="last")
    feats = get_feature_cols(d)
    idx = d.groupby(["usuario_id", "categoria"])["fecha"].idxmax()
    latest = d.loc[idx, ["usuario_id", "categoria", "fecha"] + feats].reset_index(drop=True)
    latest = latest.drop_duplicates(subset=["usuario_id", "categoria"], keep="last")

    return latest, feats

def build_features_for_day(usuario_id, fecha):
    """
    Prepara features usando FeatureDiaria (misma tabla que entrenamiento).
    AHORA incluye contexto de anomalías.
    
    Retorna un DataFrame con las columnas necesarias para predicción.
    """
    from app.models.features import FeatureDiaria
    
    rows = (
        db.session.query(FeatureDiaria)
        .filter_by(usuario_id=usuario_id)
        .filter(FeatureDiaria.fecha <= fecha)
        .all()
    )

    if not rows:
        print(f"[WARN] No hay features históricas para usuario={usuario_id}")
        return pd.DataFrame(columns=["categoria"])

    df = pd.DataFrame([{
        'usuario_id': r.usuario_id,
        'fecha': str(r.fecha),
        'categoria': r.categoria,
        'minutos': float(r.minutos or 0)
    } for r in rows])
    
    df = df.sort_values(["usuario_id", "categoria", "fecha"])
    
    # Usar make_lagged_with_context para incluir anomalías
    df_lagged = make_lagged_with_context(df, usuario_id)
    
    latest, feats = latest_X_per_categoria(df_lagged)
    latest = latest[["categoria"] + feats].copy()
    
    if feats:
        latest[feats] = (
            latest[feats]
            .apply(pd.to_numeric, errors="coerce")
            .replace([np.inf, -np.inf], np.nan)
            .fillna(0.0)
        )
    
    latest["categoria"] = latest["categoria"].astype(str)
    return latest


def calcular_baseline_mean_7d(usuario_id: int, categoria: str, fecha_actual) -> float:
    """
    MEJORA #3: Baseline para ensemble
    Calcula la media móvil de 7 días para una categoría.
    """
    from app.models.features import FeatureDiaria
    from datetime import timedelta
    
    fecha_inicio = fecha_actual - timedelta(days=7)
    
    rows = (
        db.session.query(FeatureDiaria)
        .filter_by(usuario_id=usuario_id, categoria=categoria)
        .filter(FeatureDiaria.fecha > fecha_inicio)
        .filter(FeatureDiaria.fecha <= fecha_actual)
        .all()
    )
    
    if not rows:
        return 0.0
    
    minutos = [float(r.minutos or 0) for r in rows]
    return sum(minutos) / len(minutos) if minutos else 0.0