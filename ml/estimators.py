from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from dataclasses import dataclass
import pandas as pd
from typing import Dict, Any

@dataclass
class NaiveLast:
    def fit(self, X, y): return self
    def predict(self, X):
        if "min_t-1" not in X.columns:
            raise ValueError("Falta la columna min_t-1 para NaiveLast.")
        return X["min_t-1"].to_numpy()

@dataclass
class MA7:
    def fit(self, X, y): return self
    def predict(self, X):
        if "MA7" not in X.columns:
            raise ValueError("Falta la columna MA7 para baseline MA7.")
        return X["MA7"].to_numpy()

@dataclass
class BaselineHybrid:
    """
    Usa MA7 si está disponible; si no, cae a min_t-1.
    """
    def fit(self, X, y): return self
    def predict(self, X):
        if "MA7" in X.columns:
            vals = X["MA7"]
            if "min_t-1" in X.columns:
                vals = vals.fillna(X["min_t-1"])
            return vals.to_numpy()
        elif "min_t-1" in X.columns:
            return X["min_t-1"].to_numpy()
        else:
            return np.zeros(len(X))

@dataclass
class RFReg:
    n_estimators: int = 400
    random_state: int = 42
    n_jobs: int = -1
    def __post_init__(self):
        self.model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            random_state=self.random_state,
            n_jobs=self.n_jobs
        )
    def fit(self, X, y):
        self.model.fit(X, y); return self
    def predict(self, X):
        return self.model.predict(X)

@dataclass
class NaiveMovingAverage:
    window: int = 7
    categoria_minutos_: Dict[str, float] | None = None
    fe_version_: str | None = None

    def fit(self, df_fc: pd.DataFrame, fe_version: str | None = None) -> "NaiveMovingAverage":
        """
        df_fc: DataFrame con columnas [usuario_id, fecha, categoria, minutos]
        """
        self.fe_version_ = fe_version
        df_sorted = df_fc.sort_values(["categoria", "fecha"])
        roll = (
            df_sorted
            .groupby("categoria")["minutos"]
            .apply(lambda s: s.rolling(self.window, min_periods=1).mean())
            .reset_index(level=0, drop=True)
        )
        df_mm = df_sorted.assign(mm=roll)
        self.categoria_minutos_ = (
            df_mm.groupby("categoria")["mm"].last().fillna(0.0).to_dict()
        )
        return self

    def predict_t1(self, categorias: list[str]) -> pd.DataFrame:
        """
        Devuelve DataFrame con columnas [categoria, minutos_pred]
        """
        assert self.categoria_minutos_ is not None, "Modelo no entrenado"
        preds = []
        for c in categorias:
            val = float(self.categoria_minutos_.get(c, 0.0))
            preds.append({"categoria": c, "minutos_pred": max(val, 0.0)})
        return pd.DataFrame(preds)

    def to_artifact(self) -> Dict[str, Any]:
        return {
            "type": "naive_moving_average",
            "window": self.window,
            "fe_version": self.fe_version_,
            "categoria_minutos": self.categoria_minutos_,
        }