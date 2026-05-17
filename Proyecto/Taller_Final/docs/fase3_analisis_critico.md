# Fase 3: Análisis Crítico y Propuestas de Mejora

## 1. Análisis de seguridad y ética

Al darle al agente la capacidad de ejecutar acciones (generar etiquetas de devolución), surgen nuevos riesgos:

| Riesgo | Descripción | Mitigación implementada | Mitigación futura |
|--------|-------------|-------------------------|-------------------|
| **Acciones no autorizadas** | Generar etiquetas sin validar al usuario. | Tools simuladas; validación de `producto_id` en inventario. | Autenticación; validar `pedido_id` contra BD real. |
| **Sobrecarga de herramientas** | Llamadas repetitivas a `generar_etiqueta`. | `max_iterations=3` en el agente. | Rate limiting y logging JSONL. |
| **Pérdida de contexto** | Saltarse verificación de elegibilidad. | Prompt ReAct + `fallback_return_flow` ordenado. | Reglas hard-coded en la tool. |
| **Alucinaciones** | Inventar IDs o políticas. | RAG obligatorio; respuestas determinísticas por producto; prompt anti-invención. | Validar toda salida contra `datos/`. |
| **Respuestas evasivas** | “No puedo ayudarte” con contexto disponible. | Detección de evasión + fallback desde contexto. | Evaluación automática de calidad RAG. |

**Postura ética:** El agente actúa como asistente, no como decisor final. Toda acción debería ser revisable (logs) y la interfaz debe ofrecer contacto humano.

---

## 2. Limitaciones actuales

| Limitación | Impacto |
|------------|---------|
| **Datos estáticos** | Inventario y políticas en archivos locales, no en BD en tiempo real. |
| **Etiquetas simuladas** | URLs y códigos de seguimiento no son reales. |
| **Un solo modelo local** | Dependencia de Ollama; latencia en primera carga. |
| **Matching de productos por texto** | Nombres ambiguos pueden asociarse al producto incorrecto. |
| **Sin autenticación** | Cualquier usuario puede iniciar flujos de devolución. |

---

## 3. Monitoreo y observabilidad (propuesta)

Sistema recomendado para producción:

- **Logging JSONL** por llamada a herramienta (timestamp, args, resultado, usuario).
- **Métricas:** éxito/fallo por tool, latencia RAG vs. agente.
- **Alertas:** más de 5 fallos de la misma tool en 1 hora.
- **Dashboard** Streamlit restringido para administradores.

Ejemplo de log:

```json
{
  "timestamp": "2025-05-17T10:00:00",
  "tool": "verificar_elegibilidad",
  "args": {"producto_id": "PROD-005"},
  "result": {"elegible": false},
  "usuario": "anon",
  "ruta": "responder_devolucion_producto"
}
```

---

## 4. Mejoras implementadas en esta versión

1. **RAG primero** sobre `datos/` en todas las consultas de negocio.
2. **Router ampliado:** saludos, elegibilidad por producto, devolución activa, preguntas generales.
3. **Índice versionado** con reconstrucción automática.
4. **Productos enriquecidos** con política de devolución en el texto indexado.
5. **Fallback anti-evasión** cuando el LLM ignora el contexto.
6. **Carga diferida** de Ollama/Chroma para mejor experiencia en saludos.

---

## 5. Roadmap sugerido

| Prioridad | Mejora |
|-----------|--------|
| Alta | Logging de acciones del agente |
| Alta | Autenticación de usuario antes de generar etiquetas |
| Media | API REST en lugar de solo Streamlit |
| Media | Evaluación RAG (precisión/recall sobre casos de prueba) |
| Baja | Embeddings vía Ollama para evitar descarga de Hugging Face |
| Baja | Hybrid search (BM25 + vectores) para mejor retrieval |

---

## 6. Casos de prueba de referencia

Validar manualmente o con `test_agente.py`:

1. Saludo → bienvenida sin error.
2. Política de devoluciones → 30 días, exclusiones.
3. Semillas de albahaca → no elegible (PROD-005, Perecederos).
4. Devolución PROD-003 sin pedido → pide datos.
5. Devolución completa EM-904 + PROD-003 + dirección → etiqueta generada.

Estos casos cubren los tres caminos del router y las reglas de negocio definidas en `datos/`.
