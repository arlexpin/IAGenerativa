# Fase 1: Diseño de la Arquitectura del Agente

## 1. Extensión de la arquitectura RAG
Se implementa una arquitectura **router**:
- El agente analiza la consulta del usuario y decide si es una **solicitud de devolución** (usa herramientas) o una **pregunta general** (usa el sistema RAG existente).
- El RAG se mantiene como una herramienta interna llamada `consulta_base_conocimiento`.

## 2. Definición de las herramientas (Tools)
Se definen dos herramientas simuladas (mínimo requerido):

| Herramienta | Descripción | Entrada | Salida |
|-------------|-------------|---------|--------|
| `verificar_elegibilidad` | Verifica si un producto es elegible para devolución según categoría y condiciones. | `producto_id`, `estado_producto` (usado/sin usar) | `{elegible: bool, razon: str}` |
| `generar_etiqueta_devolucion` | Crea una etiqueta de envío simulada para el cliente. | `pedido_id`, `producto_id`, `direccion_cliente` | `{etiqueta_url: str, codigo_seguimiento: str}` |

*Nota: El RAG se considera una herramienta adicional pero no se cuenta para el mínimo.*

## 3. Selección del marco de agentes
**LangChain** es elegido porque:
- Integración nativa con las herramientas y el RAG ya implementado.
- Soporte para agentes ReAct (razonamiento + acción) con modelos locales (Ollama).
- Comunidad amplia y documentación robusta.

## 4. Planificación del flujo de trabajo (devolución)
[Usuario] -> "Quiero devolver el producto PROD-003, está sin usar"
[Agente] -> Decide usar herramienta verificar_elegibilidad(producto_id="PROD-003", estado="sin sar")
[Herramienta] -> Consulta inventario (categoría "Higiene personal") -> Elegible = False
[Agente] -> Genera respuesta: "Los productos de higiene personal usados o abiertos no son legibles. Solo se aceptan sin abrir."
[Usuario] -> "Está nuevo, sin abrir"
[Agente] -> Vuelve a llamar verificar_elegibilidad(estado="sin abrir") -> Elegible = True
[Agente] -> Llama generar_etiqueta_devolucion(pedido_id, producto_id, direccion)
[Agente] -> Responde con la etiqueta y pasos a seguir.

**Decisión:** El agente debe preguntar datos faltantes (estado del producto, dirección) antes de generar la etiqueta.