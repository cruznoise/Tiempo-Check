from app.models import db, Categoria, PatronCategoria

def inicializar_categorias_usuario(usuario_id):
    """
    Crea las categorías por defecto y sus patrones para un nuevo usuario
    """
    categorias_default = {
        1: 'Productividad',
        2: 'Entretenimiento',
        3: 'Redes Sociales',
        4: 'Estudio',
        5: 'Trabajo',
        6: 'Herramientas',
        7: 'Comercio',
        9: 'Salud y bientestar',
        10: 'Informacion'
    }
    
    mapeo_ids = {}
    
    for cat_id_ref, nombre in categorias_default.items():
        nueva_categoria = Categoria(
            nombre=nombre,
            usuario_id=usuario_id
        )
        db.session.add(nueva_categoria)
        db.session.flush() 
        mapeo_ids[cat_id_ref] = nueva_categoria.id
    
    patrones_plantilla = PatronCategoria.query.filter_by(
        usuario_id=1,
        activo=True
    ).all()
    
    for patron_original in patrones_plantilla:
        # Mapear la categoría al nuevo ID
        nueva_categoria_id = mapeo_ids.get(patron_original.categoria_id)
        
        if nueva_categoria_id:
            nuevo_patron = PatronCategoria(
                usuario_id=usuario_id,
                patron=patron_original.patron,
                categoria_id=nueva_categoria_id,
                activo=True
            )
            db.session.add(nuevo_patron)
    
    db.session.commit()
    print(f" Categorías y patrones inicializados para usuario {usuario_id}")