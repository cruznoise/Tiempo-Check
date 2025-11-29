from . import create_app
import os
app = create_app()

"""try:
    print("\n== URL MAP ==")
    for r in sorted(app.url_map.iter_rules(), key=lambda x: x.rule):
        print(f"{r.methods}  {r.rule}  -> {r.endpoint}")
    print("== END URL MAP ==\n")
except Exception as e:
    print("No se pudo imprimir url_map:", e)
"""

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() in ('1', 'true', 'yes')
    
    app = create_app()

    port = int(os.environ.get('PORT', 5000))

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode,
        use_reloader=debug_mode 
    )