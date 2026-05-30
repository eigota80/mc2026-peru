-- =============================================================================
-- Migración: consecutivo global para orden_servicio + soft-delete
-- Fecha:     2026-05-29
-- Autor:     Fase 2 — MC Peru 2026
--
-- PREREQUISITOS antes de ejecutar:
--   1. Backup de la BD (ver ~/mcperu_mariadb_export_20260529_130922/)
--   2. Verificar sin duplicados en numero_os:
--        SELECT numero_os, COUNT(*) FROM orden_servicio
--        GROUP BY numero_os HAVING COUNT(*) > 1;
--      Resultado esperado: 0 filas.
--   3. Ejecutar en servidor de staging primero.
--
-- CÓMO EJECUTAR:
--   mysql -u root -p bdmcperu < 20260529_os_consecutivo_global.sql
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Tabla de secuencias (genera consecutivos atómicos para múltiples entidades)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `secuencias` (
  `nombre`     VARCHAR(80)  NOT NULL,
  `valor`      INT          NOT NULL,
  `updated_at` TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                                     ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`nombre`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='Tabla de secuencias para consecutivos atómicos';

-- Inicializar con el máximo real de numero_os en BD.
-- ON DUPLICATE KEY UPDATE: si se vuelve a correr la migración, conserva el mayor.
INSERT INTO `secuencias` (`nombre`, `valor`)
SELECT
  'orden_servicio',
  COALESCE(MAX(CAST(`numero_os` AS UNSIGNED)), 699)
FROM `orden_servicio`
ON DUPLICATE KEY UPDATE
  `valor` = GREATEST(`valor`, VALUES(`valor`));

-- -----------------------------------------------------------------------------
-- 2. Agregar columnas de soft-delete a orden_servicio (si no existen)
-- -----------------------------------------------------------------------------
ALTER TABLE `orden_servicio`
  ADD COLUMN IF NOT EXISTS `deleted_at` DATETIME NULL     DEFAULT NULL
    COMMENT 'Fecha de eliminación lógica. NULL = activa.',
  ADD COLUMN IF NOT EXISTS `deleted_by` VARCHAR(150) NULL DEFAULT NULL
    COMMENT 'Usuario que eliminó la orden.';

-- -----------------------------------------------------------------------------
-- Verificación post-migración (ejecutar manualmente para confirmar)
-- -----------------------------------------------------------------------------
-- SELECT * FROM secuencias WHERE nombre = 'orden_servicio';
-- → debe mostrar: nombre='orden_servicio', valor=703
-- → la próxima orden será: 000704
--
-- DESCRIBE orden_servicio;
-- → debe tener columnas deleted_at y deleted_by
-- =============================================================================
