"""
agente.py
=========
PAPEL EN EL SISTEMA:
    Aqui se construye EL AGENTE con LangGraph. Es el corazon del proyecto.

    Es UN SOLO AGENTE que sigue el patron ReAct:
        RAZONAR (el LLM piensa que hacer)
        -> ACTUAR (ejecuta una herramienta)
        -> OBSERVAR (lee el resultado) -> y vuelve a razonar...
    hasta que ya tiene suficiente informacion y da la recomendacion final.

    El grafo tiene solo 2 nodos y 1 condicion:

        INICIO -> [agente] --(¿pidio herramienta?)--> si -> [herramientas] -> [agente]
                                                    \\-> no -> FIN
"""

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from estado import EstadoAgente
from herramientas import HERRAMIENTAS
from llm import crear_llm

# ---------------------------------------------------------------------------
# Instrucciones del sistema: le explican al LLM QUIEN es y COMO debe trabajar.
# ---------------------------------------------------------------------------
INSTRUCCIONES = """Eres un agente de compras inteligentes para usuarios en Mexico.
Tu objetivo es ayudar al usuario a decidir que producto comprar.

Para cada consulta usa tus 4 herramientas, una por una, en este orden:
1. buscar_productos           -> para conocer las opciones en cada tienda.
2. comparar_precios           -> para obtener el precio final, el promedio y el rango.
3. analizar_resenas           -> para conocer el score y las opiniones de compradores.
4. buscar_usuarios_relevantes -> para saber que personalidades usan el producto.
Pasa a las 4 herramientas EXACTAMENTE el mismo texto que escribio el usuario
(por ejemplo "audifonos inalambricos"), sin cambiarle palabras.

Cuando ya tengas los resultados de las 4 herramientas, responde en español con este formato
(sin tablas, frases cortas y directas):

## Comparacion de precios
(precio final mas bajo, en que tienda, promedio y rango)

## Opinion de los compradores
(una linea por producto con este formato exacto: **Producto (score/10):** pro, pro; contra, contra
 Ejemplo: **Ninja Air Fryer AF101 3.8L (9.4/10):** papas crujientes, fácil de limpiar; capacidad pequeña
 Frases de 2 a 5 palabras, sin escribir "gusta" ni "no gusta". Si no hay contras, no pongas ';'.)

## Usuarios relevantes
(que personalidades lo usan o recomiendan)

## Recomendacion final
(2 o 3 parrafos cortos: QUE producto conviene comprar, EN QUE tienda y POR QUE,
equilibrando precio y score. Si aplica, menciona una alternativa mas barata o una premium.)

Reglas:
- Usa solo los datos que te den las herramientas. No inventes precios ni reseñas.
- Si las herramientas indican "origen": "real", los precios son reales de hoy (Google Shopping).
  Si indican "origen": "estimado", aclara en una frase corta que los precios son aproximados.
- En "Usuarios relevantes", si una persona tiene "real": true, es un creador real que reseño
  el producto en YouTube: di que lo reseñó (no que lo compró).
- Si las herramientas no encuentran el producto, dilo y sugiere buscar otra cosa.
- Los precios estan en pesos mexicanos (MXN)."""

# Numero maximo de pasos del grafo, para evitar ciclos infinitos si el LLM se confunde.
LIMITE_DE_PASOS = 20


def construir_agente():
    """
    Construye y compila el grafo del agente.

    Pasos:
        1. Crear el LLM y "presentarle" las herramientas (bind_tools), para que
           sepa que existen, que hacen y que parametros reciben.
        2. Definir los nodos: 'agente' (el LLM) y 'herramientas' (las ejecuta).
        3. Unir los nodos con aristas, incluida la condicion que decide si se
           usa una herramienta o se termina.
    """
    llm_con_herramientas = crear_llm().bind_tools(HERRAMIENTAS)

    # --- NODO 1: el agente (RAZONAR) ------------------------------------------
    def nodo_agente(estado: EstadoAgente) -> dict:
        """
        Le manda al LLM las instrucciones + toda la conversacion hasta ahora.
        El LLM responde con UNA de dos cosas:
            a) una peticion para usar herramienta(s)  (respuesta.tool_calls), o
            b) la respuesta final para el usuario.
        Devolvemos la respuesta y, gracias a add_messages, se AGREGA al estado.
        """
        mensajes = [SystemMessage(content=INSTRUCCIONES)] + estado["messages"]
        respuesta = llm_con_herramientas.invoke(mensajes)
        return {"messages": [respuesta]}

    # --- NODO 2: las herramientas (ACTUAR + OBSERVAR) -------------------------
    # ToolNode (de LangGraph) lee las tool_calls del ultimo mensaje del LLM,
    # ejecuta la herramienta correspondiente y agrega el resultado como ToolMessage.
    nodo_herramientas = ToolNode(HERRAMIENTAS)

    # --- CONDICION: ¿usar herramienta o terminar? -----------------------------
    def decidir_siguiente_paso(estado: EstadoAgente) -> str:
        """
        Revisa el ultimo mensaje del LLM:
            - Si pidio usar alguna herramienta -> ir al nodo "herramientas".
            - Si no pidio nada -> ya es la respuesta final -> terminar (END).
        """
        ultimo_mensaje = estado["messages"][-1]
        if ultimo_mensaje.tool_calls:
            return "herramientas"
        return END

    # --- ARMAR EL GRAFO -------------------------------------------------------
    grafo = StateGraph(EstadoAgente)
    grafo.add_node("agente", nodo_agente)
    grafo.add_node("herramientas", nodo_herramientas)

    grafo.add_edge(START, "agente")                       # siempre empieza razonando
    grafo.add_conditional_edges("agente", decidir_siguiente_paso, ["herramientas", END])
    grafo.add_edge("herramientas", "agente")              # despues de observar, vuelve a razonar

    return grafo.compile()


def preguntar_al_agente(agente, consulta: str):
    """
    Ejecuta el agente con la consulta del usuario y va devolviendo cada paso.

    Usa agente.stream(...) con stream_mode="updates": cada vez que un nodo
    termina, se obtiene {nombre_del_nodo: lo_que_devolvio}. Asi el front end
    puede mostrar en vivo que herramienta se esta usando.
    """
    estado_inicial = {"messages": [HumanMessage(content=consulta)]}
    yield from agente.stream(
        estado_inicial,
        config={"recursion_limit": LIMITE_DE_PASOS},
        stream_mode="updates",
    )
