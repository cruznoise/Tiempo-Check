import json
from pathlib import Path

SUMMARY_PATHS = [
    Path("ml/artifacts/backtesting/backtesting_summary.json"),
    Path("ml/artifacts/backtesting_summary.json"),
    Path("ml/ml/artifacts/backtesting/backtesting_summary.json"), 
]

SELECTOR_FILE = Path("ml/artifacts/model_selector.json")

def build_model_selector():
    """
    Construye model_selector.json a partir del resumen de backtesting.
    Selecciona automáticamente el mejor modelo (menor RMSE) por categoría.
    """
    summary_file = next((p for p in SUMMARY_PATHS if p.exists()), None)
    if summary_file is None:
        raise FileNotFoundError(
            "No encontré backtesting_summary.json en ninguna ruta esperada."
        )

    with open(summary_file, "r", encoding="utf-8") as f:
        summary = json.load(f)

    selector = {}
    for key, metrics in summary.items():
        if "__" in key:
            categoria, modelo = key.split("__", 1)
            selector.setdefault(categoria, {})[modelo] = metrics
        else:
            selector.setdefault(key, {}).update(metrics)
    final_selector = {}
    for categoria, modelos in selector.items():
        rmse_base = modelos.get("BaselineHybrid", {}).get("rmse", float("inf"))
        rmse_rf = modelos.get("RandomForest", {}).get("rmse", float("inf"))
        final_selector[categoria] = (
            "RandomForest" if rmse_rf < rmse_base else "BaselineHybrid"
        )

    SELECTOR_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SELECTOR_FILE, "w", encoding="utf-8") as f:
        json.dump(final_selector, f, indent=2, ensure_ascii=False)

    print("✅ Selector de modelos generado en:", SELECTOR_FILE)

if __name__ == "__main__":
    build_model_selector()
