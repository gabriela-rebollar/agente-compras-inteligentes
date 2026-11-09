"""
herramientas/datos.py
=====================
PAPEL EN EL SISTEMA:
    Es la "fuente de datos" que comparten las 4 herramientas del agente.

    Funciona en DOS niveles:
        1. CATALOGO: primero busca en data/productos_mock.json (33 productos
           simulados con precios en MXN). Es rapido y siempre funciona.
        2. ESTIMADO: si el producto no esta en el catalogo, le pide al LLM que
           estime opciones para ese producto (ver generador.py). Asi el usuario
           puede buscar CUALQUIER cosa.

    Los productos estimados se guardan en data/productos_generados.json.
    ¿Por que? Porque las 4 herramientas consultan los datos por separado:
    si cada una generara datos nuevos, verian productos distintos. Guardandolos,
    todas trabajan con exactamente la misma informacion (y la siguiente vez
    que se busque lo mismo, la respuesta es inmediata).

¿POR QUE NO PRECIOS REALES?
    Walmart, Costco y Sam's Club no ofrecen una API publica gratuita de precios,
    y hacer scraping a sus paginas no esta permitido.
"""

import json
import threading
import unicodedata
import urllib.parse
from pathlib import Path

CARPETA_DATOS = Path(__file__).resolve().parent.parent / "data"
RUTA_CATALOGO = CARPETA_DATOS / "productos_mock.json"
RUTA_GENERADOS = CARPETA_DATOS / "productos_generados.json"

# Candado para que dos herramientas que corren al mismo tiempo no generen
# (ni escriban en el archivo) a la vez.
_candado = threading.Lock()

# Palabras que no ayudan a distinguir productos y se ignoran al buscar.
PALABRAS_VACIAS = {
    "de", "del", "la", "el", "los", "las", "un", "una", "unos", "unas", "para",
    "con", "sin", "y", "o", "en", "que", "quiero", "comprar", "busco", "mejor",
    "mejores", "barato", "barata", "baratos", "baratas", "buen", "buena", "buenos",
    "precio", "me", "mi", "por",
}


def normalizar(texto: str) -> str:
    """
    Convierte el texto a minusculas y le quita los acentos.
    Asi "Audífonos" y "audifonos" se consideran iguales.
    """
    sin_acentos = unicodedata.normalize("NFD", texto)
    sin_acentos = "".join(c for c in sin_acentos if unicodedata.category(c) != "Mn")
    # El LLM a veces escribe guiones "especiales" (‑ – —); los cambiamos por "-".
    for guion in "‐‑‒–—":
        sin_acentos = sin_acentos.replace(guion, "-")
    return sin_acentos.lower()


def palabras_importantes(consulta: str) -> list[str]:
    """Separa la consulta en palabras y quita las palabras vacias."""
    return [p for p in normalizar(consulta).split() if p not in PALABRAS_VACIAS]


def crear_links(nombre: str) -> dict:
    """Arma el link de BUSQUEDA del producto en la pagina real de cada tienda."""
    q = urllib.parse.quote_plus(nombre)
    slug = urllib.parse.quote("-".join(nombre.lower().replace('"', "").split()))
    return {
        "Walmart": f"https://www.walmart.com.mx/search?q={q}",
        "Costco": f"https://www.costco.com.mx/search?text={q}",
        "Sam's Club": f"https://www.sams.com.mx/search?Ntt={q}",
        "Mercado Libre": f"https://listado.mercadolibre.com.mx/{slug}",
    }


def _palabra_aparece(palabra: str, texto: str) -> bool:
    """
    Revisa si una palabra aparece en el texto, tambien en singular
    (quitando la 's' o 'es' final): "pantallas" encuentra "pantalla".
    """
    if palabra in texto:
        return True
    if palabra.endswith("es") and palabra[:-2] in texto:
        return True
    if palabra.endswith("s") and palabra[:-1] in texto:
        return True
    return False


# ---------------------------------------------------------------------------
# Nivel 1: catalogo simulado
# ---------------------------------------------------------------------------
def buscar_en_catalogo(consulta: str) -> list[dict]:
    """
    Devuelve los productos del catalogo donde aparecen TODAS las palabras
    importantes de la consulta (en su nombre, categoria o palabras clave).

    Ejemplos:
        "celular samsung"  -> solo el Galaxy A55 (tiene ambas palabras).
        "funda de celular" -> nada ("funda" no aparece), asi que se estimara.
    """
    palabras = palabras_importantes(consulta)
    if not palabras:
        return []

    with open(RUTA_CATALOGO, encoding="utf-8") as archivo:
        productos = json.load(archivo)["productos"]

    encontrados = []
    for producto in productos:
        texto = normalizar(
            " ".join([producto["nombre"], producto["categoria"], *producto["palabras_clave"]])
        )
        if all(_palabra_aparece(p, texto) for p in palabras):
            encontrados.append(producto)
    return encontrados


