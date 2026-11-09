"""
herramientas/resenas.py
=======================
PAPEL EN EL SISTEMA:
    HERRAMIENTA 3 - "Analista de reseñas".
    Extrae las opiniones de los compradores (al menos 3 por producto) y les
    asigna un score del 1 al 10 (ejemplo: 7.5/10).

¿COMO SE CALCULA EL SCORE?
    score = promedio de estrellas (de 1 a 5) x 2   -> queda en escala de 1 a 10.
    Ejemplo: reseñas de 4, 4 y 3 estrellas -> promedio 3.67 -> score 7.3/10.
    Si hay clave de SerpAPI, se usan las estrellas REALES de Google Shopping
    (ej. 4.6 estrellas con 2,300 reseñas -> 9.2/10).

    El score lo calcula Python (resultado exacto y explicable) y el LLM se
    encarga de SINTETIZAR los comentarios en un resumen con pros y contras.
"""

import json

from langchain_core.tools import tool

from herramientas.datos import buscar_coincidencias, origen_de

MINIMO_RESENAS = 3  # Lo pide el proyecto: al menos 3 reseñas por producto.


def calcular_score(estrellas: list[int]) -> float:
    """Convierte el promedio de estrellas (1-5) a un score de 1 a 10 con un decimal."""
    promedio = sum(estrellas) / len(estrellas)
    return round(promedio * 2, 1)


@tool
def analizar_resenas(consulta: str) -> str:
    """Obtiene las reseñas de compradores de un producto (minimo 3 por producto)
    y su score del 1 al 10. Usa los comentarios para resumir pros y contras."""
    productos = buscar_coincidencias(consulta)

    if not productos:
        return json.dumps(
            {"consulta": consulta, "mensaje": "No se encontraron reseñas."},
            ensure_ascii=False,
        )

    resultados = []
    for producto in productos:
        resenas = producto["resenas"]
        if len(resenas) < MINIMO_RESENAS:
            continue  # Sin suficientes opiniones el score no seria confiable.

        fila = {
            "producto": producto["nombre"],
            "score": calcular_score([r["estrellas"] for r in resenas]),
            "numero_resenas": len(resenas),
            "fuente_score": "reseñas de compradores",
            "comentarios": [f"{r['estrellas']}★ - {r['comentario']}" for r in resenas],
        }

        # Si hay calificacion REAL de Google Shopping (con clave de SerpAPI),
        # el score se calcula con ella: estrellas de Google x 2.
        google = producto.get("calificacion_google")
        if google:
            fila["score"] = round(google["estrellas"] * 2, 1)
            fila["numero_resenas"] = google["resenas"]
            fila["fuente_score"] = "calificación de Google Shopping"

        resultados.append(fila)

    # El mejor calificado primero.
    resultados.sort(key=lambda fila: fila["score"], reverse=True)
    return json.dumps(
        {"consulta": consulta, "origen": origen_de(productos), "resenas": resultados},
        ensure_ascii=False,
    )
