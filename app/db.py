from flask_sqlalchemy import SQLAlchemy
from flask import g
import mysql.connector

db = SQLAlchemy()

def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(
            host='localhost',
            user='root',
            password='base', #contraseña de mysql propia
            database='tiempocheck_db'  
        )
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()