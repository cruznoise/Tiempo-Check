from pathlib import Path
from datetime import datetime
import hashlib, json, re

BASE = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE / "dataset"
RAW_DIR = DATASET_DIR / "raw"
PROCESSED_DIR = DATASET_DIR / "processed"
LOGS_DIR = PROCESSED_DIR / "logs"
SCHEMA_DIR = BASE / "schema"

DOM_RE = re.compile(r'^(localhost|(\w[\w-]{0,61}\.)+[A-Za-z]{2,})$')

def ensure_dirs():
    for d in [RAW_DIR, PROCESSED_DIR, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def todaystamp():
    return datetime.now().strftime("%Y%m%d")

def now_iso():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

def log_line(msg: str):
    ensure_dirs()
    p = LOGS_DIR / f"pipeline_{todaystamp()}.log"
    p.write_text((p.read_text() if p.exists() else "") + f"[{now_iso()}] {msg}\n", encoding="utf-8")

def write_meta(df, tabla: str, schema_ver: str):
    ensure_dirs()
    csv_bytes = df.to_csv(index=False).encode()
    meta = {
        "tabla": tabla,
        "schema_ver": schema_ver,
        "generated_at": now_iso(),
        "rowcount": int(len(df)),
        "sha256": hashlib.sha256(csv_bytes).hexdigest()
    }
    (LOGS_DIR / f"meta_{tabla}_{todaystamp()}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
