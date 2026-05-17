import csv
import os
import random
from datetime import datetime

# Ruta al inventario
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVENTARIO_PATH = os.path.join(BASE_DIR, "datos", "inventario_productos.csv")

def verificar_elegibilidad(producto_id: str, estado_producto: str = "sin usar") -> dict:
    """
    Verifica si un producto es elegible para devolución.
    Reglas:
    - Categorías no elegibles: Higiene personal (si está usado o abierto) y Perecederos (siempre no elegibles).
    - Para Higiene personal, solo se acepta si estado_producto es "sin abrir" o "nuevo".
    - Perecederos nunca son elegibles.
    - Otras categorías siempre elegibles (asumiendo dentro de 30 días).
    """
    try:
        with open(INVENTARIO_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["id"] == producto_id:
                    categoria = row["categoria"]
                    if categoria == "Perecederos":
                        return {"elegible": False, "razon": "Los productos perecederos no son elegibles para devolución por normas sanitarias."}
                    elif categoria == "Higiene personal":
                        if estado_producto.lower() in ["sin abrir", "nuevo", "sin usar"]:
                            return {"elegible": True, "razon": "Producto de higiene personal sin abrir. Puede devolverse."}
                        else:
                            return {"elegible": False, "razon": "Productos de higiene personal usados o abiertos no se aceptan por razones de salud."}
                    else:
                        return {"elegible": True, "razon": "Producto elegible para devolución."}
        return {"elegible": False, "razon": "Producto no encontrado en el inventario."}
    except Exception as e:
        return {"elegible": False, "razon": f"Error al verificar: {str(e)}"}

def generar_etiqueta_devolucion(pedido_id: str, producto_id: str, direccion_cliente: str) -> dict:
    """
    Simula la generación de una etiqueta de devolución.
    Devuelve un código de seguimiento y una URL simulada.
    """
    codigo = f"RET-{pedido_id}-{producto_id}-{datetime.now().strftime('%Y%m%d%H%M')}"
    etiqueta_url = f"https://api.ecomarket.co/labels/{codigo}.pdf"
    return {
        "etiqueta_url": etiqueta_url,
        "codigo_seguimiento": codigo,
        "mensaje": f"Etiqueta generada correctamente. Envíe el producto a nuestra bodega en Cali usando el código {codigo}."
    }