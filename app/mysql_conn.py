from flask import g
import mysql.connector
from app.extensions import db


def get_mysql():
    if 'mysql_conn' not in g:
        g.mysql_conn = mysql.connector.connect(
            host='localhost',
            user='angel',
            password='base',
            database='tiempocheck_db'
        )
    return g.mysql_conn

def close_mysql(e=None):
    conn = g.pop('mysql_conn', None)
    if conn is not None:
        conn.close()