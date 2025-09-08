from dataclasses import dataclass
import numpy as np
from sklearn.ensemble import RandomForestRegressor

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
