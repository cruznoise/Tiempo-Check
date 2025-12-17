-- MySQL dump 10.13  Distrib 8.0.19, for Win64 (x86_64)
--
-- Host: 172.25.51.223    Database: tiempocheck_db
-- ------------------------------------------------------
-- Server version	8.0.44-0ubuntu0.22.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `agg_estado_dia`
--

DROP TABLE IF EXISTS `agg_estado_dia`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `agg_estado_dia` (
  `usuario_id` int NOT NULL,
  `fecha` date NOT NULL,
  `categoria` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `minutos` double NOT NULL DEFAULT '0',
  `meta_min` double DEFAULT NULL,
  `limite_min` double DEFAULT NULL,
  `cumplio_meta` tinyint(1) NOT NULL DEFAULT '0',
  `excedio_limite` tinyint(1) NOT NULL DEFAULT '0',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`usuario_id`,`fecha`,`categoria`),
  KEY `idx_aed_usuario_fecha` (`usuario_id`,`fecha`),
  KEY `idx_aed_fecha` (`fecha`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `agg_kpi_rango`
--

DROP TABLE IF EXISTS `agg_kpi_rango`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `agg_kpi_rango` (
  `usuario_id` int NOT NULL,
  `rango` varchar(12) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `fecha_ref` date NOT NULL,
  `min_total` double NOT NULL DEFAULT '0',
  `min_productivo` double NOT NULL DEFAULT '0',
  `min_no_productivo` double NOT NULL DEFAULT '0',
  `pct_productivo` double NOT NULL DEFAULT '0',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`usuario_id`,`rango`,`fecha_ref`),
  UNIQUE KEY `ux_kpi` (`usuario_id`,`rango`,`fecha_ref`),
  KEY `idx_akr_fecha_ref` (`fecha_ref`),
  KEY `idx_akr_user_fecha` (`usuario_id`,`fecha_ref`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `agg_ventana_categoria`
--

DROP TABLE IF EXISTS `agg_ventana_categoria`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `agg_ventana_categoria` (
  `usuario_id` int NOT NULL,
  `categoria` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `ventana` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `fecha_fin` date NOT NULL,
  `minutos_sum` double NOT NULL DEFAULT '0',
  `minutos_promedio` double NOT NULL DEFAULT '0',
  `dias_con_datos` int NOT NULL DEFAULT '0',
  `pct_del_total` double NOT NULL DEFAULT '0',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`usuario_id`,`categoria`,`ventana`,`fecha_fin`),
  UNIQUE KEY `ux_avc` (`usuario_id`,`categoria`,`ventana`,`fecha_fin`),
  KEY `idx_avc_fecha_fin` (`fecha_fin`),
  KEY `idx_avc_user_fecha` (`usuario_id`,`fecha_fin`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `alembic_version`
--

DROP TABLE IF EXISTS `alembic_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `categorias`
--

DROP TABLE IF EXISTS `categorias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `categorias` (
  `Id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) NOT NULL,
  `usuario_id` int DEFAULT NULL,
  PRIMARY KEY (`Id`),
  UNIQUE KEY `unique` (`nombre`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `categorias_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `coach_accion_log`
--

DROP TABLE IF EXISTS `coach_accion_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `coach_accion_log` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `origen` enum('alerta','sugerencia','dashboard','dashboard_predicciones','metas','coach') NOT NULL,
  `origen_id` bigint DEFAULT NULL,
  `accion` varchar(64) NOT NULL,
  `payload` json DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_accion_user` (`usuario_id`,`created_at` DESC),
  KEY `idx_accion_fecha` (`accion`,`created_at` DESC)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `coach_alerta`
--

DROP TABLE IF EXISTS `coach_alerta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `coach_alerta` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `tipo` varchar(64) NOT NULL,
  `categoria` varchar(64) DEFAULT NULL,
  `severidad` enum('low','mid','high') NOT NULL DEFAULT 'mid',
  `titulo` varchar(160) NOT NULL,
  `mensaje` text NOT NULL,
  `contexto_json` json DEFAULT NULL,
  `fecha_desde` date NOT NULL,
  `fecha_hasta` date NOT NULL,
  `dedupe_key` varchar(128) NOT NULL,
  `creado_en` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `leido` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_alerta_dedupe` (`dedupe_key`),
  KEY `idx_alerta_user_fecha` (`usuario_id`,`fecha_hasta` DESC)
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `coach_estado_regla`
--

DROP TABLE IF EXISTS `coach_estado_regla`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `coach_estado_regla` (
  `usuario_id` int NOT NULL,
  `regla` varchar(64) NOT NULL,
  `categoria` varchar(64) NOT NULL DEFAULT '',
  `last_triggered` datetime DEFAULT NULL,
  `cooldown_until` datetime DEFAULT NULL,
  `contador` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`usuario_id`,`regla`,`categoria`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `coach_sugerencia`
--

DROP TABLE IF EXISTS `coach_sugerencia`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `coach_sugerencia` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `tipo` varchar(64) NOT NULL,
  `categoria` varchar(64) DEFAULT NULL,
  `titulo` varchar(180) NOT NULL,
  `cuerpo` text NOT NULL,
  `action_type` varchar(64) DEFAULT NULL,
  `action_payload` json DEFAULT NULL,
  `expires_at` datetime DEFAULT NULL,
  `status` enum('new','pending','acted','dismissed','expired') NOT NULL DEFAULT 'new',
  `creado_en` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_sug_user_status` (`usuario_id`,`status`,`creado_en` DESC),
  KEY `idx_sug_estado` (`status`,`creado_en` DESC)
) ENGINE=InnoDB AUTO_INCREMENT=41 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `contexto_dia`
--

DROP TABLE IF EXISTS `contexto_dia`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `contexto_dia` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `fecha` date NOT NULL,
  `es_atipico` tinyint(1) DEFAULT '0',
  `motivo` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `motivo_detalle` text COLLATE utf8mb4_unicode_ci,
  `uso_esperado_min` float DEFAULT NULL,
  `uso_real_min` float DEFAULT NULL,
  `desviacion_pct` float DEFAULT NULL,
  `fecha_registro` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_usuario_fecha` (`usuario_id`,`fecha`),
  KEY `idx_usuario_fecha` (`usuario_id`,`fecha`),
  KEY `idx_es_atipico` (`es_atipico`),
  CONSTRAINT `contexto_dia_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=68 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dominio_categoria`
--

DROP TABLE IF EXISTS `dominio_categoria`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dominio_categoria` (
  `id` int NOT NULL AUTO_INCREMENT,
  `dominio` varchar(255) NOT NULL,
  `categoria_id` int DEFAULT NULL,
  `categoria` varchar(120) NOT NULL DEFAULT 'Sin categoría',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_dominio` (`dominio`),
  KEY `categoria_id` (`categoria_id`),
  CONSTRAINT `dominio_categoria_ibfk_1` FOREIGN KEY (`categoria_id`) REFERENCES `categorias` (`Id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=391 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `features_categoria_diaria`
--

DROP TABLE IF EXISTS `features_categoria_diaria`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `features_categoria_diaria` (
  `usuario_id` int NOT NULL,
  `fecha` date NOT NULL,
  `categoria` varchar(120) NOT NULL,
  `minutos` decimal(10,2) NOT NULL,
  PRIMARY KEY (`usuario_id`,`fecha`,`categoria`),
  UNIQUE KEY `uq_fcdiaria_user_fecha_cat` (`usuario_id`,`fecha`,`categoria`),
  KEY `ix_fcdiaria_usuario_fecha` (`usuario_id`,`fecha`),
  KEY `ix_fcdiaria_usuario_categoria` (`usuario_id`,`categoria`),
  KEY `ix_fcdiaria_fecha` (`fecha`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `features_diarias`
--

DROP TABLE IF EXISTS `features_diarias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `features_diarias` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `fecha` date NOT NULL,
  `categoria` varchar(100) NOT NULL,
  `minutos` int NOT NULL,
  `racha_metas` int DEFAULT NULL,
  `racha_limites` int DEFAULT NULL,
  `confianza` enum('0-2','3-6','7-14','14+') DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ux_user_fecha_cat` (`usuario_id`,`fecha`,`categoria`),
  UNIQUE KEY `ux_user_fecha_categoria` (`usuario_id`,`fecha`,`categoria`),
  UNIQUE KEY `uq_fdiarias_user_fecha_cat` (`usuario_id`,`fecha`,`categoria`),
  KEY `idx_user_fecha` (`usuario_id`,`fecha`),
  KEY `ix_fdiarias_usuario_id` (`usuario_id`),
  KEY `ix_fdiarias_fecha` (`fecha`),
  KEY `ix_fdiarias_categoria` (`categoria`)
) ENGINE=InnoDB AUTO_INCREMENT=4855 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `features_horarias`
--

DROP TABLE IF EXISTS `features_horarias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `features_horarias` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `fecha` date NOT NULL,
  `hora` tinyint NOT NULL,
  `categoria` varchar(100) NOT NULL,
  `minutos` int NOT NULL,
  `uso_tipico_semana` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ux_user_fecha_hora_cat` (`usuario_id`,`fecha`,`hora`,`categoria`),
  UNIQUE KEY `ux_user_fecha_hora_categoria` (`usuario_id`,`fecha`,`hora`,`categoria`),
  UNIQUE KEY `uq_fchorarias_user_fecha_hora_cat` (`usuario_id`,`fecha`,`hora`,`categoria`),
  KEY `idx_user_fecha_hora` (`usuario_id`,`fecha`,`hora`),
  KEY `ix_fchorarias_usuario_id` (`usuario_id`),
  KEY `ix_fchorarias_fecha` (`fecha`),
  KEY `ix_fchorarias_categoria` (`categoria`)
) ENGINE=InnoDB AUTO_INCREMENT=4944 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `features_horarias_bak`
--

DROP TABLE IF EXISTS `features_horarias_bak`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `features_horarias_bak` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `fecha` date NOT NULL,
  `hora` tinyint NOT NULL,
  `categoria` varchar(100) NOT NULL,
  `minutos` int NOT NULL,
  `uso_tipico_semana` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ux_user_fecha_hora_cat` (`usuario_id`,`fecha`,`hora`,`categoria`),
  UNIQUE KEY `ux_user_fecha_hora_categoria` (`usuario_id`,`fecha`,`hora`,`categoria`),
  KEY `idx_user_fecha_hora` (`usuario_id`,`fecha`,`hora`)
) ENGINE=InnoDB AUTO_INCREMENT=111 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `features_uso_hora`
--

DROP TABLE IF EXISTS `features_uso_hora`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `features_uso_hora` (
  `usuario_id` int NOT NULL,
  `fecha` date NOT NULL,
  `hora_num` tinyint NOT NULL,
  `minutos` decimal(10,2) NOT NULL,
  PRIMARY KEY (`usuario_id`,`fecha`,`hora_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `intentos_bloqueo_focus`
--

DROP TABLE IF EXISTS `intentos_bloqueo_focus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `intentos_bloqueo_focus` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sesion_id` int NOT NULL,
  `momento` datetime NOT NULL,
  `url_bloqueada` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `categoria` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_sesion` (`sesion_id`),
  KEY `idx_momento` (`momento`),
  CONSTRAINT `intentos_bloqueo_focus_ibfk_1` FOREIGN KEY (`sesion_id`) REFERENCES `sesiones_focus` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `limite_categoria`
--

DROP TABLE IF EXISTS `limite_categoria`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `limite_categoria` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `categoria_id` int NOT NULL,
  `limite_minutos` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `usuario_id` (`usuario_id`),
  KEY `categoria_id` (`categoria_id`),
  CONSTRAINT `limite_categoria_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE,
  CONSTRAINT `limite_categoria_ibfk_2` FOREIGN KEY (`categoria_id`) REFERENCES `categorias` (`Id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=38 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logros`
--

DROP TABLE IF EXISTS `logros`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `logros` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `descripcion` text,
  `imagen_url` varchar(255) DEFAULT NULL,
  `nivel` enum('primerizo','intermedio','productivo','super_pro') NOT NULL,
  `icono` varchar(100) DEFAULT NULL,
  `condicion_logica` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logros_dinamicos`
--

DROP TABLE IF EXISTS `logros_dinamicos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `logros_dinamicos` (
  `logro_id` int NOT NULL,
  `tipo_condicion` varchar(50) DEFAULT NULL,
  `categoria_id` int DEFAULT NULL,
  `valor_referencia` int DEFAULT NULL,
  PRIMARY KEY (`logro_id`),
  CONSTRAINT `logros_dinamicos_ibfk_1` FOREIGN KEY (`logro_id`) REFERENCES `logros` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `metas_categoria`
--

DROP TABLE IF EXISTS `metas_categoria`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `metas_categoria` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `categoria_id` int NOT NULL,
  `minutos_meta` int NOT NULL,
  `origen` enum('manual','coach','sistema') NOT NULL DEFAULT 'manual',
  `fecha` date DEFAULT NULL,
  `cumplida` tinyint(1) DEFAULT NULL,
  `creado_en` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_meta_usuario_cat_fecha` (`usuario_id`,`categoria_id`,`fecha`),
  KEY `usuario_id` (`usuario_id`),
  KEY `categoria_id` (`categoria_id`),
  CONSTRAINT `metas_categoria_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE,
  CONSTRAINT `metas_categoria_ibfk_2` FOREIGN KEY (`categoria_id`) REFERENCES `categorias` (`Id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=36 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ml_metrics`
--

DROP TABLE IF EXISTS `ml_metrics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ml_metrics` (
  `id` int NOT NULL AUTO_INCREMENT,
  `fecha` date NOT NULL,
  `usuario_id` int NOT NULL,
  `modelo` varchar(64) NOT NULL,
  `categoria` varchar(64) NOT NULL,
  `hist_days` int NOT NULL,
  `rows_train` int NOT NULL,
  `rows_test` int NOT NULL,
  `metric_mae` float DEFAULT NULL,
  `metric_rmse` float DEFAULT NULL,
  `baseline` varchar(32) DEFAULT NULL,
  `is_promoted` tinyint(1) DEFAULT '0',
  `artifact_path` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_ml_metrics_user_date_cat` (`usuario_id`,`fecha`,`categoria`)
) ENGINE=InnoDB AUTO_INCREMENT=204 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ml_modelos`
--

DROP TABLE IF EXISTS `ml_modelos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ml_modelos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `nombre` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tipo` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `version` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `fecha_entrenamiento` datetime NOT NULL,
  `accuracy` float DEFAULT NULL,
  `precision_score` float DEFAULT NULL,
  `recall` float DEFAULT NULL,
  `f1_score` float DEFAULT NULL,
  `num_ejemplos` int DEFAULT NULL,
  `parametros` text COLLATE utf8mb4_unicode_ci,
  `ruta_archivo` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `activo` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id`),
  KEY `idx_usuario_fecha` (`usuario_id`,`fecha_entrenamiento`),
  KEY `idx_activo` (`activo`),
  CONSTRAINT `ml_modelos_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ml_predicciones_future`
--

DROP TABLE IF EXISTS `ml_predicciones_future`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ml_predicciones_future` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `fecha_pred` date NOT NULL,
  `categoria` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `yhat_minutos` float NOT NULL,
  `modelo` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `version_modelo` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=506 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `notificaciones_clasificacion`
--

DROP TABLE IF EXISTS `notificaciones_clasificacion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notificaciones_clasificacion` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `dominio` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `categoria_sugerida_id` int DEFAULT NULL,
  `confianza` float DEFAULT NULL,
  `metodo` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT 'pendiente',
  `categoria_correcta_id` int DEFAULT NULL,
  `creado_en` datetime DEFAULT CURRENT_TIMESTAMP,
  `respondido_en` datetime DEFAULT NULL,
  `usado_en_entrenamiento` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `categoria_sugerida_id` (`categoria_sugerida_id`),
  KEY `categoria_correcta_id` (`categoria_correcta_id`),
  KEY `idx_usuario_status` (`usuario_id`,`status`),
  KEY `idx_dominio` (`dominio`),
  KEY `idx_creado` (`creado_en`),
  KEY `idx_usado_entrenamiento` (`usado_en_entrenamiento`,`respondido_en`),
  CONSTRAINT `notificaciones_clasificacion_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE,
  CONSTRAINT `notificaciones_clasificacion_ibfk_2` FOREIGN KEY (`categoria_sugerida_id`) REFERENCES `categorias` (`Id`),
  CONSTRAINT `notificaciones_clasificacion_ibfk_3` FOREIGN KEY (`categoria_correcta_id`) REFERENCES `categorias` (`Id`)
) ENGINE=InnoDB AUTO_INCREMENT=179 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `patrones_categoria`
--

DROP TABLE IF EXISTS `patrones_categoria`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `patrones_categoria` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `patron` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `categoria_id` int NOT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT '1',
  `creado_en` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `actualizado_en` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ux_pc_patron` (`patron`(191)),
  KEY `idx_pc_categoria_id` (`categoria_id`),
  KEY `idx_usuario` (`usuario_id`),
  CONSTRAINT `fk_pc_categoria` FOREIGN KEY (`categoria_id`) REFERENCES `categorias` (`Id`) ON DELETE CASCADE,
  CONSTRAINT `patrones_categoria_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE,
  CONSTRAINT `patrones_categoria_ibfk_2` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rachas_usuario`
--

DROP TABLE IF EXISTS `rachas_usuario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rachas_usuario` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `tipo` enum('metas','limites') COLLATE utf8mb4_unicode_ci NOT NULL,
  `categoria_id` int DEFAULT NULL,
  `fecha_inicio` date DEFAULT NULL,
  `fecha_fin` date DEFAULT NULL,
  `dias_consecutivos` int DEFAULT '0',
  `activa` tinyint(1) NOT NULL DEFAULT '1',
  `ultima_fecha` date DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `usuario_id` (`usuario_id`),
  KEY `categoria_id` (`categoria_id`),
  CONSTRAINT `rachas_usuario_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`),
  CONSTRAINT `rachas_usuario_ibfk_2` FOREIGN KEY (`categoria_id`) REFERENCES `categorias` (`Id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `registro`
--

DROP TABLE IF EXISTS `registro`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `registro` (
  `id` int NOT NULL AUTO_INCREMENT,
  `dominio` varchar(255) DEFAULT NULL,
  `tiempo` int DEFAULT NULL,
  `fecha` datetime DEFAULT NULL,
  `fecha_hora` datetime DEFAULT NULL,
  `usuario_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `fk_registro_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=263621 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sesiones_focus`
--

DROP TABLE IF EXISTS `sesiones_focus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sesiones_focus` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `inicio` datetime NOT NULL,
  `fin_programado` datetime NOT NULL,
  `fin_real` datetime DEFAULT NULL,
  `duracion_minutos` int NOT NULL,
  `tiempo_real_minutos` int DEFAULT NULL,
  `completada` tinyint(1) DEFAULT '0',
  `modo_estricto` tinyint(1) DEFAULT '0',
  `categorias_bloqueadas` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'JSON array de categorías',
  PRIMARY KEY (`id`),
  KEY `idx_usuario` (`usuario_id`),
  KEY `idx_inicio` (`inicio`),
  KEY `idx_completada` (`completada`),
  CONSTRAINT `sesiones_focus_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `usuario_logro`
--

DROP TABLE IF EXISTS `usuario_logro`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuario_logro` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `logro_id` int NOT NULL,
  `fecha_desbloqueo` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `usuario_id` (`usuario_id`),
  KEY `logro_id` (`logro_id`),
  CONSTRAINT `usuario_logro_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`),
  CONSTRAINT `usuario_logro_ibfk_2` FOREIGN KEY (`logro_id`) REFERENCES `logros` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=117 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `correo` varchar(100) NOT NULL,
  `contrasena` varchar(255) DEFAULT NULL,
  `dedicacion` varchar(50) DEFAULT NULL,
  `horario_preferido` varchar(50) DEFAULT NULL,
  `dias_trabajo` varchar(50) DEFAULT NULL,
  `tipo_inferido` varchar(50) DEFAULT NULL,
  `confianza_inferencia` float DEFAULT '0',
  `hora_pico_inicio` int DEFAULT NULL,
  `hora_pico_fin` int DEFAULT NULL,
  `dias_activos_patron` varchar(50) DEFAULT NULL,
  `perfil_actualizado_en` datetime DEFAULT NULL,
  `creado_en` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `correo` (`correo`),
  KEY `idx_usuario_tipo_inferido` (`tipo_inferido`),
  KEY `idx_usuario_dedicacion` (`dedicacion`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary view structure for view `v_estado_actual_usuario`
--

DROP TABLE IF EXISTS `v_estado_actual_usuario`;
/*!50001 DROP VIEW IF EXISTS `v_estado_actual_usuario`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_estado_actual_usuario` AS SELECT 
 1 AS `usuario_id`,
 1 AS `nombre`,
 1 AS `ultimo_dia_calculado`,
 1 AS `categorias_activas`,
 1 AS `categorias_excedidas_hoy`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_resumen_ventanas`
--

DROP TABLE IF EXISTS `v_resumen_ventanas`;
/*!50001 DROP VIEW IF EXISTS `v_resumen_ventanas`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_resumen_ventanas` AS SELECT 
 1 AS `usuario_id`,
 1 AS `ventana`,
 1 AS `fecha_fin`,
 1 AS `total_minutos`,
 1 AS `total_categorias`,
 1 AS `promedio_general_diario`*/;
SET character_set_client = @saved_cs_client;

--
-- Dumping routines for database 'tiempocheck_db'
--

--
-- Final view structure for view `v_estado_actual_usuario`
--

/*!50001 DROP VIEW IF EXISTS `v_estado_actual_usuario`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_estado_actual_usuario` AS select `u`.`id` AS `usuario_id`,`u`.`nombre` AS `nombre`,coalesce((select max(`aes2`.`fecha`) from `agg_estado_dia` `aes2` where (`aes2`.`usuario_id` = `u`.`id`)),'1900-01-01') AS `ultimo_dia_calculado`,(select count(distinct `aes3`.`categoria`) from `agg_estado_dia` `aes3` where ((`aes3`.`usuario_id` = `u`.`id`) and (`aes3`.`fecha` = (select max(`agg_estado_dia`.`fecha`) from `agg_estado_dia` where (`agg_estado_dia`.`usuario_id` = `u`.`id`))))) AS `categorias_activas`,(select sum((case when `aes4`.`excedio_limite` then 1 else 0 end)) from `agg_estado_dia` `aes4` where ((`aes4`.`usuario_id` = `u`.`id`) and (`aes4`.`fecha` = (select max(`agg_estado_dia`.`fecha`) from `agg_estado_dia` where (`agg_estado_dia`.`usuario_id` = `u`.`id`))))) AS `categorias_excedidas_hoy` from `usuarios` `u` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_resumen_ventanas`
--

/*!50001 DROP VIEW IF EXISTS `v_resumen_ventanas`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_resumen_ventanas` AS select `agg_ventana_categoria`.`usuario_id` AS `usuario_id`,`agg_ventana_categoria`.`ventana` AS `ventana`,`agg_ventana_categoria`.`fecha_fin` AS `fecha_fin`,sum(`agg_ventana_categoria`.`minutos_sum`) AS `total_minutos`,count(distinct `agg_ventana_categoria`.`categoria`) AS `total_categorias`,round(avg(`agg_ventana_categoria`.`minutos_promedio`),2) AS `promedio_general_diario` from `agg_ventana_categoria` where (`agg_ventana_categoria`.`fecha_fin` >= (curdate() - interval 7 day)) group by `agg_ventana_categoria`.`usuario_id`,`agg_ventana_categoria`.`ventana`,`agg_ventana_categoria`.`fecha_fin` order by `agg_ventana_categoria`.`usuario_id`,`agg_ventana_categoria`.`ventana`,`agg_ventana_categoria`.`fecha_fin` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-11-28 23:11:05
