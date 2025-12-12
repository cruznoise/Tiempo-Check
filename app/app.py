from . import create_app
import os
import ssl

app = create_app()

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() in ('1', 'true', 'yes')
    port = int(os.environ.get('PORT', 5000))
    
    # Detectar si estamos en local o producción
    is_local = not os.environ.get('RAILWAY_ENVIRONMENT')
    
    if is_local:
        # DESARROLLO LOCAL con HTTPS
        print("\n" + "="*70)
        print("MODO DESARROLLO: HTTPS Local")
        print("="*70)
        print(f" URL: https://localhost:{port}")
        print(" Certificado autofirmado - Chrome mostrará advertencia")
        print("   Haz clic en 'Avanzado' → 'Continuar a localhost'")
        print("="*70 + "\n")
        
        # Crear contexto SSL
        cert_path = os.path.join(os.path.dirname(__file__), '..', 'certs', 'cert.pem')
        key_path = os.path.join(os.path.dirname(__file__), '..', 'certs', 'key.pem')
        
        # Verificar que existen los certificados
        if not os.path.exists(cert_path) or not os.path.exists(key_path):
            print(" ERROR: No se encontraron certificados SSL")
            print(f"   Cert: {cert_path}")
            print(f"   Key:  {key_path}")
            print("\n Genera certificados con:")
            print("   openssl req -x509 -newkey rsa:4096 -nodes \\")
            print("     -out certs/cert.pem -keyout certs/key.pem -days 365 \\")
            print("     -subj '/C=MX/ST=CDMX/L=Mexico/O=TiempoCheck/CN=localhost'")
            exit(1)
        
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_path, key_path)
        
        app.run(
            host='0.0.0.0',
            port=port,
            debug=debug_mode,
            use_reloader=debug_mode,
            ssl_context=context  # ← HTTPS
        )
    else:
        # PRODUCCIÓN (Railway) - Sin SSL (Railway lo maneja)
        print("\n" + "="*70)
        print(" MODO PRODUCCIÓN: Railway")
        print("="*70 + "\n")
        
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            use_reloader=False
        )