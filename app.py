"""
app.py
======
PAPEL EN EL SISTEMA:
    Es el FRONT END (la pagina web) hecho con Streamlit, una herramienta libre.

    El usuario escribe que quiere comprar (cualquier producto) y la pagina muestra:
        - La bitacora del agente: que herramienta usa en cada paso (en vivo).
        - El veredicto: la recomendacion final del agente.
        - Metricas de precio: minimo, maximo, promedio y rango.
        - Una tarjeta por producto con sus tiendas, score y opiniones.
        - Lo que opinan los compradores (resumen del LLM).
        - Los usuarios relevantes (personalidades) del producto.

    El diseño "cute" (colores pastel, bordes redondos, tipografias) esta en
    el archivo estilos.css, separado del codigo.

COMO CORRERLO:
    streamlit run app.py
"""

import html
import json
import re
from pathlib import Path

import streamlit as st

from agente import construir_agente, preguntar_al_agente
from herramientas.datos import normalizar

# ===========================================================================
# CONFIGURACION Y TEXTOS
# ===========================================================================
st.set_page_config(page_title="Lupa · Compara antes de comprar", page_icon="🐱", layout="centered")

RUTA_ESTILOS = Path(__file__).resolve().parent / "estilos.css"

# Nombre que se muestra para cada herramienta en la bitacora.
NOMBRES_HERRAMIENTAS = {
    "buscar_productos": "Buscador de productos",
    "comparar_precios": "Comparador de precios",
    "analizar_resenas": "Analista de reseñas",
    "buscar_usuarios_relevantes": "Analista de usuarios relevantes",
}

# Colores (fondo, letra) de la etiqueta de cada tienda: version pastel de su color de marca.
COLORES_TIENDA = {
    "Walmart": ("#DCEBFF", "#0B5CAD"),
    "Costco": ("#FFE0E3", "#C9202F"),
    "Sam's Club": ("#E1E8F7", "#0E3B6E"),
    "Mercado Libre": ("#FFF4B8", "#2D3277"),
    "Amazon México": ("#FFE8CC", "#8A4B00"),
    "Liverpool": ("#FCE1F3", "#B0127A"),
    "Coppel": ("#FFF1C2", "#1D4F9C"),
    "Chedraui": ("#FFE3D6", "#D2491C"),
    "Soriana": ("#FFE0E0", "#C8102E"),
    "The Home Depot": ("#FFE6D1", "#C55A00"),
}

# Colores pastel para los "avatares" de las personalidades.
COLORES_AVATAR = ["#FFE1EC", "#F1EAFF", "#E3F7EE", "#FFF7D9", "#DCEBFF"]

EJEMPLOS = ["audífonos inalámbricos", "freidora de aire", "mochila escolar", "silla de oficina"]

# Mascota: un gatito con lupa dibujado en SVG (asi no depende de imagenes externas).
MASCOTA = """<svg width="78" height="72" viewBox="0 0 120 110" xmlns="http://www.w3.org/2000/svg">
<path d="M24 44 L30 10 L52 32 Z" fill="#fff" stroke="#4A2C40" stroke-width="3.5" stroke-linejoin="round"/>
<path d="M96 44 L90 10 L68 32 Z" fill="#fff" stroke="#4A2C40" stroke-width="3.5" stroke-linejoin="round"/>
<path d="M31 36 L33 20 L44 31 Z" fill="#F9B4CC"/><path d="M89 36 L87 20 L76 31 Z" fill="#F9B4CC"/>
<ellipse cx="60" cy="62" rx="44" ry="37" fill="#fff" stroke="#4A2C40" stroke-width="3.5"/>
<ellipse cx="45" cy="60" rx="5" ry="6" fill="#4A2C40"/><ellipse cx="75" cy="60" rx="5" ry="6" fill="#4A2C40"/>
<circle cx="47" cy="58" r="1.8" fill="#fff"/><circle cx="77" cy="58" r="1.8" fill="#fff"/>
<ellipse cx="33" cy="73" rx="7" ry="4.5" fill="#F9B4CC"/><ellipse cx="87" cy="73" rx="7" ry="4.5" fill="#F9B4CC"/>
<path d="M53 71 q3.5 5 7 0 q3.5 5 7 0" fill="none" stroke="#4A2C40" stroke-width="3" stroke-linecap="round"/>
<circle cx="98" cy="86" r="14" fill="#E9F3FF" fill-opacity="0.85" stroke="#4A2C40" stroke-width="3.5"/>
<path d="M92 80 q4 -4 9 -2" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round"/>
<line x1="108" y1="96" x2="117" y2="106" stroke="#4A2C40" stroke-width="5" stroke-linecap="round"/>
</svg>"""


