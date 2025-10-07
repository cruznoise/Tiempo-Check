import numpy as np
import pandas as pd

class BaselineHybrid:
    """
    Modelo base híbrido:
    Usa la media móvil de los últimos 7 días como predicción simple.
    """
    def __init__(self):
        self.mean_7d = None
        self.trend = 0.0

    def fit(self, serie: pd.Series | list | np.ndarray):
        """
        Ajusta el modelo con los últimos valores disponibles.
        Acepta series de minutos (por día o categoría).
        """
        if isinstance(serie, (list, np.ndarray)):
            serie = pd.Series(serie)
        elif isinstance(serie, pd.DataFrame):
            if "minutos" in serie.columns:
                serie = serie["minutos"]

        serie = serie.dropna()
        if len(serie) == 0:
            self.mean_7d = 0.0
            self.trend = 0.0
            return self

        # --- ML-004 fix: usar últimos 7 valores reales ---
        tail = serie.tail(7)
        self.mean_7d = float(tail.mean())
        if len(tail) > 1:
            self.trend = (tail.iloc[-1] - tail.iloc[0]) / (len(tail) - 1)
        else:
            self.trend = 0.0
        return self

    def predict(self, X=None):
        """
        Devuelve la predicción esperada según media reciente y tendencia.
        Si no hay histórico, devuelve 0.0.
        """
        if self.mean_7d is None:
            return 0.0
        yhat = self.mean_7d + (self.trend * 0.5)
        return max(yhat, 0.0)
