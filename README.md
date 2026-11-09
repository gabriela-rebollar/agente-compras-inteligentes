# 🛒 Agente para Compras Inteligentes

Proyecto final de **Inteligencia Artificial**.

Este programa ayuda a un usuario a decidir **qué producto comprar**. Consulta los precios del producto en diferentes tiendas (**Walmart, Costco, Sam's Club** y **Mercado Libre**), analiza las reseñas de los compradores, revisa qué personalidades usan el producto y da una **recomendación final**.

Está construido como **un solo agente** con **LangGraph** que sigue el patrón **ReAct** (razonar → actuar → observar). El agente usa un LLM gratuito (el modelo abierto gpt-oss-120b en **Groq**, o Llama local con **Ollama**) y tiene un front end hecho con **Streamlit** con diseño propio, llamado **Lupa**.

Se puede buscar **cualquier producto**. Si está en el catálogo de 33 productos se usan esos datos; si no, el LLM estima modelos, precios y reseñas, y la página avisa que son precios de referencia.

---

## ✨ Acciones del agente (4 herramientas)

| # | Herramienta | Qué hace |
|---|---|---|
| 1 | 🔎 **Buscador de productos** (`buscar_productos`) | Consulta las tiendas y extrae las opciones: producto, tienda, precio y link. |
| 2 | 💲 **Comparador de precios** (`comparar_precios`) | Obtiene el precio final (el más bajo), el promedio y el rango de precio de todas las opciones. |
| 3 | ⭐ **Analista de reseñas** (`analizar_resenas`) | Extrae al menos 3 opiniones por producto y asigna un score del 1 al 10 (ej. 7.5/10). |
| 4 | 👥 **Analista de usuarios relevantes** (`buscar_usuarios_relevantes`) | Consulta qué personalidades han adquirido o recomiendan el producto. |

---

## 📁 Estructura del proyecto

```
Proyecto IA/
├── agente.py              # El grafo de LangGraph: nodo agente + nodo herramientas + condición
├── estado.py              # El estado del grafo (TypedDict con la lista de mensajes)
├── llm.py                 # Crea el LLM: Groq u Ollama, según el .env
├── herramientas/
│   ├── __init__.py        # Junta las 4 herramientas en una lista
│   ├── datos.py           # Fuente de datos: busca en el catálogo y, si no hay, usa el generador
│   ├── generador.py       # El LLM estima productos que no están en el catálogo
│   ├── datos_reales.py    # Opcional: precios reales (Google Shopping) y reseñadores de YouTube vía SerpAPI
│   ├── buscador.py        # Herramienta 1: Buscador de productos
│   ├── comparador.py      # Herramienta 2: Comparador de precios
│   ├── resenas.py         # Herramienta 3: Analista de reseñas
│   └── usuarios.py        # Herramienta 4: Analista de usuarios relevantes
├── data/
│   ├── productos_mock.json      # Catálogo: 33 productos simulados (precios en MXN, reseñas, personalidades)
│   └── productos_generados.json # Se crea solo: guarda los productos estimados por el LLM
├── .streamlit/config.toml # Colores base del front end
├── app.py                 # Front end en Streamlit
├── estilos.css            # Diseño "cute" del front end (colores pastel, tarjetas, mascota)
├── test_agente.py         # Prueba del agente desde la terminal (sin front end)
├── docs/
│   ├── ARQUITECTURA.md    # Diagrama del grafo y explicación técnica
│   ├── GUIA_EXPOSICION.md # Guion para exponer + preguntas probables del profesor
│   └── investigacion/     # Entregable: investigación sobre agentes (HTML y PDF)
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ Instalación

Requisitos: **Python 3.11 o superior**.

1. Abre una terminal en la carpeta del proyecto.
2. Crea y activa un entorno virtual:
   ```bash
   python -m venv .venv
   ```
   ```bash
   .venv\Scripts\activate
   ```
   En Mac o Linux, el segundo comando es `source .venv/bin/activate`.
3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Configura el LLM. Copia `.env.example` como `.env`:
   ```bash
   copy .env.example .env
   ```
   Elige una de dos opciones:
   - **Groq (recomendado):** crea una clave gratis en https://console.groq.com/keys y pégala en `GROQ_API_KEY`.
   - **Precios reales (opcional):** crea una clave gratis en https://serpapi.com/manage-api-key y pégala en `SERPAPI_API_KEY`. Con ella se usan precios reales de Google Shopping México, la calificación de Google y creadores reales de YouTube que reseñaron el producto.
   - **Ollama (local, sin internet):** instala https://ollama.com, ejecuta `ollama pull llama3.1` y en el `.env` pon `PROVEEDOR_LLM=ollama`.

---

## ▶️ Cómo correrlo

**Front end (página web):**
```bash
streamlit run app.py
```
Se abre en el navegador, en http://localhost:8501.

**Prueba desde la terminal (sin front end):**
```bash
python test_agente.py "freidora de aire"
```

**Probar solo las herramientas (con productos del catálogo no necesita LLM ni internet):**
```bash
python test_agente.py --solo-herramientas
```

---

## 💡 Ejemplo de uso

1. Escribe **"audífonos inalámbricos"** y presiona **Buscar y recomendar**.
2. Verás al agente trabajar paso a paso:
   - 🧠 Razona → decide usar 🔎 Buscador de productos
   - 👀 Observa el resultado…
   - 🧠 Razona → decide usar 💲 Comparador de precios
   - … y así con las 4 herramientas.
3. La página muestra:
   - La tabla comparativa de precios por tienda (con link a cada tienda).
   - Las métricas: mínimo **$499**, máximo **$6,499**, promedio y rango.
   - El score de reseñas de cada producto, por ejemplo *Sony WH-1000XM5: 9.0/10*.
   - Los usuarios relevantes.
   - La **recomendación final** del agente, que equilibra precio y calidad.

Puedes buscar lo que quieras:
- **Del catálogo (respuesta inmediata):** audífonos inalámbricos, pantalla, celular, laptop, freidora de aire, cafetera, aspiradora, reloj inteligente, consola, tablet. También búsquedas específicas, como "celular samsung" o "smart tv 55 pulgadas".
- **Fuera del catálogo (precios estimados):** mochila escolar, silla de oficina, bicicleta, licuadora… cualquier producto.

---

## 📝 Notas sobre los datos

- El **catálogo** (`data/productos_mock.json`) es simulado. Para productos fuera del catálogo, el LLM **estima** los datos y la página muestra un aviso de "precios de referencia". Las estimaciones se guardan en `data/productos_generados.json`.
- **¿Por qué simulados?** Walmart, Costco y Sam's Club no ofrecen una API pública gratuita de precios, y hacer scraping a sus páginas no está permitido. Se agregó **Mercado Libre** como cuarta tienda para enriquecer la comparación.
- Los precios son aproximados en pesos mexicanos. Las reseñas y las personalidades son **ficticias**.
- Los links llevan a la **búsqueda** del producto en la página real de cada tienda.

Para más detalle, consulta [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md) y [docs/GUIA_EXPOSICION.md](docs/GUIA_EXPOSICION.md).
