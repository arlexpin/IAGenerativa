# Fase 2: Implementación y Conexión de Componentes

## 1. Extensión del Código Base (Taller 2 → Proyecto Final)

Partiendo del código RAG del Taller 2, se han realizado las siguientes extensiones:

### Cambios principales

| Componente | Taller 2 (solo RAG) | Proyecto Final (agente) |
|------------|---------------------|-------------------------|
| **Estructura** | Un solo script `rag_llama3.1.py` | Módulos separados: `herramientas.py`, `base_conocimiento.py`, `agente_devoluciones.py` |
| **Lógica de respuesta** | `RetrievalQA` directo | Agente ReAct con herramientas |
| **Herramientas** | Ninguna | `verificar_elegibilidad`, `generar_etiqueta_devolucion`, más RAG como herramienta |
| **Flujo de decisión** | Respuesta pasiva basada en contexto | El agente decide qué herramienta usar según la intención del usuario |

### Archivos generados

- `src/herramientas.py`: funciones simuladas para verificación y generación de etiquetas.
- `src/base_conocimiento.py`: reutiliza la indexación RAG del taller anterior.
- `src/agente_devoluciones.py`: configura el agente LangChain con las herramientas y el prompt ReAct.
- `app/streamlit_app.py`: interfaz web.

## 2. Definición de las Herramientas (Tools)

### Herramienta 1: `verificar_elegibilidad`
```python
def verificar_elegibilidad(producto_id: str, estado_producto: str = "sin usar") -> dict