# Iconos propios (SVG) con el mismo estilo de la mascota: trazo oscuro,
# relleno pastel y carita con chapitas. Se usan en vez de emojis genericos.
_TRAZO = 'stroke="#4A2C40" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"'
_CARITA = (
    '<circle cx="{x1}" cy="{y}" r="2.3" fill="#4A2C40"/><circle cx="{x2}" cy="{y}" r="2.3" fill="#4A2C40"/>'
    '<ellipse cx="{b1}" cy="{yb}" rx="3.6" ry="2.2" fill="#F9A8C4"/><ellipse cx="{b2}" cy="{yb}" rx="3.6" ry="2.2" fill="#F9A8C4"/>'
    '<path d="M{m1} {ym} q3 3.2 6 0" fill="none" {trazo_fino}/>'
)


def _carita(x1, x2, y):
    """Ojos, chapitas y sonrisa centrados entre x1 y x2."""
    centro = (x1 + x2) / 2
    return _CARITA.format(
        x1=x1, x2=x2, y=y, b1=x1 - 4, b2=x2 + 4, yb=y + 5, m1=centro - 3, ym=y + 4,
        trazo_fino='stroke="#4A2C40" stroke-width="2.4" stroke-linecap="round"',
    )


ICONOS = {
    # Bolsita de compras sonriente (Busca)
    "busca": (
        '<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">'
        f'<path d="M23 23 v-5 a9 9 0 0 1 18 0 v5" fill="none" {_TRAZO}/>'
        f'<rect x="12" y="23" width="40" height="32" rx="9" fill="#FFE1EC" {_TRAZO}/>'
        + _carita(26, 38, 37)
        + '<path d="M53 8 l1.6 4 4 1.6 -4 1.6 -1.6 4 -1.6 -4 -4 -1.6 4 -1.6z" fill="#CDB8F5"/></svg>'
    ),
    # Etiqueta de precio sonriente (Compara)
    "compara": (
        '<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">'
        '<g transform="rotate(-14 32 32)">'
        f'<path d="M10 20 h30 l14 12 -14 12 h-30 a4 4 0 0 1 -4 -4 v-16 a4 4 0 0 1 4 -4z" fill="#F1EAFF" {_TRAZO}/>'
        f'<circle cx="43" cy="32" r="3.2" fill="#fff" {_TRAZO}/>'
        + _carita(17, 29, 29)
        + '</g><path d="M50 50 l1.4 3.4 3.4 1.4 -3.4 1.4 -1.4 3.4 -1.4 -3.4 -3.4 -1.4 3.4 -1.4z" fill="#FFE59A"/></svg>'
    ),
    # Corazon sonriente con brillitos (Decide)
    "decide": (
        '<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">'
        f'<path d="M32 55 C11 42 7 25 18 18 C25 14 30 18 32 23 C34 18 39 14 46 18 C57 25 53 42 32 55Z" fill="#E3F7EE" {_TRAZO}/>'
        + _carita(26, 38, 32)
        + '<path d="M54 8 l1.6 4 4 1.6 -4 1.6 -1.6 4 -1.6 -4 -4 -1.6 4 -1.6z" fill="#F27BA6"/>'
        '<path d="M8 12 l1.2 3 3 1.2 -3 1.2 -1.2 3 -1.2 -3 -3 -1.2 3 -1.2z" fill="#CDB8F5"/></svg>'
    ),
    # Huellita para la bitacora del agente
    "huella": (
        '<svg width="20" height="20" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="#F27BA6">'
        '<ellipse cx="12" cy="16" rx="5.5" ry="4.5"/><circle cx="5.5" cy="10" r="2.3"/><circle cx="9.5" cy="6" r="2.3"/>'
        '<circle cx="14.5" cy="6" r="2.3"/><circle cx="18.5" cy="10" r="2.3"/></svg>'
    ),
}


