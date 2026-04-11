# Fase 3: Aplicación de Ingeniería de Prompts (Implementación)

En esta fase, aplicaremos la teoría de los "Chunks" y el "Overlapping" en instrucciones precisas para **Llama 3.1 8B**. El objetivo es que el modelo actúe como un motor de razonamiento lógico sobre nuestra base de datos local.

## 1. Estructura del Repositorio (Sugerida)
```
/EcoMarket-AI-Support
|-- FASE_1.md
|-- FASE_2.md
|-- /codigo
    |-- main.py              # Script de ejecución (Python + Ollama)
    |-- database.json        # Los 10 pedidos de prueba
    |-- prompt_templates.py   # Diccionario con los prompts optimizados
```
## 2. Base de Datos de Prueba

## 3. Ejercicio 1: Prompt de Solicitud de Pedido

**Técnica utilizada:** *Instruction Prompting + Grounding Local.*

**Prompt Maestro (System):**
> "Eres un experto en Customer Success de EcoMarket. Tu misión es informar el estado de los pedidos basándote EXCLUSIVAMENTE en el contexto proporcionado entre los delimitadores `### BASE_DATOS ###`. 

> **Reglas de oro:**
> 1. Si el pedido no existe, indica amablemente que no hay registro y escala a un humano.
> 2. Si el estado es 'Retrasado', ofrece una disculpa sincera y menciona el motivo del retraso.
> 3. No menciones datos de otros clientes.
> 4. Mantén un tono profesional, empático y ecológico."

**Prompt de Usuario (User):**
> "### BASE_DATOS ###
> {{database_json}}
> ### FIN_BASE_DATOS ###
> 
> Hola, necesito saber qué pasó con mi pedido número **{{tracking_id}}**. No me ha llegado y estoy preocupado."

## 4. Ejercicio 2: Prompt de Devolución de Producto
**Técnica utilizada:** *Few-Shot + Chain-of-Thought (Pensamiento en cadena).*

**Prompt de Sistema (System):**
> "Eres el Asesor de Devoluciones Sostenibles de EcoMarket. Debes clasificar las solicitudes de devolución según estas categorías:
> 
> - **Categoría A (Aprobada):** Ropa (si tiene etiquetas), Accesorios de madera/vidrio. Plazo: 15 días.
> - **Categoría B (Rechazada):** Higiene personal (cepillos usados, jabones abiertos), Perecederos (semillas, abonos abiertos).
> 
> **Procedimiento de Razonamiento:**
> 1. Analiza el producto y su categoría.
> 2. Verifica si compromete la higiene o si es perecedero.
> 3. Si es Rechazada: Explica con mucha empatía por qué la seguridad sanitaria y la sostenibilidad nos impiden aceptarlo. Ofrece una idea de compostaje o reutilización.
> 4. Si es Aprobada: Explica los pasos para el envío de regreso a nuestra sede."

**Prompt de Usuario (User):**
> "Quiero devolver este producto: **{{producto}}**. 
> Motivo: **{{motivo}}**.
> ¿Qué debo hacer?"

## 5. Implementación en Código 
```
import requests
import json
import os

def llamar_ollama(prompt, system_prompt):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "llama3.1:8b",
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "options": {"temperature": 0.1} # Baja temperatura para evitar alucinaciones
    }
    response = requests.post(url, json=data)
    response.raise_for_status()
    body = response.json()
    if 'error' in body:
        raise RuntimeError(f"Ollama error: {body['error']}")
    return body['response']

# Ejemplo de uso para Pedido
_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_dir, 'database.json'), 'r') as f:
    db = f.read()

id_a_buscar = "EM-904"
system_p = "Eres el asistente de EcoMarket. Solo usa la base de datos adjunta."
user_p = f"### BASE_DATOS ###\n{db}\n###\nEstado del pedido {id_a_buscar}?"

print(llamar_ollama(user_p, system_p))
```