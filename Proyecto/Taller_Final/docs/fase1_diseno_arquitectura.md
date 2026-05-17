# Fase 1: Diseño de la Arquitectura del Agente

## 1. Extensión de la arquitectura RAG + Router

Se implementa una arquitectura **router** con **RAG obligatorio como primer paso** para consultas de negocio:

```
[Usuario]
    │
    ▼
┌─────────────────────────────────────┐
│  Router (agente_devoluciones.py)    │
└─────────────────────────────────────┘
    │
    ├─ Saludo / conversación casual ──► Bienvenida (sin LLM)
    │
    ├─ Pregunta sobre devolución de producto ──► Inventario + verificar_elegibilidad
    │
    ├─ Solicitud activa de devolución ──► Agente ReAct + herramientas + contexto RAG
    │
    └─ Pregunta general ──► RAG (recuperar contexto + LLM)
```

### Principios de diseño

1. **RAG primero:** Toda consulta de negocio recupera contexto de `datos/` antes de decidir la acción.
2. **Fuentes de verdad:** Políticas (`politicas_ecomarket.txt`), FAQs (`faqs.json`) e inventario (`inventario_productos.csv`).
3. **Router por intención:** No todas las consultas requieren el agente ReAct; las preguntas informativas usan RAG directo.
4. **Respuestas determinísticas** cuando es posible (p. ej. elegibilidad por nombre de producto) para reducir alucinaciones.

## 2. Definición de las herramientas (Tools)

| Herramienta | Descripción | Entrada | Salida |
|-------------|-------------|---------|--------|
| `verificar_elegibilidad` | Verifica si un producto es elegible según categoría y estado. | `producto_id`, `estado_producto` | `{elegible: bool, razon: str}` |
| `generar_etiqueta_devolucion` | Crea etiqueta de envío simulada. | `pedido_id`, `producto_id`, `direccion_cliente` | `{etiqueta_url, codigo_seguimiento, mensaje}` |
| `consultar_base_conocimiento` | Consulta adicional al RAG. | Pregunta en lenguaje natural | Texto con respuesta basada en contexto |

*Nota: `consultar_base_conocimiento` es herramienta auxiliar del agente ReAct; el RAG principal se ejecuta antes del router.*

### Reglas de elegibilidad (inventario)

| Categoría | Regla |
|-----------|--------|
| **Perecederos** | Nunca elegibles (normas sanitarias) |
| **Higiene personal** | Solo si está sin abrir / sin usar |
| **Otras** | Elegibles dentro de 30 días, sin usar y en empaque original |

## 3. Selección del marco de agentes

**LangChain** porque:

- Integración nativa con herramientas y RAG.
- Soporte para agentes ReAct con Ollama local.
- Comunidad amplia y documentación robusta.

**Componentes:**

- `HuggingFaceEmbeddings` + **Chroma** para el índice vectorial.
- **Ollama** (`llama3.1:8b`) como LLM.
- **AgentExecutor** con prompt ReAct para devoluciones.

## 4. Flujo de trabajo – devolución activa

```
[Usuario] → "Quiero devolver el producto PROD-003, está sin usar"
    │
    ▼ RAG recupera políticas + ficha PROD-003
    │
[Agente ReAct] → verificar_elegibilidad(PROD-003, "sin usar")
    │
[Herramienta] → Higiene personal sin abrir → elegible: true
    │
[Agente] → Pide pedido_id y dirección si faltan
    │
[Usuario] → "Pedido EM-904, dirección Calle 123"
    │
[Agente] → generar_etiqueta_devolucion(...)
    │
[Agente] → Responde con código de seguimiento
```

**Decisión:** El agente debe verificar elegibilidad antes de generar la etiqueta y solicitar datos faltantes (`pedido_id`, `direccion_cliente`, `estado_producto`).

## 5. Flujo de trabajo – pregunta informativa

```
[Usuario] → "¿Puedo devolver unas semillas de albahaca?"
    │
    ▼ Busca "Semillas albahaca" en inventario → PROD-005 (Perecederos)
    │
    ▼ verificar_elegibilidad(PROD-005) → elegible: false
    │
[Respuesta] → "No, no puedes devolver... producto perecedero..."
```

Si no se identifica un producto concreto, el RAG recupera fragmentos de políticas/FAQs y el LLM responde con el contexto inyectado.

## 6. Diagrama de componentes

```
┌──────────────┐     ┌─────────────────────┐     ┌─────────────┐
│  Streamlit   │────►│ agente_devoluciones │────►│ herramientas│
│  streamlit_  │     │     (router)        │     │    .py      │
│    app.py    │     └──────────┬──────────┘     └─────────────┘
└──────────────┘                │
                                ▼
                    ┌─────────────────────┐
                    │  base_conocimiento  │
                    │  (Chroma + RAG)     │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │       datos/        │
                    └─────────────────────┘
```