# ===========================================================================
# FUNCIONES DE APOYO
# ===========================================================================
def pesos(valor: float) -> str:
    """Da formato de pesos mexicanos: 5899 -> '$5,899'."""
    return f"${valor:,.0f}"


def e(texto) -> str:
    """Escapa texto antes de meterlo en HTML (evita que se rompa la pagina)."""
    return html.escape(str(texto))


def html_bloque(contenido: str) -> None:
    """Pinta un bloque de HTML propio dentro de la pagina."""
    st.markdown(contenido, unsafe_allow_html=True)


def titulo_seccion(numero: str, texto: str) -> None:
    html_bloque(f'<div class="seccion"><span class="num">{numero}</span><h3>{e(texto)}</h3></div>')


def chip_tienda(tienda: str) -> str:
    fondo, letra = COLORES_TIENDA.get(tienda, ("#EEE", "#444"))
    return f'<span class="chip" style="background:{fondo};color:{letra}">{e(tienda)}</span>'


def etiqueta_score(score: float) -> str:
    """Traduce el score (1-10) a palabras faciles de entender."""
    if score >= 9:
        return "¡Excelente!"
    if score >= 8:
        return "Muy bueno"
    if score >= 7:
        return "Bueno"
    if score >= 6:
        return "Regular"
    return "Flojito"


def corazones(score: float) -> str:
    """
    Dibuja 5 corazones que se "llenan" segun el score (como las estrellas de
    una tienda, pero con el tema de la pagina). Ej. 9.0/10 -> 4.5 corazones.
    Se pintan 5 corazones grises y encima 5 rosas recortados al porcentaje.
    """
    porcentaje = max(0, min(score, 10)) * 10
    return (
        '<span class="corazones"><span class="vacios">♥♥♥♥♥</span>'
        f'<span class="llenos" style="width:{porcentaje:.0f}%">♥♥♥♥♥</span></span>'
    )


def compacto(texto: str) -> str:
    """Texto normalizado y sin espacios, para comparar nombres ("3.8 L" = "3.8L")."""
    return normalizar(texto).replace(" ", "")


def pros_y_contras(texto_llm: str, producto: str) -> tuple[list[str], list[str]]:
    """
    Busca en el resumen del LLM la linea de un producto, con el formato
    "**Producto (score/10):** lo que gusta; lo que no gusta",
    y la separa en pros (antes del ';') y contras (despues).
    """
    lineas = texto_llm.splitlines()
    # Primero se busca el nombre completo; si el LLM lo abrevio, se busca la marca.
    candidatas = [l for l in lineas if compacto(producto) in compacto(l)] or [
        l for l in lineas if compacto(producto.split()[0]) in compacto(l)
    ]
    if not candidatas:
        return [], []

    linea = candidatas[0]
    contenido = linea.split(":**", 1)[-1] if ":**" in linea else linea.split(":", 1)[-1]
    contenido = contenido.replace("*", "").strip(" -•")
    partes = [p.strip(" .") for p in contenido.split(";") if p.strip(" .")]
    if not partes:
        return [], []
    def limpiar(frases: str) -> list[str]:
        """Separa por comas, quita "gusta"/"no gusta" al inicio y frases vacias."""
        resultado = []
        for frase in frases.split(","):
            frase = re.sub(r"^(lo que (mas|más|menos) )?(no )?gustan?( que)?\s+", "", frase.strip(), flags=re.I)
            if frase and not normalizar(frase).startswith("no se report"):
                resultado.append(frase[0].upper() + frase[1:])
        return resultado[:3]

    return limpiar(partes[0]), limpiar(", ".join(partes[1:]))


