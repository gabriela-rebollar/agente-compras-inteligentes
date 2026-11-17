-- =====================================================================
-- analisis_compras.sql
-- Base de datos donde el agente guarda cada precio que consulta.
--
-- COMO USARLO:
--   Opcion 1: en phpMyAdmin (http://localhost/phpmyadmin) abre la pestaña
--             "SQL", pega este archivo y presiona "Continuar".
--   Opcion 2: no hacer nada. La herramienta guardar_resultados crea la base
--             y la tabla sola la primera vez (CREATE ... IF NOT EXISTS).
-- =====================================================================

CREATE DATABASE IF NOT EXISTS analisis_compras
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE analisis_compras;

-- Una fila por cada oferta encontrada (producto + comercio + precio).
CREATE TABLE IF NOT EXISTS resultados (
  id               INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  nombre_producto  VARCHAR(200)  NOT NULL,
  comercio         VARCHAR(100)  NOT NULL,
  precio           DECIMAL(10,2) NOT NULL,
  fecha_consulta   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_producto (nombre_producto),
  CONSTRAINT chk_precio_positivo CHECK (precio >= 0)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Consultas utiles para revisar lo que guardo el agente
-- ---------------------------------------------------------------------
-- Ultimas consultas:
--   SELECT * FROM resultados ORDER BY fecha_consulta DESC LIMIT 20;
--
-- Precio mas bajo, mas alto y promedio de cada producto:
--   SELECT nombre_producto, MIN(precio) AS minimo, MAX(precio) AS maximo,
--          ROUND(AVG(precio), 2) AS promedio, COUNT(*) AS ofertas
--   FROM resultados GROUP BY nombre_producto;
--
-- Comercio mas barato en promedio:
--   SELECT comercio, ROUND(AVG(precio), 2) AS promedio
--   FROM resultados GROUP BY comercio ORDER BY promedio;
