# Guía para la exposición

Duración sugerida: **10 a 12 minutos** de exposición y unos 5 minutos de preguntas.

---

## Guion

### 1. Introducción (1 min)
> "Mi proyecto es un **Agente para Compras Inteligentes**. Ayuda a una persona a decidir qué producto comprar: compara precios en Walmart, Costco, Sam's Club y Mercado Libre, analiza las reseñas de los compradores, revisa qué personalidades usan el producto y al final da una recomendación con su justificación."

### 2. Tecnologías (1 min)
> "Lo hice en **Python** con **LangGraph**, que sirve para construir agentes como un grafo de pasos. El 'cerebro' es un **LLM gratuito**: el modelo abierto gpt-oss-120b en Groq, aunque también puede correr local con Ollama, y se cambia desde el archivo `.env`. El front end está hecho con **Streamlit**, que es libre."

### 3. ¿Qué es un agente? (1–2 min)
> "Un agente es un programa con un LLM que no solo responde, sino que **decide qué acciones tomar** para cumplir un objetivo. El mío sigue el patrón **ReAct**: **razona** qué necesita, **actúa** usando una herramienta, **observa** el resultado y vuelve a razonar, hasta que tiene información suficiente para responder."

### 4. Arquitectura: el grafo (2 min)
Muestra el diagrama de `docs/ARQUITECTURA.md` y abre `agente.py`.
> "El grafo tiene solo **dos nodos**: el nodo **agente**, donde el LLM razona, y el nodo **herramientas**, donde se ejecutan. Entre ellos hay una **condición**, `decidir_siguiente_paso`: si el LLM pidió una herramienta, vamos al nodo de herramientas; si no, ya es la respuesta final y termina. Después de cada herramienta se regresa al agente. Ese ciclo es el ReAct."

Abre `estado.py`.
> "El **estado** es un TypedDict con una sola lista de mensajes. Gracias a `add_messages`, cada nodo **agrega** mensajes en lugar de borrarlos. Así el agente recuerda todo lo que ha observado."

### 5. Las 5 herramientas (2–3 min)
Abre la carpeta `herramientas/`.
> "Son las acciones que pedía el proyecto:
> 1. **Buscador de productos:** encuentra las opciones en cada tienda con su precio y link.
> 2. **Comparador de precios:** calcula con Python el precio final más bajo, el promedio y el rango. Lo hago con Python y no con el LLM porque los LLM se pueden equivocar en las cuentas.
> 3. **Analista de reseñas:** junta al menos 3 opiniones y calcula un score del 1 al 10, que es el promedio de estrellas por dos. El LLM resume los pros y contras.
> 4. **Analista de usuarios relevantes:** indica qué personalidades usan o reseñaron el producto.
> 5. **Guardar resultados:** inserta cada precio en la tabla `resultados` de la base MySQL local `analisis_compras`, con el nombre del producto, el comercio, el precio y la fecha de consulta. Así el agente no se queda solo en buscar: **también actúa sobre otro sistema**.
>
> El LLM sabe para qué sirve cada herramienta porque lee su **docstring**."

Abre `herramientas/base_datos.py`.
> "La herramienta 5 se conecta con PyMySQL al MySQL de XAMPP, crea la base y la tabla si no existen, e inserta todas las filas dentro de una **transacción**: si algo falla hace `rollback` y no quedan datos a medias."

### 6. Datos (1 min)
> "Los precios vienen de **Google Shopping México** con SerpAPI, que es una API formal, así que son **precios reales de hoy**. Si no hay clave o no hay internet, uso un **catálogo** de 33 productos simulados. Y si busco algo que no está, el LLM **estima** modelos y precios con un formato fijo (salida estructurada). No hice scraping porque Walmart, Costco y Sam's no tienen una API pública y va contra sus términos."

### 7. Demo en vivo (3 min)
**Antes de exponer:** enciende **MySQL en XAMPP** y abre **phpMyAdmin** en otra pestaña.
1. Corre `streamlit run app.py`.
2. Escribe **"audífonos inalámbricos"**.
3. Señala la bitácora: *"Aquí se ve al agente razonar y usar cada herramienta en vivo; la última es 'Guardar en MySQL'."*
4. Recorre los precios, las calificaciones, los usuarios relevantes y la recomendación.
5. Muestra el aviso **"Guardado en MySQL"** y cambia a **phpMyAdmin** → base `analisis_compras` → tabla `resultados`: ahí aparecen las filas nuevas con la fecha de hoy.
6. Si hay tiempo, busca algo que no está en el catálogo, como **"mochila escolar"**, o algo sin sentido, como **"asdfgh"**, para mostrar que el agente no inventa.

