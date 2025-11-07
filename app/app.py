from . import create_app

app = create_app()

"""try:
    print("\n== URL MAP ==")
    for r in sorted(app.url_map.iter_rules(), key=lambda x: x.rule):
        print(f"{r.methods}  {r.rule}  -> {r.endpoint}")
    print("== END URL MAP ==\n")
except Exception as e:
    print("No se pudo imprimir url_map:", e)
"""

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
