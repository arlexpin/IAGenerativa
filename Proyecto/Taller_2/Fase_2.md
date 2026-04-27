# Taller 2 – Fase 2: Creación de la Base de Conocimiento de Documentos

## Contexto
Un sistema RAG solo es tan bueno como la información que puede recuperar. En esta fase diseñamos la base de conocimiento de EcoMarket: seleccionamos documentos críticos, definimos la estrategia de segmentación (chunking) y explicamos el proceso de indexación vectorial.

---

## 1. Identificación de Documentos (mínimo 3 tipos)

Para cubrir las consultas más frecuentes de los clientes de EcoMarket, se incluirán los siguientes documentos:

| Tipo de documento | Formato | Contenido clave | Utilidad en RAG |
|------------------|---------|----------------|------------------|
| **Política de devoluciones y garantías** | PDF | Plazos (15 días), productos excluidos (higiene, perecederos), proceso de reembolso, condiciones de empaque. | Responder preguntas sobre devoluciones, cambios y garantías. |
| **Inventario de productos** | CSV / Excel | Nombre, categoría, stock, precio, atributos ecológicos (material reciclado, biodegradable), proveedor. | Consultas de disponibilidad, precios y características sostenibles. |
| **Preguntas frecuentes (FAQs)** | JSON / Markdown | Respuestas estandarizadas sobre: tiempos de envío, seguimiento de pedidos, métodos de pago, contacto con soporte humano. | Resolver dudas comunes sin necesidad de inferencia compleja. |

### Documentos adicionales (opcionales pero recomendados)
- **Manual de servicio al cliente** (PDF) → para casos límite y escalamientos.
- **Logística de envíos** (JSON con estados reales) → para consultas de tracking en tiempo real (integración con API).

---

## 2. Estrategia de Segmentación (Chunking)

### Decisión adoptada
**Segmentación recursiva por tamaño variable con solapamiento (RecursiveCharacterTextSplitter)**  
- Tamaño del chunk: **512 tokens** (≈ 400 palabras en español).  
- Solapamiento (overlap): **64 tokens** (12.5 %).  
- Separadores: `["\n\n", "\n", ".", " ", ""]` (prioriza respetar párrafos, luego oraciones, luego palabras).

### Justificación

#### a) ¿Por qué segmentar?
Los modelos de embeddings y LLM tienen ventanas de contexto limitadas (ej. Llama 3.1 8B → 8K tokens). Enviar documentos completos sería ineficiente y costoso. La segmentación permite:
- Recuperar solo las partes relevantes para cada consulta.
- Mantener la latencia baja.
- Evitar diluir la información relevante en ruido.

#### b) ¿Por qué segmentación recursiva?
EcoMarket maneja documentos heterogéneos:
- **PDF** → párrafos largos, listas, tablas.
- **CSV** → cada fila es una entrada independiente.
- **JSON** → estructuras anidadas.

El splitter recursivo intenta primero dividir por párrafos (`\n\n`). Si un párrafo excede 512 tokens, divide por oraciones (`.`). Si aún es muy largo, divide por palabras. Esto **preserva la coherencia semántica** mucho mejor que una división fija por caracteres.

#### c) ¿Por qué solapamiento (overlap)?
Evita la pérdida de contexto en los límites de los fragmentos.  
**Ejemplo crítico:**  
> "No se aceptan devoluciones de productos de higiene personal, **excepto si el empaque está sellado**."

Sin solapamiento, la excepción podría quedar en un fragmento diferente al de la regla general. Con 64 tokens de overlap, ambas partes se incluyen en múltiples fragmentos, asegurando que el sistema recupere la información completa.

#### d) Comparativa con otras estrategias

| Estrategia | Ventajas | Desventajas para EcoMarket |
|------------|----------|----------------------------|
| **Tamaño fijo sin overlap** | Simple, rápido | Corta frases o ideas por la mitad; pérdida de contexto. |
| **Por párrafos** | Respeta estructura natural | Párrafos muy largos (ej. términos legales) exceden la ventana. |
| **Recursiva + overlap (elegida)** | Equilibrio entre coherencia y tamaño; adaptable a formatos mixtos | Ligeramente más costosa computacionalmente (insignificante). |
| **Semántica (con NLP)** | Ideal para documentos muy largos | Compleja de implementar; requiere modelos adicionales. |

---

## 3. Proceso de Indexación

Una vez definidos los documentos y la estrategia de chunking, se sigue este flujo para construir el índice vectorial:

### Paso a paso

1. **Carga de documentos**  
   - PDF → `PyPDFLoader` (LangChain)  
   - CSV → `csv.DictReader`  
   - JSON → `json.load`

2. **Limpieza y normalización**  
   - Eliminar saltos de línea excesivos, números de página, cabeceras/pies de página irrelevantes.  
   - Unificar mayúsculas/minúsculas si es necesario (opcional).

3. **Segmentación (chunking)**  
   - Aplicar `RecursiveCharacterTextSplitter` con los parámetros definidos.  
   - Cada chunk se almacena temporalmente como un objeto `Document` con su texto y metadatos (fuente, fecha, etc.).

4. **Generación de embeddings**  
   - Usar el modelo seleccionado en Fase 1: `distiluse-base-multilingual-cased-v2`.  
   - Cada chunk se convierte en un vector de 512 dimensiones.

5. **Almacenamiento en ChromaDB**  
   - ChromaDB guarda los vectores junto con el texto original y metadatos.  
   - Se construye automáticamente un índice HNSW (Hierarchical Navigable Small World) para búsqueda rápida por similitud coseno.  
   - Modo persistente: `PersistentClient` con ruta `./chroma_db`.

### Código ejemplo (extracto)

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Configuración
splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=64,
    separators=["\n\n", "\n", ".", " ", ""]
)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/distiluse-base-multilingual-cased-v2")

# Cargar, segmentar y indexar
chunks = splitter.split_documents(documentos)
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)
vectorstore.persist()