**Plan B (sin internet):** corre `python test_agente.py --solo-herramientas`, que funciona sin LLM. O cambia a Ollama en el `.env`.

### 8. Conclusión (30 s)
> "Con un solo agente y herramientas sencillas se resuelve un problema real. El LLM se encarga de **razonar e integrar** la información y Python de **calcular con exactitud**."

---

## Preguntas probables y respuestas

**1. ¿Por qué usaste un solo agente y no un sistema multiagente?**
Porque las acciones son operaciones concretas (buscar, calcular, extraer). No necesitan razonar de forma independiente. Un solo agente decide cuándo usar cada herramienta e integra los resultados. Un sistema multiagente tendría varios LLM comunicándose entre sí: sería más lento, más caro y más complejo, sin mejorar el resultado.

**2. ¿Cuál es la diferencia entre una herramienta y un agente?**
Una herramienta es una **función** que hace algo concreto y siempre igual, como calcular un promedio. Un agente tiene un **LLM que razona y decide** qué herramientas usar y en qué orden.

**3. ¿Qué es LangGraph y en qué se diferencia de LangChain?**
LangChain es una librería con piezas para trabajar con LLM: mensajes, herramientas y conexión con modelos. LangGraph está construido sobre LangChain y permite definir el flujo del agente como un **grafo con estado**, con nodos, aristas y condiciones, incluidos **ciclos**, como el de razonar → actuar → observar. Aquí uso LangChain para las herramientas y los mensajes, y LangGraph para el grafo.

**4. ¿Qué es el patrón ReAct?**
*Reasoning + Acting*. El modelo alterna entre **razonar** (decidir qué hacer) y **actuar** (usar una herramienta), y **observa** el resultado antes de decidir el siguiente paso. En mi grafo es el ciclo agente → herramientas → agente.

**5. ¿Cómo sabe el LLM qué herramienta usar?**
Con `bind_tools` le paso al LLM el nombre, la descripción (el docstring) y los parámetros de cada herramienta. El modelo responde con un `tool_call` que indica qué herramienta quiere y con qué argumentos. Además, las instrucciones del sistema le indican el orden recomendado.

**6. ¿Qué pasa si el LLM entra en un ciclo infinito?**
Hay un `recursion_limit` de 20 pasos. Si se supera, LangGraph detiene la ejecución y la página muestra un error en lugar de quedarse colgada.

**7. ¿Cómo se calcula el score de reseñas?**
Es el promedio de estrellas (de 1 a 5) por 2, redondeado a un decimal. Por ejemplo, 4, 4, 3 y 4 estrellas dan un promedio de 3.75, es decir 7.5/10. Lo calcula Python para que sea exacto y reproducible.

**8. ¿Por qué los cálculos los hace Python y no el LLM?**
Los LLM generan texto que "suena" correcto, pero pueden equivocarse en operaciones numéricas. Python es exacto. Cada parte hace lo que mejor sabe hacer.

**9. ¿Los datos son reales?**
No son precios en tiempo real. Los del catálogo son simulados pero realistas (productos reales con precios aproximados en pesos). Los de productos fuera del catálogo los estima el LLM con lo que sabe del mercado, y la página lo indica con un aviso. Las tiendas no tienen una API gratuita y el scraping no está permitido. Para usar datos reales solo habría que modificar `datos.py`.

**9a. ¿Puede usar precios reales?**
Sí. Si se pone una clave gratuita de SerpAPI en el `.env`, el agente consulta Google Shopping México y obtiene precios reales de hoy, la calificación real de Google y creadores reales de YouTube que reseñaron el producto. Si no hay clave o no hay internet, sigue funcionando con el catálogo y los datos estimados. Así la demo nunca falla.

**9b. ¿Cómo se puede buscar cualquier producto si el catálogo solo tiene 33?**
Si la búsqueda no está en el catálogo, `generador.py` le pide al LLM que llene un "molde" (clases de Pydantic, con `with_structured_output`) con productos, precios por tienda, reseñas y personalidades. Así los datos tienen exactamente el mismo formato que el catálogo y las herramientas funcionan igual. El resultado se guarda en `productos_generados.json` para que las 4 herramientas vean los mismos productos.

