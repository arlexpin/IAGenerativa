import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import re
from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools import Tool
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
from src.herramientas import verificar_elegibilidad, generar_etiqueta_devolucion
from src.base_conocimiento import (
    ensure_vectorstore,
    recuperar_contexto,
    responder_pregunta,
    buscar_productos_en_consulta,
)

_llm = None
_agent_executor = None


def get_llm():
    global _llm
    if _llm is None:
        _llm = Ollama(model="llama3.1:8b", temperature=0.0)
    return _llm


# Helpers para fallback y limpieza de salida
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
        for key in ("output", "text", "answer", "output_text", "result", "data", "response", "result_text"):
            if key in respuesta:
                val = respuesta[key]
                if isinstance(val, dict):
                    return normalize_agent_response(val)
                return val
        if "query" in respuesta and "result" in respuesta:
            return respuesta.get("result")
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


PALABRAS_NEGOCIO = (
    "política", "politica", "devoluc", "envío", "envio", "producto", "pedido",
    "prod-", "em-", "precio", "stock", "inventario", "pago", "cancelar",
    "reembolso", "elegible", "etiqueta", "compr", "entreg", "garantía",
    "garantia", "semilla", "albahaca",
)

SALUDO_PATRONES = (
    r"^hola\b",
    r"^buenos?\s+d[ií]as",
    r"^buenas?\s+tardes",
    r"^buenas?\s+noches",
    r"^hey\b",
    r"^qu[eé]\s+tal",
    r"^c[oó]mo\s+est[aá]s",
    r"^gracias\b",
    r"^muchas\s+gracias",
    r"^adi[oó]s\b",
    r"^chao\b",
    r"^hasta\s+luego",
    r"^buen\s+d[ií]a",
)


def es_conversacion_casual(text: str) -> bool:
    texto = text.strip().lower()
    if not texto:
        return True
    if any(palabra in texto for palabra in PALABRAS_NEGOCIO):
        return False
    return any(re.search(patron, texto) for patron in SALUDO_PATRONES)


def respuesta_conversacional() -> str:
    return (
        "¡Hola! Soy el asistente virtual de EcoMarket. "
        "Puedo ayudarte con políticas de devolución y envíos, consultas sobre productos "
        "o iniciar una devolución. ¿En qué te puedo ayudar?"
    )


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
    producto_match = re.search(r"(PROD[-_]?\d+)", texto, re.IGNORECASE)
    pedido_match = re.search(r"(EM[-_]?\d+)", texto, re.IGNORECASE)
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


def fallback_return_flow(text: str, contexto_rag: str = "") -> str:
    datos = parse_return_request(text)
    producto_id = datos["producto_id"]
    pedido_id = datos["pedido_id"]
    direccion_cliente = datos["direccion_cliente"]
    estado_producto = datos["estado_producto"] or "sin usar"

    if not producto_id:
        base = "Para iniciar una devolución necesito el producto_id (por ejemplo PROD-003)."
        if contexto_rag:
            return f"{base}\n\nInformación relevante de políticas:\n{contexto_rag[:600]}"
        return base

    elegibilidad = verificar_elegibilidad(producto_id=producto_id, estado_producto=estado_producto)
    if not elegibilidad.get("elegible", False):
        return elegibilidad.get("razon", "El producto no es elegible para devolución.")

    if pedido_id and direccion_cliente:
        etiqueta = generar_etiqueta_devolucion(
            pedido_id=pedido_id,
            producto_id=producto_id,
            direccion_cliente=direccion_cliente,
        )
        return (
            f"El producto {producto_id} es elegible. Generé la etiqueta de devolución para el pedido {pedido_id}. "
            f"Código de seguimiento: {etiqueta.get('codigo_seguimiento')}."
        )

    extras = []
    if not pedido_id:
        extras.append("pedido_id")
    if not direccion_cliente:
        extras.append("dirección_cliente")
    campos = " y ".join(extras)
    return f"El producto {producto_id} es elegible para devolución. Por favor proporciona {campos}."


def es_pregunta_sobre_devolucion(text: str) -> bool:
    texto = text.lower()
    return any(
        patron in texto
        for patron in (
            "puedo devolv",
            "pueden devolv",
            "aceptan devolv",
            "se puede devolv",
            "elegible",
            "devolución de",
            "devolver un",
            "devolver unas",
            "devolver el",
            "devolver la",
            "devolver mis",
        )
    )


def responder_devolucion_producto(entrada: str) -> str | None:
    if not es_pregunta_sobre_devolucion(entrada):
        return None

    productos = buscar_productos_en_consulta(entrada)
    if not productos:
        return None

    producto = productos[0]
    producto_id = producto.get("id", "")
    nombre = producto.get("nombre", "producto")
    categoria = producto.get("categoria", "")

    elegibilidad = verificar_elegibilidad(
        producto_id=producto_id,
        estado_producto="sin usar",
    )
    if elegibilidad.get("elegible"):
        return (
            f"Sí, el producto {nombre} (ID {producto_id}, categoría {categoria}) puede ser elegible "
            f"para devolución si cumple las condiciones: sin usar, empaque original y dentro de los "
            f"30 días desde la compra. {elegibilidad.get('razon', '')}"
        )

    return (
        f"No, no puedes devolver {nombre} (ID {producto_id}). "
        f"Categoría: {categoria}. {elegibilidad.get('razon', '')} "
        f"Según la política de EcoMarket, los productos perecederos no admiten devolución."
    )


