from pathlib import Path
import re
from datetime import date, datetime

def canon_cat(cat: str) -> str:
    if not cat:
        return "Sin categoría"
    cat = cat.strip().lower()
    cat = re.sub(r'[\s_]+', ' ', cat)
    cat = cat.replace("sin categoria", "sin categoría")
    cat = cat.title()
    return cat

def canon_cat_filename(cat: str) -> str:
    """
    Normaliza el nombre de una categoría para usarlo en archivos.
    Convierte a minúsculas, reemplaza espacios y barras por guiones bajos.
    """
    if not cat:
        return "sin_categoria"
    return cat.strip().lower().replace(" ", "_").replace("/", "_")


def ensure_dir(path: str | Path):
    """
    Crea el directorio si no existe.
    """
    Path(path).mkdir(parents=True, exist_ok=True)

def guardar_predicciones(
        df,
        fecha_base=None,
        tipo: str = "multi",
        canonical: bool = True
            
):
    """ Se guaran las predicciones en ml/preds/ con nombre preds_future_xx_xx_xx.csv"""

    if fecha_base is None:
        fecha_str = date.today().isoformat()
    elif isinstance(fecha_base, str):
        try:
            date.fromisoformat(fecha_base)  
        except ValueError as e:
            raise ValueError(f"fecha_base inválida (YYYY-MM-DD): {fecha_base}") from e
        fecha_str = fecha_base
    elif isinstance(fecha_base, datetime):
        fecha_str = fecha_base.date().isoformat()
    elif isinstance(fecha_base, date):
        fecha_str = fecha_base.isoformat()
    else:
        raise TypeError(f"Tipo no soportado para fecha_base: {type(fecha_base)}")
    
    out_dir = Path(__file__).resolve().parent / "preds"
    out_dir.mkdir(parents=True, exist_ok=True)

    if canonical:
        fname = f"preds_future_{fecha_str}.csv"
    else:
        fname = f"{fecha_str}_{tipo}.csv"

    out_path = out_dir / fname
    df.to_csv(out_path, index=False)
    print(f"[ML][SAVE] Predicciones guardadas en: {out_path.as_posix()}")
    return out_path


# ============================================================================
# CLASIFICACIÓN AUTOMÁTICA DE DOMINIOS CON ML
# ============================================================================

from app.services.clasificador_ml import ClasificadorDominios

# Cargar clasificador ML al inicio (singleton)
_clasificador_ml = None

def get_clasificador():
    """Obtiene clasificador ML (carga solo una vez)"""
    global _clasificador_ml
    if _clasificador_ml is None:
        _clasificador_ml = ClasificadorDominios()
        _clasificador_ml.cargar()
    return _clasificador_ml


