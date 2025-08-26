from app.extensions import db
from datetime import datetime

class CoachAlerta(db.Model):
    __tablename__ = "coach_alerta"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    fecha = db.Column(db.Date, nullable=False, index=True)
    categoria = db.Column(db.String(64), nullable=False)
    regla = db.Column(db.String(64), nullable=False)
    nivel = db.Column(db.String(16), nullable=False, default="critical")
    detalle = db.Column(db.Text, nullable=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("usuario_id", "fecha", "categoria", "regla", name="uix_alerta_unica"),
    )



class CoachSugerencia(db.Model):
    __tablename__ = 'coach_sugerencia'
    id = db.Column(db.BigInteger, primary_key=True)
    usuario_id = db.Column(db.Integer, nullable=False, index=True)
    tipo = db.Column(db.String(64), nullable=False)
    categoria = db.Column(db.String(64))
    titulo = db.Column(db.String(160), nullable=False)
    cuerpo = db.Column(db.Text, nullable=False)
    action_type = db.Column(db.String(64))
    action_payload = db.Column(db.JSON)
    expires_at = db.Column(db.DateTime)
    status = db.Column(db.Enum('new','acted','dismissed', name='sug_status'), server_default='new')
    creado_en = db.Column(db.DateTime, server_default=db.func.now())


class CoachEstadoRegla(db.Model):
    __tablename__ = 'coach_estado_regla'
    usuario_id = db.Column(db.Integer, primary_key=True)
    regla = db.Column(db.String(64), primary_key=True)
    categoria = db.Column(db.String(64), primary_key=True)
    last_triggered = db.Column(db.DateTime)
    cooldown_until = db.Column(db.DateTime)
    contador = db.Column(db.Integer, nullable=False, default=0)


class CoachAccionLog(db.Model):
    __tablename__ = 'coach_accion_log'
    id = db.Column(db.BigInteger, primary_key=True)
    usuario_id = db.Column(db.Integer, nullable=False, index=True)
    origen = db.Column(db.Enum('alerta','sugerencia', name='coach_origen'), nullable=False)
    origen_id = db.Column(db.BigInteger, nullable=False)
    accion = db.Column(db.String(64), nullable=False)
    payload = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, server_default=db.func.now())