# ---------------------------------------------------------------------------
# Nivel 2: productos estimados por el LLM (con memoria en archivo)
# ---------------------------------------------------------------------------
def _clave(consulta: str) -> str:
    """
    Clave para guardar una busqueda: palabras importantes ordenadas.
    Asi "Mochila Escolar" y "escolar mochila" se guardan en el mismo lugar.
    """
    return " ".join(sorted(palabras_importantes(consulta)))


def obtener_productos_estimados(consulta: str) -> list[dict]:
    """Regresa los productos estimados para la consulta (los genera solo la primera vez)."""
    from herramientas.generador import generar_productos

    clave = _clave(consulta)
    if not clave:
        return []

    with _candado:
        guardados = {}
        if RUTA_GENERADOS.exists():
            guardados = json.loads(RUTA_GENERADOS.read_text(encoding="utf-8"))

        if clave not in guardados:
            productos = generar_productos(consulta)
            if not productos:
                return []
            guardados[clave] = productos
            RUTA_GENERADOS.write_text(
                json.dumps(guardados, ensure_ascii=False, indent=2), encoding="utf-8"
            )

        return guardados[clave]


# ---------------------------------------------------------------------------
# Nivel 3 (opcional): datos REALES de internet con SerpAPI
# ---------------------------------------------------------------------------
RUTA_REALES = CARPETA_DATOS / "datos_reales.json"


def agregar_datos_reales(productos: list[dict]) -> list[dict]:
    """
    Si hay clave de SerpAPI, reemplaza los precios por los REALES de Google
    Shopping, agrega la calificacion real de Google y cambia las personalidades
    por personas reales que reseñaron el producto en YouTube.

    Los resultados se guardan por dia en data/datos_reales.json para no gastar
    consultas (el plan gratuito de SerpAPI tiene un limite mensual) y para que
    las 4 herramientas vean exactamente los mismos datos.
    """
    from datetime import date

    from herramientas.datos_reales import obtener_datos_reales

    hoy = date.today().isoformat()
    with _candado:
        guardados = {}
        if RUTA_REALES.exists():
            guardados = json.loads(RUTA_REALES.read_text(encoding="utf-8"))

        enriquecidos = []
        for producto in productos[:5]:  # maximo 5 productos para cuidar las consultas
            clave = f"{hoy}|{producto['nombre']}"
            if clave not in guardados:
                guardados[clave] = obtener_datos_reales(producto["nombre"])
                RUTA_REALES.write_text(json.dumps(guardados, ensure_ascii=False, indent=2), encoding="utf-8")
            reales = guardados[clave]

            nuevo = dict(producto)  # copia, para no modificar el catalogo original
            if reales["tiendas"]:
                nuevo["tiendas"] = reales["tiendas"]
                nuevo["origen"] = "real"
            if reales["calificacion"]:
                nuevo["calificacion_google"] = reales["calificacion"]
            if reales["resenadores"]:
                nuevo["usuarios_relevantes"] = reales["resenadores"]
            enriquecidos.append(nuevo)
        return enriquecidos


# ---------------------------------------------------------------------------
# Funcion que usan las 4 herramientas
# ---------------------------------------------------------------------------
def buscar_coincidencias(consulta: str) -> list[dict]:
    """
    Punto de entrada de los datos:
        1. Busca en el catalogo; si ahi no hay nada, el LLM estima productos.
        2. Si hay clave de SerpAPI, les pone precios y reseñadores REALES.
    """
    from herramientas.datos_reales import hay_clave

    productos = buscar_en_catalogo(consulta) or obtener_productos_estimados(consulta)
    if productos and hay_clave():
        productos = agregar_datos_reales(productos)
    return productos


def origen_de(productos: list[dict]) -> str:
    """Indica de donde vienen los precios: 'real', 'estimado' o 'catalogo'."""
    if any(p.get("origen") == "real" for p in productos):
        return "real"
    if productos and productos[0].get("origen") == "estimado":
        return "estimado"
    return "catalogo"