def separar_secciones(texto: str) -> dict:
    """
    Divide la respuesta del LLM por sus titulos "## ...".
    Devuelve {titulo_normalizado: contenido}. Asi la pagina puede mostrar la
    recomendacion y el resumen de opiniones cada uno en su lugar.
    """
    secciones = {}
    partes = re.split(r"^##\s+(.+)$", texto, flags=re.MULTILINE)
    # partes = [texto_antes, titulo1, contenido1, titulo2, contenido2, ...]
    for i in range(1, len(partes) - 1, 2):
        secciones[normalizar(partes[i]).strip()] = partes[i + 1].strip()
    return secciones


def buscar_seccion(secciones: dict, palabra: str) -> str:
    for titulo, contenido in secciones.items():
        if palabra in titulo:
            return contenido
    return ""


def resumen_de_paso(nombre: str, datos: dict) -> str:
    """Texto corto que aparece en la bitacora cuando termina una herramienta."""
    if nombre == "buscar_productos":
        opciones = datos.get("opciones", [])
        tiendas = {o["tienda"] for o in opciones}
        return f"{len(opciones)} ofertas · {len(tiendas)} tiendas" if opciones else "sin resultados"
    if nombre == "comparar_precios" and "resumen_general" in datos:
        return f"desde {pesos(datos['resumen_general']['precio_minimo'])}"
    if nombre == "analizar_resenas":
        resenas = datos.get("resenas", [])
        total = sum(r["numero_resenas"] for r in resenas)
        if any("Google" in r.get("fuente_score", "") for r in resenas):
            return f"{total:,} reseñas en Google"
        return f"{total} opiniones leídas"
    if nombre == "buscar_usuarios_relevantes":
        total = sum(len(u["personalidades"]) for u in datos.get("usuarios_relevantes", []))
        return f"{total} menciones"
    return "listo"


def pintar_bitacora(lugar, pasos: list[dict]) -> None:
    """Dibuja la bitacora: una fila por cada accion del agente."""
    filas = "".join(
        f'<div class="paso {p["clase"]}"><span class="n">{i}</span>'
        f'<span>{e(p["texto"])}</span><span class="estado">{e(p["estado"])}</span></div>'
        for i, p in enumerate(pasos, start=1)
    )
    lugar.markdown(
        f'<div class="bitacora"><div class="titulo">{ICONOS["huella"]} Bitácora del agente</div>{filas}</div>',
        unsafe_allow_html=True,
    )


# ===========================================================================
# EJECUCION DEL AGENTE
# ===========================================================================
@st.cache_resource
def obtener_agente():
    """
    Construye el agente UNA sola vez.
    ¿Por que @st.cache_resource? Streamlit vuelve a ejecutar todo el archivo con
    cada clic; asi evitamos crear el grafo y el LLM una y otra vez.
    """
    return construir_agente()


