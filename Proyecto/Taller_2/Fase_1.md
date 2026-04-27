# Taller 2 – Fase 1: Selección de Componentes Clave del Sistema RAG

## Contexto
EcoMarket necesita extender su asistente de IA para que responda cualquier consulta basándose en su conocimiento interno, evitando alucinaciones. Para ello se implementará un sistema **RAG (Generación Aumentada por Recuperación)**. En esta primera fase se seleccionan y justifican dos componentes fundamentales: el **modelo de embeddings** y la **base de datos vectorial**.

---

## 1. Modelo de Embeddings

### Selección
**`distiluse-base-multilingual-cased-v2`** (de Sentence Transformers, Hugging Face)

### Justificación detallada

| Criterio | Evaluación |
|----------|-------------|
| **Precisión en español** | Entrenado con pares de frases multilingües, captura semántica de alta calidad en español, ideal para políticas de devolución, inventario y FAQs de EcoMarket. |
| **Costo** | Código abierto, gratuito. No requiere llamadas a APIs externas, evitando costos por token. |
| **Soberanía de datos** | Se ejecuta localmente (CPU/GPU propia). No envía texto fuera del perímetro de la empresa, cumpliendo la Ley 1581 de Colombia. |
| **Tamaño del vector** | 512 dimensiones. Suficiente para documentos de tamaño medio sin sobrecarga computacional. |
| **Despliegue** | Funciona en hardware modesto (incluso en CPU). Compatible con LangChain y ChromaDB. |

### Opciones descartadas
- **OpenAI text-embedding-ada-002**: mayor precisión pero costoso y envía datos a servidores externos → viola políticas de privacidad.
- **BERT multilingüe (base)**: más pesado (110M parámetros) y más lento para embedding en tiempo real.

---

## 2. Base de Datos Vectorial

### Selección
**ChromaDB** (modo persistente local)

### Justificación frente a alternativas

| Característica | ChromaDB | Pinecone | Weaviate |
|----------------|----------|----------|----------|
| **Modelo de despliegue** | Local (open source) | Cloud (propietario) | Local o cloud |
| **Costo** | Gratuito | Por uso (escala con consultas) | Gratuito en local, pago en cloud |
| **Privacidad de datos** | Completa (datos en el servidor de EcoMarket) | Datos salen de la empresa | Local permite privacidad total |
| **Escalabilidad** | Hasta millones de vectores en un nodo | Escala automática | Requiere configuración para alta concurrencia |
| **Facilidad de uso** | Muy alta (integraciones nativas con LangChain/LlamaIndex) | Media | Baja (configuración más compleja) |
| **Rendimiento en latencia** | Baja latencia para volúmenes < 100k vectores | Muy baja (infraestructura optimizada) | Baja si está bien configurado |

### Decisión final
ChromaDB es la opción óptima para EcoMarket porque:
1. **Cumple la normativa**: al ser local, los datos de clientes no abandonan la infraestructura.
2. **Sin costos recurrentes**: ideal para un negocio en crecimiento con presupuesto ajustado.
3. **Fácil de prototipar y poner en producción**: se integra en minutos con LangChain.
4. **Rendimiento suficiente**: el volumen inicial de documentos de EcoMarket (políticas, inventario, FAQs) es de pocos miles de fragmentos, muy por debajo del límite práctico de ChromaDB.

### Configuración recomendada
- Modo `PersistentClient` para que la base de datos sobreviva entre reinicios.
- Índice HNSW por defecto para búsqueda de similitud coseno.
- Almacenamiento en disco local (SSD recomendado).

---

## 3. Respuesta a las Preguntas Guía del Taller

### ¿Modelo de embeddings de código abierto o propietario?
**Código abierto**. EcoMarket prioriza la soberanía de datos y la ausencia de costos operativos por consulta. Los modelos propietarios (OpenAI, Cohere) ofrecen comodidad pero generan dependencia externa y riesgo de fuga de información comercial.

### ¿Pinecone, ChromaDB o Weaviate? Ventajas y desventajas para EcoMarket

| Base de datos | Ventajas para EcoMarket | Desventajas para EcoMarket |
|---------------|------------------------|----------------------------|
| **ChromaDB** | - Sin costos<br>- Local y privado<br>- Integración simple | - Escalabilidad limitada a un nodo (pero suficiente crecimiento esperado)<br>- Sin alta disponibilidad nativa |
| **Pinecone** | - Escalabilidad infinita<br>- Mantenimiento cero | - Costo mensual creciente<br>- Datos salen de Colombia<br>- Dependencia de internet |
| **Weaviate** | - Búsqueda híbrida (vectorial + BM25)<br>- Modo local posible | - Complejidad de operación<br>- Mayor consumo de RAM/CPU |

**Conclusión:** ChromaDB es la mejor relación beneficio‑costo para una mediana empresa de e‑commerce que inicia con IA generativa.

---

## Resumen de la Selección

| Componente | Tecnología elegida | Razón principal |
|------------|-------------------|------------------|
| Embeddings | `distiluse-base-multilingual-cased-v2` | Precisión en español, gratis, local, integrable. |
| Vector DB | ChromaDB (local) | Privacidad total, costo cero, facilidad de uso. |

Ambos componentes se alinean con la estrategia de **IA ética y autónoma** de EcoMarket, permitiendo un sistema RAG preciso y conforme a la ley colombiana.