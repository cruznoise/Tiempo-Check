from app.extensions import db
from datetime import timedelta, date
import pandas as pd
from sqlalchemy import  text

def load_fc_diaria(usuario_id: int, start=None, end=None) -> pd.DataFrame:
    """
    Lee la fuente canónica: features_categoria_diaria (usuario_id, fecha, categoria, minutos).
    """
    start = start or (date.today() - timedelta(days=180))
    end = end or (date.today() - timedelta(days=1))
    sql = text("""
        SELECT usuario_id, fecha, categoria, minutos
        FROM features_categoria_diaria
        WHERE usuario_id = :u AND fecha BETWEEN :d1 AND :d2
        ORDER BY fecha
    """)
    with db.engine.begin() as conn:
        df = pd.read_sql(sql, conn, params={"u": usuario_id, "d1": start, "d2": end})
    if not df.empty:
        df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
        df["categoria"] = df["categoria"].astype(str)
    return df