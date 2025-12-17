-- ============================================
-- MIGRACIÓN FINAL - TiempoCheck v3.2.2
-- Basado en diagnóstico real
-- Solo cambios necesarios
-- ============================================

SELECT '🔍 INICIANDO MIGRACIÓN...' as '';

-- ============================================
-- TABLA 1: categorias
-- ============================================

SELECT '📋 MIGRANDO: categorias' as '';

-- Eliminar índice UNIQUE global 'unique'
ALTER TABLE categorias DROP INDEX `unique`;

-- Hacer usuario_id NOT NULL (ya no hay huérfanos)
ALTER TABLE categorias MODIFY usuario_id INT NOT NULL;

-- Crear restricción única compuesta
ALTER TABLE categorias 
ADD CONSTRAINT unique_categoria_usuario UNIQUE (nombre, usuario_id);

-- Verificar
SELECT '✅ categorias migrada' as '';
SHOW CREATE TABLE categorias\G

-- ============================================
-- TABLA 2: patrones_categoria
-- ============================================

SELECT '📋 MIGRANDO: patrones_categoria' as '';

-- Eliminar índice UNIQUE global 'ux_pc_patron'
ALTER TABLE patrones_categoria DROP INDEX `ux_pc_patron`;

-- Crear restricción única compuesta
ALTER TABLE patrones_categoria 
ADD CONSTRAINT unique_patron_usuario UNIQUE (patron, usuario_id);

-- Verificar
SELECT '✅ patrones_categoria migrada' as '';
SHOW CREATE TABLE patrones_categoria\G

-- ============================================
-- TABLA 3: dominio_categoria
-- ============================================

SELECT '✅ dominio_categoria - YA ESTABA MIGRADA' as '';
SHOW CREATE TABLE dominio_categoria\G

-- ============================================
-- VERIFICACIÓN FINAL
-- ============================================

SELECT '🎯 VERIFICACIÓN FINAL' as '';

-- Ver todas las restricciones UNIQUE
SELECT TABLE_NAME, CONSTRAINT_NAME 
FROM information_schema.TABLE_CONSTRAINTS
WHERE TABLE_SCHEMA = 'tiempocheck_db'
  AND TABLE_NAME IN ('categorias', 'patrones_categoria', 'dominio_categoria')
  AND CONSTRAINT_TYPE = 'UNIQUE'
ORDER BY TABLE_NAME;

-- Distribución de datos
SELECT 'Categorías por usuario:' as info;
SELECT usuario_id, COUNT(*) as total FROM categorias GROUP BY usuario_id;

SELECT 'Patrones por usuario:' as info;
SELECT usuario_id, COUNT(*) as total FROM patrones_categoria GROUP BY usuario_id;

SELECT 'Dominios por usuario:' as info;
SELECT usuario_id, COUNT(*) as total FROM dominio_categoria GROUP BY usuario_id;

SELECT '🎉 ¡MIGRACIÓN COMPLETADA!' as '';
