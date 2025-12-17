-- ============================================
-- MIGRACIÓN SEGURIDAD - TiempoCheck v3.2.2
-- Fecha: 16 de diciembre de 2025
-- ============================================

-- ============================================
-- PASO 1: MODIFICAR TABLA `categorias`
-- ============================================

-- 1.1 Eliminar restricción UNIQUE global en nombre
ALTER TABLE categorias DROP INDEX nombre;

-- 1.2 Hacer usuario_id NOT NULL
-- NOTA: Primero asignar usuario_id=1 a categorías sin dueño
UPDATE categorias SET usuario_id = 1 WHERE usuario_id IS NULL;

ALTER TABLE categorias MODIFY usuario_id INT NOT NULL;

-- 1.3 Crear restricción única compuesta (nombre + usuario_id)
ALTER TABLE categorias 
ADD CONSTRAINT unique_categoria_usuario UNIQUE (nombre, usuario_id);

-- ============================================
-- PASO 2: MODIFICAR TABLA `patrones_categoria`
-- ============================================

-- 2.1 Eliminar restricción UNIQUE global en patron
ALTER TABLE patrones_categoria DROP INDEX patron;

-- 2.2 Crear restricción única compuesta (patron + usuario_id)
ALTER TABLE patrones_categoria 
ADD CONSTRAINT unique_patron_usuario UNIQUE (patron, usuario_id);

-- ============================================
-- PASO 3: MODIFICAR TABLA `dominio_categoria`
-- ============================================

-- 3.1 Agregar columna usuario_id si no existe
ALTER TABLE dominio_categoria 
ADD COLUMN usuario_id INT NOT NULL DEFAULT 1 AFTER categoria_id;

-- 3.2 Agregar foreign key a usuarios
ALTER TABLE dominio_categoria 
ADD CONSTRAINT fk_dominio_usuario 
FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE;

-- 3.3 Crear restricción única compuesta (dominio + usuario_id)
ALTER TABLE dominio_categoria 
ADD CONSTRAINT uq_dominio_usuario UNIQUE (dominio, usuario_id);

-- ============================================
-- VERIFICACIÓN
-- ============================================

-- Mostrar estructura de tablas
SHOW CREATE TABLE categorias;
SHOW CREATE TABLE patrones_categoria;
SHOW CREATE TABLE dominio_categoria;

-- Verificar datos
SELECT 'Categorías por usuario:' as info;
SELECT usuario_id, COUNT(*) as total FROM categorias GROUP BY usuario_id;

SELECT 'Patrones por usuario:' as info;
SELECT usuario_id, COUNT(*) as total FROM patrones_categoria GROUP BY usuario_id;

SELECT 'Dominios por usuario:' as info;
SELECT usuario_id, COUNT(*) as total FROM dominio_categoria GROUP BY usuario_id;

-- ============================================
-- NOTAS IMPORTANTES
-- ============================================

/*
ANTES DE EJECUTAR:
1. Haz backup de tu base de datos
2. Verifica que tienes al menos un usuario (id=1)

DESPUÉS DE EJECUTAR:
1. Actualiza los archivos Python (models.py, admin_controller.py)
2. Reinicia el servidor Flask

ROLLBACK (si algo sale mal):
1. Restaura el backup con: mysql -u root -p tiempocheck_db < backup_XXXXXX.sql
*/
