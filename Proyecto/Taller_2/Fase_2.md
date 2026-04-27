# Taller 2 – Fase 2: Creación de la Base de Conocimiento de Documentos

## Contexto
Un sistema RAG solo es tan bueno como la información que puede recuperar. En esta fase diseñamos la base de conocimiento de EcoMarket: seleccionamos documentos críticos, definimos la estrategia de segmentación (chunking) y explicamos el proceso de indexación vectorial.

---

## 1. Identificación de Documentos

El sistema RAG de EcoMarket se construirá con los siguientes documentos, que cubren las consultas más comunes:

| Tipo | Formato | Nombre de archivo (ejemplo) | Contenido esencial |
|------|---------|----------------------------|--------------------|
| **Política de devoluciones** | TXT | `politicas_ecomarket.txt` | Plazos, condiciones, productos excluidos (higiene, perecederos) |
| **Inventario de productos** | CSV | `inventario_productos.csv` | ID, nombre, categoría, stock, precio, descripción, atributo ecológico |
| **Preguntas frecuentes** | JSON | `faqs.json` | Pregunta-respuesta sobre envíos, pagos, seguimiento de pedidos |

## 2. Estrategia de Segmentación (Chunking)

### Decisión adoptada
**Segmentación recursiva por tamaño variable con solapamiento (RecursiveCharacterTextSplitter)**  
- Tamaño del chunk: **256 tokens** (≈ 200 palabras en español) — reducido para mejorar recuperación de información concisa en FAQs y políticas.  
- Solapamiento (overlap): **64 tokens** (25 % del chunk) — aumentado para mantener contexto crítico en límites de fragmentos.  
- Separadores: `["\n\n", "\n", ".", " ", ""]` (prioriza respetar párrafos, luego oraciones, luego palabras).

### Optimización para EcoMarket
La reducción de tamaño de chunk de 512 a 256 tokens mejora significativamente:
- **Recuperación de FAQs**: Las preguntas frecuentes y sus respuestas consistentes se mantienen intactas en un solo chunk.
- **Políticas claras**: Secciones numeradas de políticas se recuperan sin dilución de ruido.
- **Relevancia aumentada**: El LLM recibe contexto más enfocado, mejorando la precisión de respuestas.

El overlap incrementado (64 tokens = 25 %) asegura que información crítica en límites se incluya en múltiples chunks para mejor recuperación semántica, evitando cortes de frases importantes.

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

El splitter recursivo intenta primero dividir por párrafos (`\n\n`). Si un párrafo excede 256 tokens, divide por oraciones (`.`). Si aún es muy largo, divide por palabras. Esto **preserva la coherencia semántica** mucho mejor que una división fija por caracteres.

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

## 3. Proceso de Indexación

Una vez definidos los documentos y la estrategia de chunking, se sigue este flujo para construir el índice vectorial:

### Paso a paso

1. **Carga de documentos**  
   - TXT → `Document` (LangChain)  
   - CSV → `Document` (LangChain)  
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
    chunk_size=256,
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