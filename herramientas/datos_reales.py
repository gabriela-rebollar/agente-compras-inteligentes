"""
herramientas/datos_reales.py
============================
PAPEL EN EL SISTEMA:
    Obtiene datos REALES de internet usando SerpAPI (https://serpapi.com),
    un servicio con plan gratuito que consulta Google por nosotros y devuelve
    los resultados en JSON. Solo se usa si existe SERPAPI_API_KEY en el .env.

    Con UNA sola clave obtenemos dos cosas:
        1. Precios reales de hoy en Google Shopping Mexico (motor "google_shopping"):
           precio, tienda, link y calificacion de Google (estrellas y numero de reseñas).
        2. Personas reales que reseñaron el producto en YouTube (motor "youtube"):
           nombre del canal, titulo y link del video.

¿POR QUE SERPAPI Y NO SCRAPING?
    Hacer scraping a las tiendas va contra sus terminos y se rompe facil.
    SerpAPI es una API formal, gratuita para pocas consultas al mes.

TIENDAS:
    Se aceptan Walmart, Costco y Sam's Club (las del proyecto). Como Costco y
    Sam's Club casi no aparecen en Google Shopping (gran parte de su catalogo
    exige membresia), tambien se aceptan otras tiendas de Mexico como reemplazo
    (Mercado Libre, Amazon Mexico, Liverpool, Coppel, Chedraui, Soriana y
    The Home Depot), para que siempre haya con que comparar.
"""

import json
import os
import statistics
import urllib.parse
import urllib.request

URL_SERPAPI = "https://serpapi.com/search.json"

# Palabra que aparece en el nombre de la tienda (en Google) -> nombre que mostramos.
# Solo tiendas de MEXICO: Google tambien devuelve eBay o tiendas de otros paises
# (con envio internacional), y esas se descartan. "Amazon" a secas puede ser
# Amazon de EE. UU., por eso solo se acepta "Amazon MX" / "amazon.com.mx".
TIENDAS_ACEPTADAS = {
    "walmart": "Walmart",
    "bodega aurrera": "Walmart",  # tambien es de Walmart de Mexico
    "costco": "Costco",
    "sam's": "Sam's Club",
    "sams": "Sam's Club",
    "mercado libre": "Mercado Libre",
    "mercadolibre": "Mercado Libre",
    "amazon mx": "Amazon México",
    "amazon.com.mx": "Amazon México",
    "amazon méxico": "Amazon México",
    "amazon mexico": "Amazon México",
    "liverpool": "Liverpool",
    "coppel": "Coppel",
    "chedraui": "Chedraui",
    "soriana": "Soriana",
    "home depot": "The Home Depot",
}


def hay_clave() -> bool:
    """¿Esta configurada la clave de SerpAPI en el .env?"""
    return bool(os.getenv("SERPAPI_API_KEY"))


def _consultar(parametros: dict) -> dict:
    """Hace una consulta a SerpAPI y devuelve el JSON como diccionario."""
    parametros = {**parametros, "api_key": os.getenv("SERPAPI_API_KEY")}
    url = f"{URL_SERPAPI}?{urllib.parse.urlencode(parametros)}"
    with urllib.request.urlopen(url, timeout=25) as respuesta:
        return json.loads(respuesta.read().decode("utf-8"))


def _tienda_de(fuente: str) -> str | None:
    """Convierte el nombre de la tienda de Google ('Walmart.com.mx') al nuestro ('Walmart')."""
    fuente = fuente.lower()
    for palabra, nombre in TIENDAS_ACEPTADAS.items():
        if palabra in fuente:
            return nombre
    return None


def _es_el_mismo_producto(nombre: str, titulo: str) -> bool:
    """
    Revisa que el resultado de Google sea el producto buscado y no un accesorio:
    al menos el 60 % de las palabras del nombre deben aparecer en el titulo.
    """
    from herramientas.datos import normalizar

    palabras = [p for p in normalizar(nombre).replace("(", " ").replace(")", " ").split() if len(p) > 1]
    titulo = normalizar(titulo)
    # Version sin espacios ni guiones, para que "WH-1000XM5" coincida con "WH1000XM5".
    titulo_junto = titulo.replace("-", "").replace(" ", "")
    if not palabras:
        return False
    coincidencias = sum(1 for p in palabras if p in titulo or p.replace("-", "") in titulo_junto)
    return coincidencias / len(palabras) >= 0.6


