"""
herramientas/generador.py
=========================
PAPEL EN EL SISTEMA:
    Permite buscar CUALQUIER producto, aunque no este en el catalogo simulado.

    Cuando el usuario pide algo que no existe en data/productos_mock.json
    (por ejemplo "mochila escolar"), este modulo le pide al LLM que ESTIME
    un pequeño catalogo para ese producto: modelos reales del mercado,
    precios aproximados en pesos mexicanos en cada tienda, reseñas
    representativas y personalidades ficticias.

¿POR QUE ASI Y NO CON PRECIOS REALES?
    Las tiendas no ofrecen una API publica gratuita y el scraping no esta
    permitido. El LLM conoce precios aproximados del mercado, asi que puede
    dar una referencia razonable. Por honestidad, estos productos se marcan
    con origen "estimado" y la pagina muestra un aviso al usuario.

¿COMO SE GARANTIZA QUE LA RESPUESTA TENGA EL FORMATO CORRECTO?
    Con "salida estructurada" (with_structured_output): le damos al LLM un
    molde (clases de Pydantic) y el LLM debe llenarlo. Asi siempre obtenemos
    datos con los mismos campos que el catalogo JSON.
"""

from typing import Literal

from pydantic import BaseModel, Field

TIENDAS = ["Walmart", "Costco", "Sam's Club", "Mercado Libre"]


# --- El "molde" que debe llenar el LLM -----------------------------------------
class Oferta(BaseModel):
    tienda: Literal["Walmart", "Costco", "Sam's Club", "Mercado Libre"]
    precio: float = Field(description="Precio aproximado en pesos mexicanos (MXN)")


class Resena(BaseModel):
    autor: str = Field(description="Nombre de pila e inicial, ej. 'Laura M.'")
    estrellas: int = Field(description="De 1 a 5")
    comentario: str = Field(description="Opinion corta y realista de un comprador")


class Personalidad(BaseModel):
    nombre: str = Field(description="Nombre FICTICIO de un creador de contenido")
    tipo: str = Field(description="Ej. 'YouTuber de tecnología (ficticio)'")
    comentario: str


class ProductoEstimado(BaseModel):
    nombre: str = Field(description="Marca y modelo real que se vende en Mexico")
    categoria: str
    ofertas: list[Oferta] = Field(description="De 2 a 4 tiendas")
    resenas: list[Resena] = Field(description="De 3 a 4 reseñas")
    usuarios_relevantes: list[Personalidad] = Field(description="1 o 2 personalidades")


class CatalogoEstimado(BaseModel):
    productos: list[ProductoEstimado] = Field(
        description="De 3 a 5 productos. Lista vacia si no es algo que vendan estas tiendas."
    )


INSTRUCCIONES_GENERADOR = """Eres un experto en el mercado de consumo de Mexico.
El usuario quiere comprar: "{consulta}".

Propon de 3 a 5 productos REALES (marca y modelo) que respondan a esa busqueda y que
se vendan en Mexico. Para cada uno:
- Precio aproximado en pesos mexicanos en 2 a 4 de estas tiendas: Walmart, Costco,
  Sam's Club, Mercado Libre. Los precios deben ser realistas y variar un poco entre tiendas.
- De 3 a 4 reseñas de compradores, variadas (positivas y negativas), con 1 a 5 estrellas.
- 1 o 2 personalidades FICTICIAS (nunca personas reales) que usen o recomienden el producto.

Si la busqueda no es un producto que se venda en esas tiendas, devuelve una lista vacia."""


def generar_productos(consulta: str) -> list[dict]:
    """
    Le pide al LLM un catalogo estimado para la consulta y lo convierte al
    MISMO formato que usa data/productos_mock.json, para que las herramientas
    lo traten igual. Si el LLM falla, devuelve una lista vacia.
    """
    # Importaciones aqui adentro para evitar dependencias circulares.
    from herramientas.datos import crear_links
    from llm import crear_llm

    try:
        llm_estructurado = crear_llm().with_structured_output(CatalogoEstimado)
        catalogo = llm_estructurado.invoke(INSTRUCCIONES_GENERADOR.format(consulta=consulta))
    except Exception as error:  # sin internet, sin clave, respuesta invalida...
        print(f"[generador] No se pudo estimar el catalogo: {error}")
        return []

    productos = []
    for i, producto in enumerate(catalogo.productos, start=1):
        # Validacion sencilla: al menos 1 tienda y 3 reseñas (lo pide el proyecto).
        if not producto.ofertas or len(producto.resenas) < 3:
            continue
        links = crear_links(producto.nombre)
        productos.append(
            {
                "id": f"EST-{i:02d}",
                "nombre": producto.nombre,
                "categoria": producto.categoria,
                "origen": "estimado",
                "tiendas": [
                    {"tienda": o.tienda, "precio": round(o.precio), "link": links[o.tienda]}
                    for o in producto.ofertas
                ],
                "resenas": [
                    {"autor": r.autor, "estrellas": min(max(r.estrellas, 1), 5), "comentario": r.comentario}
                    for r in producto.resenas
                ],
                "usuarios_relevantes": [p.model_dump() for p in producto.usuarios_relevantes],
            }
        )
    return productos
