# Fase 2: Implementación y Conexión de Componentes

## 1. Extensión del código base (Taller 2 → Proyecto Final)

| Componente | Taller 2 (solo RAG) | Proyecto Final (agente) |
|------------|---------------------|-------------------------|
| **Estructura** | Script único `rag_llama3.1.py` | Módulos: `herramientas.py`, `base_conocimiento.py`, `agente_devoluciones.py` |
| **Lógica** | `RetrievalQA` directo | Router + RAG mejorado + agente ReAct |
| **Herramientas** | Ninguna | `verificar_elegibilidad`, `generar_etiqueta_devolucion`, `consultar_base_conocimiento` |
| **Decisión** | Respuesta pasiva por contexto | Router por intención + respuestas determinísticas |

### Archivos principales

| Archivo | Responsabilidad |
|---------|-----------------|
| `src/base_conocimiento.py` | Carga `datos/`, indexación Chroma, recuperación de contexto, `responder_pregunta()` |
| `src/agente_devoluciones.py` | Router, saludos, elegibilidad por producto, agente ReAct, `ejecutar_agente()` |
| `src/herramientas.py` | Implementación simulada de tools |
| `app/streamlit_app.py` | Interfaz de chat web |

---

## 2. Base de conocimiento (`base_conocimiento.py`)

### Fuentes indexadas

1. **`datos/politicas_ecomarket.txt`** — Políticas de devolución, envíos y pagos.
2. **`datos/faqs.json`** — Preguntas frecuentes en formato pregunta/respuesta.
3. **`datos/inventario_productos.csv`** — Catálogo con política de devolución por categoría embebida en cada documento.

### Indexación

- **Embeddings:** `sentence-transformers/distiluse-base-multilingual-cased-v2`
- **Almacén:** Chroma en `chroma_db/`
- **Versión de índice:** `INDEX_VERSION = "2"` — reconstruye automáticamente si cambia
- **Chunking:** Políticas fragmentadas (400 chars); productos y FAQs como documento único cada uno

### Funciones clave

```python
ensure_vectorstore(rebuild=False)   # Crea o carga el índice
recuperar_contexto(query, k=8)      # Top-k fragmentos con consulta expandida
responder_pregunta(llm, pregunta)   # LLM + prompt RAG + fallback si respuesta evasiva
buscar_productos_en_consulta(texto) # Coincidencia por nombre en inventario
expandir_consulta(query)            # Añade términos relacionados para mejor retrieval
```

### Mejoras RAG (respecto a versión inicial)

- Prompt que **obliga** a usar el contexto recuperado.
- Detección de **respuestas evasivas** (“no puedo ayudar”) con fallback a contexto.
- **Consulta expandida** para devoluciones, envíos, perecederos, etc.
- Productos indexados con texto explícito de elegibilidad por categoría.

---

## 3. Router del agente (`agente_devoluciones.py`)

Función principal: `ejecutar_agente(entrada_usuario)`.

```python
def ejecutar_agente(entrada_usuario: str) -> str:
    if es_conversacion_casual(entrada):      # "Hola", "¿cómo estás?"
        return respuesta_conversacional()

    if responder_devolucion_producto(entrada):  # "¿Puedo devolver X?"
        return respuesta_deterministica

    contexto_rag = recuperar_contexto(entrada)

    if es_solicitud_devolucion(entrada):     # "Quiero devolver PROD-003"
        return ejecutar_flujo_devolucion(entrada, contexto_rag)

    return consultar_rag(entrada)            # Preguntas generales
```

### Carga diferida (lazy loading)

Ollama y Chroma solo se inicializan cuando hace falta. Los saludos responden al instante sin cargar el modelo.

---

## 4. Herramientas (`herramientas.py`)

### `verificar_elegibilidad(producto_id, estado_producto)`

```python
# Ejemplo: PROD-005 (Perecederos)
{"elegible": False, "razon": "Los productos perecederos no son elegibles..."}

# Ejemplo: PROD-003 (Higiene, sin usar)
{"elegible": True, "razon": "Producto de higiene personal sin abrir..."}
```

### `generar_etiqueta_devolucion(pedido_id, producto_id, direccion_cliente)`

```python
{
    "etiqueta_url": "https://api.ecomarket.co/labels/RET-EM-904-PROD-003-....pdf",
    "codigo_seguimiento": "RET-EM-904-PROD-003-202505171200",
    "mensaje": "Etiqueta generada correctamente..."
}
```

---

## 5. Agente ReAct (devoluciones activas)

- **Modelo:** Ollama `llama3.1:8b`, temperatura 0.0
- **Máximo de iteraciones:** 3
- **Fallback:** `fallback_return_flow()` si el agente falla o devuelve respuesta inválida
- **Contexto RAG** inyectado en la pregunta antes de invocar el agente

### Flujo fallback (sin ReAct)

1. Extrae `producto_id`, `pedido_id`, `dirección`, `estado` con regex.
2. Llama `verificar_elegibilidad`.
3. Si es elegible y hay datos completos → `generar_etiqueta_devolucion`.
4. Si faltan datos → solicita `pedido_id` y/o `dirección_cliente`.

---

## 6. Interfaz Streamlit (`app/streamlit_app.py`)

- Chat con historial en `st.session_state.messages`
- Indexación automática al primer arranque (`ensure_vectorstore()`)
- Spinner durante la carga del índice

---

## 7. Pruebas (`pruebas/`)

| Archivo | Contenido |
|---------|-----------|
| `test_devoluciones.py` | Tools, parser, saludos, semillas albahaca, fallback |
| `test_agente.py` | Casos de integración manual (requiere Ollama) |

Ejecutar:

```bash
python pruebas/test_devoluciones.py
```

---

## 8. Ejemplos de uso

| Entrada | Salida esperada |
|---------|-----------------|
| `Hola` | Bienvenida con opciones de ayuda |
| `¿Cuál es la política de devoluciones?` | 30 días, condiciones, exclusiones (RAG) |
| `¿Puedo devolver unas semillas de albahaca?` | No — PROD-005, categoría Perecederos |
| `Quiero devolver PROD-003, está sin usar` | Verificación + solicitud de pedido/dirección |
| `EM-904, Calle 123, devolver PROD-003` | Etiqueta generada con código de seguimiento |

---

## 9. Dependencias (`requirements.txt`)

```
langchain==0.3.0
langchain-community==0.3.0
chromadb==1.5.9
ollama==0.6.1
streamlit==1.35.0
pypdf==4.0.0
pandas==2.2.0
```

*Los embeddings de Hugging Face descargan `sentence-transformers` en el primer uso.*
