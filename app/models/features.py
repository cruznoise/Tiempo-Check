from app.extensions import db

class FeatureDiaria(db.Model):
    __tablename__ = 'features_diarias'
    id = db.Column(db.BigInteger, primary_key=True)
    usuario_id = db.Column(db.Integer, nullable=False, index=True)
    fecha = db.Column(db.Date, nullable=False, index=True)
    categoria = db.Column(db.String(100), nullable=False)
    minutos = db.Column(db.Integer, nullable=False)
    racha_metas = db.Column(db.Integer)
    racha_limites = db.Column(db.Integer)
    confianza = db.Column(db.Enum('0-2','3-6','7-14','14+'))
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    __table_args__ = (db.UniqueConstraint('usuario_id','fecha','categoria', name='ux_user_fecha_cat'),)

class FeatureHoraria(db.Model):
    __tablename__ = 'features_horarias'
    id = db.Column(db.BigInteger, primary_key=True)
    usuario_id = db.Column(db.Integer, nullable=False, index=True)
    fecha = db.Column(db.Date, nullable=False, index=True)
    hora = db.Column(db.SmallInteger, nullable=False, index=True)
    categoria = db.Column(db.String(100), nullable=False)
    minutos = db.Column(db.Integer, nullable=False)
    uso_tipico_semana = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    __table_args__ = (db.UniqueConstraint('usuario_id','fecha','hora','categoria', name='ux_user_fecha_hora_cat'),)
