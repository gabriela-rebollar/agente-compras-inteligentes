"""
test_agente.py
==============
PAPEL EN EL SISTEMA:
    Script sencillo para probar el proyecto desde la terminal, SIN el front end.

    Hace dos pruebas:
        1. Prueba de herramientas: ejecuta las 4 herramientas directamente.
           Con productos del catalogo no necesita LLM ni internet; con otros
           productos usa el LLM para estimar los datos.
        2. Prueba del agente completo: el LLM decide que herramientas usar y
           da la recomendacion final (necesita la configuracion del .env).

USO:
    python test_agente.py                          -> busca "audifonos inalambricos"
    python test_agente.py "freidora de aire"       -> busca lo que tu escribas
    python test_agente.py --solo-herramientas      -> solo la prueba 1
"""

import json
import sys

from herramientas import HERRAMIENTAS


def probar_herramientas(consulta: str) -> None:
    """Ejecuta cada herramienta con la consulta y muestra un resumen de su resultado."""
    print("=" * 70)
    print(f"PRUEBA 1: herramientas (sin LLM) -> '{consulta}'")
    print("=" * 70)

    for herramienta in HERRAMIENTAS:
        resultado = json.loads(herramienta.invoke({"consulta": consulta}))
        print(f"\n🔧 {herramienta.name}")
        # Mostramos solo los primeros caracteres para no llenar la pantalla.
        texto = json.dumps(resultado, ensure_ascii=False, indent=2)
        print(texto[:800] + ("\n   ..." if len(texto) > 800 else ""))


def probar_agente(consulta: str) -> None:
    """Corre el agente completo e imprime cada paso (razonar -> actuar -> observar)."""
    # Se importa aqui para que la prueba 1 funcione aunque no haya LLM configurado.
    from agente import construir_agente, preguntar_al_agente

    print("\n" + "=" * 70)
    print(f"PRUEBA 2: agente completo (con LLM) -> '{consulta}'")
    print("=" * 70)

    try:
        agente = construir_agente()
    except ValueError as error:
        print(f"⚠️  No se pudo crear el LLM: {error}")
        return

    respuesta_final = ""
    for paso in preguntar_al_agente(agente, consulta):
        for nodo, salida in paso.items():
            mensaje = salida["messages"][-1]
            if nodo == "agente" and mensaje.tool_calls:
                for llamada in mensaje.tool_calls:
                    print(f"🧠 El agente decidio usar: {llamada['name']}({llamada['args']})")
            elif nodo == "herramientas":
                for m in salida["messages"]:
                    print(f"👀 Observo el resultado de: {m.name}")
            else:
                respuesta_final = mensaje.content

    print("\n✅ RESPUESTA FINAL DEL AGENTE:\n")
    print(respuesta_final)


if __name__ == "__main__":
    # En Windows, la consola a veces no muestra emojis/acentos; esto lo evita.
    sys.stdout.reconfigure(encoding="utf-8")

    argumentos = [a for a in sys.argv[1:] if not a.startswith("--")]
    consulta = argumentos[0] if argumentos else "audifonos inalambricos"

    probar_herramientas(consulta)
    if "--solo-herramientas" not in sys.argv:
        probar_agente(consulta)
