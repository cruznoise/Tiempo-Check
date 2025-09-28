from app.app import app
from app.models.models import db

with app.app_context():
    db.create_all()
    print("✅ Tablas creadas correctamente.")
