import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import re
from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools import Tool
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
from src.herramientas import verificar_elegibilidad, generar_etiqueta_devolucion
from src.base_conocimiento import obtener_retriever

# 1. Configuración LLM
llm = Ollama(model="llama3.1:8b", temperature=0.0)

# 2. Herramienta RAG (consulta a base de conocimiento)
retriever = obtener_retriever()
rag_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, chain_type="stuff")


# 3. Helpers para fallback y limpieza de salida
def clean_agent_output(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    if "Final Answer:" in text:
        text = text.split("Final Answer:")[-1]
    if "Respuesta final:" in text:
        text = text.split("Respuesta final:")[-1]
    return text.strip()


def normalize_agent_response(respuesta):
    if isinstance(respuesta, dict):
        # Chequear claves comunes retornadas por chains/llms
        for key in ("output", "text", "answer", "output_text", "result", "data", "response", "result_text"):
            if key in respuesta:
                val = respuesta[key]
                if isinstance(val, dict):
                    return normalize_agent_response(val)
                return val
        # Algunas invocaciones devuelven {"query":..., "result":...}
        if "query" in respuesta and "result" in respuesta:
            return respuesta.get("result")
        # Fallback: retornar representación legible
        return json.dumps(respuesta, ensure_ascii=False)
    return str(respuesta)


def is_invalid_agent_response(text: str) -> bool:
    if not text or text.strip() == "":
        return True
    invalid_signals = [
        "Agent stopped due to iteration limit",
        "time limit",
        "Invalid Format",
        "There was an error",
        "Lo siento",
        "No se pudo",
    ]
    return any(signal in text for signal in invalid_signals)


def es_solicitud_devolucion(text: str) -> bool:
    texto = text.lower()
    motivos_directos = [
        "quiero devolver",
        "iniciar una devolución",
        "iniciar devolución",
        "necesito devolver",
        "deseo devolver",
        "quiero iniciar una devolución",
        "quiero una devolución",
        "devolver mi",
        "devolver el producto",
        "devolver pedido",
        "retornar producto",
        "regresar producto",
        "quiero retornar",
        "quiero reembolso",
        "solicitar reembolso",
    ]
    if any(phrase in texto for phrase in motivos_directos):
        return True
    if "devolver" in texto and re.search(r"prod[-_]?\d+|em[-_]?\d+|pedido_id|pedido", texto):
        return True
    return False


def parse_return_request(text: str) -> dict:
    parsed = {
        "pedido_id": None,
        "producto_id": None,
        "direccion_cliente": None,
        "estado_producto": None,
    }
    texto = text.replace("\n", " ")
    producto_match = re.search(r"(PROD[-_]?
\d+)", texto, re.IGNORECASE)
    pedido_match = re.search(r"(EM[-_]?
\d+)", texto, re.IGNORECASE)
    direccion_match = re.search(r"direcci[oó]n(?:\s*[:\-]?\s*)([^,\.]+)", texto, re.IGNORECASE)
    estado_match = re.search(r"(sin usar|sin abrir|usado|nuevo|dañado)", texto, re.IGNORECASE)
    if producto_match:
        parsed["producto_id"] = producto_match.group(1).upper()
    if pedido_match:
        parsed["pedido_id"] = pedido_match.group(1).upper()
    if direccion_match:
        parsed["direccion_cliente"] = direccion_match.group(1).strip()
    if estado_match:
        parsed["estado_producto"] = estado_match.group(1).lower()
    return parsed


def fallback_return_flow(text: str) -> str:
    datos = parse_return_request(text)
    producto_id = datos["producto_id"]
    pedido_id = datos["pedido_id"]
    direccion_cliente = datos["direccion_cliente"]
    estado_producto = datos["estado_producto"] or "sin usar"

    if not producto_id:
        return "Para iniciar una devolución necesito el producto_id (por ejemplo PROD-003)."

    elegibilidad = verificar_elegibilidad(producto_id=producto_id, estado_producto=estado_producto)
    if not elegibilidad.get("elegible", False):
        return elegibilidad.get("razon", "El producto no es elegible para devolución.")

    if pedido_id and direccion_cliente:
        etiqueta = generar_etiqueta_devolucion(pedido_id=pedido_id, producto_id=producto_id, direccion_cliente=direccion_cliente)
        return (
            f"El producto {producto_id} es elegible. Generé la etiqueta de devolución para el pedido {pedido_id}. "
            f"Código de seguimiento: {etiqueta.get('codigo_seguimiento')}.")

    extras = []
    if not pedido_id:
        extras.append("pedido_id")
    if not direccion_cliente:
        extras.append("dirección_cliente")
    campos = " y ".join(extras)
    return f"El producto {producto_id} es elegible para devolución. Por favor proporciona {campos}."


# 4. Definir herramientas del agente
tools = [
    Tool(
        name="consultar_base_conocimiento",
        func=lambda q: consultar_rag(q) if isinstance(q, str) else consultar_rag(str(q)),
        description="Útil para responder preguntas generales sobre políticas, envíos, productos, devoluciones. Entrada: una pregunta en lenguaje natural."
    ),
    Tool(
        name="verificar_elegibilidad",
        func=lambda args: json.dumps(verificar_elegibilidad(**json.loads(args)), ensure_ascii=False),
        description="Verifica si un producto puede ser devuelto. Argumentos: producto_id (str), estado_producto (str: 'sin usar', 'sin abrir', 'usado'). Ejemplo: {\"producto_id\":\"PROD-003\", \"estado_producto\":\"sin usar\"}"
    ),
    Tool(
        name="generar_etiqueta_devolucion",
        func=lambda args: json.dumps(generar_etiqueta_devolucion(**json.loads(args)), ensure_ascii=False),
        description="Genera una etiqueta de envío para devolución. Argumentos: pedido_id (str), producto_id (str), direccion_cliente (str). Ejemplo: {\"pedido_id\":\"EM-904\", \"producto_id\":\"PROD-003\", \"direccion_cliente\":\"Calle 123, Cali\"}"
    )
]


# Prompt ReAct mejorado
agent_prompt = PromptTemplate.from_template("""
Eres un asistente especializado en devoluciones para EcoMarket.

Dispones SOLO de las herramientas listadas abajo. Sigue el protocolo EXACTO ReAct a continuación y no añadas texto fuera del formato.

Formato REQUERIDO (respeta mayúsculas y dos puntos exactamente):

Question: <pregunta del usuario>
Thought: <razonamiento corto, una o dos frases>
Action: <nombre_de_herramienta>
Action Input: <argumentos en JSON estrictamente válido>
Observation: <respuesta de la herramienta>
... (repetir Thought/Action/Observation si es necesario)
Thought: <pensamiento final>
Final Answer: <respuesta final concisa para el usuario>

Reglas importantes:
- Únicamente los tokens permitidos: Question, Thought, Action, Action Input, Observation, Final Answer.
- Nunca incluyas texto adicional fuera del formato.
- `Action Input` debe ser JSON válido cuando la herramienta espere parámetros estructurados.
- Si ya conoces la respuesta sin usar herramientas, escribe solo `Final Answer: ...`.
- Si el usuario solicita iniciar una devolución, primero `verificar_elegibilidad` antes de `generar_etiqueta_devolucion`.
- Mantén `Thought` corto y orientado a la acción (no es necesario explicar en exceso).

Ejemplo 1 — consulta simple (sin herramientas):
Question: ¿Cuál es la política de devoluciones?
Thought: Buscar en la base de conocimiento.
Final Answer: Nuestra política permite devoluciones hasta 15 días desde la entrega si el producto está sin usar y en su empaque original.

Ejemplo 2 — usar herramienta con JSON:
Question: Quiero devolver el producto PROD-003
Thought: Verificar si el producto es elegible.
Action: verificar_elegibilidad
Action Input: {"producto_id": "PROD-003", "estado_producto": "sin usar"}
Observation: {"elegible": true, "razon": "Producto elegible para devolución."}
Thought: Pide datos faltantes.
Final Answer: El producto es elegible. Por favor proporciona `pedido_id` y `direccion_cliente` para generar la etiqueta.

Herramienta JSON schema (ejemplos de Action Input):
- `verificar_elegibilidad`: {"producto_id": "PROD-xxx", "estado_producto": "sin usar|sin abrir|usado"}
- `generar_etiqueta_devolucion`: {"pedido_id": "EM-xxx", "producto_id": "PROD-xxx", "direccion_cliente": "Calle 123, Ciudad"}

Question: {input}
{agent_scratchpad}
""")


# 5. Crear agente
agent = create_react_agent(llm, tools, agent_prompt)
# Reducimos iteraciones para evitar bucles y permitimos manejo de parsing
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False, handle_parsing_errors=True, max_iterations=2)


def consultar_rag(query: str) -> str:
    resultado = rag_chain.invoke({"query": query})
    return clean_agent_output(normalize_agent_response(resultado))


def ejecutar_agente(entrada_usuario: str) -> str:
    try:
        respuesta = agent_executor.invoke({"input": entrada_usuario})
        raw_output = normalize_agent_response(respuesta)
        output = clean_agent_output(raw_output)
        if is_invalid_agent_response(output):
            raise ValueError("Respuesta del agente inválida")
        return output
    except Exception:
        if es_solicitud_devolucion(entrada_usuario):
            return fallback_return_flow(entrada_usuario)
        return consultar_rag(entrada_usuario)


if __name__ == "__main__":
    print("Agente de Devoluciones de EcoMarket (escribe 'salir')")
    while True:
        user_input = input("\nTú: ")
        if user_input.lower() == "salir":
            break
        respuesta = ejecutar_agente(user_input)
        print(f"Agente: {respuesta}")
