import pandas as pd
from datetime import datetime
from app.extensions import db
from app.models.ml import MLPrediccionFuture


def sync_preds_future_to_db(usuario_id: int, csv_path: str):
    """
    Inserta predicciones futuras desde un CSV en la tabla ml_predicciones_future.

    El CSV debe tener columnas:
      fecha_pred, categoria, yhat_minutos, modelo, version_modelo
    """
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"[ERROR] No se pudo leer el archivo CSV: {csv_path}\n{e}")
        return

    if df.empty:
        print("[WARN] El CSV está vacío, no se insertaron registros.")
        return

    required_cols = {"fecha_pred", "categoria", "yhat_minutos"}
    if not required_cols.issubset(df.columns):
        print(f"[ERROR] El CSV no contiene las columnas requeridas: {required_cols}")
        return
    df["fecha_pred"] = pd.to_datetime(df["fecha_pred"]).dt.date
    df["modelo"] = df.get("modelo", "Desconocido")
    df["version_modelo"] = df.get("version_modelo", "v3.2")
    nuevos = 0
    for _, row in df.iterrows():
        existe = MLPrediccionFuture.query.filter_by(
            usuario_id=usuario_id,
            fecha_pred=row["fecha_pred"],
            categoria=row["categoria"]
        ).first()
        if existe:
            continue  
        registro = MLPrediccionFuture(
            usuario_id=usuario_id,
            fecha_pred=row["fecha_pred"],
            categoria=row["categoria"],
            yhat_minutos=float(row["yhat_minutos"]),
            modelo=row["modelo"],
            version_modelo=row["version_modelo"],
            fecha_creacion=datetime.utcnow()
        )
        db.session.add(registro)
        nuevos += 1

    db.session.commit()
    print(f" Insertadas {nuevos} predicciones nuevas en ml_predicciones_future desde {csv_path}")
