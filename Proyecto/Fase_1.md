# Fase 1: Selección y Justificación de la Arquitectura de IA - Proyecto EcoMarket

## 1. Contextualización del Problema
EcoMarket se enfrenta con un cuello de botella: el tiempo de respuesta de 24 horas que genera desconfianza en el cliente. El 80% de las consultas son transaccionales (estado de pedido, dudas de catálogo), lo que las hace candidatas perfectas para la automatización, dejando el 20% de casos de alta carga emocional.

## 2. Selección y Justificación del Modelo de IA

### **Modelo Seleccionado:** Llama 3.1 8B (vía Ollama)
Tras analizar opciones como GPT-4 (Cloud-based) y modelos de mayor escala (70B+), hemos optado por un **Modelo de Lenguaje Pequeño (SLM)** optimizado para despliegue local.

#### **¿Por qué esta arquitectura?**
1.  **Soberanía y Privacidad de la información:** Como empresa operando en Colombia (asumimos esta parte), la protección de datos personales es innegociable. Al ejecutar **Llama 3.1 8B** sobre una **RTX 5090** local (Es lo minímo que esperamos tener o con lo que contamos en este momento), garantizamos que la información sensible de los clientes (direcciones, teléfonos, historial de compras) nunca salga de los servidores de la empresa.
2.  **Optimización de Hardware (RTX 5090 de 24GB):**
    - **Throughput Masivo:** Mientras que un modelo de 70B saturaría la VRAM limitando la concurrencia, el modelo de 8B nos permite procesar muchas conversaciones en paralelo con poca latencia ($<20ms$).
    - **Cuantización:** Utilizaremos una cuantización de 4 o 8 bits para maximizar la velocidad sin sacrificar la coherencia semántica o sentido de la información.
3.  **Estrategia RAG con Overlapping Semántico:**
    - No usaremos el modelo de forma aislada. Implementaremos **Generación Aumentada por Recuperación (RAG)**.
    - **Técnica de Chunking:** Fragmentos de 1024 tokens con un **overlapping (solapamiento) del 20% (200 tokens)**.
    - **Justificación del Overlap:** Esto previene la pérdida de contexto en los límites de los fragmentos, asegurando que las políticas y especificaciones técnicas de productos sostenibles se recuperen de la forma que necesitamos.