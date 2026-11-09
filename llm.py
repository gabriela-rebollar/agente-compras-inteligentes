"""
llm.py
======
PAPEL EN EL SISTEMA:
    Crea el modelo de lenguaje (LLM) que funciona como el "cerebro" del agente.

    Se puede elegir entre dos proveedores GRATUITOS desde el archivo .env:
        - groq   (por defecto): modelo abierto gpt-oss-120b en la nube de Groq, rapido y
                                gratis con una API key gratuita (https://console.groq.com).
                                (Groq retiro sus modelos Llama de chat, por eso se usa gpt-oss.)
        - ollama (local)      : modelos Llama corriendo en tu propia computadora,
                                sin internet y sin API key (https://ollama.com).

    Separarlo en su propio archivo permite cambiar de LLM sin tocar el agente.
"""

import os

from dotenv import load_dotenv

# Lee el archivo .env (si existe) y carga sus variables al entorno.
load_dotenv()


def crear_llm():
    """
    Crea y devuelve el LLM segun la variable PROVEEDOR_LLM del .env.

    ¿Por que temperature=0?
        Queremos respuestas consistentes y "serias" (comparar precios, recomendar),
        no creativas. Con 0 el modelo casi siempre responde igual ante la misma pregunta.

    Lanza ValueError con un mensaje claro si falta la configuracion necesaria.
    """
    proveedor = os.getenv("PROVEEDOR_LLM", "groq").strip().lower()

    if proveedor == "groq":
        if not os.getenv("GROQ_API_KEY"):
            raise ValueError(
                "Falta GROQ_API_KEY en el archivo .env. "
                "Consigue una gratis en https://console.groq.com/keys"
            )
        # Se importa aqui adentro para no exigir la libreria si se usa Ollama.
        from langchain_groq import ChatGroq

        modelo = os.getenv("MODELO_GROQ", "openai/gpt-oss-120b")
        return ChatGroq(model=modelo, temperature=0)

    if proveedor == "ollama":
        from langchain_ollama import ChatOllama

        # Debe ser un modelo que soporte "tool calling", por ejemplo llama3.1.
        modelo = os.getenv("MODELO_OLLAMA", "llama3.1")
        return ChatOllama(model=modelo, temperature=0)

    raise ValueError(f"PROVEEDOR_LLM desconocido: '{proveedor}'. Usa 'groq' u 'ollama'.")
