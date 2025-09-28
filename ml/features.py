import pandas as pd

def _calendar_feats(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    dt = pd.to_datetime(d["fecha"])
    d["dow"] = dt.dt.weekday
    d["is_weekend"] = (d["dow"] >= 5).astype(int)
    d["day"] = dt.dt.day
    d["days_to_eom"] = dt.dt.daysinmonth - d["day"]
    return d

def make_lagged(df: pd.DataFrame, lags=(1,2,3,7), ma_windows=(7,)) -> pd.DataFrame:
    """
    Construye features por usuario-categoría con índice alineado (sin MultiIndex).
    Requiere al menos min_t-1; MA7 se calcula como rolling(7) del shift(1).
    """
    d = df.sort_values(["usuario_id","categoria","fecha"]).copy()
    d = _calendar_feats(d)
    g = d.groupby(["usuario_id","categoria"], group_keys=False)

    for L in lags:
        d[f"min_t-{L}"] = g["minutos"].shift(L)

    for W in ma_windows:
        d[f"MA{W}"] = g["minutos"].transform(lambda s: s.shift(1).rolling(W, min_periods=1).mean())

    d = d.dropna(subset=["min_t-1"])
    return d

def get_feature_cols(d: pd.DataFrame):
    return [c for c in d.columns if c.startswith("min_t-") or c.startswith("MA")] + [
        "dow","is_weekend","day","days_to_eom"
    ]

def split_train_holdout(d: pd.DataFrame, holdout_days=7):
    d = d.sort_values(["usuario_id","categoria","fecha"]).copy()
    max_date = pd.to_datetime(d["fecha"]).max().normalize()
    mask = pd.to_datetime(d["fecha"]).dt.normalize() > (max_date - pd.Timedelta(days=holdout_days))
    return d.loc[~mask].copy(), d.loc[mask].copy()

def latest_X_per_categoria(d: pd.DataFrame):
    d = d.sort_values(["usuario_id","categoria","fecha"]).copy()
    feats = get_feature_cols(d)
    idx = d.groupby(["usuario_id","categoria"])["fecha"].idxmax()
    latest = d.loc[idx, ["usuario_id","categoria","fecha"] + feats].reset_index(drop=True)
    return latest, feats