def ejecutar_agente(consulta: str) -> dict:
    """
    Corre el agente mostrando cada paso en la bitacora (razonar -> actuar -> observar)
    y guarda los resultados de cada herramienta y la respuesta final.
    """
    lugar_bitacora = st.empty()
    pasos = [{"texto": "Leyendo tu búsqueda", "estado": "pensando…", "clase": "activo"}]
    pintar_bitacora(lugar_bitacora, pasos)

    resultados = {}
    respuesta_final = ""

    for paso in preguntar_al_agente(obtener_agente(), consulta):
        for nodo, salida in paso.items():
            if nodo == "agente":
                # El LLM termino de pensar: se quita la fila temporal "Pensando…"
                # y el primer paso ("Leyendo tu búsqueda") queda como hecho.
                if pasos[-1].get("temporal"):
                    pasos.pop()
                elif pasos[-1]["clase"] == "activo":
                    pasos[-1].update(estado="hecho", clase="listo")
                mensaje = salida["messages"][-1]
                if mensaje.tool_calls:
                    # RAZONAR: el LLM decidio usar una o varias herramientas.
                    for llamada in mensaje.tool_calls:
                        pasos.append({
                            "herramienta": llamada["name"],
                            "texto": NOMBRES_HERRAMIENTAS.get(llamada["name"], llamada["name"]),
                            "estado": "trabajando…",
                            "clase": "activo",
                        })
                else:
                    respuesta_final = mensaje.content
            elif nodo == "herramientas":
                # ACTUAR + OBSERVAR: llego el resultado de la herramienta.
                for mensaje in salida["messages"]:
                    try:
                        datos = json.loads(mensaje.content)
                    except json.JSONDecodeError:
                        datos = {}
                    resultados[mensaje.name] = datos
                    for p in pasos:
                        if p.get("herramienta") == mensaje.name and p["clase"] == "activo":
                            p.update(estado=resumen_de_paso(mensaje.name, datos), clase="listo")
                # Fila temporal mientras el LLM decide el siguiente paso.
                pasos.append({"texto": "Pensando el siguiente paso", "estado": "…", "clase": "activo", "temporal": True})
            pintar_bitacora(lugar_bitacora, pasos)

    pasos.append({"texto": "Recomendación final", "estado": "lista ♡", "clase": "listo"})
    pintar_bitacora(lugar_bitacora, pasos)
    return {"consulta": consulta, "resultados": resultados, "respuesta_final": respuesta_final, "pasos": pasos}


