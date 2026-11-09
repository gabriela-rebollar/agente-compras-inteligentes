"""
herramientas/comparador.py
==========================
PAPEL EN EL SISTEMA:
    HERRAMIENTA 2 - "Comparador de precios".
    Detecta los precios de cada opcion y obtiene, con Python normal:
        - el precio final (el mas bajo y en que tienda),
        - el precio promedio,
        - el rango de precio (minimo, maximo y la diferencia entre ellos).

¿POR QUE CALCULARLO CON PYTHON Y NO CON EL LLM?
    Los LLM pueden equivocarse haciendo cuentas. Python no. Asi el agente
    se encarga de RAZONAR y la herramienta de CALCULAR con exactitud.
"""

import json

from langchain_core.tools import tool

from herramientas.datos import buscar_coincidencias, origen_de


def calcular_estadisticas(precios: list[float]) -> dict:
    """Calcula minimo, maximo, promedio y rango de una lista de precios."""
    minimo = min(precios)
    maximo = max(precios)
    return {
        "precio_minimo": minimo,
        "precio_maximo": maximo,
        "precio_promedio": round(sum(precios) / len(precios), 2),
        "rango": maximo - minimo,
    }


@tool
def comparar_precios(consulta: str) -> str:
    """Compara los precios de un producto entre tiendas. Devuelve, para cada producto,
    el precio final mas bajo y su tienda, el promedio y el rango de precios; y tambien
    el resumen de TODAS las opciones juntas. Usala despues de buscar_productos."""
    productos = buscar_coincidencias(consulta)

    if not productos:
        return json.dumps(
            {"consulta": consulta, "mensaje": "No se encontraron productos para comparar."},
            ensure_ascii=False,
        )

    por_producto = []
    todos_los_precios = []

    for producto in productos:
        precios = [oferta["precio"] for oferta in producto["tiendas"]]
        todos_los_precios.extend(precios)

        # La oferta mas barata es el "precio final" que pagaria el usuario.
        mas_barata = min(producto["tiendas"], key=lambda oferta: oferta["precio"])

        por_producto.append(
            {
                "producto": producto["nombre"],
                "precio_final": mas_barata["precio"],
                "tienda_mas_barata": mas_barata["tienda"],
                **calcular_estadisticas(precios),
            }
        )

    # Ordenamos de mas barato a mas caro para facilitar la lectura.
    por_producto.sort(key=lambda fila: fila["precio_final"])

    return json.dumps(
        {
            "consulta": consulta,
            "origen": origen_de(productos),
            "por_producto": por_producto,
            "resumen_general": calcular_estadisticas(todos_los_precios),
        },
        ensure_ascii=False,
    )
