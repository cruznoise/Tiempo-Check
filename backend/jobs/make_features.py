
#!/usr/bin/env python3
"""
make_features.py — Actualiza tablas de FEATURES desde la BD `registro`.

- features_uso_hora(usuario_id, fecha, hora_num, minutos)
- features_categoria_diaria(usuario_id, fecha, categoria, minutos)

Modo de uso:
  python make_features.py --db "mysql+mysqlconnector://root:base@localhost/tiempocheck_db" \
                          --user 1 --since 2025-07-28 --until today

  # Incremental (auto):
  python make_features.py --db ... --user 1 --since auto --until today --lookback-days 1

Sugerido: correr cada 15 min con cron/launchd.
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
import pandas as pd
import sqlalchemy as sa

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.getenv("TC_DB_URL", "mysql+mysqlconnector://root:base@localhost/tiempocheck_db"),
                    help="SQLAlchemy DB URL")
    ap.add_argument("--user", type=int, required=True, help="usuario_id")
    ap.add_argument("--since", default="auto", help="'YYYY-MM-DD' | 'auto' (desde max(fecha)-lookback)")
    ap.add_argument("--until", default="today", help="'YYYY-MM-DD' | 'today' (mañana 00:00 local)")
    ap.add_argument("--lookback-days", type=int, default=1, help="Días a re-procesar para late arrivals")
    ap.add_argument("--tz", default=None, help="Ej: 'America/Mexico_City' para CONVERT_TZ (opcional)")
    ap.add_argument("--create-tables", action="store_true", help="Crear tablas de features si no existen")
    return ap.parse_args()

def engine_from_url(url):
    return sa.create_engine(url, pool_pre_ping=True)

def dt_bounds(since, until, lookback_days, engine, user_id):
    # until
    if until.lower() == "today":
        fin = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    else:
        fin = pd.to_datetime(until).to_pydatetime()

    # since
    if since.lower() == "auto":
        with engine.begin() as cx:
            res = cx.exec_driver_sql("""
            SELECT GREATEST(
              IFNULL((SELECT MAX(fecha) FROM features_uso_hora WHERE usuario_id=%s), '1970-01-01'),
              IFNULL((SELECT MAX(fecha) FROM features_categoria_diaria WHERE usuario_id=%s), '1970-01-01')
            ) AS maxf
            """, (user_id, user_id)).fetchone()
        maxf = res[0]
        if maxf is None:
            ini = fin - timedelta(days=30)  # backfill 30 días si no hay features
        else:
            ini = (pd.to_datetime(maxf).to_pydatetime() - timedelta(days=lookback_days))
    else:
        ini = pd.to_datetime(since).to_pydatetime()
    return ini, fin

def ensure_tables(engine):
    with engine.begin() as cx:
        cx.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS features_uso_hora (
          usuario_id INT NOT NULL,
          fecha DATE NOT NULL,
          hora_num TINYINT NOT NULL,
          minutos DECIMAL(10,2) NOT NULL,
          PRIMARY KEY (usuario_id, fecha, hora_num)
        );
        """)
        cx.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS features_categoria_diaria (
          usuario_id INT NOT NULL,
          fecha DATE NOT NULL,
          categoria VARCHAR(120) NOT NULL,
          minutos DECIMAL(10,2) NOT NULL,
          PRIMARY KEY (usuario_id, fecha, categoria)
        );
        """)

def upsert_uso_hora(engine, user_id, ini, fin, tz=None):
    tz_hour = "HOUR(fecha)"
    tz_date = "DATE(fecha)"
    if tz:
        tz_hour = f"HOUR(CONVERT_TZ(fecha,'+00:00',@@global.time_zone))"  # fallback si no se configuró tz tables
        # Nota: para exacto, reemplaza @@global.time_zone por el offset fijo o configura time_zone en la conexión.
        # Si conoces el offset fijo: HOUR(CONVERT_TZ(fecha,'+00:00','-06:00'))
        tz_date = f"DATE(CONVERT_TZ(fecha,'+00:00',@@global.time_zone))"

    sql = f"""
    INSERT INTO features_uso_hora (usuario_id, fecha, hora_num, minutos)
    SELECT r.usuario_id,
           {tz_date}  AS fecha,
           {tz_hour}  AS hora_num,
           SUM(LEAST(GREATEST(r.tiempo,0),21600))/60.0 AS minutos
    FROM registro r
    WHERE r.usuario_id=%s AND r.fecha >= %s AND r.fecha < %s
    GROUP BY r.usuario_id, {tz_date}, {tz_hour}
    ON DUPLICATE KEY UPDATE minutos = VALUES(minutos);
    """
    with engine.begin() as cx:
        cx.exec_driver_sql(sql, (user_id, ini, fin))

def upsert_categoria_diaria(engine, user_id, ini, fin, tz=None):
    tz_date = "DATE(fecha)"
    if tz:
        tz_date = f"DATE(CONVERT_TZ(fecha,'+00:00',@@global.time_zone))"

    # Con mapping en BD (dominio_categoria). Si no existe, cae en 'Sin categoría'.
    sql = f"""
    INSERT INTO features_categoria_diaria (usuario_id, fecha, categoria, minutos)
    SELECT r.usuario_id,
           {tz_date} AS fecha,
           COALESCE(dc.categoria, 'Sin categoría') AS categoria,
           SUM(LEAST(GREATEST(r.tiempo,0),21600))/60.0 AS minutos
    FROM registro r
    LEFT JOIN dominio_categoria dc ON dc.dominio = r.dominio
    WHERE r.usuario_id=%s AND r.fecha >= %s AND r.fecha < %s
    GROUP BY r.usuario_id, {tz_date}, categoria
    ON DUPLICATE KEY UPDATE minutos = VALUES(minutos);
    """
    with engine.begin() as cx:
        cx.exec_driver_sql(sql, (user_id, ini, fin))

def main():
    args = parse_args()
    engine = engine_from_url(args.db)
    if args.create_tables:
        ensure_tables(engine)
    ini, fin = dt_bounds(args.since, args.until, args.lookback_days, engine, args.user)
    print(f"[features] user={args.user} rango {ini} → {fin}")
    upsert_uso_hora(engine, args.user, ini, fin, tz=args.tz)
    upsert_categoria_diaria(engine, args.user, ini, fin, tz=args.tz)
    print("[features] OK")

if __name__ == "__main__":
    import pandas as pd
    main()
