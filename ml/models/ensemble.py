
import numpy as np
from pathlib import Path
from ml.features import calcular_baseline_mean_7d


class EnsemblePredictor:
    """
    Combina predicciones de RF con baseline de media móvil.
    
    Estrategia de ponderación:
    - Pocas muestras (<30):  70% baseline, 30% RF
    - Muestras medias (30-60): 50% baseline, 50% RF  
    - Muchas muestras (>60):  30% baseline, 70% RF
    """
    
    def __init__(self, modelo_rf, usuario_id: int, categoria: str):
        self.modelo_rf = modelo_rf
        self.usuario_id = usuario_id
        self.categoria = categoria
        self.n_muestras = self._contar_muestras_historicas()
        self.peso_rf, self.peso_baseline = self._calcular_pesos()
    
    def _contar_muestras_historicas(self) -> int:
        """
        Cuenta cuántas muestras históricas tiene esta categoría.
        Se usa para ajustar los pesos del ensemble.
        """
        from app.models.features import FeatureDiaria
        from app.extensions import db
        
        try:
            count = (
                db.session.query(FeatureDiaria)
                .filter_by(usuario_id=self.usuario_id, categoria=self.categoria)
                .count()
            )
            return count
        except:
            return 50  # Valor por defecto si falla
    
    def _calcular_pesos(self) -> tuple:
        """
        Calcula pesos adaptativos según cantidad de datos.
        
        Returns:
            (peso_rf, peso_baseline)
        """
        if self.n_muestras < 30:
            # Pocos datos: confía más en baseline
            return (0.30, 0.70)
        elif self.n_muestras < 60:
            # Datos medios: equilibrado
            return (0.50, 0.50)
        else:
            # Muchos datos: confía más en RF
            return (0.70, 0.30)
    
    def predict(self, X, fecha_actual) -> float:
        """
        Genera predicción ensemble.
        
        Args:
            X: Features para el modelo RF
            fecha_actual: Fecha base para calcular baseline
        
        Returns:
            Predicción combinada (minutos)
        """
        # Predicción RF
        pred_rf_raw = self.modelo_rf.predict(X)
        pred_rf = float(pred_rf_raw[0]) if isinstance(pred_rf_raw, (list, tuple, np.ndarray)) else float(pred_rf_raw)
        pred_rf = max(0.0, pred_rf)  # No negativos
        
        # Predicción Baseline (media 7 días)
        pred_baseline = calcular_baseline_mean_7d(
            self.usuario_id, 
            self.categoria, 
            fecha_actual
        )
        
        # Ensemble ponderado
        pred_ensemble = (self.peso_rf * pred_rf) + (self.peso_baseline * pred_baseline)
        
        # Debug info (solo si hay diferencia significativa)
        if abs(pred_rf - pred_baseline) > 10:
            print(f"[ENSEMBLE] {self.categoria}: RF={pred_rf:.1f}, Base={pred_baseline:.1f}, "
                  f"Final={pred_ensemble:.1f} (n={self.n_muestras}, w_rf={self.peso_rf:.2f})")
        
        return pred_ensemble
    
    def get_weights_info(self) -> dict:
        """Devuelve info sobre los pesos usados"""
        return {
            'n_muestras': self.n_muestras,
            'peso_rf': self.peso_rf,
            'peso_baseline': self.peso_baseline,
            'estrategia': 'pocos_datos' if self.n_muestras < 30 else 
                         'datos_medios' if self.n_muestras < 60 else 
                         'muchos_datos'
        }


def crear_ensemble_predictor(modelo_rf, usuario_id: int, categoria: str):
    """
    Factory function para crear un EnsemblePredictor.
    
    Usage:
        from ml.models.baseline import BaselineHybrid
        from ml.models.ensemble import crear_ensemble_predictor
        
        modelo_rf = joblib.load('ml/artifacts/usuario_12/estudio/rf_estudio.joblib')
        predictor = crear_ensemble_predictor(modelo_rf, usuario_id=12, categoria='Estudio')
        
        pred = predictor.predict(X_features, fecha_actual=date.today())
    """
    return EnsemblePredictor(modelo_rf, usuario_id, categoria)