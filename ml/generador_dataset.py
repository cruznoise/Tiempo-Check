import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import pandas as pd
from datetime import datetime
from flask import Flask
from app import db
from app.models import Registro, Categoria, DominioCategoria
from sqlalchemy.orm import joinedload



# Configuración de Flask para usar SQLAlchemy
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:base@localhost/tiempocheck_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def generar_dataset(usuario_id=1):
    with app.app_context():
        # Query con OUTER JOIN para traer todos los registros
        registros = db.session.query(Registro, Categoria.nombre)\
            .outerjoin(DominioCategoria, Registro.dominio == DominioCategoria.dominio)\
            .outerjoin(Categoria, Categoria.id == DominioCategoria.categoria_id)\
            .filter(Registro.usuario_id == usuario_id)\
            .all()

        print(f"Total registros obtenidos: {len(registros)}")

        # Crear DataFrame con relleno de "Sin categoría"
        data = []
        for r, categoria in registros:
            data.append({
                "fecha": r.fecha,
                "dominio": r.dominio,
                "tiempo_segundos": r.tiempo,
                "categoria": categoria if categoria else "Sin categoría"
            })

        df = pd.DataFrame(data)

        if df.empty:
            print("⚠️ No se generaron datos para este usuario.")
            return

        # Guardar CSV
        output_path = os.path.join(os.path.dirname(__file__), 'dataset', f'dataset_usuario_{usuario_id}.csv')
        df.to_csv(output_path, index=False)
        print(f"✅ Dataset generado en: {output_path}")

if __name__ == "__main__":
    generar_dataset(usuario_id=1) 
