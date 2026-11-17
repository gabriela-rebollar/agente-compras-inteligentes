"""
herramientas/base_datos.py
==========================
PAPEL EN EL SISTEMA:
    HERRAMIENTA 5 - "Guardar resultados en MySQL".
    Inserta en la tabla `resultados` de la base de datos local `analisis_compras`
    una fila por cada oferta encontrada:
        nombre_producto | comercio | precio | fecha_consulta

¿POR QUE ES UNA HERRAMIENTA DEL AGENTE?
    Para que el agente no se quede solo en la busqueda: tambien ACTUA sobre otro
    sistema (una base de datos). Asi queda un historial de precios que despues se
    puede consultar con SQL (por ejemplo, ver como cambia un precio con el tiempo).

CONFIGURACION (archivo .env):
    MYSQL_HOST=127.0.0.1     MYSQL_PORT=3307 (XAMPP)    MYSQL_USER=root
    MYSQL_PASSWORD=          MYSQL_DB=analisis_compras

    Si MySQL no esta encendido (o la pagina corre en la nube), la herramienta
    responde que no pudo guardar y el agente sigue funcionando normalmente.
"""

import json
import os
from datetime import datetime

from langchain_core.tools import tool

from herramientas.datos import buscar_coincidencias

# Instrucciones SQL que se ejecutan para asegurar que existan la base y la tabla
# (las mismas del archivo database/analisis_compras.sql).
CREAR_TABLA = """
CREATE TABLE IF NOT EXISTS resultados (
  id               INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  nombre_producto  VARCHAR(200)  NOT NULL,
  comercio         VARCHAR(100)  NOT NULL,
  precio           DECIMAL(10,2) NOT NULL,
  fecha_consulta   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_producto (nombre_producto),
  CONSTRAINT chk_precio_positivo CHECK (precio >= 0)
) ENGINE=InnoDB
"""

INSERTAR = """
INSERT INTO resultados (nombre_producto, comercio, precio, fecha_consulta)
VALUES (%s, %s, %s, %s)
"""


def conectar():
    """
    Abre la conexion a MySQL con los datos del .env.
    Primero crea la base `analisis_compras` si no existe, y luego la usa.
    """
    import pymysql  # se importa aqui para que el resto del proyecto no dependa de MySQL

    nombre_bd = os.getenv("MYSQL_DB", "analisis_compras")
    conexion = pymysql.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3307")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        charset="utf8mb4",
        connect_timeout=4,
        autocommit=False,
    )
    with conexion.cursor() as cursor:
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{nombre_bd}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
    conexion.select_db(nombre_bd)
    return conexion


@tool
def guardar_resultados(consulta: str) -> str:
    """Guarda en la base de datos MySQL (tabla resultados de analisis_compras) cada
    oferta encontrada: nombre del producto, comercio, precio y fecha de consulta.
    Usala al final, despues de las otras herramientas, con el mismo texto de busqueda."""
    productos = buscar_coincidencias(consulta)
    if not productos:
        return json.dumps(
            {"consulta": consulta, "guardado": False, "mensaje": "No hay productos que guardar."},
            ensure_ascii=False,
        )

    # Todas las filas de esta consulta llevan la misma fecha y hora.
    fecha = datetime.now().replace(microsecond=0)
    filas = [
        (producto["nombre"], oferta["tienda"], oferta["precio"], fecha)
        for producto in productos
        for oferta in producto["tiendas"]
    ]

    try:
        conexion = conectar()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(CREAR_TABLA)
                # executemany inserta todas las filas en una sola operacion.
                cursor.executemany(INSERTAR, filas)
            # TRANSACCION: o se guardan todas las filas o ninguna.
            conexion.commit()
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()
    except Exception as error:
        return json.dumps(
            {
                "consulta": consulta,
                "guardado": False,
                "mensaje": f"No se pudo guardar en MySQL ({type(error).__name__}). "
                "Revisa que XAMPP tenga MySQL encendido.",
            },
            ensure_ascii=False,
        )

    return json.dumps(
        {
            "consulta": consulta,
            "guardado": True,
            "base_de_datos": os.getenv("MYSQL_DB", "analisis_compras"),
            "tabla": "resultados",
            "filas_insertadas": len(filas),
            "fecha_consulta": fecha.isoformat(sep=" "),
        },
        ensure_ascii=False,
    )