def consultar_rag(query: str) -> str:
    respuesta_producto = responder_devolucion_producto(query)
    if respuesta_producto:
        return respuesta_producto
    return clean_agent_output(responder_pregunta(get_llm(), query))


def enriquecer_entrada_con_rag(entrada_usuario: str, contexto_rag: str) -> str:
    return (
        "Contexto recuperado de la base de conocimiento (carpeta datos):\n"
        f"{contexto_rag}\n\n"
        f"Consulta del usuario: {entrada_usuario}"
    )


# 3. Herramientas del agente (devoluciones)
tools = [
    Tool(
        name="consultar_base_conocimiento",
        func=lambda q: consultar_rag(q) if isinstance(q, str) else consultar_rag(str(q)),
        description=(
            "Consulta adicional a la base de conocimiento (políticas, FAQs, inventario). "
            "Úsala solo si necesitas más detalle. Entrada: pregunta en lenguaje natural."
        ),
    ),
    Tool(
        name="verificar_elegibilidad",
        func=lambda args: json.dumps(verificar_elegibilidad(**json.loads(args)), ensure_ascii=False),
        description=(
            'Verifica si un producto puede ser devuelto. Argumentos JSON: '
            '{"producto_id":"PROD-003", "estado_producto":"sin usar"}'
        ),
    ),
    Tool(
        name="generar_etiqueta_devolucion",
        func=lambda args: json.dumps(generar_etiqueta_devolucion(**json.loads(args)), ensure_ascii=False),
        description=(
            'Genera etiqueta de devolución. Argumentos JSON: '
            '{"pedido_id":"EM-904", "producto_id":"PROD-003", "direccion_cliente":"Calle 123, Cali"}'
        ),
    ),
]

agent_prompt = PromptTemplate(
    template="""
Eres un asistente especializado en devoluciones para EcoMarket.

Ya se ejecutó un proceso RAG sobre la carpeta datos. El contexto recuperado viene incluido en la pregunta.
Úsalo como fuente principal antes de invocar herramientas.

Dispones SOLO de las herramientas listadas abajo. Sigue el protocolo EXACTO ReAct:

Herramientas disponibles:
{tools}
Nombres de herramienta válidos: {tool_names}

Formato REQUERIDO:

Question: <pregunta del usuario con contexto RAG>
Thought: <razonamiento corto>
Action: <nombre_de_herramienta>
Action Input: <JSON válido>
Observation: <respuesta de la herramienta>
Thought: <pensamiento final>
Final Answer: <respuesta final para el usuario>

Reglas:
- Para devoluciones: primero `verificar_elegibilidad`, luego `generar_etiqueta_devolucion` si aplica.
- Respeta las políticas del contexto RAG (plazos, categorías no elegibles).
- `Action Input` debe ser JSON válido cuando la herramienta lo requiera.

Question: {input}
{agent_scratchpad}
""",
    input_variables=["input", "agent_scratchpad", "tools", "tool_names"],
)

def get_agent_executor():
    global _agent_executor
    if _agent_executor is None:
        try:
            agent = create_react_agent(get_llm(), tools, agent_prompt)
            _agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=False,
                handle_parsing_errors=True,
                max_iterations=3,
            )
        except Exception as e:
            print(f"Warning creating agent: {e}")
            _agent_executor = False
    return _agent_executor if _agent_executor is not False else None


def ejecutar_flujo_devolucion(entrada_usuario: str, contexto_rag: str) -> str:
    entrada_enriquecida = enriquecer_entrada_con_rag(entrada_usuario, contexto_rag)
    try:
        executor = get_agent_executor()
        if executor is not None:
            respuesta = executor.invoke({"input": entrada_enriquecida})
            output = clean_agent_output(normalize_agent_response(respuesta))
            if not is_invalid_agent_response(output):
                return output
            raise ValueError("Respuesta del agente inválida")
    except Exception:
        pass
    return fallback_return_flow(entrada_usuario, contexto_rag)


def ejecutar_agente(entrada_usuario: str) -> str:
    """
    Flujo router (docs/fase1): RAG sobre datos/, luego:
    - Saludo / conversación casual → bienvenida (sin exigir contexto RAG)
    - Solicitud de devolución → agente con herramientas + contexto RAG
    - Pregunta general → respuesta RAG
    """
    entrada = entrada_usuario.strip()
    if not entrada:
        return respuesta_conversacional()

    if es_conversacion_casual(entrada):
        return respuesta_conversacional()

    respuesta_producto = responder_devolucion_producto(entrada)
    if respuesta_producto:
        return respuesta_producto

    ensure_vectorstore()
    contexto_rag = recuperar_contexto(entrada)

    if es_solicitud_devolucion(entrada):
        return ejecutar_flujo_devolucion(entrada, contexto_rag)

    return consultar_rag(entrada)


if __name__ == "__main__":
    print("Agente de Devoluciones de EcoMarket (escribe 'salir')")
    while True:
        user_input = input("\nTú: ")
        if user_input.lower() == "salir":
            break
        respuesta = ejecutar_agente(user_input)
        print(f"Agente: {respuesta}")
