"""
estado.py
=========
PAPEL EN EL SISTEMA:
    Define el "estado" del grafo de LangGraph, es decir, la informacion que
    viaja entre los nodos (el nodo del agente y el nodo de herramientas).

    Piensalo como la "memoria de trabajo" del agente durante una consulta:
    cada nodo LEE el estado, hace su trabajo y DEVUELVE lo que quiere agregar.
"""

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class EstadoAgente(TypedDict):
    """
    Estado del agente de compras.

    Solo tiene UN campo: la lista de mensajes de la conversacion.

    ¿Que mensajes hay ahi?
        - HumanMessage : lo que escribio el usuario ("audifonos inalambricos").
        - AIMessage    : lo que responde el LLM. Puede traer "tool_calls"
                         (cuando decide usar una herramienta) o la respuesta final.
        - ToolMessage  : el resultado de ejecutar una herramienta (la "observacion").

    ¿Por que "Annotated[..., add_messages]"?
        'add_messages' es un "reductor": le dice a LangGraph que cuando un nodo
        devuelva mensajes nuevos, los AGREGUE al final de la lista en lugar de
        reemplazarla. Asi el agente conserva todo el historial y puede razonar
        con lo que ya observo (patron ReAct: razonar -> actuar -> observar).
    """

    messages: Annotated[list[AnyMessage], add_messages]
