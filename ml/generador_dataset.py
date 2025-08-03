import sys
import os

# Añadir la ruta raíz del proyecto (donde está /app) al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from datetime import datetime
from flask import Flask
from app import db
from app.models import Registro, Categoria, DominioCategoria
from sqlalchemy.orm import joinedload

# Crear instancia de Flask para usar db
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:base@localhost/tiempocheck_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Función principal
def generar_dataset(usuario_id=1):
    with app.app_context():
        # Consulta: registros del usuario con dominio y categoría
        registros = db.session.query(Registro, Categoria.nombre)\
            .join(DominioCategoria, Registro.dominio == DominioCategoria.dominio)\
            .join(Categoria, DominioCategoria.categoria_id == Categoria.id)\
            .filter(Registro.usuario_id == usuario_id)\
            .all()

        datos = [{
            'usuario_id': r.Registro.usuario_id,
            'fecha': r.Registro.fecha.strftime("%Y-%m-%d"),
            'hora': r.Registro.fecha.strftime("%H:%M"),
            'dominio': r.Registro.dominio,
            'tiempo_segundos': r.Registro.tiempo,
            'categoria': r.nombre  
        } for r in registros]


        df = pd.DataFrame(datos)

        ruta_salida = os.path.join("ml", "dataset", f"dataset_usuario_{usuario_id}.csv")
        df.to_csv(ruta_salida, index=False)
        print(f"Dataset exportado a {ruta_salida}")


if __name__ == "__main__":
    generar_dataset()