def extraer_ofertas(nombre: str, resultados: list[dict]) -> dict:
    """
    De los resultados de Google Shopping se queda con:
        - la oferta MAS BARATA de cada tienda aceptada,
        - la calificacion de Google (la del resultado con mas reseñas).
    Descarta accesorios (titulo distinto) y precios sospechosamente bajos.
    """
    candidatos = []
    for r in resultados:
        tienda = _tienda_de(r.get("source", ""))
        precio = r.get("extracted_price")
        if tienda and precio and _es_el_mismo_producto(nombre, r.get("title", "")):
            candidatos.append({**r, "_tienda": tienda})

    # Precios menores al 40 % de la mediana suelen ser fundas o refacciones, y los
    # mayores al 220 % suelen ser otro modelo (mas grande) o paquetes.
    if candidatos:
        mediana = statistics.median(c["extracted_price"] for c in candidatos)
        candidatos = [c for c in candidatos if 0.4 * mediana <= c["extracted_price"] <= 2.2 * mediana]

    mejores = {}
    for c in candidatos:
        actual = mejores.get(c["_tienda"])
        if actual is None or c["extracted_price"] < actual["extracted_price"]:
            mejores[c["_tienda"]] = c

    tiendas = [
        {
            "tienda": tienda,
            "precio": round(c["extracted_price"]),
            "link": c.get("link") or c.get("product_link") or "",
        }
        for tienda, c in mejores.items()
    ]

    # Calificacion: Google repite el numero de reseñas del producto en varios
    # resultados, pero las estrellas varian. Usamos la MEDIANA de las estrellas
    # de todos los resultados del mismo producto (de cualquier tienda), que es
    # mas confiable que tomar un solo resultado.
    con_calificacion = [
        r for r in resultados
        if r.get("rating") and r.get("reviews") and _es_el_mismo_producto(nombre, r.get("title", ""))
    ]
    calificacion = None
    if con_calificacion:
        calificacion = {
            "estrellas": round(statistics.median(r["rating"] for r in con_calificacion), 1),
            "resenas": max(r["reviews"] for r in con_calificacion),
        }

    return {"tiendas": tiendas, "calificacion": calificacion}


def _parecido(nombre: str, titulo: str) -> int:
    """Cuantas palabras del nombre del producto aparecen en el titulo del video."""
    from herramientas.datos import normalizar

    titulo_junto = normalizar(titulo).replace("-", "").replace(" ", "")
    palabras = [p.replace("-", "") for p in normalizar(nombre).split() if len(p) > 1]
    return sum(1 for p in palabras if p in titulo_junto)


def extraer_resenadores(resultados: list[dict], nombre: str = "", maximo: int = 2) -> list[dict]:
    """
    De los resultados de YouTube toma canales distintos que hicieron reseña del producto.
    Solo acepta videos que mencionen la MARCA, y los ordena por que tanto se parece
    el titulo al modelo (para no mostrar reseñas de otro producto de la marca).
    """
    from herramientas.datos import normalizar

    marca = normalizar(nombre.split()[0]) if nombre else ""
    if marca:
        resultados = [v for v in resultados if marca in normalizar(v.get("title", ""))]
        resultados = sorted(resultados, key=lambda v: _parecido(nombre, v.get("title", "")), reverse=True)

    personas, vistos = [], set()
    for video in resultados:
        canal = (video.get("channel") or {}).get("name")
        if not canal or canal in vistos:
            continue
        vistos.add(canal)
        personas.append(
            {
                "nombre": canal,
                "tipo": "Creador de YouTube · video de reseña",
                "comentario": video.get("title", ""),
                "link": video.get("link", ""),
                "real": True,
            }
        )
        if len(personas) == maximo:
            break
    return personas


def obtener_datos_reales(nombre: str) -> dict:
    """
    Consulta Google Shopping y YouTube para UN producto.
    Devuelve {"tiendas": [...], "calificacion": {...} | None, "resenadores": [...]}.
    Si algo falla (sin internet, sin creditos...), devuelve listas vacias.
    """
    datos = {"tiendas": [], "calificacion": None, "resenadores": []}
    try:
        compras = _consultar(
            {"engine": "google_shopping", "q": nombre, "gl": "mx", "hl": "es", "location": "Mexico"}
        )
        datos.update(extraer_ofertas(nombre, compras.get("shopping_results", [])))
    except Exception as error:
        print(f"[datos_reales] Google Shopping fallo para '{nombre}': {error}")

    try:
        videos = _consultar({"engine": "youtube", "search_query": f"{nombre} reseña", "gl": "mx", "hl": "es"})
        datos["resenadores"] = extraer_resenadores(videos.get("video_results", []), nombre)
    except Exception as error:
        print(f"[datos_reales] YouTube fallo para '{nombre}': {error}")

    return datos