**10. ¿Por qué agregaste Mercado Libre si el proyecto pedía Walmart, Costco y Sam's?**
Para tener una cuarta tienda muy usada en México y enriquecer la comparación. Además, si se conectara a datos reales, Mercado Libre sí tiene una presencia en línea amplia, a diferencia de Costco y Sam's, que exigen membresía para gran parte de su catálogo.

**11. ¿Las personalidades son reales?**
Con SerpAPI, sí: son creadores **reales** de YouTube que hicieron un video de reseña del producto, con el link al video. Digo que lo *reseñaron* y no que lo compraron, porque eso es lo que se puede comprobar. Sin clave, el catálogo usa personalidades ficticias a propósito, para no inventar algo falso sobre personas reales.

**12. ¿Qué es el estado y por qué es un TypedDict?**
Es la información que comparten los nodos del grafo. Un TypedDict es un diccionario con campos y tipos definidos, lo que lo hace claro y fácil de revisar. El mío solo tiene `messages`, la lista de la conversación.

**13. ¿Qué hace `add_messages`?**
Es un reductor. Le indica a LangGraph que **agregue** los mensajes nuevos a la lista en lugar de reemplazarla, para conservar todo el historial.

**14. ¿Qué LLM usaste y por qué?**
El modelo abierto **gpt-oss-120b** en Groq: es gratuito, rápido y soporta *tool calling*. Al principio planeé usar Llama 3.3, pero Groq retiró sus modelos Llama de chat. Como el modelo se lee del `.env`, cambiarlo fue editar una sola línea, sin tocar el código del agente. Llama sigue disponible de forma local con Ollama, sin internet ni clave. Se elige con `PROVEEDOR_LLM` en el `.env`.

**15. ¿Qué pasa si busco un producto que no existe?**
Si es un producto real que no está en el catálogo, se estiman sus datos (ver 9b). Si no es algo que vendan esas tiendas, por ejemplo "asdfgh", el generador devuelve una lista vacía, las herramientas responden "No se encontraron productos" y el agente lo dice y sugiere buscar otra cosa.

**16. ¿Cómo mejorarías el proyecto?**
- Usar el historial de la tabla `resultados` para mostrar **gráficas de cómo cambia el precio** con el tiempo y avisar cuándo baja.
- Agregar memoria entre conversaciones para recordar las preferencias del usuario.
- Dejar que el usuario indique su presupuesto para filtrar opciones.
- Hacer una búsqueda semántica (con *embeddings*) en lugar de por palabras clave.

**17. ¿Por qué Streamlit?**
Es libre, se programa en Python puro y permite hacer una interfaz web con tablas y métricas en pocas líneas, ideal para prototipos de IA.

**18. ¿Para qué guardas los resultados en MySQL?**
Para que el agente **interactúe con otra herramienta** y no se quede solo en la búsqueda. Además deja un **historial de precios**: con SQL se puede ver qué tienda es más barata en promedio o cómo cambió el precio de un producto. Es el mismo patrón que se usa en agentes reales, que escriben en bases de datos, mandan correos o crean tickets.

**19. ¿Cómo es la tabla y cómo se conecta?**
Base `analisis_compras`, tabla `resultados` con `id` (llave primaria autoincremental), `nombre_producto`, `comercio`, `precio` (`DECIMAL(10,2)` con un `CHECK` que impide negativos) y `fecha_consulta` (`DATETIME`). Me conecto con **PyMySQL** al MySQL de XAMPP; los datos de conexión están en el `.env`, no escritos en el código.

**20. ¿Qué pasa si MySQL está apagado?**
La herramienta captura el error y responde `"guardado": false` con un mensaje. El agente sigue y da su recomendación normalmente; solo no aparece el aviso de guardado. Por eso la versión publicada en la nube también funciona, aunque no tenga acceso a mi MySQL local.

**21. ¿Por qué usas una transacción?**
Porque guardo varias filas a la vez. Con `commit()` al final y `rollback()` si algo falla, o se guardan **todas** las filas de la consulta o **ninguna**, y nunca quedan datos a medias.
