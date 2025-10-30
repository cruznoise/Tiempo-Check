from datetime import datetime
from app.extensions import db

class MlMetric(db.Model):
    __tablename__ = "ml_metrics"
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False, index=True)
    usuario_id = db.Column(db.Integer, nullable=False, index=True)
    modelo = db.Column(db.String(64), nullable=False)
    categoria = db.Column(db.String(64), nullable=False, index=True)
    hist_days = db.Column(db.Integer, nullable=False)
    rows_train = db.Column(db.Integer, nullable=False)
    rows_test = db.Column(db.Integer, nullable=False)
    metric_mae = db.Column(db.Float)
    metric_rmse = db.Column(db.Float)
    baseline = db.Column(db.String(32))
    is_promoted = db.Column(db.Boolean, default=False)
    artifact_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))

class MlPrediccionFuture(db.Model):
    __tablename__ = "ml_predicciones_future"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, nullable=False)
    fecha_pred = db.Column(db.Date, nullable=False)
    categoria = db.Column(db.String(100), nullable=False)
    yhat_minutos = db.Column(db.Float, nullable=False)
    modelo = db.Column(db.String(50), nullable=False)
    version_modelo = db.Column(db.String(20))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PredFuture {self.usuario_id} {self.fecha_pred} {self.categoria}>"