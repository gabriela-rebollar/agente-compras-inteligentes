"""
herramientas/buscador.py
========================
PAPEL EN EL SISTEMA:
    HERRAMIENTA 1 - "Buscador de productos".
    Consulta las tiendas (Walmart, Costco, Sam's Club y Mercado Libre) y extrae
    las opciones disponibles: nombre del producto, tienda, precio y link.

    Es normalmente la PRIMERA herramienta que usa el agente, porque sin saber
    que opciones existen no puede comparar ni recomendar nada.
"""

import json

from langchain_core.tools import tool

from herramientas.datos import buscar_coincidencias, origen_de


@tool
def buscar_productos(consulta: str) -> str:
    """Busca un producto en las tiendas (Walmart, Costco, Sam's Club, Mercado Libre)
    y devuelve las opciones encontradas con nombre, tienda, precio en MXN y link.
    Usala primero, con lo que el usuario quiere comprar, por ejemplo 'audifonos inalambricos'.
    Funciona con cualquier producto."""
    # NOTA: el docstring de arriba lo LEE EL LLM para saber cuando usar la
    # herramienta, por eso esta escrito como instruccion corta y clara.

    productos = buscar_coincidencias(consulta)

    if not productos:
        return json.dumps(
            {"consulta": consulta, "opciones": [], "mensaje": "No se encontraron productos."},
            ensure_ascii=False,
        )

    # "Aplanamos" los datos: una fila por cada (producto, tienda).
    opciones = []
    for producto in productos:
        for oferta in producto["tiendas"]:
            opciones.append(
                {
                    "producto": producto["nombre"],
                    "tienda": oferta["tienda"],
                    "precio": oferta["precio"],
                    "link": oferta["link"],
                }
            )

    # Se devuelve texto JSON porque es facil de leer tanto para el LLM
    # como para el front end (que arma la tabla con estos mismos datos).
    # "origen" indica si los datos vienen del catalogo o fueron estimados por el LLM.
    return json.dumps(
        {"consulta": consulta, "origen": origen_de(productos), "opciones": opciones},
        ensure_ascii=False,
    )