# ===========================================================================
# SECCIONES DE RESULTADOS
# ===========================================================================
def mostrar_resultados(datos: dict) -> None:
    resultados = datos["resultados"]
    busqueda = resultados.get("buscar_productos", {})
    comparacion = resultados.get("comparar_precios", {})
    resenas = resultados.get("analizar_resenas", {})
    usuarios = resultados.get("buscar_usuarios_relevantes", {})
    secciones = separar_secciones(datos["respuesta_final"])

    # ---- Veredicto ----
    recomendacion = buscar_seccion(secciones, "recomendacion") or datos["respuesta_final"]
    if recomendacion:
        with st.container(key="veredicto"):
            insignia = (
                '<span class="etiqueta-veredicto real">● Precios reales de hoy · Google Shopping</span>'
                if busqueda.get("origen") == "real" else ""
            )
            html_bloque(
                f'<span class="etiqueta-veredicto">✦ Veredicto</span>{insignia}'
                f'<div class="consulta-veredicto">{e(datos["consulta"]).capitalize()}</div>'
            )
            st.markdown(recomendacion)

    if not busqueda.get("opciones"):
        return

    # ---- Precios ----
    titulo_seccion("1", "Precios")
    resumen = comparacion.get("resumen_general")
    if resumen:
        html_bloque(
            '<div class="metricas">'
            f'<div class="metrica"><div class="rotulo">Mínimo</div><div class="valor">{pesos(resumen["precio_minimo"])}</div></div>'
            f'<div class="metrica"><div class="rotulo">Máximo</div><div class="valor">{pesos(resumen["precio_maximo"])}</div></div>'
            f'<div class="metrica"><div class="rotulo">Promedio</div><div class="valor">{pesos(resumen["precio_promedio"])}</div></div>'
            f'<div class="metrica"><div class="rotulo">Rango</div><div class="valor">{pesos(resumen["rango"])}</div></div>'
            "</div>"
        )

    # Juntamos por producto: ofertas (buscador), precio final (comparador) y score (reseñas).
    scores = {r["producto"]: r for r in resenas.get("resenas", [])}
    finales = {c["producto"]: c for c in comparacion.get("por_producto", [])}
    ofertas_por_producto = {}
    for o in busqueda["opciones"]:
        ofertas_por_producto.setdefault(o["producto"], []).append(o)

    # El "ganador" se marca con el producto que la recomendacion menciona primero.
    # Se comparan sin espacios ("3.8 L" = "3.8L"); si el LLM abrevio el nombre,
    # se usa la marca (primera palabra) como respaldo.
    texto_rec = compacto(recomendacion)
    menciones = [(texto_rec.find(compacto(n)), n) for n in ofertas_por_producto if compacto(n) in texto_rec]
    if not menciones:
        menciones = [
            (texto_rec.find(compacto(n.split()[0])), n)
            for n in ofertas_por_producto if compacto(n.split()[0]) in texto_rec
        ]
    ganador = min(menciones)[1] if menciones else None

    # Orden: ganador primero, luego por score.
    orden = sorted(
        ofertas_por_producto,
        key=lambda n: (n != ganador, -scores.get(n, {}).get("score", 0)),
    )

    tarjetas = []
    for nombre in orden:
        ofertas = sorted(ofertas_por_producto[nombre], key=lambda o: o["precio"])
        info = scores.get(nombre, {})
        score = info.get("score")
        final = finales.get(nombre, {})

        filas = "".join(
            f'<div class="oferta{" mejor" if i == 0 else ""}">{chip_tienda(o["tienda"])}'
            f'<div class="derecha"><span>{pesos(o["precio"])}</span>'
            f'<a href="{e(o["link"])}" target="_blank">ver →</a></div></div>'
            for i, o in enumerate(ofertas)
        )
        opiniones = "".join(f"<p>{e(c)}</p>" for c in info.get("comentarios", []))
        detalle = (
            f'<details><summary>Leer {info.get("numero_resenas", 0)} opiniones</summary>{opiniones}</details>'
            if opiniones else ""
        )
        tarjetas.append(
            f'<div class="producto{" ganador" if nombre == ganador else ""}">'
            + ('<div class="cinta">Recomendado</div>' if nombre == ganador else "")
            + f'<div class="nombre">{e(nombre)}</div>'
            + (f'<div class="mini-score">{corazones(score)}<b>{score}</b> {etiqueta_score(score)}</div>' if score else "")
            + f'<div class="precio-grande">{pesos(ofertas[0]["precio"])}<small>en {e(ofertas[0]["tienda"])}</small></div>'
            + (f'<div class="prueba">Promedio {pesos(final["precio_promedio"])} · diferencia {pesos(final["rango"])}</div>' if final else "")
            + f'<div class="ofertas">{filas}</div>{detalle}</div>'
        )
    html_bloque(f'<div class="rejilla">{"".join(tarjetas)}</div>')

    # ---- Calificaciones (grafico de corazones + pros y contras) ----
    opiniones_llm = buscar_seccion(secciones, "opinion")
    if scores:
        titulo_seccion("2", "Calificaciones")
        tarjetas_cal = []
        for nombre in orden:
            info = scores.get(nombre)
            if not info:
                continue
            score = info["score"]
            pros, contras = pros_y_contras(opiniones_llm, nombre)
            chips = "".join(f'<span class="pro">{e(p)}</span>' for p in pros) + "".join(
                f'<span class="contra">{e(c)}</span>' for c in contras
            )
            tarjetas_cal.append(
                '<div class="calificacion">'
                f'<div class="cal-score"><div class="cal-numero">{score}</div><div class="cal-de">de 10</div></div>'
                f'<div class="cal-cuerpo"><div class="cal-nombre">{e(nombre)}</div>'
                f'<div class="cal-fila">{corazones(score)}<span class="cal-etiqueta">{etiqueta_score(score)}</span></div>'
                f'<div class="barra"><div style="width:{score * 10:.0f}%"></div></div>'
                f'<div class="cal-fuente">Basado en {info["numero_resenas"]:,} reseñas · {e(info.get("fuente_score", "reseñas de compradores"))}</div>'
                + (f'<div class="chips">{chips}</div>' if chips else "")
                + "</div></div>"
            )
        html_bloque("".join(tarjetas_cal))

    # ---- Usuarios relevantes ----
    if usuarios.get("usuarios_relevantes"):
        titulo_seccion("3", "Quién lo usa")
        personas = [
            (item["producto"], p) for item in usuarios["usuarios_relevantes"] for p in item["personalidades"]
        ]
        def tarjeta_persona(producto: str, p: dict) -> str:
            # El color del avatar depende del nombre: la misma persona siempre tiene el mismo color.
            color = COLORES_AVATAR[sum(map(ord, p["nombre"])) % len(COLORES_AVATAR)]
            # Personas reales (YouTube): el comentario es el titulo del video, con link.
            if p.get("real") and p.get("link"):
                comentario = f'<a class="video" href="{e(p["link"])}" target="_blank">▶ {e(p["comentario"])}</a>'
            else:
                comentario = f'<div>{e(p["comentario"])}</div>'
            return (
                f'<div class="persona"><div class="avatar" style="background:{color}">{e(p["nombre"][:1].upper())}</div><div>'
                f'<div class="quien">{e(p["nombre"])}<small>{e(p["tipo"])}</small></div>'
                f'<span class="producto-de">{e(producto)}</span>{comentario}</div></div>'
            )

        tarjetas_personas = "".join(tarjeta_persona(producto, p) for producto, p in personas)
        html_bloque(f'<div class="personas">{tarjetas_personas}</div>')


