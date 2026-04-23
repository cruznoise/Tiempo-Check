from flask import g
import mysql.connector
import os
from app.extensions import db


def get_mysql():
    """
    Obtiene una conexión MySQL leyendo las variables de entorno.
    Compatible con Railway y desarrollo local.
    """
    if 'mysql_conn' not in g:
        # Leer variables de entorno (Railway las proporciona automáticamente)
        g.mysql_conn = mysql.connector.connect(
            host=os.environ.get('MYSQLHOST', 'localhost'),
            port=int(os.environ.get('MYSQLPORT', '3306')),
            user=os.environ.get('MYSQLUSER', 'angel'),
            password=os.environ.get('MYSQLPASSWORD', 'base'),
            database=os.environ.get('MYSQLDATABASE', 'tiempocheck_db')
        )
    return g.mysql_conn


def close_mysql(e=None):
    """Cierra la conexión MySQL al final del request"""
    conn = g.pop('mysql_conn', None)
    if conn is not None:
        conn.close()