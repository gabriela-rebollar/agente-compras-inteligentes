"""
herramientas/__init__.py
========================
PAPEL EN EL SISTEMA:
    Reune las 4 herramientas del agente en una sola lista (HERRAMIENTAS).
    El agente (agente.py) importa esta lista para:
        1. "Presentarle" las herramientas al LLM (bind_tools), y
        2. Ejecutarlas en el nodo de herramientas (ToolNode).

    Las 4 herramientas corresponden a las 4 acciones del documento del proyecto.
"""

from herramientas.buscador import buscar_productos
from herramientas.comparador import comparar_precios
from herramientas.resenas import analizar_resenas
from herramientas.usuarios import buscar_usuarios_relevantes

HERRAMIENTAS = [
    buscar_productos,            # 1. Buscador de productos
    comparar_precios,            # 2. Comparador de precios
    analizar_resenas,            # 3. Analista de reseñas
    buscar_usuarios_relevantes,  # 4. Analista de usuarios relevantes
]