def clasificar_dominio_automatico(dominio, usuario_id=1):
    """
    Clasifica un dominio usando ML + Regex como fallback
    Si falla, crea notificación para clasificación manual
    
    Args:
        dominio: URL del dominio a clasificar (ej: 'facebook.com')
        usuario_id: ID del usuario
    
    Returns:
        categoria_id (int) o None
    """
    # Imports dentro de función para evitar circular imports
    from app import db
    from app.models.models import Categoria
    from app.models.models_coach import NotificacionClasificacion
    from app.utils import get_mysql
    
    print(f"[CLASIFICACIÓN] 🔍 Procesando: {dominio}")
    
    categoria_id = None
    confianza = 0.0
    metodo = None
    necesita_clasificacion_manual = False
    
    # ========================================================================
    # PASO 1: Intentar clasificación con ML
    # ========================================================================
    clasificador = get_clasificador()
    
    if clasificador.entrenado:
        categoria_nombre, confianza = clasificador.predecir(dominio)
        
        if categoria_nombre and confianza >= 0.50:  # 50% confianza mínima
            print(f"[ML]  {dominio} → {categoria_nombre} ({confianza:.0%})")
            
            # Buscar ID de categoría en BD
            cat_obj = Categoria.query.filter_by(nombre=categoria_nombre).first()
            
            if cat_obj:
                categoria_id = cat_obj.id
                metodo = 'ml'
            else:
                print(f"[ML]   Categoría '{categoria_nombre}' no existe en BD")
        else:
            print(f"[ML]   Confianza muy baja ({confianza:.0%})")
    else:
        print("[ML]   Clasificador no entrenado")
    
    # ========================================================================
    # PASO 2: Fallback a Regex si ML no dio resultado confiable
    # ========================================================================
    if not categoria_id:
        print("[FALLBACK]  Intentando con Regex...")
        
        try:
            conexion = get_mysql()
            
            with conexion.cursor() as cursor:
                cursor.execute("SELECT patron, categoria_id FROM patrones_categoria")
                patrones = cursor.fetchall()
                
                for patron, cat_id in patrones:
                    if re.search(patron, dominio, re.IGNORECASE):
                        print(f"[REGEX]  Match: {patron} → categoría {cat_id}")
                        categoria_id = cat_id
                        confianza = 0.85  
                        metodo = 'regex'
                        break
        except Exception as e:
            print(f"[REGEX][ERROR] {e}")
    
    # ========================================================================
    # PASO 3: Si nada funcionó → Marcar para clasificación manual
    # ========================================================================
    if not categoria_id:
        print(f"[CLASIFICACIÓN]  No se pudo clasificar: {dominio}")
        necesita_clasificacion_manual = True
        
        # CRÍTICO: Asignar temporalmente a "Sin categoría" SIEMPRE
        try:
            cat_default = Categoria.query.filter_by(nombre='Sin categoría').first()
            if cat_default:
                categoria_id = cat_default.id
                metodo = 'sin_clasificar'
                print(f"[DEFAULT] Asignando temporalmente a 'Sin categoría' (ID: {categoria_id})")
            else:
                # FALLBACK: Si no existe "Sin categoría", buscar cualquier categoría
                primera_cat = Categoria.query.first()
                if primera_cat:
                    categoria_id = primera_cat.id
                    print(f"[DEFAULT][FALLBACK] Usando primera categoría disponible (ID: {categoria_id})")
                else:
                    print(f"[DEFAULT][ERROR] No hay categorías en la BD!")
                    # Crear categoría por defecto si no existe ninguna
                    nueva_cat = Categoria(nombre='Sin categoría', usuario_id=usuario_id)
                    db.session.add(nueva_cat)
                    db.session.commit()
                    categoria_id = nueva_cat.id
                    print(f"[DEFAULT][CREATED] Categoría 'Sin categoría' creada (ID: {categoria_id})")
        except Exception as e:
            print(f"[DEFAULT][ERROR] {e}")
            # Último recurso: usar 1 (asumiendo que existe)
            categoria_id = 1
            print(f"[DEFAULT][EMERGENCY] Usando categoría ID=1")
    
    # ========================================================================
    # PASO 4: Guardar en BD
    # ========================================================================
    if categoria_id:
        try:
            conexion = get_mysql()
            with conexion.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO dominio_categoria (dominio, categoria_id) 
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE categoria_id = %s
                """, (dominio, categoria_id, categoria_id))
                conexion.commit()
                print(f"[BD]  Guardado: {dominio} → categoría {categoria_id}")
        except Exception as e:
            print(f"[BD][ERROR] {e}")
    
    # ========================================================================
    # PASO 5: Crear notificación (confirmación O clasificación manual)
    # ========================================================================
    try:
        # Verificar si ya existe notificación pendiente
        notif_existente = NotificacionClasificacion.query.filter_by(
            dominio=dominio,
            usuario_id=usuario_id,
            status='pendiente'
        ).first()
        
        if not notif_existente:
            if necesita_clasificacion_manual:
                # NOTIFICACIÓN DE CLASIFICACIÓN MANUAL
                notif = NotificacionClasificacion(
                    usuario_id=usuario_id,
                    dominio=dominio,
                    categoria_sugerida_id=categoria_id,  # Puede ser None si BD lo permite
                    confianza=0.0,
                    metodo='manual_required'
                )
                db.session.add(notif)
                db.session.commit()
                print(f"[NOTIF] Clasificación MANUAL requerida: {dominio}")
            else:
                # NOTIFICACIÓN DE CONFIRMACIÓN
                if categoria_id:  # Solo crear si hay categoría válida
                    notif = NotificacionClasificacion(
                        usuario_id=usuario_id,
                        dominio=dominio,
                        categoria_sugerida_id=categoria_id,
                        confianza=confianza,
                        metodo=metodo
                    )
                    db.session.add(notif)
                    db.session.commit()
                    print(f"[NOTIF] Confirmación creada: {dominio}")
                else:
                    print(f"[NOTIF]  No se creó notificación (sin categoría válida)")
        else:
            print(f"[NOTIF]  Ya existe notificación pendiente")
            
    except Exception as e:
        print(f"[NOTIF][ERROR] {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
            
    except Exception as e:
        print(f"[NOTIF][ERROR] {e}")
        db.session.rollback()
    
    return categoria_id