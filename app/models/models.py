from app.extensions import db
from datetime import datetime

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    contraseña = db.Column(db.String(100), nullable=False)

class Registro(db.Model):
    __tablename__ = 'registro'
    id = db.Column(db.Integer, primary_key=True)
    dominio = db.Column(db.String(255), nullable=False)
    tiempo = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha_hora = db.Column(db.DateTime, nullable=True, index=True)

class Categoria(db.Model):
    __tablename__ = 'categorias'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)

class DominioCategoria(db.Model):
    __tablename__ = 'dominio_categoria'
    id = db.Column(db.Integer, primary_key=True)
    dominio = db.Column(db.String(255), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    categoria = db.relationship('Categoria')

class MetaCategoria(db.Model):
    __tablename__ = 'metas_categoria'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    limite_minutos = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    cumplida = db.Column(db.Boolean, default=False) 

    usuario = db.relationship('Usuario')
    categoria = db.relationship('Categoria')

class LimiteCategoria(db.Model):
    __tablename__ = 'limite_categoria'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id  = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    limite_minutos = db.Column(db.Integer, nullable=False)

    usuario = db.relationship('Usuario')
    categoria = db.relationship('Categoria')

class UsuarioLogro(db.Model):
    __tablename__ = 'usuario_logro'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    logro_id = db.Column(db.Integer, nullable=False)

    usuario = db.relationship('Usuario')

    def to_dict(self):
        return {
            "usuario_id": self.usuario_id,
            "logro_id": self.logro_id
        }

class FeatureDiaria(db.Model):
    __tablename__ = 'features_diarias'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    fecha = db.Column(db.Date, nullable=False, index=True)
    categoria = db.Column(db.String(64), nullable=False, index=True)
    minutos = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    __table_args__ = (db.UniqueConstraint('usuario_id','fecha','categoria', name='uq_features_diarias'),)

class FeatureHoraria(db.Model):
    __tablename__ = 'features_horarias'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    fecha = db.Column(db.Date, nullable=False, index=True)
    hora = db.Column(db.SmallInteger, nullable=False)  # 0..23
    categoria = db.Column(db.String(64), nullable=False, index=True)
    minutos = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    __table_args__ = (db.UniqueConstraint('usuario_id','fecha','hora','categoria', name='uq_features_horarias'),)