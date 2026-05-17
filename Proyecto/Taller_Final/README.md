# Agente de IA para Automatización de Devoluciones – EcoMarket

Agente conversacional que combina **RAG** (Retrieval-Augmented Generation) sobre la base de conocimiento de EcoMarket con **herramientas** para gestionar devoluciones: verificar elegibilidad y generar etiquetas de envío simuladas.

## Características

- **RAG primero** sobre la carpeta `datos/` (políticas, FAQs e inventario).
- **Router de intención**: saludos, preguntas informativas, consultas de elegibilidad por producto y solicitudes activas de devolución.
- **Agente ReAct** (LangChain + Ollama) para flujos de devolución con herramientas.
- **Interfaz web** con Streamlit.
- **Índice vectorial** Chroma con reconstrucción automática al actualizar la versión del índice.

## Estructura del proyecto

```
Taller_Final/
├── app/
│   └── streamlit_app.py      # Interfaz de chat
├── datos/
│   ├── politicas_ecomarket.txt
│   ├── faqs.json
│   └── inventario_productos.csv
├── docs/
│   ├── fase1_diseno_arquitectura.md
│   ├── fase2_implementacion.md
│   └── fase3_analisis_critico.md
├── pruebas/
│   ├── test_devoluciones.py
│   └── test_agente.py
├── src/
│   ├── base_conocimiento.py  # Indexación y RAG
│   ├── agente_devoluciones.py # Router + agente ReAct
│   └── herramientas.py       # Tools simuladas
├── chroma_db/                # Índice vectorial (generado)
├── requirements.txt
└── README.md
```

## Requisitos

- Python 3.10+
- [Ollama](https://ollama.com/) con el modelo `llama3.1:8b` instalado
- Dependencias en `requirements.txt`

## Instalación

```bash
cd Proyecto/Taller_Final
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
ollama pull llama3.1:8b
```

## Uso

### Interfaz web (Streamlit)

```bash
cd app
streamlit run streamlit_app.py
```

La primera ejecución indexa automáticamente los archivos de `datos/` en `chroma_db/`.

### Consola

```bash
python -m src.agente_devoluciones
```

### Pruebas

```bash
python pruebas/test_devoluciones.py
python pruebas/test_agente.py
```

### Reconstruir el índice vectorial

Si modificas archivos en `datos/`:

```bash
python -c "from src.base_conocimiento import ensure_vectorstore; ensure_vectorstore(rebuild=True)"
```

## Flujo de respuesta

| Tipo de mensaje | Ejemplo | Comportamiento |
|-----------------|---------|----------------|
| Saludo | "Hola" | Bienvenida instantánea (sin LLM) |
| Elegibilidad por producto | "¿Puedo devolver semillas de albahaca?" | Inventario + `verificar_elegibilidad` |
| Pregunta general | "¿Cuál es la política de devoluciones?" | RAG con contexto ampliado |
| Solicitud de devolución | "Quiero devolver PROD-003" | Agente ReAct + herramientas + contexto RAG |

## Herramientas del agente

| Herramienta | Descripción |
|-------------|-------------|
| `consultar_base_conocimiento` | Consulta adicional al RAG |
| `verificar_elegibilidad` | Valida devolución por `producto_id` y estado |
| `generar_etiqueta_devolucion` | Genera etiqueta simulada de devolución |

## Documentación técnica

Detalle de arquitectura, implementación y análisis crítico en la carpeta [`docs/`](docs/).

## Modelo y embeddings

- **LLM:** Ollama `llama3.1:8b` (temperatura 0.0)
- **Embeddings:** `sentence-transformers/distiluse-base-multilingual-cased-v2`
- **Vector store:** ChromaDB (`chroma_db/`)

## Licencia y autoría

Proyecto académico – curso IA Generativa. EcoMarket es un caso de estudio ficticio.