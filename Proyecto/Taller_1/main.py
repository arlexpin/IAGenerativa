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