# ===========================================================================
# PAGINA PRINCIPAL
# ===========================================================================
html_bloque(f"<style>{RUTA_ESTILOS.read_text(encoding='utf-8')}</style>")
html_bloque(
    f'<div class="marca">{MASCOTA}<div><div class="logo">Lupa<span>.</span></div>'
    '<div class="lema">Compara precios y opiniones antes de comprar</div></div>'
    '<div class="brillos">✦ ♡ ✦</div></div>'
    '<div class="tiendas-linea"><span>Walmart</span><span>Costco</span>'
    "<span>Sam's Club</span><span>Mercado Libre</span><span>+ más tiendas de México</span></div>"
)


def usar_ejemplo(texto: str) -> None:
    """Al hacer clic en un ejemplo: lo escribe en el buscador y lo deja listo para buscar."""
    st.session_state["entrada"] = texto
    st.session_state["pendiente"] = texto


with st.form("buscador", border=False):
    col_texto, col_boton = st.columns([4, 1], vertical_alignment="bottom")
    consulta = col_texto.text_input("Producto", key="entrada", placeholder="¿Qué quieres comprar hoy?")
    enviado = col_boton.form_submit_button("Comparar ✦")

with st.container(horizontal=True, gap="small", vertical_alignment="center"):
    st.markdown('<div class="prueba">Prueba con:</div>', unsafe_allow_html=True, width="content")
    for ejemplo in EJEMPLOS:
        st.button(ejemplo, type="tertiary", on_click=usar_ejemplo, args=(ejemplo,), key=f"ej-{ejemplo}")

# ¿Que se debe buscar en esta ejecucion? (formulario o boton de ejemplo)
a_buscar = consulta.strip() if enviado else st.session_state.pop("pendiente", "")

if a_buscar:
    try:
        # Se guarda en session_state para que los resultados no se borren
        # cuando Streamlit vuelve a ejecutar la pagina.
        st.session_state["datos"] = ejecutar_agente(a_buscar)
    except ValueError as error:  # falta configurar el LLM en el .env
        st.error(str(error))
    except Exception as error:  # errores del LLM o de conexion
        st.error(f"No se pudo completar la búsqueda: {error}")

if "datos" in st.session_state:
    if not a_buscar:
        # En recargas posteriores se vuelve a dibujar la bitacora guardada.
        pintar_bitacora(st.empty(), st.session_state["datos"]["pasos"])
    mostrar_resultados(st.session_state["datos"])
elif not a_buscar:
    # Pantalla inicial: explica en tres pasos lo que hace el agente.
    html_bloque(
        '<div class="como">'
        f'<div><span>{ICONOS["busca"]}</span><b>Busca</b>Revisa el producto en varias tiendas y junta todas las ofertas.</div>'
        f'<div><span>{ICONOS["compara"]}</span><b>Compara</b>Calcula el precio más bajo, el promedio y el rango, y lee las reseñas.</div>'
        f'<div><span>{ICONOS["decide"]}</span><b>Decide</b>Te dice qué conviene comprar, dónde y por qué.</div>'
        "</div>"
    )
