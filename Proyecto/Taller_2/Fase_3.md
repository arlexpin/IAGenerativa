# Taller 2 – Fase 3: Integración y Ejecución del Código

# Taller 2 – Fase 3: Integración y Ejecución del Código (Respuesta Completa)

## Contexto
En esta fase se implementa un sistema RAG (Generación Aumentada por Recuperación) completo para EcoMarket, utilizando exclusivamente herramientas locales: **Ollama** con el modelo **Llama 3.1 8B** (el mismo usado en los talleres anteriores), **LangChain** y **ChromaDB** como base de datos vectorial. El objetivo es que el asistente responda preguntas basándose en los documentos internos de la empresa, evitando alucinaciones.

## 1. Estructura del Repositorio en GitHub


├── requirements.txt
├── datos/
│ └── politicas_ecomarket.txt
├── scripts/
│ └── rag_llama3.1.py
└── notebooks/
└── demo_rag.ipynb


## 2. Archivos del Sistema

Sistema RAG para atención al cliente usando Ollama + Llama 3.1 8B.

## Requisitos
- Ollama instalado y en ejecución
- Modelo `llama3.1:8b` descargado: `ollama pull llama3.1:8b`
- Python 3.8+

## Instalación
pip install -r requirements.txt

## Ejecución
cd scripts && python rag_llama3.1.py

## 3. Adaptación del Taller Práctico #1 (sin RAG) a este sistema

En el taller anterior se usaba directamente Ollama sin contexto:

  respuesta = ollama.generate(model="llama3.1:8b", prompt="¿Puedo devolver?")

Con RAG (este script), se añade la recuperación de documentos para enriquecer el prompt. No es necesario cambiar el modelo; solo se añade la capa de búsqueda vectorial. El LLM sigue siendo el mismo llama3.1:8b.