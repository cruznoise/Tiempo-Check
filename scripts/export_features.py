import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
from app import create_app
from app.mysql_conn import get_mysql

OUT_PATH = Path("ml/dataset/processed/features_categoria_diaria.csv")
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

def export_features():
    app = create_app()
    with app.app_context():
        conn = get_mysql()
        query = """
            SELECT usuario_id, fecha, categoria, minutos
            FROM features_categoria_diaria
            ORDER BY usuario_id, fecha, categoria
        """
        df = pd.read_sql(query, conn)
        conn.close()

        df.to_csv(OUT_PATH, index=False)
        print(f"✅ Exportado {len(df)} registros a {OUT_PATH}")

if __name__ == "__main__":
    export_features()
