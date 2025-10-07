from datetime import datetime, timedelta, date
from ml.pipeline import predict, get_model_for_categoria, _bootstrap_flask_context
import json

USUARIO_ID = 1 

def main():
    print("=== Test del selector automático ===")
    _bootstrap_flask_context()
    from ml.pipeline import MODEL_SELECTOR
    print("\nModelos asignados en model_selector.json:")
    print(json.dumps(MODEL_SELECTOR, indent=2, ensure_ascii=False))
    res = predict(USUARIO_ID, fecha=date.today() + timedelta(days=1), save_csv=False)
    print("\nResultado de predicción:")
    print(json.dumps(res, indent=2, ensure_ascii=False))

    print("\nCategorías y modelo elegido:")
    for p in res["predicciones"]:
        modelo = get_model_for_categoria(p["categoria"])
        print(f" - {p['categoria']}: {modelo}")

if __name__ == "__main__":
    main()