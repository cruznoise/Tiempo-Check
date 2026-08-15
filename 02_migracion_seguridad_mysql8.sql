-- ============================================
-- MIGRACIÓN SEGURIDAD - TiempoCheck v3.2.2
-- Fecha: 16 de diciembre de 2025
-- Compatible con MySQL 8.0.44
-- ============================================

-- Verificación previa
SELECT VERSION() AS 'MySQL Version';
SELECT COUNT(*) AS 'Total Usuarios' FROM usuarios;

-- ============================================
-- PASO 1: MODIFICAR TABLA `categorias`
-- ============================================

-- 1.1 Verificar estructura actual
SHOW CREATE TABLE categorias\G

-- 1.2 Eliminar restricción UNIQUE global en nombre
-- (El nombre del índice puede variar, lo detectamos primero)
SELECT CONSTRAINT_NAME 
FROM information_schema.TABLE_CONSTRAINTS 
WHERE TABLE_SCHEMA = 'tiempocheck_db' 
  AND TABLE_NAME = 'categorias' 
  AND CONSTRAINT_TYPE = 'UNIQUE';

-- Si el índice se llama 'nombre', ejecuta:
ALTER TABLE categorias DROP INDEX nombre;
-- Si da error "Can't DROP 'nombre'; check that column/key exists", 
-- intenta con:
-- ALTER TABLE categorias DROP INDEX `nombre`;
-- Si aún da error, el índice tiene otro nombre, revisa arriba

-- 1.3 Asignar usuario_id=1 a categorías huérfanas
UPDATE categorias SET usuario_id = 1 WHERE usuario_id IS NULL;

-- 1.4 Hacer usuario_id NOT NULL
ALTER TABLE categorias MODIFY usuario_id INT NOT NULL;

-- 1.5 Crear restricción única compuesta
ALTER TABLE categorias 
ADD CONSTRAINT unique_categoria_usuario UNIQUE (nombre, usuario_id);

-- Verificar
SHOW CREATE TABLE categorias\G
SELECT 'Categorías por usuario:' as info;
SELECT usuario_id, COUNT(*) as total FROM categorias GROUP BY usuario_id;

-- ============================================
-- PASO 2: MODIFICAR TABLA `patrones_categoria`
-- ============================================

-- 2.1 Verificar estructura actual
SHOW CREATE TABLE patrones_categoria\G

-- 2.2 Detectar nombre del índice UNIQUE en patron
SELECT CONSTRAINT_NAME 
FROM information_schema.TABLE_CONSTRAINTS 
WHERE TABLE_SCHEMA = 'tiempocheck_db' 
  AND TABLE_NAME = 'patrones_categoria' 
  AND CONSTRAINT_TYPE = 'UNIQUE';

-- Eliminar restricción UNIQUE global (ajusta el nombre si es diferente)
ALTER TABLE patrones_categoria DROP INDEX patron;
-- Si da error, intenta:
-- ALTER TABLE patrones_categoria DROP INDEX `ux_pc_patron`;
-- Revisa el nombre exacto arriba

-- 2.3 Crear restricción única compuesta
ALTER TABLE patrones_categoria 
ADD CONSTRAINT unique_patron_usuario UNIQUE (patron, usuario_id);

-- Verificar
SHOW CREATE TABLE patrones_categoria\G
SELECT 'Patrones por usuario:' as info;
SELECT usuario_id, COUNT(*) as total FROM patrones_categoria GROUP BY usuario_id;

-- ============================================
-- PASO 3: MODIFICAR TABLA `dominio_categoria`
-- ============================================

-- 3.1 Verificar estructura actual
SHOW CREATE TABLE dominio_categoria\G

-- 3.2 Verificar si usuario_id ya existe
SELECT COLUMN_NAME 
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'tiempocheck_db' 
  AND TABLE_NAME = 'dominio_categoria' 
  AND COLUMN_NAME = 'usuario_id';

-- 3.3 Agregar columna usuario_id si NO existe
-- (Si ya existe, este comando dará error y puedes continuar)
ALTER TABLE dominio_categoria 
ADD COLUMN usuario_id INT NOT NULL DEFAULT 1 AFTER categoria_id;

-- 3.4 Agregar foreign key (solo si no existe)
ALTER TABLE dominio_categoria 
ADD CONSTRAINT fk_dominio_usuario 
FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE;

-- 3.5 Crear restricción única compuesta
ALTER TABLE dominio_categoria 
ADD CONSTRAINT uq_dominio_usuario UNIQUE (dominio, usuario_id);

-- Verificar
SHOW CREATE TABLE dominio_categoria\G
SELECT 'Dominios por usuario:' as info;
SELECT usuario_id, COUNT(*) as total FROM dominio_categoria GROUP BY usuario_id;

-- ============================================
-- VERIFICACIÓN FINAL
-- ============================================

SELECT '=== VERIFICACIÓN FINAL ===' as '';

-- Contar registros por usuario
SELECT 'Categorías:' as tabla, usuario_id, COUNT(*) as total 
FROM categorias GROUP BY usuario_id
UNION ALL
SELECT 'Patrones:', usuario_id, COUNT(*) 
FROM patrones_categoria GROUP BY usuario_id
UNION ALL
SELECT 'Dominios:', usuario_id, COUNT(*) 
FROM dominio_categoria GROUP BY usuario_id
ORDER BY tabla, usuario_id;

-- Verificar que NO hay duplicados
SELECT 'Verificando duplicados en categorias...' as '';
SELECT nombre, usuario_id, COUNT(*) as duplicados
FROM categorias
GROUP BY nombre, usuario_id
HAVING COUNT(*) > 1;

SELECT 'Verificando duplicados en patrones...' as '';
SELECT patron, usuario_id, COUNT(*) as duplicados
FROM patrones_categoria
GROUP BY patron, usuario_id
HAVING COUNT(*) > 1;

SELECT 'Verificando duplicados en dominios...' as '';
SELECT dominio, usuario_id, COUNT(*) as duplicados
FROM dominio_categoria
GROUP BY dominio, usuario_id
HAVING COUNT(*) > 1;

-- ============================================
-- NOTAS IMPORTANTES
-- ============================================

/*
COMPATIBILIDAD MySQL 8.0.44:
✅ ALTER TABLE ... MODIFY
✅ CONSTRAINT UNIQUE
✅ FOREIGN KEY ... ON DELETE CASCADE
✅ information_schema queries

USUARIOS ACTUALES EN TU BD:
1  - Ángel
12 - María Estudiante  
13 - Carlos Trabajador
14 - Ana Freelancer

Todos los datos huérfanos se asignarán a usuario_id=1 (Ángel)

DESPUÉS DE EJECUTAR:
1. Actualiza app/models/models.py
2. Actualiza app/controllers/admin_controller.py
3. Reinicia Flask

ROLLBACK SI FALLA:
mysql -u root -p tiempocheck_db < backups/backup_20251216_233933.sql
*/
