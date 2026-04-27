# Taller 2 – Fase 3: Integración y Ejecución del Código

## Contexto
En esta fase se implementa un sistema RAG (Generación Aumentada por Recuperación) completo para EcoMarket, utilizando exclusivamente herramientas locales: **Ollama** con el modelo **Llama 3.1 8B**, **LangChain**, **ChromaDB** como base de datos vectorial y **HuggingFace embeddings** para la vectorización de documentos. El objetivo es que el asistente responda preguntas basándose en los documentos internos de la empresa, evitando alucinaciones.

## 1. Mejoras Implementadas en la Configuración

### Optimización del Chunking
Para mejorar significativamente la calidad de recuperación de información:
- **Chunk size reducido**: de 512 a **256 tokens** (≈ 200 palabras en español)
- **Overlap aumentado**: mantiene **64 tokens** de solapamiento (ahora 25% del chunk vs 12.5% anterior)

**Razón**: Los documentos de EcoMarket contienen respuestas claras y concisas en FAQs y políticas. El tamaño de chunk más pequeño evita dilución de información relevante y mejora la recuperación semántica.

### Documentos Enriquecidos
Se han expandido los archivos base para mejorar la recuperación:

1. **politicas_ecomarket.txt**: Ahora estructurado en secciones claras
   - Plazo de devolución: **30 días** (explícito)
   - Productos no elegibles: Alimentos, perecederos (explícito)
   - Métodos de pago (nueva sección)

2. **faqs.json**: Añadidas preguntas críticas
   - "¿Cuánto tiempo tengo para devolver un producto?"
   - "¿Aceptan devolución de alimentos?"
   - "¿Qué productos ecológicos tienen en inventario?"

3. **inventario_productos.csv**: Descripciones expandidas
   - Palabras clave ecológicas integradas en descripciones

## 2. Estructura del Repositorio

```
Proyecto/Taller_2/
├── requirements.txt
├── Fase_1.md
├── Fase_2.md
├── Fase_3.md
├── demo_rag_actualizado.ipynb
├── data/
│   ├── politicas_ecomarket.txt
│   ├── faqs.json
│   └── inventario_productos.csv
└── scripts/
    └── rag_llama3.1.py
```

## 3. Requisitos

- Ollama instalado y en ejecución
- Modelo `llama3.1:8b`: `ollama pull llama3.1:8b`
- Python 3.8+

## 4. Instalación

```bash
pip install -r requirements.txt
```

## 5. Ejecución

### Modo interactivo (recomendado)
```bash
cd scripts
python rag_llama3.1.py --rebuild
```

### Una sola pregunta
```bash
cd scripts
python rag_llama3.1.py --query "¿Aceptan devolución de alimentos?"
```

## 6. Comparativa de Resultados (Antes y Después)

| Pregunta | Antes | Después |
|----------|-------|---------|
| ¿Cuánto tiempo tengo para devolver un producto? | No tengo información... | Tienes 30 días desde la fecha de compra |
| ¿Aceptan devolución de alimentos? | Lo siento, pero no hay información... | No. Los produtos perecederos NO son elegibles |
| ¿Qué métodos de pago aceptan? | ✅ Tarjetas de crédito, Mercado Pago... | ✅ Tarjetas de crédito, Mercado Pago... |
| ¿Qué productos ecológicos tienen? | No tengo información... | Termo de acero, Chaqueta de algodón, Cepillo de bambú... |