-- ============================================
-- DIAGNÓSTICO PRE-MIGRACIÓN
-- ============================================

SELECT '=== VERSIÓN MYSQL ===' as '';
SELECT VERSION();

SELECT '=== USUARIOS ACTUALES ===' as '';
SELECT id, nombre, correo FROM usuarios;

-- ============================================
-- ESTRUCTURA: categorias
-- ============================================
SELECT '=== ESTRUCTURA: categorias ===' as '';
SHOW CREATE TABLE categorias\G

SELECT '=== ÍNDICES: categorias ===' as '';
SHOW INDEX FROM categorias;

SELECT '=== CONSTRAINTS: categorias ===' as '';
SELECT CONSTRAINT_NAME, CONSTRAINT_TYPE
FROM information_schema.TABLE_CONSTRAINTS
WHERE TABLE_SCHEMA = 'tiempocheck_db' AND TABLE_NAME = 'categorias';

-- ============================================
-- ESTRUCTURA: patrones_categoria
-- ============================================
SELECT '=== ESTRUCTURA: patrones_categoria ===' as '';
SHOW CREATE TABLE patrones_categoria\G

SELECT '=== ÍNDICES: patrones_categoria ===' as '';
SHOW INDEX FROM patrones_categoria;

SELECT '=== CONSTRAINTS: patrones_categoria ===' as '';
SELECT CONSTRAINT_NAME, CONSTRAINT_TYPE
FROM information_schema.TABLE_CONSTRAINTS
WHERE TABLE_SCHEMA = 'tiempocheck_db' AND TABLE_NAME = 'patrones_categoria';

-- ============================================
-- ESTRUCTURA: dominio_categoria
-- ============================================
SELECT '=== ESTRUCTURA: dominio_categoria ===' as '';
SHOW CREATE TABLE dominio_categoria\G

SELECT '=== ÍNDICES: dominio_categoria ===' as '';
SHOW INDEX FROM dominio_categoria;

SELECT '=== CONSTRAINTS: dominio_categoria ===' as '';
SELECT CONSTRAINT_NAME, CONSTRAINT_TYPE
FROM information_schema.TABLE_CONSTRAINTS
WHERE TABLE_SCHEMA = 'tiempocheck_db' AND TABLE_NAME = 'dominio_categoria';

-- ============================================
-- DATOS ACTUALES
-- ============================================
SELECT '=== CONTEO ACTUAL ===' as '';
SELECT 'categorias' as tabla, COUNT(*) as total FROM categorias
UNION ALL
SELECT 'patrones_categoria', COUNT(*) FROM patrones_categoria
UNION ALL
SELECT 'dominio_categoria', COUNT(*) FROM dominio_categoria;

SELECT '=== CATEGORÍAS CON usuario_id NULL ===' as '';
SELECT COUNT(*) as huerfanas FROM categorias WHERE usuario_id IS NULL;

SELECT '=== DISTRIBUCIÓN POR USUARIO ===' as '';
SELECT usuario_id, COUNT(*) as total FROM categorias GROUP BY usuario_id;
