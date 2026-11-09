"""
herramientas/usuarios.py
========================
PAPEL EN EL SISTEMA:
    HERRAMIENTA 4 - "Analista de usuarios relevantes del producto".
    Consulta que personalidades (influencers, creadores de contenido, etc.)
    han adquirido o recomiendan el producto.

NOTA IMPORTANTE:
    No existe una API gratuita que diga que famosos compraron un producto, por
    lo que esta informacion es SIMULADA y las personalidades son FICTICIAS
    (no se usan nombres de personas reales para no inventar algo falso sobre
    ellas). En un sistema real se conectaria a redes sociales o noticias.
"""

import json

from langchain_core.tools import tool

from herramientas.datos import buscar_coincidencias, origen_de


@tool
def buscar_usuarios_relevantes(consulta: str) -> str:
    """Consulta que personalidades (influencers, creadores de contenido) han adquirido
    o recomiendan el producto, y que opinan de el."""
    productos = buscar_coincidencias(consulta)

    if not productos:
        return json.dumps(
            {"consulta": consulta, "mensaje": "No se encontraron usuarios relevantes."},
            ensure_ascii=False,
        )

    resultados = [
        {"producto": producto["nombre"], "personalidades": producto["usuarios_relevantes"]}
        for producto in productos
    ]
    return json.dumps(
        {"consulta": consulta, "origen": origen_de(productos), "usuarios_relevantes": resultados},
        ensure_ascii=False,
    )
