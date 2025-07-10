
from flask_sqlalchemy import SQLAlchemy

from app.db import db  

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