from app.extensions import db
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.dialects.mysql import JSON as MySQLJSON

class CoachAlerta(db.Model):
    __tablename__ = "coach_alerta"
    __table_args__ = (
        db.Index("ix_coach_alerta_user_created", "usuario_id", "creado_en"),
        {"extend_existing": True},
    )
    id           = db.Column(db.BigInteger, primary_key=True)
    usuario_id   = db.Column(db.Integer, nullable=False, index=True)
    tipo         = db.Column(db.String(32), nullable=False, default="general")
    categoria    = db.Column(db.String(64))
    severidad    = db.Column(db.String(8), nullable=False, default="mid")  # simplificado
    titulo       = db.Column(db.String(160))
    mensaje      = db.Column(db.Text)
    contexto_json= db.Column(MySQLJSON)
    fecha_desde  = db.Column(db.Date)
    fecha_hasta  = db.Column(db.Date)
    dedupe_key   = db.Column(db.String(128), unique=True)
    creado_en    = db.Column(db.DateTime, nullable=False, server_default=func.current_timestamp())
    leido        = db.Column(db.Boolean, nullable=False, default=False)

class CoachSugerencia(db.Model):
    __tablename__ = "coach_sugerencia"
    id             = db.Column(db.BigInteger, primary_key=True)
    usuario_id     = db.Column(db.Integer, nullable=False, index=True)
    tipo           = db.Column(db.String(32), nullable=False, default="general")
    categoria      = db.Column(db.String(64))
    titulo         = db.Column(db.String(160))
    cuerpo         = db.Column(db.Text)
    action_type    = db.Column(db.String(32))
    action_payload = db.Column(MySQLJSON)
    expires_at     = db.Column(db.DateTime, nullable=True) 
    status         = db.Column(db.String(16), nullable=False, default="new")  
    creado_en      = db.Column(db.DateTime, nullable=False, server_default=func.current_timestamp())

class CoachAccionLog(db.Model):
    __tablename__ = "coach_accion_log"
    id         = db.Column(db.BigInteger, primary_key=True)
    usuario_id = db.Column(db.Integer, nullable=False, index=True)
    origen     = db.Column(db.String(32))  
    origen_id  = db.Column(db.BigInteger)
    accion     = db.Column(db.String(32))
    payload    = db.Column(MySQLJSON)
    creado_en  = db.Column(db.DateTime, nullable=False, server_default=func.current_timestamp())

class CoachEstadoRegla(db.Model):
    __tablename__ = "coach_estado_regla"
    __table_args__ = (
        {"extend_existing": True},
    )

    usuario_id     = db.Column(db.Integer, primary_key=True)
    regla          = db.Column(db.String(64), primary_key=True)
    categoria      = db.Column(db.String(64), primary_key=True, default="", nullable=False)
    last_triggered = db.Column(db.DateTime)
    cooldown_until = db.Column(db.DateTime, index=True)
    contador       = db.Column(db.Integer, nullable=False, default=0)
    creado_en      = db.Column(db.DateTime, nullable=False, server_default=func.current_timestamp())
    actualizado_en = db.Column(
        db.DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
