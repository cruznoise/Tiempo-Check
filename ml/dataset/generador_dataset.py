import sys
import os
from datetime import datetime, date, time
import argparse
import zoneinfo
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from flask import Flask
from sqlalchemy import func
from app import db
from app.models import Registro, Categoria, DominioCategoria

# ---- Config Flask/DB
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:base@localhost/tiempocheck_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

CATEGORIA_DEFECTO = "Sin clasificar"
RAW_DIR_DEFAULT = os.path.join(os.path.dirname(__file__), 'raw')


def exportar_raw(
    usuario_id: int = 1,
    dia: date = None,
    outdir: str = RAW_DIR_DEFAULT,
    categoria_por_defecto: str = CATEGORIA_DEFECTO
):
    """
    Exporta registros RAW a CSV con columnas:
    fecha, hora, dominio, categoria, tiempo_segundos, usuario_id

    Filtra por rango [00:00, 23:59:59] del día para aprovechar índices en Registro.fecha.
    Usa streaming/yield_per para reducir uso de memoria.
    """
    if dia is None:
        dia = date.today()

    inicio = datetime(dia.year, dia.month, dia.day, 0, 0, 0)
    fin    = datetime(dia.year, dia.month, dia.day, 23, 59, 59)

    with app.app_context():
        q = (
            db.session.query(
                Registro.fecha.label("ts"),
                Registro.dominio,
                Registro.tiempo.label("tiempo_segundos"),
                Categoria.nombre.label("categoria")
            )
            .outerjoin(DominioCategoria, Registro.dominio == DominioCategoria.dominio)
            .outerjoin(Categoria, Categoria.id == DominioCategoria.categoria_id)
            .filter(
                Registro.usuario_id == usuario_id,
                Registro.fecha >= inicio,
                Registro.fecha <= fin
            )
            .order_by(Registro.fecha)
            .execution_options(stream_results=True)
        )

        rows = q.yield_per(1000)

        data = []
        for ts, dominio, t_seg, cat in rows:
            f = ts.date() if isinstance(ts, datetime) else ts
            h = ts.hour   if isinstance(ts, datetime) else 0

            data.append({
                "fecha": f,
                "hora": h,
                "dominio": dominio,
                "categoria": cat or categoria_por_defecto,
                "tiempo_segundos": int(t_seg) if t_seg is not None else 0,
                "usuario_id": usuario_id
            })

        print(f"[RAW] {dia} usuario={usuario_id} → {len(data)} registros")

        df = pd.DataFrame(data, columns=[
            "fecha", "hora", "dominio", "categoria", "tiempo_segundos", "usuario_id"
        ])

        if not df.empty:
            df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
            df["hora"] = df["hora"].fillna(0).astype(int)
            df["tiempo_segundos"] = df["tiempo_segundos"].fillna(0).astype(int)
            df["usuario_id"] = df["usuario_id"].astype(int)

        os.makedirs(outdir, exist_ok=True)
        out_name = f"{dia.isoformat()}_usuario_{usuario_id}.csv"
        out_path = os.path.join(outdir, out_name)
        df.to_csv(out_path, index=False, encoding="utf-8")
        print(f"[RAW] Exportado: {out_path}")

        return out_path, len(df)


def _ultima_fecha_disponible(usuario_id: int):
    with app.app_context():
        return db.session.query(func.max(Registro.fecha)).filter(Registro.usuario_id == usuario_id).scalar()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exportar dataset RAW por día")
    parser.add_argument("--usuario", type=int, default=1, help="ID de usuario")
    parser.add_argument("--fecha", type=str, help="YYYY-MM-DD")
    parser.add_argument("--hoy-mx", action="store_true", help="Usa la fecha actual en America/Mexico_City")
    parser.add_argument("--outdir", type=str, default=RAW_DIR_DEFAULT, help="Directorio de salida (por defecto: ml/dataset/raw)")
    parser.add_argument("--debug", action="store_true", help="Imprime info de depuración")
    args = parser.parse_args()

    with app.app_context():
        if args.hoy_mx:
            tz = zoneinfo.ZoneInfo("America/Mexico_City")
            d = datetime.now(tz).date()
        elif args.fecha:
            d = datetime.strptime(args.fecha, "%Y-%m-%d").date()
        else:
            ult = _ultima_fecha_disponible(args.usuario)
            if ult is None:
                print("[RAW] No hay fechas disponibles para ese usuario.")
                raise SystemExit(0)
            d = ult.date() if isinstance(ult, datetime) else ult
            print(f"[RAW] Sin fecha: usaré la última fecha con datos → {d}")

        if args.debug:
            ahora_db, hoy_db = db.session.query(func.now(), func.curdate()).first()
            print(f"[DEBUG] ahora_db={ahora_db}  hoy_db={hoy_db}  dia_elegido={d}  outdir={args.outdir}")

    exportar_raw(usuario_id=args.usuario, dia=d, outdir=args.outdir)
