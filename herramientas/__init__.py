"""
herramientas/__init__.py
========================
PAPEL EN EL SISTEMA:
    Reune las 5 herramientas del agente en una sola lista (HERRAMIENTAS).
    El agente (agente.py) importa esta lista para:
        1. "Presentarle" las herramientas al LLM (bind_tools), y
        2. Ejecutarlas en el nodo de herramientas (ToolNode).

    Las 5 herramientas corresponden a las acciones que pide el proyecto:
    4 de consulta y analisis, y 1 que guarda los resultados en MySQL.
"""

from herramientas.base_datos import guardar_resultados
from herramientas.buscador import buscar_productos
from herramientas.comparador import comparar_precios
from herramientas.resenas import analizar_resenas
from herramientas.usuarios import buscar_usuarios_relevantes

HERRAMIENTAS = [
    buscar_productos,            # 1. Buscador de productos
    comparar_precios,            # 2. Comparador de precios
    analizar_resenas,            # 3. Analista de reseñas
    buscar_usuarios_relevantes,  # 4. Analista de usuarios relevantes
    guardar_resultados,          # 5. Guarda los resultados en MySQL (analisis_compras.resultados)
]
