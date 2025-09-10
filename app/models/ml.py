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
