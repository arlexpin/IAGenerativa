# Fase 2: Evaluación de Fortalezas, Limitaciones y Riesgos Éticos

## 1. Fortalezas de la Solución

- **Disponibilidad Inmediata (24/7):** El modelo se puede mantener activo. Para una empresa en crecimiento, pasar de una respuesta en 24 horas a una respuesta en milisegundos es una mejora experiencia del usuario.
- **Consistencia en la Narrativa de Marca:** Al ser un e-commerce de productos sostenibles, el modelo garantiza que el 100% de las respuestas mantengan el tono eco-consciente de la empresa, algo que a veces se pierde con los comerciales humanos.
- **Soberanía de Datos y Velocidad:** Gracias al despliegue del modelo con la **RTX 5090**, la latencia es mínima. Pero lo más importante: la información de los clientes no viaja a servidores extranjeros, lo que nos da una ventaja competitiva en seguridad y se puede utilizar como publicidad de marca.
- **Precisión mediante Overlapping:** Nuestra estrategia de solapamiento del 20% en la vectorización ayuda a asegura que el modelo recupere contextos completos, minimizando errores en la interpretación de políticas e información de la empresa.

## 2. Limitaciones Técnicas

- **La Barrera del 20% (Casos Complejos):** El modelo de 8B es excelente siguiendo instrucciones, pero carece de la "profundidad cognitiva" para resolver conflictos emocionales graves o problemas logísticos que no estén documentados. Si un cliente está furioso porque su pedido llegó roto para un regalo de hoy, el bot puede sonar frío o repetitivo, lo que nos indica que en el mediano plazo debamos buscar tecnología o algo que nos permita identificar estos casos.
- **Dependencia de la infraestructura (Hardware):** Tenemos un punto único de fallo. Si la RTX 5090 falla o si hay un corte de energía prolongado en nuestra sede sin respaldo suficiente, el soporte de EcoMarket desaparece, lo que nos indica que debamos buscar las formas de cerrar estas brechas o minimizar este riesgo.
- **Basura entra, Basura sale (GIGO):** Si el SQL de envíos tiene un error de digitación, el modelo propagará ese error con total "seguridad", informando estados de pedido incorrectos.

## 3. Riesgos Éticos y Mitigación

### A. Alucinaciones
El modelo podría "inventar" fechas de entrega para calmar al cliente.
- **Mitigación:** Implementamos un *Grounding* estricto. Si el dato no viene del SQL o de los chunks vectorizados, el modelo tiene prohibido especular. Usamos una temperatura de **0.1** para forzar respuestas deterministas.

### B. Sesgo Algorítmico y Cultural
Llama 3.1 fue entrenado mayoritariamente con datos en inglés y español neutro.
- **Riesgo:** Podría no entender modismos regionales o tratar de forma "preferencial" a quienes escriben con una gramática perfecta, discriminando involuntariamente otras formas de expresión.
- **Mitigación:** Auditoría semanal de logs de chat para ajustar el *System Prompt* y asegurar que el modelo sea inclusivo y entienda el contexto local colombiano. Esto sería una especie de feedback, pero tomaría tiempo poder hacer los ajustes en el modelo.

### C. Privacidad de Datos
Aunque los datos son locales, el riesgo de acceso interno no autorizado persiste.
- **Riesgo:** Uso de historial de compras sensible como contexto en los prompts.
- **Mitigación:** Capa de **Anonimización Dinámica (PII Masking)** antes de que el texto llegue al modelo. El modelo nunca "ve" el nombre real o la cédula, solo etiquetas como `[CLIENTE_ID]`.

### D. Impacto Laboral
- **Riesgo:** Que el equipo de soporte vea la IA como una amenaza a sus empleos.
- **Postura de EcoMarket:** El objetivo no es reducir nómina, sino **eliminar la carga operativa**. Queremos que nuestros agentes comerciales humanos dejen de copiar y pegar números de guía y se conviertan en "Especialistas en Éxito del Cliente", manejando solo los casos que requieren empatía y criterio humano.

## 4. Análisis de Confiabilidad Técnica

La confiabilidad de este sistema reside en la **Arquitectura RAG**. Al no confiar en el "conocimiento paramétrico" del modelo (lo que aprendió en su entrenamiento), sino en el "conocimiento de contexto" (lo que extraemos en tiempo real con overlapping).