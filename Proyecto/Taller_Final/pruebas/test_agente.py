import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.agente_devoluciones import ejecutar_agente

casos_prueba = [
    "¿Cuál es la política de devoluciones?",
    "Quiero devolver el producto PROD-003, está sin usar.",
    "Mi pedido es EM-904, dirección Calle 123, devolver PROD-003",
    "¿Puedo devolver unas semillas de albahaca?",
    "Hola, ¿cómo estás?",
]

for pregunta in casos_prueba:
    print(f"\n--- Pregunta: {pregunta}")
    respuesta = ejecutar_agente(pregunta)
    print(f"Respuesta: {respuesta[:200]}...")